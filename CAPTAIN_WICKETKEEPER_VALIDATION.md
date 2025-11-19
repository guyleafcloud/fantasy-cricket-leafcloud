# Captain/Vice-Captain/Wicketkeeper Validation - Requirements

## Current Situation

### Database Schema
**fantasy_teams table:**
- `captain_id` (VARCHAR, FK to players.id) - Currently nullable
- `vice_captain_id` (VARCHAR, FK to players.id) - Currently nullable

**fantasy_team_players table:**
- `is_captain` (BOOLEAN, default false)
- `is_vice_captain` (BOOLEAN, default false)
- `is_wicket_keeper` (BOOLEAN, default false)

### Current Finalization Logic
**Location:** `backend/user_team_endpoints.py` lines 611-660

**Current validations:**
1. ✅ Squad size (exactly 11 players)
2. ✅ Min batsmen (at least 3)
3. ✅ Min bowlers (at least 3)
4. ✅ Max players per RL team (max 2)
5. ✅ Require from each RL team (1 from each of 10 teams)

**Missing validations:**
- ❌ Captain must be selected
- ❌ Vice-captain must be selected
- ❌ At least one wicketkeeper must be selected

## Requirements

### Backend Validation
Before allowing team finalization, validate:

1. **Captain Required:**
   - `team.captain_id` must not be NULL
   - Captain must be one of the players in the team
   - At least one `fantasy_team_players` row must have `is_captain = true`

2. **Vice-Captain Required:**
   - `team.vice_captain_id` must not be NULL
   - Vice-captain must be one of the players in the team
   - Vice-captain must be different from captain
   - At least one `fantasy_team_players` row must have `is_vice_captain = true`

3. **Wicketkeeper Required:**
   - At least one `fantasy_team_players` row must have `is_wicket_keeper = true`
   - The player marked as wicketkeeper should ideally have role = WICKET_KEEPER

### Frontend Requirements
Team builder/management page should:
1. Show clear UI to select captain (with 2x points badge)
2. Show clear UI to select vice-captain (with 1.5x points badge)
3. Show clear UI to select wicketkeeper (with bonus catches multiplier)
4. Disable finalize button until all three are selected
5. Show validation errors if user tries to finalize without selections

## Implementation Plan

### Step 1: Backend Validation (Priority: HIGH)
Add validation to `finalize_team()` endpoint:

```python
@router.post("/teams/{team_id}/finalize")
async def finalize_team(...):
    # ... existing validations ...

    # NEW: Validate captain
    if not team.captain_id:
        raise HTTPException(
            status_code=400,
            detail="You must select a captain before finalizing your team"
        )

    # Verify captain is in team
    captain_in_team = any(
        ftp.player_id == team.captain_id and ftp.is_captain
        for ftp in team.players
    )
    if not captain_in_team:
        raise HTTPException(
            status_code=400,
            detail="Captain must be a player in your team"
        )

    # NEW: Validate vice-captain
    if not team.vice_captain_id:
        raise HTTPException(
            status_code=400,
            detail="You must select a vice-captain before finalizing your team"
        )

    # Verify vice-captain is in team and different from captain
    if team.vice_captain_id == team.captain_id:
        raise HTTPException(
            status_code=400,
            detail="Vice-captain must be different from captain"
        )

    vice_captain_in_team = any(
        ftp.player_id == team.vice_captain_id and ftp.is_vice_captain
        for ftp in team.players
    )
    if not vice_captain_in_team:
        raise HTTPException(
            status_code=400,
            detail="Vice-captain must be a player in your team"
        )

    # NEW: Validate wicketkeeper
    has_wicketkeeper = any(ftp.is_wicket_keeper for ftp in team.players)
    if not has_wicketkeeper:
        raise HTTPException(
            status_code=400,
            detail="You must select at least one wicketkeeper before finalizing your team"
        )

    # ... rest of finalization ...
```

### Step 2: Check Existing Endpoints
Review endpoints that set captain/vice-captain/wicketkeeper:
- `POST /teams/{team_id}/players` - Sets roles when adding player
- `PUT /teams/{team_id}/players/{player_id}` - Updates player roles
- Need to ensure `fantasy_teams` table captain_id/vice_captain_id are updated

### Step 3: Frontend Updates (If Needed)
Check if frontend already has UI for selecting these roles:
- `frontend/app/teams/[team_id]/build/page.tsx` - Team builder
- `frontend/app/teams/[team_id]/page.tsx` - Team management

### Step 4: Testing
1. Try to finalize team without captain → should fail
2. Try to finalize team without vice-captain → should fail
3. Try to finalize team without wicketkeeper → should fail
4. Try to finalize team with same player as captain and vice-captain → should fail
5. Finalize team with all roles selected → should succeed

## Error Messages

User-friendly error messages:
- "🧑‍✈️ Please select a captain before finalizing your team"
- "👨‍✈️ Please select a vice-captain before finalizing your team"
- "🧤 Please select at least one wicketkeeper before finalizing your team"
- "⚠️ Your captain and vice-captain must be different players"

## Backwards Compatibility

**Existing teams:**
- Teams finalized before this change may not have captain/vice-captain/wicketkeeper
- Don't retroactively invalidate existing finalized teams
- Only enforce validation on NEW finalizations

## Database Consistency Check

Before deploying, check existing finalized teams:
```sql
SELECT
    COUNT(*) as total_finalized,
    COUNT(captain_id) as has_captain,
    COUNT(vice_captain_id) as has_vice_captain
FROM fantasy_teams
WHERE is_finalized = true;
```

If many existing teams lack captain/vice-captain, may need migration or grace period.
