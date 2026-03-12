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
    Bulk create/update players from CSV file (Admin only)

    CSV is the source of truth for team assignments.
    - Duplicate names: Updates existing player's team assignment
    - New names: Creates new player

    Required CSV columns:
    - name: Player full name (e.g., "MickBoendermaker")
    - team_name: Team assignment (e.g., "ACC 1", "ACC 2")

    Optional CSV columns:
    - player_type: batsman, bowler, or all-rounder (defaults to null)
    - multiplier: 0.5-5.0 (defaults to 1.0, kept if player exists)
    - is_wicket_keeper: true/false (defaults to false)

    Example CSV:
    name,team_name,player_type,multiplier,is_wicket_keeper
    MickBoendermaker,ACC 1,batsman,1.5,false
    GurlabhSingh,ACC 5,all-rounder,1.46,true
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

    # Get all teams for this club for lookup
    teams = {team.name: team.id for team in db.query(Team).filter_by(club_id=club_id).all()}

    # Get all existing players for this club (for duplicate checking)
    existing_players = {
        player.name.lower(): player
        for player in db.query(Player).filter_by(club_id=club_id).all()
    }

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []
    results = []

    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
        try:
            # Validate required fields
            if 'name' not in row or not row['name'].strip():
                errors.append(f"Row {row_num}: Missing player name")
                skipped_count += 1
                continue

            player_name = row['name'].strip()
            player_name_lower = player_name.lower()

            # Validate team_name (required)
            if 'team_name' not in row or not row['team_name'].strip():
                errors.append(f"Row {row_num}: Missing team_name for {player_name}")
                skipped_count += 1
                continue

            team_name = row['team_name'].strip()
            if team_name not in teams:
                errors.append(f"Row {row_num}: Team '{team_name}' not found for {player_name}")
                skipped_count += 1
                continue

            team_id = teams[team_name]

            # Parse optional fields
            player_type = row.get('player_type', '').strip() or None
            if player_type:
                valid_types = ["batsman", "bowler", "all-rounder"]
                if player_type not in valid_types:
                    errors.append(f"Row {row_num}: Invalid player type '{player_type}' for {player_name}")
                    skipped_count += 1
                    continue

            # Parse multiplier
            multiplier = None
            if 'multiplier' in row and row['multiplier'].strip():
                try:
                    multiplier = float(row['multiplier'])
                    if multiplier < 0.5 or multiplier > 5.0:
                        errors.append(f"Row {row_num}: Multiplier must be between 0.5 and 5.0 for {player_name}")
                        skipped_count += 1
                        continue
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid multiplier value for {player_name}")
                    skipped_count += 1
                    continue

            # Parse is_wicket_keeper
            is_wicket_keeper = False
            if 'is_wicket_keeper' in row and row['is_wicket_keeper'].strip():
                wk_value = row['is_wicket_keeper'].strip().lower()
                is_wicket_keeper = wk_value in ['true', '1', 'yes']

            # Check for duplicate - UPDATE if exists, CREATE if new
            if player_name_lower in existing_players:
                # DUPLICATE FOUND - Update existing player
                existing_player = existing_players[player_name_lower]

                # CSV is leading for team assignment - always update
                existing_player.team_id = team_id

                # Update player_type if provided in CSV
                if player_type is not None:
                    existing_player.player_type = player_type

                # Only update multiplier if explicitly provided in CSV
                if multiplier is not None:
                    existing_player.multiplier = multiplier

                # Update is_wicket_keeper if provided
                if 'is_wicket_keeper' in row:
                    existing_player.is_wicket_keeper = is_wicket_keeper

                updated_count += 1
                results.append({
                    "action": "updated",
                    "name": player_name,
                    "team_name": team_name,
                    "player_type": existing_player.player_type,
                    "multiplier": existing_player.multiplier,
                    "is_wicket_keeper": existing_player.is_wicket_keeper
                })

            else:
                # NEW PLAYER - Create
                player = Player(
                    id=str(uuid.uuid4()),
                    name=player_name,
                    club_id=club_id,
                    team_id=team_id,
                    player_type=player_type,
                    multiplier=multiplier if multiplier is not None else 1.0,
                    is_wicket_keeper=is_wicket_keeper,
                    created_by=admin["user_id"]
                )

                db.add(player)
                existing_players[player_name_lower] = player  # Add to cache to catch duplicates within CSV

                created_count += 1
                results.append({
                    "action": "created",
                    "name": player_name,
                    "team_name": team_name,
                    "player_type": player.player_type,
                    "multiplier": player.multiplier,
                    "is_wicket_keeper": player.is_wicket_keeper
                })

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            skipped_count += 1

    # Commit all changes
    if created_count > 0 or updated_count > 0:
        db.commit()

    return {
        "message": f"Bulk upload completed: {created_count} created, {updated_count} updated, {skipped_count} skipped",
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "error_count": len(errors),
        "results": results if len(results) <= 50 else results[:50],  # Limit to first 50 for display
        "total_processed": created_count + updated_count,
        "errors": errors if errors else None
    }
