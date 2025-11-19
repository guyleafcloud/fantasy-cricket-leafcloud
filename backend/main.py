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
            weekly_points=0  # Field not available in current schema
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
    from database_models import FantasyTeamPlayer, Player, Team

    players_query = db.query(
        FantasyTeamPlayer,
        Player,
        Team.name.label('team_name')
    ).join(
        Player, FantasyTeamPlayer.player_id == Player.id
    ).outerjoin(
        Team, Player.team_id == Team.id
    ).filter(
        FantasyTeamPlayer.fantasy_team_id == team_id
    ).all()

    players = []
    for ftp, player, team_name in players_query:
        players.append({
            'id': str(player.id),
            'name': player.name,
            'club_name': team_name or 'Unknown',
            'total_points': ftp.total_points or 0,
            'is_captain': ftp.is_captain,
            'is_vice_captain': ftp.is_vice_captain,
            'is_wicket_keeper': player.is_wicket_keeper
        })

    return {
        'team_id': str(team.id),
        'team_name': team.team_name,
        'total_points': team.total_points,
        'players': players
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

    return {
        "best_batsman": best_batsman,
        "best_bowler": best_bowler,
        "best_fielder": best_fielder,
        "best_team": best_team,
        "top_players": top_players
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

