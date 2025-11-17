#!/usr/bin/env python3
"""
Database Models for Fantasy Cricket Platform
============================================
SQLAlchemy models for seasons, clubs, teams, players, leagues, and fantasy teams.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a unique ID"""
    return str(uuid.uuid4())


# =============================================================================
# USER MANAGEMENT
# =============================================================================

class User(Base):
    """
    User account for authentication and admin access
    """
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)

    # Status flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
    )


# =============================================================================
# SEASON & CLUB MANAGEMENT
# =============================================================================

class Season(Base):
    """
    Cricket season (e.g., 2026)
    Only one season can be active at a time.
    """
    __tablename__ = "seasons"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    year = Column(String(10), nullable=False, unique=True)  # "2026"
    name = Column(String(100), nullable=False)  # "Topklasse 2026"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)

    # Status flags
    is_active = Column(Boolean, default=False)  # Only one can be active
    registration_open = Column(Boolean, default=False)
    scraping_enabled = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=True)  # Admin user ID

    # Relationships
    clubs = relationship("Club", back_populates="season", cascade="all, delete-orphan")
    leagues = relationship("League", back_populates="season", cascade="all, delete-orphan")


class Club(Base):
    """
    Cricket club (e.g., ACC, VRA)
    """
    __tablename__ = "clubs"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)  # "ACC"
    tier = Column(String(50), nullable=False)  # HOOFDKLASSE, etc.
    location = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    season_id = Column(String(50), ForeignKey("seasons.id"), nullable=True)

    # Relationships
    season = relationship("Season", back_populates="clubs")
    teams = relationship("Team", back_populates="club", cascade="all, delete-orphan")
    players = relationship("Player", back_populates="club", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_clubs_season_id', 'season_id'),
    )


class Team(Base):
    """
    Team within a club (e.g., ACC 1st, ACC 2nd)
    """
    __tablename__ = "teams"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    club_id = Column(String(50), ForeignKey("clubs.id"), nullable=False)

    # Team info
    name = Column(String(100), nullable=False)  # "ACC 1"
    level = Column(String(20), nullable=False)  # "1st", "2nd", "3rd", "social"
    tier_type = Column(String(50), default="senior")  # senior, youth, women

    # Fantasy multipliers
    value_multiplier = Column(Float, default=1.0)  # For player values (1st=1.0, 2nd=1.1, etc.)
    points_multiplier = Column(Float, default=1.0)  # For fantasy points

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="teams")

    # Unique constraint: one team level per club
    __table_args__ = (
        UniqueConstraint('club_id', 'level', name='uq_club_team_level'),
        Index('idx_team_club', 'club_id'),
    )


# =============================================================================
# PLAYER MANAGEMENT
# =============================================================================

class Player(Base):
    """
    Cricket player with season statistics and fantasy value
    """
    __tablename__ = "players"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    club_id = Column(String(50), ForeignKey("clubs.id"), nullable=False)

    # Real-life team assignment (e.g., "ACC 1", "ACC ZAMI", "U17")
    rl_team = Column(String(50), nullable=True)

    role = Column(String(50), nullable=False)  # BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER
    tier = Column(String(50), nullable=False)  # HOOFDKLASSE, etc. (only used for web scraping)

    # Pricing
    base_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False)

    # Performance multiplier (lower = better historical performance)
    multiplier = Column(Float, default=1.0, nullable=True)
    multiplier_updated_at = Column(DateTime, nullable=True)

    # Season statistics
    matches_played = Column(Integer, nullable=True)
    runs_scored = Column(Integer, nullable=True)
    balls_faced = Column(Integer, nullable=True)
    wickets_taken = Column(Integer, nullable=True)
    balls_bowled = Column(Integer, nullable=True)
    catches = Column(Integer, nullable=True)
    stumpings = Column(Integer, nullable=True)
    batting_average = Column(Float, nullable=True)
    strike_rate = Column(Float, nullable=True)
    bowling_average = Column(Float, nullable=True)
    economy_rate = Column(Float, nullable=True)
    total_fantasy_points = Column(Float, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="players")
    fantasy_team_players = relationship("FantasyTeamPlayer", back_populates="player", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_player_club', 'club_id'),
    )


class PlayerPriceHistory(Base):
    """
    Track player value changes over time
    """
    __tablename__ = "player_price_history"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    player_id = Column(String(50), ForeignKey("players.id"), nullable=False)

    # Price change
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    change_reason = Column(String(50), nullable=False)  # "calculated", "manual", "performance"
    reason_details = Column(Text, nullable=True)

    # Metadata
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(50), nullable=True)  # Admin user ID if manual

    # Relationships
    player = relationship("Player")

    # Indexes
    __table_args__ = (
        Index('idx_price_history_player', 'player_id'),
        Index('idx_price_history_date', 'changed_at'),
    )


# =============================================================================
# LEAGUE & FANTASY TEAM MANAGEMENT
# =============================================================================

class League(Base):
    """
    Fantasy league (group of users competing)
    """
    __tablename__ = "leagues"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    season_id = Column(String(50), ForeignKey("seasons.id"), nullable=False)
    club_id = Column(String(50), ForeignKey("clubs.id"), nullable=False)

    # League info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    league_code = Column(String(20), unique=True, nullable=False)  # Join code

    # Rules
    squad_size = Column(Integer, default=11)  # 11-player teams
    budget = Column(Float, default=500.0)
    currency = Column(String(10), default="EUR")
    transfers_per_season = Column(Integer, default=4)  # Free transfers allowed per season

    # Constraints
    # With 10 ACC teams, requiring 1 from each = 10 players + 1 flex spot
    min_players_per_team = Column(Integer, default=1)  # Minimum 1 from each team
    max_players_per_team = Column(Integer, default=2)  # Maximum 2 from any team
    require_from_each_team = Column(Boolean, default=True)  # Must have 1 from all 10 teams

    # Player type constraints
    min_batsmen = Column(Integer, default=3)  # Minimum batsmen required
    min_bowlers = Column(Integer, default=3)  # Minimum bowlers required
    require_wicket_keeper = Column(Boolean, default=True)  # Must have at least 1 wicket-keeper

    # Status
    is_public = Column(Boolean, default=False)
    max_participants = Column(Integer, default=100)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=False)  # User ID of commissioner

    # Relationships
    season = relationship("Season", back_populates="leagues")
    club = relationship("Club")
    fantasy_teams = relationship("FantasyTeam", back_populates="league", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_league_season', 'season_id'),
        Index('idx_league_club', 'club_id'),
        Index('idx_league_code', 'league_code'),
    )


class FantasyTeam(Base):
    """
    User's fantasy team in a league
    """
    __tablename__ = "fantasy_teams"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    league_id = Column(String(50), ForeignKey("leagues.id"), nullable=False)
    user_id = Column(String(50), nullable=False)  # From auth system

    # Team info
    team_name = Column(String(200), nullable=False)
    budget_used = Column(Float, default=0.0)
    budget_remaining = Column(Float, default=500.0)

    # Status
    is_finalized = Column(Boolean, default=False)  # Locked in for season
    total_points = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)

    # Transfer tracking
    transfers_used = Column(Integer, default=0)  # Transfers used this season
    extra_transfers_granted = Column(Integer, default=0)  # Additional transfers from admin

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    league = relationship("League", back_populates="fantasy_teams")
    players = relationship("FantasyTeamPlayer", back_populates="fantasy_team", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="fantasy_team", cascade="all, delete-orphan")

    # Unique constraint: one team per user per league
    __table_args__ = (
        UniqueConstraint('league_id', 'user_id', name='uq_league_user'),
        Index('idx_fantasy_team_league', 'league_id'),
        Index('idx_fantasy_team_user', 'user_id'),
    )


class FantasyTeamPlayer(Base):
    """
    Player in a fantasy team (many-to-many relationship)
    """
    __tablename__ = "fantasy_team_players"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    fantasy_team_id = Column(String(50), ForeignKey("fantasy_teams.id"), nullable=False)
    player_id = Column(String(50), ForeignKey("players.id"), nullable=False)

    # Selection details
    purchase_value = Column(Float, nullable=False)  # Value when added
    is_captain = Column(Boolean, default=False)
    is_vice_captain = Column(Boolean, default=False)
    is_wicket_keeper = Column(Boolean, default=False)
    position = Column(Integer, nullable=True)  # Order in lineup

    # Performance tracking
    total_points = Column(Float, default=0.0)

    # Metadata
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fantasy_team = relationship("FantasyTeam", back_populates="players")
    player = relationship("Player", back_populates="fantasy_team_players")

    # Unique constraint: one player per team (can't add same player twice)
    __table_args__ = (
        UniqueConstraint('fantasy_team_id', 'player_id', name='uq_team_player'),
        Index('idx_ftp_team', 'fantasy_team_id'),
        Index('idx_ftp_player', 'player_id'),
    )


class Transfer(Base):
    """
    Transfer history for fantasy teams
    Tracks all player swaps, additions, and removals
    """
    __tablename__ = "transfers"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    fantasy_team_id = Column(String(50), ForeignKey("fantasy_teams.id"), nullable=False)

    # Transfer details
    player_out_id = Column(String(50), ForeignKey("players.id"), nullable=True)  # Null for initial squad
    player_in_id = Column(String(50), ForeignKey("players.id"), nullable=False)
    transfer_type = Column(String(50), default="regular")  # regular, extra_granted, initial

    # Admin approval for extra transfers
    requires_approval = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(50), nullable=True)  # Admin user ID
    proof_url = Column(String(500), nullable=True)  # Link to sponsor proof

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    fantasy_team = relationship("FantasyTeam", back_populates="transfers")
    player_out = relationship("Player", foreign_keys=[player_out_id])
    player_in = relationship("Player", foreign_keys=[player_in_id])

    # Indexes
    __table_args__ = (
        Index('idx_transfer_team', 'fantasy_team_id'),
        Index('idx_transfer_approval', 'requires_approval', 'is_approved'),
    )


# =============================================================================
# MATCH & PERFORMANCE TRACKING
# =============================================================================

class Match(Base):
    """
    Cricket match (used for performance tracking and points calculation)
    """
    __tablename__ = "matches"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    season_id = Column(String(50), ForeignKey("seasons.id"), nullable=False)
    club_id = Column(String(50), ForeignKey("clubs.id"), nullable=False)

    # Match info
    match_date = Column(DateTime, nullable=False)
    opponent = Column(String(200), nullable=False)
    match_title = Column(String(300), nullable=True)  # Full match title from scorecard
    venue = Column(String(200), nullable=True)

    # Match Centre data
    matchcentre_id = Column(String(100), nullable=True)  # Match ID from KNCB Match Centre
    scorecard_url = Column(String(500), nullable=True)
    period_id = Column(String(100), nullable=True)  # Period ID from URL

    # Match result
    result = Column(String(50), nullable=True)  # "won", "lost", "tied", "no_result"
    match_type = Column(String(50), default="league")  # league, cup, friendly

    # Processing status
    is_processed = Column(Boolean, default=False)  # Has performance data been extracted?
    processed_at = Column(DateTime, nullable=True)

    # Raw scorecard data
    raw_scorecard_data = Column(JSON, nullable=True)  # Store full scorecard JSON

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    season = relationship("Season")
    club = relationship("Club")
    player_performances = relationship("PlayerPerformance", back_populates="match", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_match_season', 'season_id'),
        Index('idx_match_club', 'club_id'),
        Index('idx_match_date', 'match_date'),
        Index('idx_match_processed', 'is_processed'),
        Index('idx_match_matchcentre', 'matchcentre_id'),
    )


class PlayerPerformance(Base):
    """
    Individual player performance in a specific match
    Used to calculate fantasy points and update player stats
    """
    __tablename__ = "player_performances"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    match_id = Column(String(50), ForeignKey("matches.id"), nullable=False)
    player_id = Column(String(50), ForeignKey("players.id"), nullable=False)

    # Batting stats
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    batting_strike_rate = Column(Float, nullable=True)
    is_out = Column(Boolean, default=False)
    dismissal_type = Column(String(50), nullable=True)  # bowled, caught, lbw, run out, etc.

    # Bowling stats
    overs_bowled = Column(Float, default=0.0)
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    bowling_economy = Column(Float, nullable=True)

    # Fielding stats
    catches = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)

    # Fantasy points
    fantasy_points = Column(Float, default=0.0)
    points_breakdown = Column(JSON, nullable=True)  # Detailed breakdown of how points were earned
    """
    points_breakdown JSON structure:
    {
        "batting": {
            "runs": 45,
            "fours": 20,
            "sixes": 24,
            "strike_rate_bonus": 10,
            "fifty_bonus": 25,
            "total": 124
        },
        "bowling": {
            "wickets": 50,
            "maidens": 10,
            "economy_bonus": 5,
            "total": 65
        },
        "fielding": {
            "catches": 16,
            "run_outs": 12,
            "total": 28
        },
        "grand_total": 217
    }
    """

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    match = relationship("Match", back_populates="player_performances")
    player = relationship("Player")

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('match_id', 'player_id', name='uq_match_player_performance'),
        Index('idx_perf_match', 'match_id'),
        Index('idx_perf_player', 'player_id'),
        Index('idx_perf_points', 'fantasy_points'),
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_database(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(engine)
