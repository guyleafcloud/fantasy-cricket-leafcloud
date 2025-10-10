from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# Dutch Cricket Tiers
class CricketTier(enum.Enum):
    HOOFDKLASSE = "Hoofdklasse"
    OVERGANGSKLASSE = "Overgangsklasse"
    EERSTE_KLASSE = "1e Klasse"
    TWEEDE_KLASSE = "2e Klasse"
    DERDE_KLASSE = "3e Klasse"
    VIERDE_KLASSE = "4e Klasse"

class PlayerRole(enum.Enum):
    BATSMAN = "Batsman"
    BOWLER = "Bowler"
    ALL_ROUNDER = "All-rounder"
    WICKET_KEEPER = "Wicket Keeper"

class MatchStatus(enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# Users table (already exists in auth_db.py)
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fantasy_teams = relationship("FantasyTeam", back_populates="owner")
    league_memberships = relationship("LeagueMember", back_populates="user")

# Real cricket clubs
class Club(Base):
    __tablename__ = "clubs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    tier = Column(SQLEnum(CricketTier), nullable=False)
    location = Column(String)
    founded_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    players = relationship("Player", back_populates="club")

# Real cricket players
class Player(Base):
    __tablename__ = "players"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    role = Column(SQLEnum(PlayerRole), nullable=False)
    tier = Column(SQLEnum(CricketTier), nullable=False)
    
    # Fantasy pricing based on tier
    base_price = Column(Integer, nullable=False)  # Credits
    current_price = Column(Integer, nullable=False)
    
    # Season stats
    matches_played = Column(Integer, default=0)
    runs_scored = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    balls_bowled = Column(Integer, default=0)
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    
    # Calculated stats
    batting_average = Column(Float, default=0.0)
    strike_rate = Column(Float, default=0.0)
    bowling_average = Column(Float, default=0.0)
    economy_rate = Column(Float, default=0.0)
    
    # Fantasy points
    total_fantasy_points = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="players")
    match_performances = relationship("PlayerPerformance", back_populates="player")

# Real matches
class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    home_club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    away_club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    tier = Column(SQLEnum(CricketTier), nullable=False)
    
    match_date = Column(DateTime, nullable=False)
    venue = Column(String)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED)
    
    # Scores
    home_score = Column(Integer)
    home_wickets = Column(Integer)
    away_score = Column(Integer)
    away_wickets = Column(Integer)
    
    winner_club_id = Column(String, ForeignKey("clubs.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_club = relationship("Club", foreign_keys=[home_club_id])
    away_club = relationship("Club", foreign_keys=[away_club_id])
    winner = relationship("Club", foreign_keys=[winner_club_id])
    performances = relationship("PlayerPerformance", back_populates="match")

# Player performance in specific match
class PlayerPerformance(Base):
    __tablename__ = "player_performances"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    
    # Batting
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    is_out = Column(Boolean, default=False)
    
    # Bowling
    overs_bowled = Column(Float, default=0.0)
    runs_conceded = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    maidens = Column(Integer, default=0)
    
    # Fielding
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    # Fantasy points for this match
    fantasy_points = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="performances")
    player = relationship("Player", back_populates="match_performances")

# Fantasy Leagues
class League(Base):
    __tablename__ = "leagues"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)  # Join code
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    max_members = Column(Integer, default=12)
    is_private = Column(Boolean, default=True)
    
    season_start = Column(DateTime)
    season_end = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User")
    members = relationship("LeagueMember", back_populates="league")

# League membership
class LeagueMember(Base):
    __tablename__ = "league_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    total_points = Column(Float, default=0.0)
    rank = Column(Integer)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="members")
    user = relationship("User", back_populates="league_memberships")

# Association table for fantasy team players
fantasy_team_players = Table('fantasy_team_players', Base.metadata,
    Column('fantasy_team_id', String, ForeignKey('fantasy_teams.id')),
    Column('player_id', String, ForeignKey('players.id'))
)

# Fantasy Teams
class FantasyTeam(Base):
    __tablename__ = "fantasy_teams"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    
    name = Column(String, nullable=False)
    budget_remaining = Column(Integer, default=10000)  # Credits
    
    # Captain gets 2x points, vice-captain 1.5x
    captain_id = Column(String, ForeignKey("players.id"))
    vice_captain_id = Column(String, ForeignKey("players.id"))
    
    total_points = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="fantasy_teams")
    league = relationship("League")
    players = relationship("Player", secondary=fantasy_team_players)
    captain = relationship("Player", foreign_keys=[captain_id])
    vice_captain = relationship("Player", foreign_keys=[vice_captain_id])
