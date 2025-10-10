#!/usr/bin/env python3
"""
Fantasy Cricket Platform - Backend API
=====================================
Enhanced with weekly points system and social team support
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from passlib.context import CryptContext
from enum import Enum
from jose import jwt
import uuid
import redis
import os
import logging
from celery import Celery
from celery.schedules import crontab

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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis client
redis_client = redis.from_url(REDIS_URL)

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

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    owned_leagues = relationship("League", back_populates="owner", foreign_keys="League.owner_id")
    leagues = relationship("League", secondary=user_league_association, back_populates="members")
    fantasy_teams = relationship("FantasyTeam", back_populates="owner")

class Club(Base):
    __tablename__ = 'clubs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False, default="Netherlands")
    cricket_board = Column(String(100), default="KNCB")
    board_club_id = Column(String(100))
    website_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    leagues = relationship("League", back_populates="club")
    teams = relationship("ClubTeam", back_populates="club")
    players = relationship("Player", back_populates="club")

class ClubTeam(Base):
    __tablename__ = 'club_teams'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    name = Column(String(255), nullable=False)
    level = Column(String(50), nullable=False)  # 1st, 2nd, 3rd, youth, social, etc.
    tier_type = Column(String(50), nullable=False, default="senior")
    multiplier = Column(Float, default=1.0)
    
    # Relationships
    club = relationship("Club", back_populates="teams")
    players = relationship("Player", back_populates="team")

class League(Base):
    __tablename__ = 'leagues'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # League settings
    season = Column(String(10), nullable=False, default="2025")
    invite_code = Column(String(10), unique=True, nullable=False, index=True)
    squad_size = Column(Integer, default=15)
    budget = Column(Float, default=500.0)
    currency = Column(String(5), default="EUR")
    
    # Constraints
    min_from_each_team = Column(Boolean, default=True)
    max_from_top_tier = Column(Integer, default=6)
    min_from_lower_tiers = Column(Integer, default=2)
    
    # Weekly update system
    weekly_update_day = Column(String(10), default='tuesday')
    weekly_update_time = Column(String(8), default='10:00')
    auto_updates_enabled = Column(Boolean, default=True)
    last_update_completed = Column(DateTime, nullable=True)
    
    # Points freeze system
    points_frozen = Column(Boolean, default=False)
    freeze_reason = Column(Text, nullable=True)
    frozen_at = Column(DateTime, nullable=True)
    frozen_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    draft_started = Column(Boolean, default=False)
    season_started = Column(Boolean, default=False)
    teams_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="leagues")
    owner = relationship("User", back_populates="owned_leagues", foreign_keys=[owner_id])
    members = relationship("User", secondary=user_league_association, back_populates="leagues")
    fantasy_teams = relationship("FantasyTeam", back_populates="league")
    weekly_updates = relationship("WeeklyUpdate", back_populates="league")

class WeeklyUpdate(Base):
    __tablename__ = 'weekly_updates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey('leagues.id'), nullable=False)
    
    scheduled_date = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    status = Column(String(20), default=UpdateStatus.PENDING.value)
    matches_processed = Column(Integer, default=0)
    players_updated = Column(Integer, default=0)
    teams_updated = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    triggered_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    auto_scheduled = Column(Boolean, default=True)
    
    update_summary = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="weekly_updates")
    triggered_by_user = relationship("User")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('club_teams.id'), nullable=True)
    
    name = Column(String(255), nullable=False, index=True)
    position = Column(String(50))
    
    # Career statistics
    matches_played = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    total_wickets = Column(Integer, default=0)
    total_catches = Column(Integer, default=0)
    average_runs = Column(Float, default=0.0)
    strike_rate = Column(Float, default=0.0)
    economy_rate = Column(Float, default=0.0)
    
    # Enhanced pricing system
    suggested_price = Column(Float, default=20.0)
    current_price = Column(Float, default=20.0)
    price_locked = Column(Boolean, default=False)
    price_justification = Column(Text)
    performance_score = Column(Float, default=1.0)
    league_rank_percentile = Column(Float)
    consistency_rating = Column(Float, default=1.0)
    admin_notes = Column(Text)
    manual_adjustments = Column(JSONB)
    
    # Fantasy data
    fantasy_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    form = Column(String(20), default='Average')
    
    is_available = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="players")
    team = relationship("ClubTeam", back_populates="players")
    fantasy_teams = relationship("FantasyTeam", secondary=team_player_association, back_populates="players")
    performances = relationship("PlayerPerformance", back_populates="player")
    price_history = relationship("PlayerPriceHistory", back_populates="player")

class PlayerPriceHistory(Base):
    __tablename__ = 'player_price_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey('players.id'), nullable=False)
    
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    change_reason = Column(String(50))
    justification = Column(Text)
    changed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="price_history")
    changed_by_user = relationship("User")

class FantasyTeam(Base):
    __tablename__ = 'fantasy_teams'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = Column(UUID(as_uuid=True), ForeignKey('leagues.id'), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    total_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    budget_used = Column(Float, default=0.0)
    
    is_complete = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="fantasy_teams")
    owner = relationship("User", back_populates="fantasy_teams")
    players = relationship("Player", secondary=team_player_association, back_populates="fantasy_teams")

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    
    date = Column(DateTime, nullable=False)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    format = Column(String(20))
    result = Column(String(500))
    home_score = Column(String(100))
    away_score = Column(String(100))
    
    match_url = Column(String(500))
    scorecard_parsed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    performances = relationship("PlayerPerformance", back_populates="match")

class PlayerPerformance(Base):
    __tablename__ = 'player_performances'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey('players.id'), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey('matches.id'), nullable=False)
    
    # Batting stats
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    
    # Bowling stats
    wickets = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    overs_bowled = Column(Float, default=0.0)
    maidens = Column(Integer, default=0)
    
    # Fielding stats
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    # Fantasy points
    total_fantasy_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="performances")
    match = relationship("Match", back_populates="performances")

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    
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
    team_name: str
    owner_name: str
    total_points: int
    weekly_points: int

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Fantasy Cricket Platform API",
    description="Amsterdam-based sustainable cricket fantasy platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc" 
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fantcric.fun",
        "https://www.fantcric.fun", 
        "https://api.fantcric.fun"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
from passlib.hash import pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

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
    except jwt.PyJWTError:
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

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/login")
async def login(email: EmailStr, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY,
        algorithm="HS256"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

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
    teams = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == league_id
    ).order_by(FantasyTeam.total_points.desc()).all()
    
    return [
        LeaderboardEntry(
            rank=rank,
            team_name=team.name,
            owner_name=team.owner.full_name,
            total_points=team.total_points,
            weekly_points=team.weekly_points
        )
        for rank, team in enumerate(teams, 1)
    ]

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

