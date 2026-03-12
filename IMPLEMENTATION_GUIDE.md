# League-Specific Rosters & Confirmation - Implementation Guide

## Overview

Based on the architecture analysis, this guide outlines how to implement league-specific rosters with proper confirmation/launch functionality.

**Key Finding**: The system already has `LeagueRoster` (junction table) for league-specific players, but lacks:
1. Explicit league confirmation/launch workflow
2. League status management (draft/active/locked)
3. Team finalization endpoints
4. Protection against mid-season rule changes

---

## Phase 1: Add League Status Management (Database)

### 1.1 Database Migration

Add these fields to `League` model in `database_models.py`:

```python
class League(Base):
    # ... existing fields ...
    
    # New status fields
    status = Column(String(50), default="draft")  # draft|active|locked|completed
    confirmed_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Frozen rules snapshot (to prevent mid-season changes)
    frozen_squad_size = Column(Integer, nullable=True)
    frozen_transfers_per_season = Column(Integer, nullable=True)
    frozen_min_batsmen = Column(Integer, nullable=True)
    frozen_min_bowlers = Column(Integer, nullable=True)
    frozen_require_wicket_keeper = Column(Boolean, nullable=True)
    frozen_max_players_per_team = Column(Integer, nullable=True)
    frozen_require_from_each_team = Column(Boolean, nullable=True)
```

**Migration Command**:
```bash
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend
alembic revision --autogenerate -m "Add league status and frozen rules"
alembic upgrade head
```

### 1.2 Add Team Finalization Timestamp

Add to `FantasyTeam`:

```python
class FantasyTeam(Base):
    # ... existing fields ...
    
    finalized_at = Column(DateTime, nullable=True)  # When user locked in their team
```

---

## Phase 2: Implement League Confirmation Workflow

### 2.1 Create League Lifecycle Service

New file: `/backend/league_lifecycle_service.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from database_models import League, FantasyTeam, LeagueRoster
from typing import Tuple, List

class LeagueLifecycleService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def confirm_league(self, league_id: str) -> Tuple[bool, str]:
        """
        Transition league from 'draft' to 'active' status.
        
        - Validates all configuration is complete
        - Freezes league rules
        - Enables team creation
        - Returns: (success, message)
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found"
        
        if league.status != "draft":
            return False, f"League is {league.status}, not draft"
        
        # Validate league configuration
        if not league.squad_size or league.squad_size < 11:
            return False, "Invalid squad size"
        
        if league.squad_size > len(league.roster_players):
            return False, f"Roster has {len(league.roster_players)} players, need {league.squad_size}"
        
        # Check role distribution
        roster_players = self.db.query(LeagueRoster).filter_by(league_id=league_id).all()
        player_ids = [rp.player_id for rp in roster_players]
        
        if len(player_ids) < league.squad_size:
            return False, f"Not enough players: {len(player_ids)} < {league.squad_size}"
        
        # Freeze league rules
        league.status = "active"
        league.confirmed_at = datetime.utcnow()
        league.frozen_squad_size = league.squad_size
        league.frozen_transfers_per_season = league.transfers_per_season
        league.frozen_min_batsmen = league.min_batsmen
        league.frozen_min_bowlers = league.min_bowlers
        league.frozen_require_wicket_keeper = league.require_wicket_keeper
        league.frozen_max_players_per_team = league.max_players_per_team
        league.frozen_require_from_each_team = league.require_from_each_team
        
        self.db.commit()
        return True, "League confirmed and rules frozen"
    
    def lock_league(self, league_id: str) -> Tuple[bool, str]:
        """
        Transition league from 'active' to 'locked' status.
        
        - Prevents new team registration
        - Validates all existing teams are finalized
        - Returns: (success, message)
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found"
        
        if league.status != "active":
            return False, f"League is {league.status}, not active"
        
        # Check all teams are finalized
        unfinalized_teams = self.db.query(FantasyTeam).filter(
            FantasyTeam.league_id == league_id,
            FantasyTeam.is_finalized == False
        ).count()
        
        if unfinalized_teams > 0:
            return False, f"{unfinalized_teams} teams not finalized yet"
        
        league.status = "locked"
        league.locked_at = datetime.utcnow()
        self.db.commit()
        
        return True, "League locked for play"
    
    def complete_league(self, league_id: str) -> Tuple[bool, str]:
        """Mark league as completed (end of season)"""
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found"
        
        league.status = "completed"
        league.completed_at = datetime.utcnow()
        self.db.commit()
        
        return True, "League marked as completed"
    
    def get_league_status(self, league_id: str) -> dict:
        """Get detailed league status and readiness"""
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return None
        
        teams = self.db.query(FantasyTeam).filter_by(league_id=league_id).all()
        finalized_count = sum(1 for t in teams if t.is_finalized)
        
        return {
            "status": league.status,
            "confirmed_at": league.confirmed_at.isoformat() if league.confirmed_at else None,
            "locked_at": league.locked_at.isoformat() if league.locked_at else None,
            "teams_total": len(teams),
            "teams_finalized": finalized_count,
            "roster_size": len(league.roster_players),
            "can_confirm": league.status == "draft",
            "can_lock": league.status == "active" and finalized_count == len(teams),
            "can_complete": league.status == "locked"
        }
```

### 2.2 Add Endpoints to Admin League Management

Update `/backend/admin_endpoints.py` or create new `/backend/league_status_endpoints.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from league_lifecycle_service import LeagueLifecycleService
from database import get_db
from admin_endpoints import verify_admin

router = APIRouter(prefix="/api/admin", tags=["league-status"])

@router.post("/leagues/{league_id}/confirm")
async def confirm_league(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Transition league from draft to active status.
    Freezes league rules and enables team creation.
    """
    service = LeagueLifecycleService(db)
    success, message = service.confirm_league(league_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    status_info = service.get_league_status(league_id)
    
    return {
        "message": message,
        "league_id": league_id,
        "status": status_info
    }


@router.post("/leagues/{league_id}/lock")
async def lock_league(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Lock league - prevent new team registrations, validate all teams finalized.
    """
    service = LeagueLifecycleService(db)
    success, message = service.lock_league(league_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    status_info = service.get_league_status(league_id)
    
    return {
        "message": message,
        "league_id": league_id,
        "status": status_info
    }


@router.post("/leagues/{league_id}/complete")
async def complete_league(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Mark league as completed (end of season)"""
    service = LeagueLifecycleService(db)
    success, message = service.complete_league(league_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "league_id": league_id
    }


@router.get("/leagues/{league_id}/status")
async def get_league_status(
    league_id: str,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get detailed status of league (readiness to play)"""
    service = LeagueLifecycleService(db)
    status = service.get_league_status(league_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="League not found")
    
    return status
```

---

## Phase 3: Team Finalization

### 3.1 Add Team Finalization Service

Update or create `/backend/team_finalization_service.py`:

```python
from datetime import datetime
from sqlalchemy.orm import Session
from database_models import FantasyTeam, League

class TeamFinalizationService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def finalize_team(self, team_id: str) -> Tuple[bool, str]:
        """
        Finalize a fantasy team (lock in for season).
        """
        team = self.db.query(FantasyTeam).filter_by(id=team_id).first()
        if not team:
            return False, "Team not found"
        
        if team.is_finalized:
            return False, "Team already finalized"
        
        league = self.db.query(League).filter_by(id=team.league_id).first()
        if not league:
            return False, "League not found"
        
        if league.status not in ["draft", "active"]:
            return False, f"Cannot finalize team in {league.status} league"
        
        # Validate team composition before finalizing
        from team_validation import validate_team_composition
        is_valid, errors = validate_team_composition(self.db, league, team)
        
        if not is_valid:
            return False, f"Invalid team composition: {', '.join(errors)}"
        
        # Finalize
        team.is_finalized = True
        team.finalized_at = datetime.utcnow()
        self.db.commit()
        
        return True, "Team finalized successfully"
    
    def unfinalize_team(self, team_id: str) -> Tuple[bool, str]:
        """
        Unfinalize a team (admin only, before league locks).
        """
        team = self.db.query(FantasyTeam).filter_by(id=team_id).first()
        if not team:
            return False, "Team not found"
        
        league = self.db.query(League).filter_by(id=team.league_id).first()
        if league.status == "locked":
            return False, "Cannot unfinalize team - league is locked"
        
        team.is_finalized = False
        team.finalized_at = None
        self.db.commit()
        
        return True, "Team unfinalized"
```

### 3.2 Add User-Facing Team Finalization Endpoint

Update `/backend/user_team_endpoints.py`:

```python
@router.post("/leagues/{league_id}/teams/{team_id}/finalize")
async def finalize_team(
    league_id: str,
    team_id: str,
    current_user: dict = Depends(verify_user),
    db: Session = Depends(get_db)
):
    """
    User endpoint: Finalize their fantasy team.
    
    Once finalized, team cannot be edited until admin unfinalizes.
    """
    # Verify team exists and belongs to user
    team = db.query(FantasyTeam).filter_by(
        id=team_id,
        league_id=league_id,
        user_id=current_user["user_id"]
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    service = TeamFinalizationService(db)
    success, message = service.finalize_team(team_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "team_id": team_id,
        "is_finalized": True
    }
```

---

## Phase 4: League-Specific Multipliers (Optional)

### 4.1 Store Multipliers at League Confirmation

When confirming a league, capture current multipliers:

```python
class League(Base):
    # ... existing ...
    
    # Snapshot of multipliers at confirmation
    multipliers_snapshot = Column(JSON, nullable=True)  # {player_id: multiplier}
    multipliers_frozen_at = Column(DateTime, nullable=True)
```

Update `LeagueLifecycleService.confirm_league()`:

```python
def confirm_league(self, league_id: str):
    # ... validation ...
    
    # Capture current multipliers for all roster players
    roster_players = self.db.query(LeagueRoster).filter_by(league_id=league_id).all()
    
    multipliers = {}
    for roster_entry in roster_players:
        player = self.db.query(Player).filter_by(id=roster_entry.player_id).first()
        if player:
            multipliers[player.id] = player.multiplier
    
    league.multipliers_snapshot = multipliers
    league.multipliers_frozen_at = datetime.utcnow()
    
    # ... rest of confirmation ...
```

### 4.2 Use Frozen Multipliers in Scoring

Update scoring logic to use `league.multipliers_snapshot` instead of `player.multiplier`:

```python
def calculate_points_for_performance(performance, team, league):
    # Use frozen multipliers if league is confirmed
    if league.multipliers_snapshot and league.multipliers_frozen_at:
        multiplier = league.multipliers_snapshot.get(performance.player_id, 1.0)
    else:
        multiplier = performance.player.multiplier
    
    # Apply multiplier
    base_points = calculate_base_points(performance)
    with_multiplier = base_points * multiplier
    
    # Apply captain bonus
    if performance.is_captain:
        final_points = with_multiplier * 2.0
    elif performance.is_vice_captain:
        final_points = with_multiplier * 1.5
    else:
        final_points = with_multiplier
    
    return final_points
```

---

## Phase 5: Prevent Rule Changes Mid-Season

### 5.1 Update League Update Endpoint

Modify `/api/admin/leagues/{league_id}` to check status:

```python
@router.patch("/leagues/{league_id}")
async def update_league(
    league_id: str,
    league_data: LeagueUpdate,
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    league = db.query(League).filter_by(id=league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Prevent rule changes if league is locked
    if league.status == "locked":
        raise HTTPException(
            status_code=400,
            detail="Cannot modify locked league"
        )
    
    # Warn if active (but allow - might need adjustments)
    if league.status == "active" and league_data.squad_size is not None:
        logger.warning(f"Rule change on active league {league_id}")
    
    # ... apply updates ...
```

---

## Implementation Checklist

- [ ] Add migration for League status fields
- [ ] Add migration for FantasyTeam.finalized_at
- [ ] Create `league_lifecycle_service.py`
- [ ] Add admin endpoints for league confirmation/lock/complete
- [ ] Create `team_finalization_service.py`
- [ ] Add user endpoint for team finalization
- [ ] Update admin/user endpoints to check league.status
- [ ] Update scoring to use frozen multipliers
- [ ] Add frontend UI for team finalization
- [ ] Add admin UI for league status management
- [ ] Update admin procedures documentation
- [ ] Test end-to-end workflow

---

## Testing Scenarios

### Scenario 1: Complete League Confirmation Flow

```
1. Admin creates league (draft status)
2. Admin confirms league (draft → active)
3. Users create teams
4. Users finalize teams one by one
5. Admin locks league when all finalized (active → locked)
6. Season plays out
7. Admin marks complete (locked → completed)
```

### Scenario 2: Prevent Mid-Season Rule Changes

```
1. Admin creates league with squad_size=11
2. Admin confirms league (rules frozen)
3. Admin tries to change squad_size to 15
4. ✓ Endpoint returns error: "Cannot modify locked league"
```

### Scenario 3: Prevent Finalizing Incomplete Team

```
1. User creates team with only 10 players
2. User tries to finalize
3. ✓ Validation returns error: "Missing 1 player"
```

---

## Database Queries for Testing

```sql
-- Check league status
SELECT id, name, status, confirmed_at, locked_at FROM leagues ORDER BY created_at DESC;

-- Check team finalization
SELECT ft.id, ft.team_name, ft.is_finalized, ft.finalized_at, l.status
FROM fantasy_teams ft
JOIN leagues l ON ft.league_id = l.id
ORDER BY ft.created_at;

-- Check frozen rules
SELECT id, name, status, frozen_squad_size, frozen_min_batsmen FROM leagues WHERE status = 'active';

-- Check frozen multipliers
SELECT id, name, 
       jsonb_object_keys(multipliers_snapshot) as player_count,
       multipliers_frozen_at
FROM leagues WHERE multipliers_snapshot IS NOT NULL;
```

---

**File Locations for Implementation:**
- Database Models: `/backend/database_models.py`
- New Services: `/backend/league_lifecycle_service.py`, `/backend/team_finalization_service.py`
- Admin Endpoints: `/backend/admin_endpoints.py` or new `/backend/league_status_endpoints.py`
- User Endpoints: `/backend/user_team_endpoints.py`
- Tests: `/backend/tests/test_league_confirmation.py`

**Estimated Effort:**
- Database: 1-2 hours (migration, testing)
- Services: 3-4 hours (code, testing)
- Endpoints: 2-3 hours (code, testing)
- Frontend: 4-6 hours (UI, testing)
- Testing: 2-3 hours (scenarios, edge cases)
- **Total: 12-18 hours**

