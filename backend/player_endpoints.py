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
                existing_player.rl_team = team_name  # NEW: Also update rl_team field

                # Update player_type if provided in CSV
                if player_type is not None:
                    existing_player.player_type = player_type
                    existing_player.role = player_type.upper().replace('-', '_')  # NEW: Also update role field

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
                    rl_team=team_name,  # NEW: Set rl_team field
                    player_type=player_type,
                    role=player_type.upper().replace('-', '_') if player_type else 'ALL_ROUNDER',  # NEW: Set role field
                    multiplier=multiplier if multiplier is not None else 1.0,
                    is_wicket_keeper=is_wicket_keeper,
                    tier='HOOFDKLASSE',  # NEW: Set tier field
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


# =============================================================================
# DATA QUALITY ENDPOINTS
# =============================================================================

@router.get("/players/quality-check")
async def player_quality_check(
    club_id: Optional[str] = None,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Run data quality checks on player roster (Admin only)

    Checks for:
    - Invalid player names (dates, scorecard text, team names)
    - Default multiplier players (likely opposition players)
    - Duplicate player names
    - Players without team assignments
    - Opposition team players

    Returns detailed report with recommendations.
    """
    import re
    from sqlalchemy import func
    from collections import defaultdict

    # Define validation patterns
    INVALID_PATTERNS = [
        (r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', 'Date format'),
        (r'EXTRAS:', 'Scorecard text'),
        (r'Fall of wickets', 'Scorecard text'),
        (r'^c\s+\w+\s+b\s+\w+', 'Dismissal notation'),
        (r'^\d+\s+(CEST|GMT)', 'Timestamp'),
        (r'CSV Test Player', 'Test data'),
        (r'^Team\s+\d', 'Team placeholder'),
        (r'TOTAL:', 'Scorecard total'),
        (r'Result:', 'Match result'),
        (r'Toss won by', 'Match metadata'),
        (r'Venue:', 'Match metadata'),
    ]

    OPPOSITION_TEAMS = [
        'Rood en Wit', 'Salland', 'Ajax', 'Quick', 'VRA', 'VOC', 'Kampong',
        'HCC', 'HBS', 'Excelsior', 'VVV', 'Qui Vive', 'Voorburg', 'Hercules',
        'Dosti', 'SV Kampong', 'Bloemendaal', 'Koninklijke', 'HCC 1', 'VRA 1',
        'Ajax 1', 'Quick 1', 'VOC 1', 'Kampong 1', 'Kampong 2', 'Kampong 3'
    ]

    # Build query
    query = db.query(Player)
    if club_id:
        query = query.filter(Player.club_id == club_id)

    players = query.all()

    issues = {
        'invalid_names': [],
        'default_multipliers': [],
        'duplicates': [],
        'no_team_assignment': [],
        'opposition_players': [],
        'suspicious_patterns': []
    }

    # Track name counts for duplicate detection
    name_counts = defaultdict(list)

    for player in players:
        # Check for invalid name patterns
        for pattern, reason in INVALID_PATTERNS:
            if re.search(pattern, player.name, re.IGNORECASE):
                issues['invalid_names'].append({
                    'id': player.id,
                    'name': player.name,
                    'reason': reason,
                    'team': getattr(player, 'rl_team', 'Unknown')
                })
                break

        # Check for default multipliers (potential opposition players)
        if player.multiplier == 1.0 and hasattr(player, 'role'):
            role_val = player.role
            if isinstance(role_val, str):
                role_str = role_val
            else:
                # It's an enum
                role_str = str(role_val.value) if hasattr(role_val, 'value') else str(role_val)

            if role_str in ['ALL_ROUNDER', 'all-rounder', None, '']:
                issues['default_multipliers'].append({
                    'id': player.id,
                    'name': player.name,
                    'team': getattr(player, 'rl_team', 'Unknown'),
                    'role': role_str
                })

        # Check for opposition team names
        for opp_team in OPPOSITION_TEAMS:
            if opp_team.lower() in player.name.lower():
                issues['opposition_players'].append({
                    'id': player.id,
                    'name': player.name,
                    'matched_pattern': opp_team,
                    'team': getattr(player, 'rl_team', 'Unknown')
                })
                break

        # Check for missing team assignment
        if not hasattr(player, 'rl_team') or not player.rl_team:
            issues['no_team_assignment'].append({
                'id': player.id,
                'name': player.name
            })

        # Track for duplicate detection
        name_counts[player.name.lower()].append({
            'id': player.id,
            'name': player.name,
            'team': getattr(player, 'rl_team', 'Unknown')
        })

        # Check for suspicious patterns
        # Single letter names
        if len(player.name) == 1 or player.name.upper() in ['W', 'O', 'M', 'NB', 'LB']:
            issues['suspicious_patterns'].append({
                'id': player.id,
                'name': player.name,
                'reason': 'Single letter or cricket abbreviation',
                'team': getattr(player, 'rl_team', 'Unknown')
            })
        # All uppercase names (often opposition)
        elif player.name.isupper() and len(player.name) > 3:
            issues['suspicious_patterns'].append({
                'id': player.id,
                'name': player.name,
                'reason': 'All uppercase',
                'team': getattr(player, 'rl_team', 'Unknown')
            })

    # Find duplicates
    for name, player_list in name_counts.items():
        if len(player_list) > 1:
            issues['duplicates'].append({
                'name': name,
                'count': len(player_list),
                'players': player_list
            })

    # Calculate summary statistics
    total_issues = sum(len(v) for v in issues.values())
    total_players = len(players)

    # Generate recommendations
    recommendations = []
    if issues['invalid_names']:
        recommendations.append(f"Delete {len(issues['invalid_names'])} players with invalid names (dates, scorecard text)")
    if issues['default_multipliers']:
        recommendations.append(f"Review {len(issues['default_multipliers'])} players with default multipliers (might be opposition)")
    if issues['duplicates']:
        recommendations.append(f"Merge {len(issues['duplicates'])} duplicate player records")
    if issues['no_team_assignment']:
        recommendations.append(f"Assign teams to {len(issues['no_team_assignment'])} players")
    if issues['opposition_players']:
        recommendations.append(f"Remove {len(issues['opposition_players'])} opposition team players")
    if issues['suspicious_patterns']:
        recommendations.append(f"Review {len(issues['suspicious_patterns'])} players with suspicious name patterns")

    # Health score (0-100)
    health_score = max(0, 100 - (total_issues / total_players * 100)) if total_players > 0 else 100

    return {
        "summary": {
            "total_players": total_players,
            "total_issues": total_issues,
            "health_score": round(health_score, 1),
            "status": "excellent" if health_score >= 95 else "good" if health_score >= 85 else "fair" if health_score >= 70 else "poor"
        },
        "issues": issues,
        "recommendations": recommendations,
        "timestamp": "2026-03-12T00:00:00Z"  # Could use datetime.utcnow().isoformat()
    }
