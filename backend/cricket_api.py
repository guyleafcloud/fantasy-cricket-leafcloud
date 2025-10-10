from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import secrets
import string

from models import (
    Club, Player, Match, League, FantasyTeam, LeagueMember,
    PlayerPerformance, CricketTier, PlayerRole, MatchStatus, User
)
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/cricket", tags=["cricket"])

# Pydantic models
class ClubCreate(BaseModel):
    name: str
    tier: str
    location: Optional[str] = None
    founded_year: Optional[int] = None

class ClubResponse(BaseModel):
    id: str
    name: str
    tier: str
    location: Optional[str]
    founded_year: Optional[int]
    
    class Config:
        from_attributes = True

class PlayerCreate(BaseModel):
    name: str
    club_id: str
    role: str
    tier: str
    base_price: int

class PlayerResponse(BaseModel):
    id: str
    name: str
    club_id: str
    role: str
    tier: str
    current_price: int
    matches_played: int
    runs_scored: int
    wickets_taken: int
    batting_average: float
    strike_rate: float
    total_fantasy_points: float
    
    class Config:
        from_attributes = True

class LeagueCreate(BaseModel):
    name: str
    max_members: int = 12
    is_private: bool = True

class LeagueResponse(BaseModel):
    id: str
    name: str
    code: str
    max_members: int
    is_private: bool
    member_count: int
    
    class Config:
        from_attributes = True

class FantasyTeamCreate(BaseModel):
    name: str
    league_id: str
    player_ids: List[str]
    captain_id: str
    vice_captain_id: str

class FantasyTeamResponse(BaseModel):
    id: str
    name: str
    budget_remaining: int
    total_points: float
    player_count: int
    
    class Config:
        from_attributes = True

def generate_league_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

# Club endpoints
@router.post("/clubs", response_model=ClubResponse)
async def create_club(
    club: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_club = Club(
        name=club.name,
        tier=CricketTier[club.tier],
        location=club.location,
        founded_year=club.founded_year
    )
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    return new_club

@router.get("/clubs", response_model=List[ClubResponse])
async def list_clubs(
    tier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Club)
    if tier:
        query = query.filter(Club.tier == CricketTier[tier])
    return query.all()

@router.get("/clubs/{club_id}", response_model=ClubResponse)
async def get_club(club_id: str, db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

# Player endpoints
@router.post("/players", response_model=PlayerResponse)
async def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    club = db.query(Club).filter(Club.id == player.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    new_player = Player(
        name=player.name,
        club_id=player.club_id,
        role=PlayerRole[player.role],
        tier=CricketTier[player.tier],
        base_price=player.base_price,
        current_price=player.base_price
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

@router.get("/players", response_model=List[PlayerResponse])
async def list_players(
    tier: Optional[str] = None,
    club_id: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Player).filter(Player.is_active == True)
    
    if tier:
        query = query.filter(Player.tier == CricketTier[tier])
    if club_id:
        query = query.filter(Player.club_id == club_id)
    if role:
        query = query.filter(Player.role == PlayerRole[role])
    
    return query.order_by(Player.total_fantasy_points.desc()).all()

@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

# League endpoints
@router.post("/leagues", response_model=LeagueResponse)
async def create_league(
    league: LeagueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code = generate_league_code()
    while db.query(League).filter(League.code == code).first():
        code = generate_league_code()
    
    new_league = League(
        name=league.name,
        code=code,
        creator_id=current_user.id,
        max_members=league.max_members,
        is_private=league.is_private
    )
    db.add(new_league)
    db.commit()
    db.refresh(new_league)
    
    membership = LeagueMember(
        league_id=new_league.id,
        user_id=current_user.id
    )
    db.add(membership)
    db.commit()
    
    return {
        **new_league.__dict__,
        "member_count": 1
    }

@router.post("/leagues/{code}/join")
async def join_league(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    league = db.query(League).filter(League.code == code).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    existing = db.query(LeagueMember).filter(
        LeagueMember.league_id == league.id,
        LeagueMember.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    
    member_count = db.query(LeagueMember).filter(LeagueMember.league_id == league.id).count()
    if member_count >= league.max_members:
        raise HTTPException(status_code=400, detail="League is full")
    
    membership = LeagueMember(
        league_id=league.id,
        user_id=current_user.id
    )
    db.add(membership)
    db.commit()
    
    return {"message": "Joined league successfully", "league_name": league.name}

@router.get("/leagues/my", response_model=List[LeagueResponse])
async def my_leagues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memberships = db.query(LeagueMember).filter(LeagueMember.user_id == current_user.id).all()
    leagues = []
    for membership in memberships:
        league = db.query(League).filter(League.id == membership.league_id).first()
        if league:
            member_count = db.query(LeagueMember).filter(LeagueMember.league_id == league.id).count()
            leagues.append({
                **league.__dict__,
                "member_count": member_count
            })
    return leagues

# Fantasy Team endpoints
@router.post("/fantasy-teams", response_model=FantasyTeamResponse)
async def create_fantasy_team(
    team: FantasyTeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == team.league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this league")
    
    existing_team = db.query(FantasyTeam).filter(
        FantasyTeam.league_id == team.league_id,
        FantasyTeam.owner_id == current_user.id
    ).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Already have a team in this league")
    
    if len(team.player_ids) != 11:
        raise HTTPException(status_code=400, detail="Team must have exactly 11 players")
    
    players = db.query(Player).filter(Player.id.in_(team.player_ids)).all()
    if len(players) != 11:
        raise HTTPException(status_code=400, detail="Some players not found")
    
    total_cost = sum(p.current_price for p in players)
    BUDGET = 10000
    if total_cost > BUDGET:
        raise HTTPException(status_code=400, detail=f"Team cost ({total_cost}) exceeds budget ({BUDGET})")
    
    if team.captain_id not in team.player_ids or team.vice_captain_id not in team.player_ids:
        raise HTTPException(status_code=400, detail="Captain/Vice-captain must be in the team")
    
    new_team = FantasyTeam(
        name=team.name,
        owner_id=current_user.id,
        league_id=team.league_id,
        budget_remaining=BUDGET - total_cost,
        captain_id=team.captain_id,
        vice_captain_id=team.vice_captain_id
    )
    db.add(new_team)
    db.flush()
    
    for player_id in team.player_ids:
        player = db.query(Player).filter(Player.id == player_id).first()
        new_team.players.append(player)
    
    db.commit()
    db.refresh(new_team)
    
    return {
        **new_team.__dict__,
        "player_count": len(team.player_ids)
    }

@router.get("/fantasy-teams/my", response_model=List[FantasyTeamResponse])
async def my_fantasy_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    teams = db.query(FantasyTeam).filter(FantasyTeam.owner_id == current_user.id).all()
    return [{
        **team.__dict__,
        "player_count": len(team.players)
    } for team in teams]
