"""
League Management Endpoints

Admin endpoints for creating and managing fantasy leagues
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from database_models import League, Season, FantasyTeam, Transfer, Club
from admin_endpoints import verify_admin
from team_validation import validate_team_composition, get_team_composition_summary
import secrets
import string

router = APIRouter(prefix="/api/admin", tags=["leagues"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class LeagueCreate(BaseModel):
    season_id: str
    club_id: str
    name: str
    description: Optional[str] = None
    squad_size: int = 11
    transfers_per_season: int = 4
    require_from_each_team: bool = True
    is_public: bool = True
    max_participants: int = 100


class LeagueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    squad_size: Optional[int] = None
    transfers_per_season: Optional[int] = None
    require_from_each_team: Optional[bool] = None
    is_public: Optional[bool] = None
    max_participants: Optional[int] = None
    min_batsmen: Optional[int] = None
    min_bowlers: Optional[int] = None
    require_wicket_keeper: Optional[bool] = None
    max_players_per_team: Optional[int] = None


class GrantTransferRequest(BaseModel):
    extra_transfers: int = 1


# =============================================================================
# LEAGUE MANAGEMENT ENDPOINTS
# =============================================================================

def generate_league_code() -> str:
    """Generate a random 6-character league code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(6))


@router.post("/leagues", status_code=status.HTTP_201_CREATED)
async def create_league(
    league_data: LeagueCreate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Create a new fantasy league (Admin only)"""

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating league with data: season_id={league_data.season_id}, club_id={league_data.club_id}, name={league_data.name}")
    logger.info(f"Checking if club exists with ID: {league_data.club_id}")

    # Verify season exists
    season = db.query(Season).filter_by(id=league_data.season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Verify club exists
    all_clubs = db.query(Club).all()
    logger.info(f"All clubs in database: {[(c.id, c.name) for c in all_clubs]}")

    club = db.query(Club).filter_by(id=league_data.club_id).first()
    if not club:
        logger.error(f"Club not found with ID: {league_data.club_id}")
        raise HTTPException(status_code=404, detail="Club not found")

    logger.info(f"Found club: {club.name} ({club.id})")

    # Generate unique league code
    league_code = generate_league_code()
    while db.query(League).filter_by(league_code=league_code).first():
        league_code = generate_league_code()

    # Create league
    league = League(
        season_id=league_data.season_id,
        club_id=league_data.club_id,
        name=league_data.name,
        description=league_data.description,
        league_code=league_code,
        squad_size=league_data.squad_size,
        transfers_per_season=league_data.transfers_per_season,
        require_from_each_team=league_data.require_from_each_team,
        is_public=league_data.is_public,
        max_participants=league_data.max_participants,
        created_by=admin["user_id"]
    )

    db.add(league)
    db.commit()
    db.refresh(league)

    return {
        "message": "League created successfully",
        "league": {
            "id": league.id,
            "name": league.name,
            "league_code": league.league_code,
            "season_id": league.season_id
        }
    }


@router.get("/leagues")
async def list_leagues(
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """List all leagues (Admin only)"""

    leagues = db.query(League).order_by(League.created_at.desc()).all()

    return {
        "leagues": [
            {
                "id": l.id,
                "season_id": l.season_id,
                "season_name": l.season.name if l.season else "Unknown",
                "club_id": l.club_id,
                "club_name": l.club.name if l.club else "Unknown",
                "name": l.name,
                "description": l.description,
                "league_code": l.league_code,
                "squad_size": l.squad_size,
                "transfers_per_season": l.transfers_per_season,
                "require_from_each_team": l.require_from_each_team,
                "is_public": l.is_public,
                "participants_count": len(l.fantasy_teams),
                "max_participants": l.max_participants,
                "created_at": l.created_at.isoformat()
            }
            for l in leagues
        ]
    }


@router.get("/leagues/{league_id}")
async def get_league(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get detailed league information (Admin only)"""

    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get fantasy teams with transfer info
    teams_info = []
    for team in league.fantasy_teams:
        transfers_remaining = (
            league.transfers_per_season
            + team.extra_transfers_granted
            - team.transfers_used
        )

        teams_info.append({
            "id": team.id,
            "team_name": team.team_name,
            "user_id": team.user_id,
            "total_points": team.total_points,
            "rank": team.rank,
            "transfers_used": team.transfers_used,
            "transfers_remaining": transfers_remaining,
            "extra_transfers_granted": team.extra_transfers_granted,
            "is_finalized": team.is_finalized
        })

    return {
        "id": league.id,
        "season_id": league.season_id,
        "season_name": league.season.name if league.season else "Unknown",
        "name": league.name,
        "description": league.description,
        "league_code": league.league_code,
        "squad_size": league.squad_size,
        "transfers_per_season": league.transfers_per_season,
        "require_from_each_team": league.require_from_each_team,
        "is_public": league.is_public,
        "max_participants": league.max_participants,
        "participants_count": len(league.fantasy_teams),
        "teams": teams_info,
        "created_at": league.created_at.isoformat(),
        "min_batsmen": league.min_batsmen,
        "min_bowlers": league.min_bowlers,
        "require_wicket_keeper": league.require_wicket_keeper,
        "max_players_per_team": league.max_players_per_team
    }


@router.patch("/leagues/{league_id}")
async def update_league(
    league_id: str,
    league_data: LeagueUpdate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Update league rules and settings (Admin only)"""

    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Update fields if provided
    if league_data.name is not None:
        league.name = league_data.name
    if league_data.description is not None:
        league.description = league_data.description
    if league_data.squad_size is not None:
        league.squad_size = league_data.squad_size
    if league_data.transfers_per_season is not None:
        league.transfers_per_season = league_data.transfers_per_season
    if league_data.require_from_each_team is not None:
        league.require_from_each_team = league_data.require_from_each_team
    if league_data.is_public is not None:
        league.is_public = league_data.is_public
    if league_data.max_participants is not None:
        league.max_participants = league_data.max_participants
    if league_data.min_batsmen is not None:
        league.min_batsmen = league_data.min_batsmen
    if league_data.min_bowlers is not None:
        league.min_bowlers = league_data.min_bowlers
    if league_data.require_wicket_keeper is not None:
        league.require_wicket_keeper = league_data.require_wicket_keeper
    if league_data.max_players_per_team is not None:
        league.max_players_per_team = league_data.max_players_per_team

    db.commit()
    db.refresh(league)

    return {
        "message": "League updated successfully",
        "league": {
            "id": league.id,
            "name": league.name,
            "description": league.description,
            "squad_size": league.squad_size,
            "transfers_per_season": league.transfers_per_season,
            "require_from_each_team": league.require_from_each_team,
            "is_public": league.is_public,
            "max_participants": league.max_participants,
            "min_batsmen": league.min_batsmen,
            "min_bowlers": league.min_bowlers,
            "require_wicket_keeper": league.require_wicket_keeper,
            "max_players_per_team": league.max_players_per_team
        }
    }


@router.post("/leagues/{league_id}/teams/{team_id}/grant-transfer")
async def grant_extra_transfer(
    league_id: str,
    team_id: str,
    request: GrantTransferRequest,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Grant extra transfers to a fantasy team (Admin only)"""

    # Verify league exists
    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Verify team exists and belongs to league
    team = db.query(FantasyTeam).filter_by(id=team_id, league_id=league_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Fantasy team not found in this league")

    # Grant extra transfers
    team.extra_transfers_granted += request.extra_transfers
    db.commit()

    transfers_remaining = (
        league.transfers_per_season
        + team.extra_transfers_granted
        - team.transfers_used
    )

    return {
        "message": f"Granted {request.extra_transfers} extra transfer(s)",
        "team_id": team.id,
        "team_name": team.team_name,
        "extra_transfers_granted": team.extra_transfers_granted,
        "transfers_remaining": transfers_remaining
    }


@router.get("/leagues/{league_id}/transfer-requests")
async def get_transfer_requests(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get pending transfer requests for a league (Admin only)"""

    # Verify league exists
    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get all fantasy teams in this league
    team_ids = [team.id for team in league.fantasy_teams]

    # Get pending transfers that require approval
    pending_transfers = (
        db.query(Transfer)
        .filter(
            Transfer.fantasy_team_id.in_(team_ids),
            Transfer.requires_approval == True,
            Transfer.is_approved == False
        )
        .order_by(Transfer.created_at.desc())
        .all()
    )

    return {
        "requests": [
            {
                "id": t.id,
                "fantasy_team_id": t.fantasy_team_id,
                "team_name": t.fantasy_team.team_name,
                "player_out": t.player_out.name if t.player_out else None,
                "player_in": t.player_in.name if t.player_in else None,
                "proof_url": t.proof_url,
                "created_at": t.created_at.isoformat()
            }
            for t in pending_transfers
        ]
    }


@router.post("/leagues/{league_id}/transfer-requests/{transfer_id}/approve")
async def approve_transfer_request(
    league_id: str,
    transfer_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Approve a transfer request (Admin only)"""

    transfer = db.query(Transfer).filter_by(id=transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    # Verify the transfer belongs to a team in this league
    if transfer.fantasy_team.league_id != league_id:
        raise HTTPException(status_code=400, detail="Transfer does not belong to this league")

    # Grant the extra transfer
    transfer.fantasy_team.extra_transfers_granted += 1
    transfer.is_approved = True
    transfer.approved_by = admin["user_id"]

    from datetime import datetime
    transfer.approved_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Transfer request approved",
        "transfer_id": transfer.id,
        "team_name": transfer.fantasy_team.team_name,
        "extra_transfers_granted": transfer.fantasy_team.extra_transfers_granted
    }


@router.get("/leagues/{league_id}/teams/{team_id}/validate")
async def validate_fantasy_team(
    league_id: str,
    team_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Validate a fantasy team's composition against league rules (Admin only)

    Checks:
    - Minimum batsmen requirement
    - Minimum bowlers requirement
    - Wicket-keeper requirement
    - Squad size
    - Players per team constraints
    """
    # Verify league exists
    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Verify team exists and belongs to league
    team = db.query(FantasyTeam).filter_by(id=team_id, league_id=league_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Fantasy team not found in this league")

    # Validate team composition
    is_valid, errors = validate_team_composition(db, league, team)

    # Get team composition summary
    composition = get_team_composition_summary(db, team)

    return {
        "team_id": team.id,
        "team_name": team.team_name,
        "is_valid": is_valid,
        "errors": errors,
        "composition": composition,
        "league_requirements": {
            "squad_size": league.squad_size,
            "min_batsmen": league.min_batsmen,
            "min_bowlers": league.min_bowlers,
            "require_wicket_keeper": league.require_wicket_keeper,
            "max_players_per_team": league.max_players_per_team,
            "require_from_each_team": league.require_from_each_team
        }
    }
