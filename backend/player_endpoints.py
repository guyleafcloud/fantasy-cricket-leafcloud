"""
Player Management Endpoints

Admin endpoints for creating and managing players
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from database_models import Player, Club, Team
from admin_endpoints import verify_admin
import csv
import io
import uuid

router = APIRouter(prefix="/api/admin", tags=["players"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class PlayerCreate(BaseModel):
    name: str
    club_id: str
    team_id: Optional[str] = None
    player_type: Optional[str] = None  # batsman, bowler, all-rounder
    is_wicket_keeper: bool = False  # Secondary flag for wicket-keepers
    multiplier: float = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "club_id": "a7a580a7-7d3f-476c-82ea-afa6ae7ee276",
                "team_id": "some-team-id",
                "player_type": "batsman",
                "is_wicket_keeper": False,
                "multiplier": 1.5
            }
        }


# =============================================================================
# PLAYER MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/players", status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Create a new player (Admin only)"""

    # Verify club exists
    club = db.query(Club).filter_by(id=player_data.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Verify team exists if provided
    if player_data.team_id:
        team = db.query(Team).filter_by(id=player_data.team_id, club_id=player_data.club_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found in this club")

    # Validate player type
    valid_types = ["batsman", "bowler", "all-rounder", None]
    if player_data.player_type and player_data.player_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid player type. Must be one of: {valid_types}")

    # Validate multiplier
    if player_data.multiplier < 0.5 or player_data.multiplier > 5.0:
        raise HTTPException(status_code=400, detail="Multiplier must be between 0.5 and 5.0")

    # Create player
    player = Player(
        id=str(uuid.uuid4()),
        name=player_data.name,
        club_id=player_data.club_id,
        team_id=player_data.team_id,
        player_type=player_data.player_type,
        is_wicket_keeper=player_data.is_wicket_keeper,
        multiplier=player_data.multiplier,
        created_by=admin["user_id"]
    )

    db.add(player)
    db.commit()
    db.refresh(player)

    return {
        "message": "Player created successfully",
        "player": {
            "id": player.id,
            "name": player.name,
            "club_id": player.club_id,
            "team_id": player.team_id,
            "player_type": player.player_type,
            "is_wicket_keeper": player.is_wicket_keeper,
            "multiplier": player.multiplier
        }
    }


@router.post("/players/bulk", status_code=status.HTTP_201_CREATED)
async def create_players_bulk(
    file: UploadFile = File(...),
    club_id: str = None,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Bulk create players from CSV file (Admin only)

    CSV format:
    name,team_name,player_type,multiplier

    Example:
    John Doe,ACC 1,batsman,1.5
    Jane Smith,ACC 2,bowler,2.0
    """

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # If no club_id provided, try to get default ACC club
    if not club_id:
        club = db.query(Club).filter(Club.name == "ACC").first()
        if not club:
            raise HTTPException(status_code=400, detail="Club ID required or ACC club not found")
        club_id = club.id
    else:
        # Verify club exists
        club = db.query(Club).filter_by(id=club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")

    # Read and parse CSV
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_file)

    created_players = []
    errors = []

    # Get all teams for this club for lookup
    teams = {team.name: team.id for team in db.query(Team).filter_by(club_id=club_id).all()}

    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
        try:
            # Validate required fields
            if 'name' not in row or not row['name'].strip():
                errors.append(f"Row {row_num}: Missing player name")
                continue

            # Get team_id if team_name provided
            team_id = None
            if 'team_name' in row and row['team_name'].strip():
                team_name = row['team_name'].strip()
                if team_name in teams:
                    team_id = teams[team_name]
                else:
                    errors.append(f"Row {row_num}: Team '{team_name}' not found")
                    continue

            # Parse player type
            player_type = row.get('player_type', '').strip() or None
            if player_type:
                valid_types = ["batsman", "bowler", "all-rounder"]
                if player_type not in valid_types:
                    errors.append(f"Row {row_num}: Invalid player type '{player_type}'")
                    continue

            # Parse multiplier
            try:
                multiplier = float(row.get('multiplier', 1.0))
                if multiplier < 0.5 or multiplier > 5.0:
                    errors.append(f"Row {row_num}: Multiplier must be between 0.5 and 5.0")
                    continue
            except ValueError:
                errors.append(f"Row {row_num}: Invalid multiplier value")
                continue

            # Create player
            player = Player(
                id=str(uuid.uuid4()),
                name=row['name'].strip(),
                club_id=club_id,
                team_id=team_id,
                player_type=player_type,
                multiplier=multiplier,
                created_by=admin["user_id"]
            )

            db.add(player)
            created_players.append({
                "name": player.name,
                "team_name": row.get('team_name', 'N/A'),
                "player_type": player.player_type,
                "multiplier": player.multiplier
            })

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    # Commit all players
    if created_players:
        db.commit()

    return {
        "message": f"Bulk upload completed",
        "created_count": len(created_players),
        "error_count": len(errors),
        "created_players": created_players,
        "errors": errors if errors else None
    }
