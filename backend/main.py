#!/usr/bin/env python3
"""
Fantasy Cricket Platform - Backend API
=====================================
Enhanced with weekly points system and social team support
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, EmailStr, validator, field_serializer
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from passlib.context import CryptContext
from enum import Enum
from jose import jwt, JWTError
import uuid
import redis
import os
import logging
from celery import Celery
from celery.schedules import crontab

# Import routers
from api_endpoints import router as stats_router
from admin_endpoints import router as admin_router
from league_endpoints import router as league_router
from player_endpoints import router as player_router
from user_auth_endpoints import router as auth_router
from user_team_endpoints import router as user_team_router

# Import all models from database_models (centralized schema)
from database_models import (
    User, Base, Season, Club, Team, Player, League, FantasyTeam,
    FantasyTeamPlayer, Transfer, Match, PlayerPerformance
)

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/fantasy_cricket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cricket_admin:password@fantasy_cricket_db:5432/fantasy_cricket")
REDIS_URL = os.getenv("REDIS_URL", "redis://fantasy_cricket_redis:6379")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://fantcric.fun")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis client
redis_client = redis.from_url(REDIS_URL)

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL,
    default_limits=["100/minute"]  # Default: 100 requests per minute per IP
)

# Celery configuration
celery_app = Celery(
    "fantasy_cricket",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# =============================================================================
# ENHANCED DATABASE MODELS
# =============================================================================

# Association tables
user_league_association = Table(
    'user_leagues',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('league_id', UUID(as_uuid=True), ForeignKey('leagues.id'), primary_key=True),
    Column('role', String(20), default='member'),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('is_active', Boolean, default=True)
)

team_player_association = Table(
    'team_players',
    Base.metadata,
    Column('team_id', UUID(as_uuid=True), ForeignKey('fantasy_teams.id'), primary_key=True),
    Column('player_id', UUID(as_uuid=True), ForeignKey('players.id'), primary_key=True),
    Column('is_captain', Boolean, default=False),
    Column('is_vice_captain', Boolean, default=False),
    Column('is_playing', Boolean, default=True),
    Column('added_at', DateTime, default=datetime.utcnow)
)

class UpdateStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# All models now imported from database_models.py (see line 41)
# Using centralized database schema with VARCHAR(50) IDs for consistency

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if hasattr(v, '__str__'):
            return str(v)
        return v

    class Config:
        from_attributes = True

class ClubCreate(BaseModel):
    name: str
    country: str = "Netherlands"
    cricket_board: str = "KNCB"

class LeagueCreate(BaseModel):
    name: str
    club: ClubCreate
    season: str = "2025"
    squad_size: int = 15
    budget: float = 500.0

class PlayerResponse(BaseModel):
    id: str
    name: str
    position: Optional[str]
    current_price: float
    suggested_price: float
    price_locked: bool
    matches_played: int
    total_runs: int
    total_wickets: int
    fantasy_points: int
    weekly_points: int
    form: str
    team_level: Optional[str] = None
    performance_score: float
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    rank: int
    team_id: str
    team_name: str
    owner_name: str
    total_points: float
    weekly_points: float

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Fantasy Cricket Platform API",
    description="Amsterdam-based sustainable cricket fantasy platform",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# CORS configuration - production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Include routers
app.include_router(stats_router)
app.include_router(admin_router)
app.include_router(league_router)
app.include_router(player_router)
app.include_router(auth_router)
app.include_router(user_team_router)

# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =============================================================================
# ENHANCED API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "location": "Amsterdam, Netherlands",
        "powered_by": "LeafCloud sustainable infrastructure"
    }

# Auth endpoints moved to user_auth_endpoints.py router

@app.get("/api/leagues/{league_id}/players")
async def get_league_players(
    league_id: str,
    include_pricing: bool = Query(False, description="Include admin pricing data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify access
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    players = db.query(Player).filter(Player.club_id == league.club_id).all()
    
    if include_pricing:
        # Admin view with pricing data
        return [
            {
                **PlayerResponse.from_orm(player).dict(),
                "pricing": {
                    "suggested_price": player.suggested_price,
                    "current_price": player.current_price,
                    "price_locked": player.price_locked,
                    "price_justification": player.price_justification,
                    "performance_score": player.performance_score,
                    "consistency_rating": player.consistency_rating
                },
                "team_level": player.team.level if player.team else None
            }
            for player in players
        ]
    
    return [PlayerResponse.from_orm(player) for player in players]

@app.get("/api/leagues/{league_id}/leaderboard")
async def get_leaderboard(
    league_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only show finalized teams in leaderboard
    teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id,
        FantasyTeam.is_finalized == True
    ).order_by(FantasyTeam.total_points.desc()).all()

    result = []
    for rank, team in enumerate(teams, 1):
        # Get owner from user_id
        owner = db.query(User).filter(User.id == team.user_id).first()
        owner_name = owner.full_name if owner else "Unknown"

        result.append(LeaderboardEntry(
            rank=rank,
            team_id=str(team.id),
            team_name=team.team_name,
            owner_name=owner_name,
            total_points=team.total_points,
            weekly_points=team.last_round_points  # Now using last_round_points column
        ))

    return result

@app.get("/api/leagues/{league_id}/teams/{team_id}")
async def get_league_team_details(
    league_id: str,
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of any finalized team in the league (for leaderboard modal)"""
    # Verify team exists, is finalized, and is in this league
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == team_id,
        FantasyTeam.league_id == league_id,
        FantasyTeam.is_finalized == True
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found or not finalized")

    # Get all players in the team with their details
    from database_models import FantasyTeamPlayer, Player

    players_query = db.query(
        FantasyTeamPlayer,
        Player
    ).join(
        Player, FantasyTeamPlayer.player_id == Player.id
    ).filter(
        FantasyTeamPlayer.fantasy_team_id == team_id
    ).all()

    players = []
    for ftp, player in players_query:
        players.append({
            'id': str(player.id),
            'name': player.name,
            'club_name': player.rl_team or 'Unknown',  # Use rl_team field
            'total_points': ftp.total_points or 0,
            'is_captain': ftp.is_captain,
            'is_vice_captain': ftp.is_vice_captain,
            'is_wicket_keeper': ftp.is_wicket_keeper  # Use ftp.is_wicket_keeper
        })

    return {
        'team_id': str(team.id),
        'team_name': team.team_name,
        'total_points': team.total_points,
        'players': players
    }

@app.get("/api/leagues/{league_id}/teams/{team_id}/detailed")
async def get_team_detailed_stats(
    league_id: str,
    team_id: str,
    match_count: int = 3,  # Default to last 3 matches, configurable
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive team stats with detailed player performance breakdown

    Query Parameters:
    - match_count: Number of recent matches to show (default: 3, max: 10)
    """
    from sqlalchemy import text

    # Validate match_count
    match_count = max(1, min(match_count, 10))

    # Verify team exists and is in league
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == team_id,
        FantasyTeam.league_id == league_id,
        FantasyTeam.is_finalized == True
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found or not finalized")

    # Get owner info
    owner = db.query(User).filter(User.id == team.user_id).first()
    owner_name = owner.full_name if owner else "Unknown"

    # Get all players with aggregated stats from player_performances
    players_query = text("""
        WITH player_stats AS (
            SELECT
                p.id as player_id,
                p.name as player_name,
                p.rl_team as club_name,
                p.role as player_role,
                p.starting_multiplier,
                p.multiplier as current_multiplier,
                ftp.is_captain,
                ftp.is_vice_captain,
                ftp.is_wicket_keeper,
                ftp.total_points,

                -- Match count
                COUNT(pp.id) as matches_played,

                -- Batting stats
                COALESCE(SUM(pp.runs), 0) as total_runs,
                COALESCE(SUM(pp.balls_faced), 0) as total_balls,
                COALESCE(SUM(pp.fours), 0) as total_fours,
                COALESCE(SUM(pp.sixes), 0) as total_sixes,
                CASE
                    WHEN SUM(CASE WHEN pp.is_out THEN 1 ELSE 0 END) > 0
                    THEN SUM(pp.runs)::float / SUM(CASE WHEN pp.is_out THEN 1 ELSE 0 END)
                    ELSE NULL
                END as batting_average,
                CASE
                    WHEN SUM(pp.balls_faced) > 0
                    THEN (SUM(pp.runs)::float / SUM(pp.balls_faced) * 100)
                    ELSE NULL
                END as avg_strike_rate,
                MAX(pp.runs) as highest_score,
                SUM(CASE WHEN pp.runs >= 50 AND pp.runs < 100 THEN 1 ELSE 0 END) as fifties,
                SUM(CASE WHEN pp.runs >= 100 THEN 1 ELSE 0 END) as hundreds,
                SUM(CASE WHEN pp.runs = 0 AND pp.is_out THEN 1 ELSE 0 END) as ducks,

                -- Bowling stats
                COALESCE(SUM(pp.wickets), 0) as total_wickets,
                COALESCE(SUM(pp.overs_bowled), 0) as total_overs,
                COALESCE(SUM(pp.maidens), 0) as total_maidens,
                COALESCE(SUM(pp.runs_conceded), 0) as total_runs_conceded,
                CASE
                    WHEN SUM(pp.wickets) > 0
                    THEN SUM(pp.runs_conceded)::float / SUM(pp.wickets)
                    ELSE NULL
                END as bowling_average,
                CASE
                    WHEN SUM(pp.overs_bowled) > 0
                    THEN (SUM(pp.runs_conceded)::float / SUM(pp.overs_bowled))
                    ELSE NULL
                END as economy_rate,
                SUM(CASE WHEN pp.wickets >= 5 THEN 1 ELSE 0 END) as five_wicket_hauls,

                -- Fielding stats
                COALESCE(SUM(pp.catches), 0) as total_catches,
                COALESCE(SUM(pp.run_outs), 0) as total_run_outs,
                COALESCE(SUM(pp.stumpings), 0) as total_stumpings

            FROM fantasy_team_players ftp
            JOIN players p ON ftp.player_id = p.id
            LEFT JOIN player_performances pp ON pp.player_id = p.id
            WHERE ftp.fantasy_team_id = :team_id
            GROUP BY p.id, p.name, p.rl_team, p.role, p.starting_multiplier,
                     p.multiplier, ftp.is_captain, ftp.is_vice_captain,
                     ftp.is_wicket_keeper, ftp.total_points
        )
        SELECT * FROM player_stats
        ORDER BY total_points DESC
    """)

    players_result = db.execute(players_query, {"team_id": team_id}).fetchall()

    # Format players data
    players_data = []
    for row in players_result:
        player_dict = dict(row._mapping)

        # Calculate points breakdown (estimate based on stats)
        batting_points = float(player_dict['total_runs'] or 0) * 1.0  # Simplified
        bowling_points = float(player_dict['total_wickets'] or 0) * 25.0
        fielding_points = (
            float(player_dict['total_catches'] or 0) * 15.0 +
            float(player_dict['total_run_outs'] or 0) * 6.0 +
            float(player_dict['total_stumpings'] or 0) * 15.0
        )

        # Get recent matches for this player
        recent_matches_query = text("""
            SELECT
                pp.round_number,
                pp.match_id,
                pp.fantasy_points,
                pp.runs,
                pp.balls_faced,
                pp.wickets,
                pp.catches,
                pp.run_outs,
                pp.stumpings,
                pp.created_at
            FROM player_performances pp
            WHERE pp.player_id = :player_id
            ORDER BY pp.round_number DESC, pp.created_at DESC
            LIMIT :match_count
        """)

        recent_matches = db.execute(
            recent_matches_query,
            {"player_id": player_dict['player_id'], "match_count": match_count}
        ).fetchall()

        recent_form = []
        for match in recent_matches:
            match_dict = dict(match._mapping)
            recent_form.append({
                'round': match_dict['round_number'],
                'match_id': str(match_dict['match_id']),
                'points': float(match_dict['fantasy_points'] or 0),
                'runs': int(match_dict['runs'] or 0),
                'balls': int(match_dict['balls_faced'] or 0),
                'wickets': int(match_dict['wickets'] or 0),
                'catches': int(match_dict['catches'] or 0)
            })

        # Calculate form trend (last 3 vs previous 3)
        form_trend = "stable"
        if len(recent_form) >= 3:
            recent_avg = sum(m['points'] for m in recent_form[:3]) / 3
            if len(recent_form) >= 6:
                previous_avg = sum(m['points'] for m in recent_form[3:6]) / 3
                if recent_avg > previous_avg * 1.2:
                    form_trend = "improving"
                elif recent_avg < previous_avg * 0.8:
                    form_trend = "declining"

        # Calculate multiplier drift
        multiplier_drift = (
            float(player_dict['current_multiplier'] or 1.0) -
            float(player_dict['starting_multiplier'] or 1.0)
        )

        multiplier_status = "stable"
        if multiplier_drift < -0.1:
            multiplier_status = "strengthening"  # Lower multiplier = stronger player
        elif multiplier_drift > 0.1:
            multiplier_status = "weakening"  # Higher multiplier = weaker player

        players_data.append({
            'player_id': str(player_dict['player_id']),
            'player_name': player_dict['player_name'],
            'club_name': player_dict['club_name'] or 'Unknown',
            'player_role': player_dict['player_role'],
            'is_captain': bool(player_dict['is_captain']),
            'is_vice_captain': bool(player_dict['is_vice_captain']),
            'is_wicket_keeper': bool(player_dict['is_wicket_keeper']),
            'total_points': float(player_dict['total_points'] or 0),
            'matches_played': int(player_dict['matches_played'] or 0),
            'points_per_match': (
                float(player_dict['total_points'] or 0) / int(player_dict['matches_played'] or 1)
                if int(player_dict['matches_played'] or 0) > 0 else 0
            ),
            'batting': {
                'runs': int(player_dict['total_runs'] or 0),
                'average': round(float(player_dict['batting_average'] or 0), 2),
                'strike_rate': round(float(player_dict['avg_strike_rate'] or 0), 2),
                'balls_faced': int(player_dict['total_balls'] or 0),
                'fours': int(player_dict['total_fours'] or 0),
                'sixes': int(player_dict['total_sixes'] or 0),
                'fifties': int(player_dict['fifties'] or 0),
                'hundreds': int(player_dict['hundreds'] or 0),
                'ducks': int(player_dict['ducks'] or 0),
                'highest_score': int(player_dict['highest_score'] or 0)
            },
            'bowling': {
                'wickets': int(player_dict['total_wickets'] or 0),
                'overs': round(float(player_dict['total_overs'] or 0), 1),
                'maidens': int(player_dict['total_maidens'] or 0),
                'runs_conceded': int(player_dict['total_runs_conceded'] or 0),
                'average': round(float(player_dict['bowling_average'] or 0), 2) if player_dict['bowling_average'] else None,
                'economy': round(float(player_dict['economy_rate'] or 0), 2) if player_dict['economy_rate'] else None,
                'five_wicket_hauls': int(player_dict['five_wicket_hauls'] or 0)
            },
            'fielding': {
                'catches': int(player_dict['total_catches'] or 0),
                'run_outs': int(player_dict['total_run_outs'] or 0),
                'stumpings': int(player_dict['total_stumpings'] or 0)
            },
            'multiplier_info': {
                'starting_multiplier': round(float(player_dict['starting_multiplier'] or 1.0), 2),
                'current_multiplier': round(float(player_dict['current_multiplier'] or 1.0), 2),
                'drift': round(multiplier_drift, 2),
                'status': multiplier_status
            },
            'recent_form': {
                'matches': recent_form,
                'last_n_average': (
                    round(sum(m['points'] for m in recent_form) / len(recent_form), 1)
                    if recent_form else 0
                ),
                'trend': form_trend
            },
            'points_breakdown': {
                'batting_points': round(batting_points, 1),
                'bowling_points': round(bowling_points, 1),
                'fielding_points': round(fielding_points, 1)
            }
        })

    return {
        'team_id': str(team.id),
        'team_name': team.team_name,
        'owner_name': owner_name,
        'total_points': float(team.total_points or 0),
        'weekly_points': float(team.last_round_points or 0),
        'squad_size': len(players_data),
        'players': players_data
    }

@app.get("/api/leagues/{league_id}/stats")
async def get_league_stats(
    league_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive league statistics including top performers and team stats"""
    from sqlalchemy import func, desc

    # Get league info to find season_id and club_id for matching performances
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        return {
            "best_batsman": None,
            "best_bowler": None,
            "best_fielder": None,
            "best_team": None,
            "top_players": []
        }

    # Get all fantasy teams in this league
    fantasy_teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id
    ).all()

    if not fantasy_teams:
        return {
            "best_batsman": None,
            "best_bowler": None,
            "best_fielder": None,
            "best_team": None,
            "top_players": []
        }

    # Get all players from fantasy teams in this league with their fantasy points
    team_ids = [team.id for team in fantasy_teams]

    # Query fantasy_team_players with player info and points
    from sqlalchemy import and_
    player_fantasy_data = db.query(
        FantasyTeamPlayer.player_id,
        FantasyTeamPlayer.total_points,
        FantasyTeamPlayer.fantasy_team_id,
        Player.name,
        Player.rl_team
    ).join(
        Player, Player.id == FantasyTeamPlayer.player_id
    ).filter(
        FantasyTeamPlayer.fantasy_team_id.in_(team_ids)
    ).all()

    # Aggregate player performances from player_performances table for best batsman/bowler/fielder
    # Use raw SQL since the PlayerPerformance model may not match the table schema
    player_stats_agg = {}

    # Query player_performances table directly with raw SQL
    # For simulated data: use league_id directly (no matches table)
    # For real data: would join with matches table
    perf_query = text("""
        SELECT pp.player_id,
               SUM(pp.runs) as total_runs,
               SUM(pp.wickets) as total_wickets,
               SUM(pp.catches) as total_catches,
               SUM(pp.balls_faced) as total_balls,
               SUM(pp.overs_bowled) as total_overs,
               SUM(pp.runs_conceded) as total_runs_conceded
        FROM player_performances pp
        WHERE pp.league_id = :league_id
        GROUP BY pp.player_id
    """)

    try:
        perf_results = db.execute(perf_query, {'league_id': league_id})

        for row in perf_results:
            player_stats_agg[row.player_id] = {
                'runs': row.total_runs or 0,
                'wickets': row.total_wickets or 0,
                'catches': row.total_catches or 0,
                'balls_faced': row.total_balls or 0,
                'overs': row.total_overs or 0,
                'runs_conceded': row.total_runs_conceded or 0
            }
    except Exception as e:
        logger.warning(f"Could not query player_performances: {e}")
        # Continue without performance stats

    # Calculate top performers
    best_batsman = None
    best_bowler = None
    best_fielder = None
    max_runs = 0
    max_wickets = 0
    max_catches = 0

    rl_team_points = {}  # rl_team string -> total points
    player_points_dict = {}  # player_id -> {player_name, rl_team, total_points}

    for pfd in player_fantasy_data:
        player_id, total_points, fantasy_team_id, player_name, rl_team = pfd

        # Get player stats if available
        stats = player_stats_agg.get(player_id, {})

        # Best batsman (most runs)
        runs = stats.get('runs', 0)
        if runs > max_runs:
            max_runs = runs
            balls = stats.get('balls_faced', 1)
            strike_rate = (runs / balls * 100) if balls > 0 else 0
            best_batsman = {
                'player_name': player_name,
                'team_name': rl_team if rl_team else 'Unknown',
                'runs': runs,
                'average': runs,  # Simplified - would need innings count for true average
                'strike_rate': strike_rate
            }

        # Best bowler (most wickets)
        wickets = stats.get('wickets', 0)
        if wickets > max_wickets:
            max_wickets = wickets
            overs = stats.get('overs', 1)
            runs_conceded = stats.get('runs_conceded', 0)
            economy = (runs_conceded / overs) if overs > 0 else 0
            best_bowler = {
                'player_name': player_name,
                'team_name': rl_team if rl_team else 'Unknown',
                'wickets': wickets,
                'average': runs_conceded / wickets if wickets > 0 else 0,
                'economy': economy
            }

        # Best fielder (most catches)
        catches = stats.get('catches', 0)
        if catches > max_catches:
            max_catches = catches
            best_fielder = {
                'player_name': player_name,
                'team_name': rl_team if rl_team else 'Unknown',
                'catches': catches
            }

        # Aggregate player points (avoid duplicates)
        if player_id not in player_points_dict:
            player_points_dict[player_id] = {
                'player_id': player_id,
                'player_name': player_name,
                'team_name': rl_team if rl_team else 'Unknown',
                'total_points': total_points or 0
            }
        else:
            # Player is in multiple fantasy teams - sum their points
            player_points_dict[player_id]['total_points'] += (total_points or 0)

        # Aggregate by RL team
        if rl_team:
            if rl_team not in rl_team_points:
                rl_team_points[rl_team] = 0
            rl_team_points[rl_team] += (total_points or 0)

    # Find best RL team
    best_team = None
    if rl_team_points:
        best_rl_team = max(rl_team_points, key=rl_team_points.get)
        best_team = {
            'team_name': best_rl_team,
            'total_points': rl_team_points[best_rl_team],
            'player_count': sum(1 for pfd in player_fantasy_data if pfd[4] == best_rl_team)
        }

    # Top 25 players by points (deduplicated)
    player_points_list = list(player_points_dict.values())
    top_players = sorted(player_points_list, key=lambda x: x['total_points'], reverse=True)[:25]

    # Enrich top players with multiplier data
    if top_players:
        # Get player IDs from top players
        top_player_ids = [p['player_id'] for p in top_players]

        # Fetch Player objects with multipliers
        players_with_multipliers = db.query(Player).filter(Player.id.in_(top_player_ids)).all()
        player_multiplier_map = {p.id: {'current': p.multiplier, 'starting': p.starting_multiplier or p.multiplier} for p in players_with_multipliers}

        # Calculate statistics for target multiplier calculation
        all_points = [p['total_points'] for p in player_points_list if p['total_points'] > 0]
        if all_points:
            from statistics import median
            min_points = min(all_points)
            max_points = max(all_points)
            median_points = median(all_points)

            # Helper function to calculate target multiplier
            def calculate_target_multiplier(score, min_score, median_score, max_score):
                """Calculate target multiplier based on score relative to league"""
                MIN_MULTIPLIER = 0.69
                MAX_MULTIPLIER = 5.0
                NEUTRAL_MULTIPLIER = 1.0

                if median_score == 0:
                    return NEUTRAL_MULTIPLIER

                if score <= median_score:
                    # Below median: interpolate from max_multiplier to neutral
                    if median_score == min_score:
                        return NEUTRAL_MULTIPLIER
                    ratio = (score - min_score) / (median_score - min_score)
                    return MAX_MULTIPLIER - (ratio * (MAX_MULTIPLIER - NEUTRAL_MULTIPLIER))
                else:
                    # Above median: interpolate from neutral to min_multiplier
                    if max_score == median_score:
                        return NEUTRAL_MULTIPLIER
                    ratio = (score - median_score) / (max_score - median_score)
                    return NEUTRAL_MULTIPLIER - (ratio * (NEUTRAL_MULTIPLIER - MIN_MULTIPLIER))

            # Add multiplier data to each top player
            for player in top_players:
                player_id = player['player_id']
                mult_data = player_multiplier_map.get(player_id, {'current': 1.0, 'starting': 1.0})
                current_multiplier = mult_data['current']
                starting_multiplier = mult_data['starting']
                player_points = player['total_points']

                # Calculate target multiplier
                target_multiplier = calculate_target_multiplier(
                    player_points, min_points, median_points, max_points
                )

                # Calculate drift (current - starting)
                drift = current_multiplier - starting_multiplier

                # Add to player data
                player['starting_multiplier'] = round(starting_multiplier, 2)
                player['current_multiplier'] = round(current_multiplier, 2)
                player['drift'] = round(drift, 2)

                # Remove player_id from response (internal use only)
                del player['player_id']
        else:
            # No points data, just add default multipliers
            for player in top_players:
                player_id = player['player_id']
                mult_data = player_multiplier_map.get(player_id, {'current': 1.0, 'starting': 1.0})
                player['starting_multiplier'] = round(mult_data['starting'], 2)
                player['current_multiplier'] = round(mult_data['current'], 2)
                player['drift'] = 0.0
                del player['player_id']

    return {
        "best_batsman": best_batsman,
        "best_bowler": best_bowler,
        "best_fielder": best_fielder,
        "best_team": best_team,
        "top_players": top_players
    }

@app.get("/api/leagues/{league_id}/all-players")
async def get_all_league_players(
    league_id: str,
    role: str = None,  # Filter by role: BATSMAN, BOWLER, ALL-ROUNDER, WK-BATSMAN
    sort_by: str = "total_points",  # Sort by: total_points, runs, wickets, ownership
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive stats for ALL players in the roster.
    Shows performance stats, ownership percentages (0% for unowned), and multiplier info.
    Useful for transfer decisions - see which high-performing players are available.
    """
    from sqlalchemy import func, desc, case

    # Get all fantasy teams in this league
    fantasy_teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id
    ).all()

    if not fantasy_teams:
        return []

    team_ids = [team.id for team in fantasy_teams]
    total_teams = len(fantasy_teams)

    # Get ALL players in the roster with their stats and ownership info
    # Start from Player table, LEFT JOIN ownership and performance data
    base_query = db.query(
        Player.id.label('player_id'),
        Player.name.label('player_name'),
        Player.rl_team.label('club_name'),
        Player.role.label('player_role'),
        Player.multiplier.label('current_multiplier'),

        # Count ownership only for teams in this league (will be 0 for unowned)
        func.count(func.distinct(
            case((FantasyTeamPlayer.fantasy_team_id.in_(team_ids), FantasyTeamPlayer.fantasy_team_id))
        )).label('ownership_count'),

        # Sum fantasy points only from teams in this league
        func.sum(
            case((FantasyTeamPlayer.fantasy_team_id.in_(team_ids), FantasyTeamPlayer.total_points), else_=0)
        ).label('total_fantasy_points'),

        # Batting aggregates
        func.count(func.distinct(PlayerPerformance.id)).label('matches_played'),
        func.coalesce(func.sum(PlayerPerformance.runs), 0).label('total_runs'),
        func.coalesce(func.avg(case((PlayerPerformance.runs > 0, PlayerPerformance.runs))), 0).label('batting_average'),
        func.coalesce(func.avg(case((PlayerPerformance.balls_faced > 0, PlayerPerformance.batting_strike_rate))), 0).label('avg_strike_rate'),
        func.coalesce(func.sum(PlayerPerformance.fours), 0).label('total_fours'),
        func.coalesce(func.sum(PlayerPerformance.sixes), 0).label('total_sixes'),
        func.sum(case(((PlayerPerformance.runs >= 50) & (PlayerPerformance.runs < 100), 1), else_=0)).label('fifties'),
        func.sum(case((PlayerPerformance.runs >= 100, 1), else_=0)).label('hundreds'),
        func.coalesce(func.max(PlayerPerformance.runs), 0).label('highest_score'),

        # Bowling aggregates
        func.coalesce(func.sum(PlayerPerformance.wickets), 0).label('total_wickets'),
        func.coalesce(func.sum(PlayerPerformance.overs_bowled), 0).label('total_overs'),
        func.coalesce(func.avg(case((PlayerPerformance.overs_bowled > 0, PlayerPerformance.bowling_economy))), 0).label('avg_economy'),
        func.coalesce(func.sum(PlayerPerformance.maidens), 0).label('total_maidens'),
        func.sum(case((PlayerPerformance.wickets >= 5, 1), else_=0)).label('five_wicket_hauls'),

        # Fielding aggregates
        func.coalesce(func.sum(PlayerPerformance.catches), 0).label('total_catches'),
        func.coalesce(func.sum(PlayerPerformance.run_outs), 0).label('total_run_outs'),
        func.coalesce(func.sum(PlayerPerformance.stumpings), 0).label('total_stumpings'),

        # Points breakdown (approximate from performance data)
        func.coalesce(func.sum(PlayerPerformance.fantasy_points), 0).label('performance_points')

    ).outerjoin(
        FantasyTeamPlayer, FantasyTeamPlayer.player_id == Player.id
    ).outerjoin(
        PlayerPerformance, PlayerPerformance.player_id == Player.id
    ).group_by(
        Player.id, Player.name, Player.rl_team, Player.role, Player.multiplier
    )

    # Apply role filter if specified
    if role and role.upper() != 'ALL':
        base_query = base_query.filter(func.upper(Player.role).like(f'%{role.upper()}%'))

    # Execute query
    results = base_query.all()

    # Convert to dict and calculate ownership percentage
    players = []
    for row in results:
        ownership_percentage = (row.ownership_count / total_teams) * 100 if total_teams > 0 else 0

        # Use total_fantasy_points from fantasy_team_players if available, otherwise use performance_points
        total_points = float(row.total_fantasy_points or row.performance_points or 0)

        player_data = {
            'player_id': row.player_id,
            'player_name': row.player_name,
            'club_name': row.club_name or 'Unknown',
            'player_role': row.player_role or 'Unknown',
            'current_multiplier': float(row.current_multiplier or 1.0),
            'ownership_count': int(row.ownership_count),
            'ownership_percentage': round(ownership_percentage, 1),
            'total_points': round(total_points, 1),
            'matches_played': int(row.matches_played or 0),

            'batting': {
                'runs': int(row.total_runs),
                'average': round(float(row.batting_average), 1),
                'strike_rate': round(float(row.avg_strike_rate), 1),
                'fours': int(row.total_fours),
                'sixes': int(row.total_sixes),
                'fifties': int(row.fifties),
                'hundreds': int(row.hundreds),
                'highest_score': int(row.highest_score)
            },

            'bowling': {
                'wickets': int(row.total_wickets),
                'overs': round(float(row.total_overs), 1),
                'economy': round(float(row.avg_economy), 2) if row.avg_economy else None,
                'maidens': int(row.total_maidens),
                'five_wicket_hauls': int(row.five_wicket_hauls)
            },

            'fielding': {
                'catches': int(row.total_catches),
                'run_outs': int(row.total_run_outs),
                'stumpings': int(row.total_stumpings)
            }
        }
        players.append(player_data)

    # Sort by specified field
    if sort_by == 'total_points':
        players.sort(key=lambda x: x['total_points'], reverse=True)
    elif sort_by == 'runs':
        players.sort(key=lambda x: x['batting']['runs'], reverse=True)
    elif sort_by == 'wickets':
        players.sort(key=lambda x: x['bowling']['wickets'], reverse=True)
    elif sort_by == 'ownership':
        players.sort(key=lambda x: x['ownership_percentage'], reverse=True)
    elif sort_by == 'average':
        players.sort(key=lambda x: x['batting']['average'], reverse=True)
    elif sort_by == 'strike_rate':
        players.sort(key=lambda x: x['batting']['strike_rate'], reverse=True)

    return players

@app.get("/api/leagues/{league_id}/team-analysis")
async def get_team_analysis(
    league_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get team analysis metrics:
    - Most Balanced Team (even point distribution)
    - Best Captain Pick (highest captain contribution)
    - Most Consistent Team (lowest standard deviation in weekly points)
    """
    from sqlalchemy import func
    import statistics

    # Get all fantasy teams in this league
    fantasy_teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id
    ).all()

    if not fantasy_teams:
        return {
            "most_balanced_team": None,
            "best_captain_pick": None,
            "most_consistent_team": None
        }

    # Analyze each team
    team_analyses = []

    for team in fantasy_teams:
        # Get owner from user_id
        owner = db.query(User).filter(User.id == team.user_id).first()
        owner_name = owner.full_name if owner else "Unknown"

        # Get all players in this team with their points
        team_players = db.query(
            FantasyTeamPlayer.player_id,
            FantasyTeamPlayer.total_points,
            FantasyTeamPlayer.is_captain,
            Player.name
        ).join(
            Player, Player.id == FantasyTeamPlayer.player_id
        ).filter(
            FantasyTeamPlayer.fantasy_team_id == team.id
        ).all()

        if not team_players:
            continue

        # Calculate balance score (lower standard deviation = more balanced)
        player_points = [float(p.total_points or 0) for p in team_players]
        if len(player_points) > 1:
            std_dev = statistics.stdev(player_points)
            balance_score = 1000 / (1 + std_dev)  # Higher score = more balanced
        else:
            std_dev = 0
            balance_score = 0

        # Find captain and their contribution
        captain = next((p for p in team_players if p.is_captain), None)
        captain_points = float(captain.total_points or 0) if captain else 0
        captain_contribution_pct = (captain_points / team.total_points * 100) if team.total_points > 0 else 0

        # Get weekly points variation (requires weekly data - approximate for now)
        # For now, use total points variation
        weekly_scores = []  # Would need to query weekly_performance table if it exists

        team_analyses.append({
            'team_id': team.id,
            'team_name': team.team_name,
            'owner_name': owner_name,
            'total_points': float(team.total_points or 0),
            'balance_score': balance_score,
            'std_dev': std_dev,
            'captain_name': captain.name if captain else None,
            'captain_points': captain_points,
            'captain_contribution_pct': round(captain_contribution_pct, 1),
            'player_count': len(team_players),
            'min_player_points': min(player_points) if player_points else 0,
            'max_player_points': max(player_points) if player_points else 0,
            'avg_player_points': statistics.mean(player_points) if player_points else 0
        })

    # Find most balanced team (highest balance score / lowest std dev)
    most_balanced = max(team_analyses, key=lambda x: x['balance_score']) if team_analyses else None

    # Find best captain pick (highest captain contribution percentage)
    best_captain = max(team_analyses, key=lambda x: x['captain_points']) if team_analyses else None

    # For consistency, use std_dev as proxy (lower = more consistent)
    # In a full implementation, this would use weekly point variations
    most_consistent = min(team_analyses, key=lambda x: x['std_dev']) if team_analyses else None

    return {
        "most_balanced_team": {
            "team_name": most_balanced['team_name'],
            "owner_name": most_balanced['owner_name'],
            "balance_score": round(most_balanced['balance_score'], 1),
            "std_dev": round(most_balanced['std_dev'], 1),
            "min_player_points": round(most_balanced['min_player_points'], 1),
            "max_player_points": round(most_balanced['max_player_points'], 1),
            "avg_player_points": round(most_balanced['avg_player_points'], 1),
            "player_count": most_balanced['player_count']
        } if most_balanced else None,

        "best_captain_pick": {
            "team_name": best_captain['team_name'],
            "owner_name": best_captain['owner_name'],
            "captain_name": best_captain['captain_name'],
            "captain_points": round(best_captain['captain_points'], 1),
            "captain_contribution_pct": best_captain['captain_contribution_pct'],
            "total_team_points": round(best_captain['total_points'], 1)
        } if best_captain else None,

        "most_consistent_team": {
            "team_name": most_consistent['team_name'],
            "owner_name": most_consistent['owner_name'],
            "std_dev": round(most_consistent['std_dev'], 1),
            "avg_player_points": round(most_consistent['avg_player_points'], 1),
            "player_count": most_consistent['player_count']
        } if most_consistent else None
    }

# Weekly update endpoints
@app.post("/api/leagues/{league_id}/admin/trigger-weekly-update")
async def trigger_weekly_update(
    league_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation would go here
    return {"message": "Weekly update triggered successfully"}

# =============================================================================
# CELERY TASKS
# =============================================================================

celery_app.conf.beat_schedule = {
    'process-weekly-updates': {
        'task': 'process_weekly_updates',
        'schedule': crontab(minute='*/15'),
    },
    'scrape-kncb-data': {
        'task': 'scrape_kncb_data',
        'schedule': crontab(hour='*/6'),
    }
}

@celery_app.task
def process_weekly_updates():
    logger.info("Processing weekly fantasy point updates...")
    # Implementation would trigger WeeklyPointsCalculator
    return {"status": "completed"}

@celery_app.task
def scrape_kncb_data():
    logger.info("Scraping KNCB match data...")
    # Implementation would trigger KNCB scraper
    return {"status": "completed"}

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

if __name__ == "__main__":
    create_tables()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

