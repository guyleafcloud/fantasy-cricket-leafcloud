#!/usr/bin/env python3
"""
Admin API Endpoints for Season Setup
=====================================
Administrative endpoints for configuring seasons, clubs, teams, and players.
Only accessible to users with admin role.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from jose import jwt
from sqlalchemy.orm import Session
import os

from database import get_db
from database_models import Season, Club, Team, Player, User, League, FantasyTeam
from season_setup_service import SeasonSetupService

# Router for admin endpoints
router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# =============================================================================
# PYDANTIC MODELS FOR ADMIN OPERATIONS
# =============================================================================

class SeasonCreate(BaseModel):
    """Create a new season"""
    year: str = Field(..., example="2026")
    name: str = Field(..., example="Topklasse 2026")
    start_date: str = Field(..., example="2026-04-01")
    end_date: str = Field(..., example="2026-09-30")
    description: Optional[str] = None
    is_active: bool = True

class SeasonUpdate(BaseModel):
    """Update season settings"""
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    registration_open: Optional[bool] = None

class ClubCreate(BaseModel):
    """Create a new club"""
    season_id: Optional[str] = Field(None, description="Season ID this club belongs to")
    name: str = Field(..., example="ACC")
    tier: str = Field(default="HOOFDKLASSE", example="HOOFDKLASSE")
    location: Optional[str] = Field(None, example="Amsterdam")
    founded_year: Optional[int] = Field(None, example=1921)

class TeamCreate(BaseModel):
    """Create a team within a club"""
    name: str = Field(..., example="ACC 1")
    level: str = Field(..., example="1st")
    tier_type: str = Field(default="senior", example="senior")
    multiplier: float = Field(default=1.0, example=1.2)

class PlayerValueUpdate(BaseModel):
    """Update player value"""
    player_id: str
    new_value: float = Field(..., ge=1.0, le=100.0)
    reason: Optional[str] = None

class LeagueTemplate(BaseModel):
    """League configuration template"""
    name: str = Field(..., example="Standard League")
    squad_size: int = Field(default=11, ge=11, le=15, description="Team size (11 players)")
    budget: float = Field(default=500.0, ge=100.0, description="Budget in EUR")
    currency: str = Field(default="EUR")
    min_players_per_team: int = Field(default=1, description="Minimum players from each team")
    max_players_per_team: int = Field(default=2, description="Maximum players from any team")
    require_from_each_team: bool = Field(default=True, description="Require 1 from all 10 teams")

# =============================================================================
# AUTHENTICATION & AUTHORIZATION
# =============================================================================

async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify that the user has admin privileges"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        is_admin = payload.get("is_admin", False)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        return {"user_id": user_id, "is_admin": is_admin}

    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# =============================================================================
# SEASON MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/seasons", status_code=status.HTTP_201_CREATED)
async def create_season(
    season: SeasonCreate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new season (Admin only)

    Creates a new cricket season with configuration settings.
    Only one season can be active at a time.
    """
    try:
        service = SeasonSetupService(db)

        # Parse dates
        start_date = datetime.fromisoformat(season.start_date)
        end_date = datetime.fromisoformat(season.end_date)

        # Create season
        created_season = service.create_season(
            year=season.year,
            name=season.name,
            start_date=start_date,
            end_date=end_date,
            description=season.description,
            created_by=admin["user_id"],
            activate=season.is_active
        )

        db.commit()

        return {
            "message": "Season created successfully",
            "season": {
                "id": created_season.id,
                "year": created_season.year,
                "name": created_season.name,
                "is_active": created_season.is_active,
                "start_date": created_season.start_date.isoformat(),
                "end_date": created_season.end_date.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create season: {str(e)}")

@router.get("/seasons")
async def list_seasons(
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """List all seasons (Admin only)"""
    seasons = db.query(Season).order_by(Season.year.desc()).all()

    return {
        "seasons": [
            {
                "id": s.id,
                "year": s.year,
                "name": s.name,
                "is_active": s.is_active,
                "registration_open": s.registration_open,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "description": s.description,
                "clubs_count": len(s.clubs),
                "created_at": s.created_at.isoformat()
            }
            for s in seasons
        ]
    }

@router.get("/seasons/{season_id}")
async def get_season(
    season_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get detailed season information (Admin only)"""
    season = db.query(Season).filter_by(id=season_id).first()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Count players across all clubs
    total_players = sum(len(club.players) for club in season.clubs)

    return {
        "id": season.id,
        "year": season.year,
        "name": season.name,
        "is_active": season.is_active,
        "registration_open": season.registration_open,
        "scraping_enabled": season.scraping_enabled,
        "start_date": season.start_date.isoformat(),
        "end_date": season.end_date.isoformat(),
        "description": season.description,
        "clubs_count": len(season.clubs),
        "players_count": total_players,
        "leagues_count": len(season.leagues),
        "created_at": season.created_at.isoformat()
    }

@router.patch("/seasons/{season_id}")
async def update_season(
    season_id: str,
    updates: SeasonUpdate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Update season settings (Admin only)"""
    season = db.query(Season).filter_by(id=season_id).first()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Apply updates
    update_data = updates.dict(exclude_none=True)

    if "start_date" in update_data:
        update_data["start_date"] = datetime.fromisoformat(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = datetime.fromisoformat(update_data["end_date"])

    for key, value in update_data.items():
        setattr(season, key, value)

    db.commit()

    return {
        "message": "Season updated successfully",
        "season_id": season_id,
        "updates": list(update_data.keys())
    }

@router.post("/seasons/{season_id}/activate")
async def activate_season(
    season_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Activate a season (Admin only)

    Deactivates all other seasons and activates this one.
    Enables league creation and automated scraping.
    """
    service = SeasonSetupService(db)

    try:
        season = service.activate_season(season_id)
        db.commit()

        return {
            "message": "Season activated successfully",
            "season_id": season.id,
            "year": season.year,
            "scraping_enabled": season.scraping_enabled,
            "registration_open": season.registration_open
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate season: {str(e)}")

# =============================================================================
# CLUB & TEAM MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/clubs", status_code=status.HTTP_201_CREATED)
async def create_club(
    club: ClubCreate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Create a new club (Admin only)"""
    # Create club in database with correct schema
    db_club = Club(
        name=club.name,
        tier=club.tier,
        location=club.location,
        founded_year=club.founded_year,
        season_id=club.season_id
    )

    db.add(db_club)
    db.commit()
    db.refresh(db_club)

    return {
        "message": "Club created successfully",
        "club_id": db_club.id,
        "club": {
            "id": db_club.id,
            "name": db_club.name,
            "tier": db_club.tier,
            "location": db_club.location,
            "founded_year": db_club.founded_year,
            "season_id": db_club.season_id
        }
    }

@router.get("/clubs")
async def list_clubs(
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """List all clubs (Admin only)"""
    clubs = db.query(Club).all()

    return {
        "clubs": [
            {
                "id": club.id,
                "name": club.name,
                "full_name": club.full_name,
                "country": club.country,
                "cricket_board": club.cricket_board,
                "teams_count": len(club.teams) if club.teams else 0,
                "players_count": len(club.players) if club.players else 0
            }
            for club in clubs
        ]
    }

@router.post("/clubs/{club_id}/teams", status_code=status.HTTP_201_CREATED)
async def create_team(
    club_id: str,
    team: TeamCreate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Create a team within a club (Admin only)"""
    # Verify club exists
    club = db.query(Club).filter_by(id=club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail=f"Club not found: {club_id}")

    # Create team in database
    db_team = Team(
        club_id=club_id,
        name=team.name,
        level=team.level,
        tier_type=team.tier_type,
        value_multiplier=team.multiplier,
        points_multiplier=team.multiplier
    )

    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    return {
        "message": "Team created successfully",
        "team_id": db_team.id,
        "club_id": club_id,
        "team": {
            "id": db_team.id,
            "name": db_team.name,
            "level": db_team.level,
            "tier_type": db_team.tier_type,
            "value_multiplier": db_team.value_multiplier,
            "points_multiplier": db_team.points_multiplier
        }
    }

@router.get("/clubs/{club_id}/teams")
async def list_club_teams(
    club_id: str,
    admin: dict = Depends(verify_admin)
):
    """List all teams for a club (Admin only)"""
    # TODO: Fetch from database
    return {
        "club_id": club_id,
        "teams": []
    }

@router.patch("/teams/{team_id}/multiplier")
async def update_team_multiplier(
    team_id: str,
    multiplier: float,
    admin: dict = Depends(verify_admin)
):
    """Update fantasy points multiplier for a team (Admin only)"""
    # TODO: Update in database
    return {
        "message": "Team multiplier updated",
        "team_id": team_id,
        "multiplier": multiplier
    }

# =============================================================================
# PLAYER MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/clubs/{club_id}/players")
async def get_club_players(
    club_id: str,
    role: Optional[str] = None,
    min_multiplier: Optional[float] = None,
    max_multiplier: Optional[float] = None,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Get all players for a club (Admin only)

    Supports filtering by role and multiplier range.
    """
    query = db.query(Player).filter_by(club_id=club_id)

    # Apply filters
    if role:
        query = query.filter(Player.role == role)
    if min_multiplier:
        query = query.filter(Player.multiplier >= min_multiplier)
    if max_multiplier:
        query = query.filter(Player.multiplier <= max_multiplier)

    players = query.all()

    return {
        "club_id": club_id,
        "total_players": len(players),
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "tier": p.tier,
                "base_price": p.base_price,
                "current_price": p.current_price,
                "multiplier": p.multiplier,
                "multiplier_updated_at": p.multiplier_updated_at.isoformat() if p.multiplier_updated_at else None,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat()
            }
            for p in players
        ]
    }

class PlayerManualAdd(BaseModel):
    """Add a player manually"""
    name: str
    role: str = Field(..., description="Player role: BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER")
    tier: str = Field(default="HOOFDKLASSE", description="Cricket tier")
    base_price: int = Field(default=100, description="Base price in credits")
    current_price: Optional[int] = None
    multiplier: float = Field(default=1.0, ge=0.5, le=5.0, description="Performance multiplier (0.5-5.0)")

@router.post("/clubs/{club_id}/players", status_code=status.HTTP_201_CREATED)
async def add_player_manually(
    club_id: str,
    player: PlayerManualAdd,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Manually add a new player to a club (Admin only)

    Use this to add players who weren't in the legacy roster
    or to add new players during the season.
    """
    try:
        # Verify club exists
        club = db.query(Club).filter_by(id=club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail=f"Club not found: {club_id}")

        # Create player
        new_player = Player(
            club_id=club_id,
            name=player.name,
            role=player.role,
            tier=player.tier,
            base_price=player.base_price,
            current_price=player.current_price or player.base_price,
            multiplier=player.multiplier,
            multiplier_updated_at=datetime.utcnow(),
            is_active=True
        )

        db.add(new_player)
        db.commit()
        db.refresh(new_player)

        return {
            "message": "Player added successfully",
            "player": {
                "id": new_player.id,
                "name": new_player.name,
                "role": new_player.role,
                "tier": new_player.tier,
                "base_price": new_player.base_price,
                "current_price": new_player.current_price,
                "multiplier": new_player.multiplier
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add player: {str(e)}")

@router.patch("/players/{player_id}/value")
async def update_player_value(
    player_id: str,
    update: PlayerValueUpdate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Update a player's fantasy team value (Admin only)

    Sets the cost for adding this player to a fantasy team.
    Changes are tracked in price history.
    """
    try:
        service = SeasonSetupService(db)

        updated_player = service.update_player_value(
            player_id=update.player_id,
            new_value=update.new_value,
            reason=update.reason or "Manual adjustment",
            changed_by=admin["user_id"]
        )

        db.commit()

        return {
            "message": "Player value updated",
            "player": {
                "id": updated_player.id,
                "name": updated_player.name,
                "fantasy_value": updated_player.fantasy_value,
                "manually_adjusted": updated_player.value_manually_adjusted
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update value: {str(e)}")

class PlayerUpdate(BaseModel):
    """Update player details"""
    name: Optional[str] = None
    role: Optional[str] = Field(None, description="Player role: BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER")
    tier: Optional[str] = Field(None, description="Cricket tier")
    base_price: Optional[int] = None
    current_price: Optional[int] = None
    multiplier: Optional[float] = Field(None, ge=0.5, le=5.0, description="Performance multiplier (0.5-5.0)")
    is_active: Optional[bool] = None

@router.put("/players/{player_id}")
async def update_player(
    player_id: str,
    update: PlayerUpdate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Update player details (Admin only)

    Allows editing player name, role, tier, pricing, multiplier, and active status.
    """
    try:
        # Get player
        player = db.query(Player).filter_by(id=player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail=f"Player not found: {player_id}")

        # Update fields
        if update.name is not None:
            player.name = update.name

        if update.role is not None:
            player.role = update.role

        if update.tier is not None:
            player.tier = update.tier

        if update.base_price is not None:
            player.base_price = update.base_price

        if update.current_price is not None:
            player.current_price = update.current_price

        if update.multiplier is not None:
            player.multiplier = update.multiplier
            player.multiplier_updated_at = datetime.utcnow()

        if update.is_active is not None:
            player.is_active = update.is_active

        db.commit()
        db.refresh(player)

        return {
            "message": "Player updated successfully",
            "player": {
                "id": player.id,
                "name": player.name,
                "role": player.role,
                "tier": player.tier,
                "base_price": player.base_price,
                "current_price": player.current_price,
                "multiplier": player.multiplier,
                "multiplier_updated_at": player.multiplier_updated_at.isoformat() if player.multiplier_updated_at else None,
                "is_active": player.is_active
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update player: {str(e)}")

@router.delete("/players/{player_id}")
async def delete_player(
    player_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Remove a player from the roster (Admin only)

    This will also remove the player from any fantasy teams.
    """
    try:
        # Get player
        player = db.query(Player).filter_by(id=player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail=f"Player not found: {player_id}")

        player_name = player.name

        # Delete player (cascade will handle fantasy_team_players and price_history)
        db.delete(player)
        db.commit()

        return {
            "message": "Player deleted successfully",
            "player_id": player_id,
            "player_name": player_name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete player: {str(e)}")

@router.post("/players/bulk-value-update")
async def bulk_update_player_values(
    updates: List[PlayerValueUpdate],
    admin: dict = Depends(verify_admin)
):
    """Bulk update player values (Admin only)"""
    # TODO: Batch update in database
    return {
        "message": f"Updated {len(updates)} player values",
        "updated_count": len(updates)
    }

@router.get("/players/unassigned")
async def get_unassigned_players(admin: dict = Depends(verify_admin)):
    """Get players not assigned to any team (Admin only)"""
    # TODO: Query database for players with team_id = NULL
    return {
        "unassigned_players": []
    }

# =============================================================================
# LEAGUE TEMPLATE CONFIGURATION
# =============================================================================

@router.post("/league-templates", status_code=status.HTTP_201_CREATED)
async def create_league_template(
    template: LeagueTemplate,
    admin: dict = Depends(verify_admin)
):
    """
    Create a league configuration template (Admin only)

    Users can select from these templates when creating leagues.
    """
    # TODO: Save to database
    return {
        "message": "League template created",
        "template_id": "temp_template_id",
        "template": template.dict()
    }

@router.get("/league-templates")
async def list_league_templates(admin: dict = Depends(verify_admin)):
    """List all league templates (Admin only)"""
    # TODO: Fetch from database
    return {
        "templates": [
            {
                "id": "standard",
                "name": "Standard League",
                "squad_size": 15,
                "budget": 500.0
            }
        ]
    }

# =============================================================================
# DATA IMPORT ENDPOINTS
# =============================================================================

class SeasonSetupRequest(BaseModel):
    """Complete season setup with club and roster"""
    year: str = Field(..., example="2026")
    season_name: str = Field(..., example="Topklasse 2026")
    start_date: str = Field(..., example="2026-04-01")
    end_date: str = Field(..., example="2026-09-30")
    club_name: str = Field(..., example="ACC")
    club_full_name: str = Field(..., example="Amsterdamsche Cricket Club")
    roster_file: str = Field(default="rosters/acc_2025_complete.json")
    activate: bool = Field(default=True)


class PasswordResetRequest(BaseModel):
    """Request body for password reset"""
    new_password: str = Field(..., min_length=6)


@router.post("/setup-season", status_code=status.HTTP_201_CREATED)
async def setup_complete_season(
    request: SeasonSetupRequest,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Complete season setup workflow (Admin only)

    This is the main endpoint for admins to set up a new season:
    1. Creates the season
    2. Creates the club
    3. Creates teams (1st, 2nd, 3rd, social)
    4. Loads all players from legacy roster JSON
    5. Optionally activates the season

    Example request:
    {
        "year": "2026",
        "season_name": "Topklasse 2026",
        "start_date": "2026-04-01",
        "end_date": "2026-09-30",
        "club_name": "ACC",
        "club_full_name": "Amsterdamsche Cricket Club",
        "roster_file": "rosters/acc_2025_complete.json",
        "activate": true
    }
    """
    try:
        service = SeasonSetupService(db)

        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)

        # Run complete setup workflow
        result = service.setup_season_with_club(
            year=request.year,
            season_name=request.season_name,
            start_date=start_date,
            end_date=end_date,
            club_name=request.club_name,
            club_full_name=request.club_full_name,
            roster_file_path=request.roster_file,
            created_by=admin["user_id"],
            activate=request.activate
        )

        db.commit()

        return {
            "message": f"Season {request.year} setup complete!",
            "result": result
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Roster file not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to setup season: {str(e)}")

@router.post("/clubs/{club_id}/load-roster")
async def load_roster_for_club(
    club_id: str,
    roster_file: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Load legacy roster for an existing club (Admin only)

    Use this endpoint to load additional players or reload a roster
    for a club that already exists.
    """
    try:
        service = SeasonSetupService(db)

        result = service.load_legacy_roster(
            club_id=club_id,
            roster_file_path=roster_file
        )

        db.commit()

        return {
            "message": "Roster loaded successfully",
            "result": result
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Roster file not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to load roster: {str(e)}")

# =============================================================================
# SYSTEM MANAGEMENT
# =============================================================================

@router.get("/system/status")
async def get_system_status(admin: dict = Depends(verify_admin)):
    """Get system status and configuration (Admin only)"""
    return {
        "scraping_enabled": True,
        "active_season": "2026",
        "total_clubs": 1,
        "total_players": 25,
        "total_leagues": 0,
        "last_scrape": None,
        "next_scrape": "Monday 01:00 AM"
    }

@router.post("/scrape/trigger")
async def trigger_manual_scrape(
    clubs: Optional[List[str]] = None,
    days_back: int = 7,
    admin: dict = Depends(verify_admin)
):
    """
    Manually trigger a scraping task (Admin only)

    Useful for testing or catching up on missed data.
    """
    # TODO: Trigger celery task
    return {
        "message": "Scraping task triggered",
        "clubs": clubs or ["ACC"],
        "days_back": days_back,
        "status": "queued"
    }

@router.get("/health/admin")
async def admin_health_check(admin: dict = Depends(verify_admin)):
    """Admin-authenticated health check"""
    return {
        "status": "healthy",
        "admin": True,
        "user_id": admin["user_id"],
        "timestamp": datetime.utcnow().isoformat()
    }

# =============================================================================
# PLAYER VALUE CALCULATION
# =============================================================================

@router.post("/calculate-values/{club_name}")
async def calculate_club_player_values(
    club_name: str,
    season_year: str = "2025",
    admin: dict = Depends(verify_admin)
):
    """
    Calculate fantasy values for all players in a club (Admin only)

    Uses the PlayerValueCalculator to assign initial values based on
    their 2025 season performance. Values are calculated relative to
    other players in the same club.

    This should be run:
    - When setting up a new season
    - After importing legacy rosters
    - When you want to recalculate based on new data
    """
    # TODO: Implement actual calculation
    # 1. Load all players from club (from database or aggregator)
    # 2. Convert to PlayerStats format
    # 3. Run calculator.calculate_team_values()
    # 4. Update player values in database
    # 5. Log price changes

    return {
        "message": f"Value calculation triggered for {club_name}",
        "club": club_name,
        "season": season_year,
        "status": "processing",
        "note": "This endpoint will calculate values based on 2025 performance data"
    }

@router.get("/player-value-breakdown/{player_id}")
async def get_player_value_breakdown(
    player_id: str,
    admin: dict = Depends(verify_admin)
):
    """
    Get detailed breakdown of how a player's value was calculated (Admin only)

    Useful for understanding why a player has a certain value
    and for making informed manual adjustments.
    """
    # TODO: Fetch player stats and recalculate to show breakdown
    return {
        "player_id": player_id,
        "current_value": 35.0,
        "breakdown": {
            "performance_score": 62.1,
            "batting_contribution": 25.5,
            "bowling_contribution": 30.0,
            "fielding_contribution": 6.6,
            "tier_adjustment": 0.0,
            "consistency_bonus": 0.0
        },
        "justification": "Detailed calculation breakdown will appear here"
    }


# =============================================================================
# USER MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/users")
async def list_users(
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """List all users in the system"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    }


@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Promote a user to admin status"""
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    user.is_admin = True
    db.commit()
    
    return {
        "message": f"User {user.email} promoted to admin",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    }


@router.post("/users/{user_id}/demote")
async def demote_admin_user(
    user_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Demote an admin user to regular user"""
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )
    
    # Prevent demoting yourself
    requesting_user_id = admin_data.get("user_id")
    if user.id == requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    user.is_admin = False
    db.commit()
    
    return {
        "message": f"User {user.email} demoted to regular user",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    }


@router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to reset a user's password"""
    from user_auth_endpoints import hash_password

    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Hash and update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {
        "message": f"Password reset for user {user.email}",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to permanently delete a user"""

    # Prevent admins from deleting themselves
    admin_user_id = admin_data.get("sub") or admin_data.get("user_id")
    if user_id == admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_email = user.email
    db.delete(user)
    db.commit()

    return {
        "message": f"User {user_email} deleted successfully",
        "deleted_user_id": user_id
    }


@router.delete("/leagues/{league_id}")
async def delete_league(
    league_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to delete a league and all associated fantasy teams"""
    
    league = db.query(League).filter(League.id == league_id).first()
    
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Count fantasy teams that will be deleted
    team_count = db.query(FantasyTeam).filter(FantasyTeam.league_id == league_id).count()
    
    # Delete the league (cascade will delete fantasy teams)
    db.delete(league)
    db.commit()
    
    return {
        "message": f"League '{league.name}' deleted successfully",
        "league_id": league_id,
        "fantasy_teams_deleted": team_count
    }
