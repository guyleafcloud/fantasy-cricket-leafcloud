"""
User Team Management Endpoints

User-facing endpoints for joining leagues, creating teams, and managing players
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Tuple
from database import get_db
from database_models import League, Season, FantasyTeam, FantasyTeamPlayer, Player, Team
from user_auth_endpoints import verify_token
from collections import Counter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user_teams"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class JoinLeagueByCode(BaseModel):
    league_code: str


class CreateTeam(BaseModel):
    league_id: str
    team_name: str


class AddPlayerToTeam(BaseModel):
    player_id: str
    is_captain: bool = False
    is_vice_captain: bool = False
    is_wicket_keeper: bool = False


class RemovePlayerFromTeam(BaseModel):
    player_id: str


class TransferPlayer(BaseModel):
    player_out_id: str
    player_in_id: str


# =============================================================================
# HELPER FUNCTIONS FOR LEAGUE RULE VALIDATION
# =============================================================================

def validate_league_rules(
    league: League,
    current_players: List[FantasyTeamPlayer],
    player_to_add: Player = None,
    player_to_remove_id: str = None,
    db: Session = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a squad composition follows league rules.

    Returns: (is_valid, error_message)
    """
    # Build the proposed squad
    proposed_squad = []

    # Get all current player IDs (excluding the one being removed)
    player_ids = [
        ftp.player_id for ftp in current_players
        if not (player_to_remove_id and ftp.player_id == player_to_remove_id)
    ]

    # Load all players at once
    if player_ids and db:
        players = db.query(Player).filter(Player.id.in_(player_ids)).all()
        proposed_squad = players
    else:
        # Fallback: try to use loaded relationships
        for ftp in current_players:
            # Skip the player being removed (for transfers)
            if player_to_remove_id and ftp.player_id == player_to_remove_id:
                continue
            if ftp.player:
                proposed_squad.append(ftp.player)

    # Add the player being added
    if player_to_add:
        proposed_squad.append(player_to_add)

    # If squad is empty, no validation needed yet
    if not proposed_squad:
        return True, None

    # Count player types
    batsmen_count = 0
    bowlers_count = 0

    for player in proposed_squad:
        if player.role == 'BATSMAN':
            batsmen_count += 1
        elif player.role == 'BOWLER':
            bowlers_count += 1
        elif player.role == 'ALL_ROUNDER':
            # All-rounders count as both batsman and bowler
            batsmen_count += 1
            bowlers_count += 1

    # Count players per RL team using rl_team string field
    team_counts = Counter()
    unique_teams = set()
    for player in proposed_squad:
        if player.rl_team:
            team_counts[player.rl_team] += 1
            unique_teams.add(player.rl_team)

    # Validate max_players_per_team
    if league.max_players_per_team:
        for rl_team, count in team_counts.items():
            if count > league.max_players_per_team:
                return False, f"Cannot have more than {league.max_players_per_team} players from {rl_team}"

    # For adding a player (not finalizing), we need to check if we're moving towards the rule, not enforce it strictly
    is_adding_player = player_to_add is not None and len(proposed_squad) < league.squad_size

    # Validate min_batsmen (only enforce when squad is complete or would prevent completion)
    if league.min_batsmen:
        if not is_adding_player and batsmen_count < league.min_batsmen:
            return False, f"Team must have at least {league.min_batsmen} batsmen (currently {batsmen_count})"

    # Validate min_bowlers (only enforce when squad is complete or would prevent completion)
    if league.min_bowlers:
        if not is_adding_player and bowlers_count < league.min_bowlers:
            return False, f"Team must have at least {league.min_bowlers} bowlers (currently {bowlers_count})"

    # Validate require_from_each_team using rl_team
    if league.require_from_each_team and league.min_players_per_team:
        if not is_adding_player:
            # Get total number of distinct RL teams in the club
            if db:
                from sqlalchemy import func
                total_teams = db.query(func.count(func.distinct(Player.rl_team)))\
                    .filter(Player.club_id == league.club_id, Player.rl_team.isnot(None))\
                    .scalar()

                if len(unique_teams) < total_teams:
                    return False, f"Team must have players from all {total_teams} RL teams (currently have players from {len(unique_teams)} teams)"

                # Also check that each team has at least min_players_per_team
                for rl_team, count in team_counts.items():
                    if count < league.min_players_per_team:
                        return False, f"Must have at least {league.min_players_per_team} player(s) from each RL team (only {count} from {rl_team})"

    return True, None


# =============================================================================
# LEAGUE BROWSING & JOINING
# =============================================================================

@router.get("/leagues/public")
async def browse_public_leagues(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Browse all public leagues that user can join

    Returns leagues the user hasn't joined yet
    """
    # Get all public leagues
    leagues = db.query(League).filter_by(is_public=True).all()

    # Get user's current league memberships
    user_league_ids = {
        team.league_id
        for team in db.query(FantasyTeam).filter_by(user_id=user["sub"]).all()
    }

    # Filter out leagues user has already joined
    available_leagues = [
        {
            "id": league.id,
            "name": league.name,
            "description": league.description,
            "season_name": league.season.name if league.season else "Unknown",
            "club_name": league.club.name if league.club else "Unknown",
            "league_code": league.league_code,
            "participants_count": len(league.fantasy_teams),
            "max_participants": league.max_participants,
            "is_full": len(league.fantasy_teams) >= league.max_participants,
            "squad_size": league.squad_size,
            "transfers_per_season": league.transfers_per_season
        }
        for league in leagues
        if league.id not in user_league_ids
    ]

    return {"leagues": available_leagues}


@router.post("/leagues/join")
async def join_league(
    request: JoinLeagueByCode,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Join a league using a league code

    Creates a fantasy team entry for the user in the league
    """
    # Find league by code
    league = db.query(League).filter_by(league_code=request.league_code.upper()).first()
    if not league:
        raise HTTPException(
            status_code=404,
            detail="League not found. Please check the code and try again."
        )

    # Check if league is full
    if len(league.fantasy_teams) >= league.max_participants:
        raise HTTPException(
            status_code=400,
            detail="This league is full and cannot accept more participants."
        )

    # Check if user already joined this league
    existing_team = db.query(FantasyTeam).filter_by(
        league_id=league.id,
        user_id=user["sub"]
    ).first()

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="You have already joined this league."
        )

    return {
        "league": {
            "id": league.id,
            "name": league.name,
            "description": league.description,
            "season_name": league.season.name if league.season else "Unknown",
            "club_name": league.club.name if league.club else "Unknown",
            "squad_size": league.squad_size,
            "budget": league.budget,
            "require_from_each_team": league.require_from_each_team,
            "max_players_per_team": league.max_players_per_team
        },
        "message": "Ready to create your team!"
    }


# =============================================================================
# TEAM CREATION & MANAGEMENT
# =============================================================================

@router.post("/teams", status_code=status.HTTP_201_CREATED)
async def create_fantasy_team(
    team_data: CreateTeam,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Create a new fantasy team in a league

    This happens after joining a league
    """
    # Verify league exists
    league = db.query(League).filter_by(id=team_data.league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Check if user already has a team in this league
    existing_team = db.query(FantasyTeam).filter_by(
        league_id=team_data.league_id,
        user_id=user["sub"]
    ).first()

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="You already have a team in this league"
        )

    # Check if team name is unique in league
    name_taken = db.query(FantasyTeam).filter_by(
        league_id=team_data.league_id,
        team_name=team_data.team_name
    ).first()

    if name_taken:
        raise HTTPException(
            status_code=400,
            detail="Team name is already taken in this league"
        )

    # Create fantasy team
    fantasy_team = FantasyTeam(
        league_id=team_data.league_id,
        user_id=user["sub"],
        team_name=team_data.team_name,
        budget_remaining=league.budget,
        budget_used=0.0
    )

    db.add(fantasy_team)
    db.commit()
    db.refresh(fantasy_team)

    return {
        "message": "Team created successfully",
        "team": {
            "id": fantasy_team.id,
            "team_name": fantasy_team.team_name,
            "league_id": fantasy_team.league_id,
            "league_name": league.name,
            "budget_remaining": fantasy_team.budget_remaining
        }
    }


@router.get("/teams")
async def get_my_teams(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get all fantasy teams for the current user
    """
    teams = db.query(FantasyTeam).filter_by(user_id=user["sub"]).all()

    return {
        "teams": [
            {
                "id": team.id,
                "team_name": team.team_name,
                "league_id": team.league_id,
                "league_name": team.league.name if team.league else "Unknown",
                "season_name": team.league.season.name if team.league and team.league.season else "Unknown",
                "club_name": team.league.club.name if team.league and team.league.club else "Unknown",
                "total_points": team.total_points,
                "rank": team.rank,
                "is_finalized": team.is_finalized,
                "players_count": len(team.players),
                "budget_remaining": team.budget_remaining,
                "budget_used": team.budget_used,
                "transfers_used": team.transfers_used,
                "transfers_remaining": (
                    team.league.transfers_per_season
                    + team.extra_transfers_granted
                    - team.transfers_used
                ) if team.league else 0
            }
            for team in teams
        ]
    }


@router.get("/teams/{team_id}")
async def get_team_details(
    team_id: str,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific team
    """
    team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get player details
    players_info = []
    for ftp in team.players:
        player = ftp.player
        players_info.append({
            "id": player.id,
            "name": player.name,
            "club_name": player.club.name if player.club else "Unknown",
            "team_name": player.rl_team if player.rl_team else "Unassigned",
            "player_type": player.role.lower().replace('_', '-') if player.role else "unknown",
            "multiplier": player.multiplier,
            "is_captain": ftp.is_captain,
            "is_vice_captain": ftp.is_vice_captain,
            "is_wicket_keeper": ftp.is_wicket_keeper,
            "total_points": ftp.total_points
        })

    return {
        "id": team.id,
        "team_name": team.team_name,
        "league_id": team.league_id,
        "league_name": team.league.name if team.league else "Unknown",
        "season_name": team.league.season.name if team.league and team.league.season else "Unknown",
        "squad_size": team.league.squad_size if team.league else 11,
        "total_points": team.total_points,
        "rank": team.rank,
        "is_finalized": team.is_finalized,
        "transfers_used": team.transfers_used,
        "transfers_remaining": (
            team.league.transfers_per_season
            + team.extra_transfers_granted
            - team.transfers_used
        ) if team.league else 0,
        "players": players_info,
        "league_rules": {
            "squad_size": team.league.squad_size if team.league else 11,
            "budget": team.league.budget if team.league else 500.0,
            "require_from_each_team": team.league.require_from_each_team if team.league else True,
            "max_players_per_team": team.league.max_players_per_team if team.league else 2,
            "min_batsmen": team.league.min_batsmen if team.league else 3,
            "min_bowlers": team.league.min_bowlers if team.league else 3,
            "require_wicket_keeper": team.league.require_wicket_keeper if team.league else True
        }
    }


# =============================================================================
# PLAYER SELECTION & TEAM BUILDING
# =============================================================================

@router.get("/teams/{team_id}/available-players")
async def get_available_players(
    team_id: str,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get all players available for selection in a team's league
    """
    team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    league = team.league
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get all players from the league's club
    players = db.query(Player).filter_by(club_id=league.club_id).all()

    # Get players already in this team
    team_player_ids = {ftp.player_id for ftp in team.players}

    # Return available players
    available_players = []
    for player in players:
        if player.id not in team_player_ids:
            available_players.append({
                "id": player.id,
                "name": player.name,
                "club_name": player.club.name if player.club else "Unknown",
                "team_name": player.rl_team if player.rl_team else "Unassigned",
                "player_type": player.role.lower().replace('_', '-') if player.role else "unknown",
                "is_wicket_keeper": player.role == "WICKET_KEEPER" if player.role else False,
                "multiplier": player.multiplier if player.multiplier else 1.0,
                "stats": {
                    "matches": player.matches_played or 0,
                    "runs": player.runs_scored or 0,
                    "wickets": player.wickets_taken or 0,
                    "catches": player.catches or 0
                }
            })

    return {
        "available_players": available_players,
        "current_squad_size": len(team.players),
        "max_squad_size": league.squad_size
    }


@router.post("/teams/{team_id}/players")
async def add_player_to_team(
    team_id: str,
    request: AddPlayerToTeam,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Add a player to a fantasy team
    """
    logger.info(f"Adding player {request.player_id} to team {team_id}")

    team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.is_finalized:
        logger.warning(f"Cannot add player to finalized team {team_id}")
        raise HTTPException(status_code=400, detail="Team is finalized and cannot be modified")

    league = team.league
    player = db.query(Player).filter_by(id=request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    logger.info(f"Player: {player.name}, Value: {player.current_price}")

    # Verify player is from the correct club
    if player.club_id != league.club_id:
        logger.error(f"Player {player.name} not from correct club. Player club: {player.club_id}, League club: {league.club_id}")
        raise HTTPException(
            status_code=400,
            detail="Player does not belong to this league's club"
        )

    # Check if player already in team
    existing = db.query(FantasyTeamPlayer).filter_by(
        fantasy_team_id=team_id,
        player_id=request.player_id
    ).first()

    if existing:
        logger.warning(f"Player {player.name} already in team {team_id}")
        raise HTTPException(status_code=400, detail="Player already in team")

    # Check squad size
    if len(team.players) >= league.squad_size:
        logger.warning(f"Team {team_id} is full: {len(team.players)}/{league.squad_size}")
        raise HTTPException(
            status_code=400,
            detail=f"Team is full (max {league.squad_size} players)"
        )

    # Validate league rules before adding player
    logger.info(f"Validating league rules for team {team_id}")
    is_valid, error_message = validate_league_rules(
        league=league,
        current_players=team.players,
        player_to_add=player,
        db=db
    )

    if not is_valid:
        logger.error(f"League rule validation failed: {error_message}")
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    # Add player to team
    team_player = FantasyTeamPlayer(
        fantasy_team_id=team_id,
        player_id=request.player_id,
        purchase_value=0,
        is_captain=request.is_captain,
        is_vice_captain=request.is_vice_captain,
        is_wicket_keeper=request.is_wicket_keeper
    )

    db.add(team_player)
    db.commit()
    db.refresh(team_player)

    return {
        "message": "Player added to team",
        "player": {
            "id": player.id,
            "name": player.name
        },
        "squad_size": len(team.players) + 1
    }


@router.delete("/teams/{team_id}/players/{player_id}")
async def remove_player_from_team(
    team_id: str,
    player_id: str,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Remove a player from a fantasy team
    """
    team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.is_finalized:
        raise HTTPException(status_code=400, detail="Team is finalized and cannot be modified")

    # Find player in team
    team_player = db.query(FantasyTeamPlayer).filter_by(
        fantasy_team_id=team_id,
        player_id=player_id
    ).first()

    if not team_player:
        raise HTTPException(status_code=404, detail="Player not in team")

    # Refund budget
    team.budget_used -= team_player.purchase_value
    team.budget_remaining += team_player.purchase_value

    # Remove player
    db.delete(team_player)
    db.commit()

    return {
        "message": "Player removed from team",
        "team_budget_remaining": team.budget_remaining,
        "squad_size": len(team.players) - 1
    }


@router.post("/teams/{team_id}/finalize")
async def finalize_team(
    team_id: str,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Finalize a team (lock in for the season)

    Validates team composition before finalizing
    """
    team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.is_finalized:
        raise HTTPException(status_code=400, detail="Team is already finalized")

    league = team.league

    # Validate squad size
    if len(team.players) != league.squad_size:
        raise HTTPException(
            status_code=400,
            detail=f"Team must have exactly {league.squad_size} players (currently has {len(team.players)})"
        )

    # Comprehensive league rule validation
    is_valid, error_message = validate_league_rules(
        league=league,
        current_players=team.players,
        player_to_add=None,  # No new player, just validating current squad
        db=db
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    # Finalize team
    team.is_finalized = True
    db.commit()

    return {
        "message": "Team finalized successfully! Good luck!",
        "team_id": team.id,
        "team_name": team.team_name
    }


# =============================================================================
# TRANSFERS
# =============================================================================

@router.post("/teams/{team_id}/transfer")
async def transfer_player(
    team_id: str,
    request: TransferPlayer,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Transfer a player (swap one player for another)

    Only works on finalized teams and requires available transfers
    """
    import traceback
    try:
        print(f"DEBUG: Transfer request - team_id={team_id}, player_out={request.player_out_id}, player_in={request.player_in_id}")

        # Verify team ownership
        team = db.query(FantasyTeam).filter_by(id=team_id, user_id=user["sub"]).first()
        if not team:
            print("DEBUG: Team not found")
            raise HTTPException(status_code=404, detail="Team not found")

        print(f"DEBUG: Team found, is_finalized={team.is_finalized}")

        # Check if team is finalized (transfers only work on finalized teams)
        if not team.is_finalized:
            print("DEBUG: Team not finalized")
            raise HTTPException(
                status_code=400,
                detail="Team must be finalized before making transfers"
            )

        league = team.league
        print(f"DEBUG: League loaded, transfers_per_season={league.transfers_per_season}")

        # Calculate transfers remaining
        transfers_remaining = (
            league.transfers_per_season
            + team.extra_transfers_granted
            - team.transfers_used
        )
        print(f"DEBUG: transfers_remaining={transfers_remaining}, transfers_used={team.transfers_used}")

        if transfers_remaining <= 0:
            print("DEBUG: No transfers remaining")
            raise HTTPException(
                status_code=400,
                detail="No transfers remaining. You have used all your transfers for this season."
            )

        # Get the player being transferred out
        team_player_out = db.query(FantasyTeamPlayer).filter_by(
            fantasy_team_id=team_id,
            player_id=request.player_out_id
        ).first()
        print(f"DEBUG: team_player_out found: {team_player_out is not None}")

        if not team_player_out:
            print("DEBUG: Player to transfer out not in team")
            raise HTTPException(
                status_code=404,
                detail="Player to transfer out is not in your team"
            )

        player_out = team_player_out.player
        print(f"DEBUG: player_out loaded: {player_out.name if player_out else 'None'}")

        # Get the player being transferred in
        player_in = db.query(Player).filter_by(id=request.player_in_id).first()
        print(f"DEBUG: player_in found: {player_in is not None}, name={player_in.name if player_in else 'None'}")
        if not player_in:
            print("DEBUG: Player to transfer in not found")
            raise HTTPException(status_code=404, detail="Player to transfer in not found")

        # Verify new player is from the correct club
        if player_in.club_id != league.club_id:
            raise HTTPException(
                status_code=400,
                detail="Player does not belong to this league's club"
            )

        # Check if new player is already in team
        existing = db.query(FantasyTeamPlayer).filter_by(
            fantasy_team_id=team_id,
            player_id=request.player_in_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Player is already in your team"
            )

        print("DEBUG: About to validate league rules")
        # Validate league rules after transfer
        is_valid, error_message = validate_league_rules(
            league=league,
            current_players=team.players,
            player_to_add=player_in,
            player_to_remove_id=request.player_out_id,
            db=db
        )
        print(f"DEBUG: League rules validation result: is_valid={is_valid}, error_message={error_message}")

        if not is_valid:
            print(f"DEBUG: League rules validation failed: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        print("DEBUG: All validations passed, proceeding with transfer")

        # Preserve captain/vice-captain roles
        was_captain = team_player_out.is_captain
        was_vice_captain = team_player_out.is_vice_captain

        # Remove old player
        db.delete(team_player_out)

        # Add new player with preserved roles
        team_player_in = FantasyTeamPlayer(
            fantasy_team_id=team_id,
            player_id=request.player_in_id,
            purchase_value=0,
            is_captain=was_captain,
            is_vice_captain=was_vice_captain
        )

        # Increment transfers used
        team.transfers_used += 1

        db.add(team_player_in)
        db.commit()
        db.refresh(team)

        return {
            "message": "Transfer successful",
            "player_out": {
                "id": player_out.id,
                "name": player_out.name
            },
            "player_in": {
                "id": player_in.id,
                "name": player_in.name
            },
            "transfers_remaining": transfers_remaining - 1
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in transfer_player: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
