# Leaderboard /stats Endpoint - Error Analysis

## Problem
**Error:** 500 Internal Server Error on `/api/leagues/{league_id}/stats`
**Impact:** Leaderboard page cannot display top 25 players and other statistics

## Root Cause

### Issue 1: Invalid Field Reference - `Player.team_id`
**Location:** `backend/main.py` line 422

```python
player_fantasy_data = db.query(
    FantasyTeamPlayer.player_id,
    FantasyTeamPlayer.total_points,
    FantasyTeamPlayer.fantasy_team_id,
    Player.name,
    Player.team_id  # ❌ THIS FIELD DOESN'T EXIST
).join(
    Player, Player.id == FantasyTeamPlayer.player_id
)
```

**Problem:** The code queries `Player.team_id` but this field does NOT exist in production.
**Correct field:** `Player.rl_team` (string field, e.g., "ACC 1", "ACC 2")

### Issue 2: Team Lookups Using Non-Existent team_id
**Locations:** Lines 471, 484, 499, 511, 518, 523-526, 532, 537

The code tries to:
1. Get `cricket_team_id` from the query result (line 471)
2. Look up `Team.name` using `cricket_team_id` (lines 484, 499, 511, 518)
3. Aggregate points by `cricket_team_id` (lines 523-526)
4. Find best team using `cricket_team_id` (lines 532-537)

**Problem:** All of these operations assume `team_id` exists as a foreign key, but it doesn't.

## What the Endpoint Should Display

Based on the code logic, the `/stats` endpoint should return:

```json
{
  "best_batsman": {
    "player_name": "...",
    "team_name": "ACC 1",
    "runs": 150,
    "average": 150,
    "strike_rate": 125.5
  },
  "best_bowler": {
    "player_name": "...",
    "team_name": "ACC 2",
    "wickets": 15,
    "average": 12.5,
    "economy": 4.2
  },
  "best_fielder": {
    "player_name": "...",
    "team_name": "ACC 3",
    "catches": 8
  },
  "best_team": {
    "team_name": "ACC 1",
    "total_points": 1250,
    "player_count": 45
  },
  "top_players": [
    {
      "player_name": "...",
      "team_name": "ACC 1",
      "total_points": 125.5
    },
    // ... 24 more players
  ]
}
```

## Frontend Usage

**File:** `frontend/app/leagues/[league_id]/leaderboard/page.tsx`

The leaderboard page makes two parallel requests:
1. `/api/leagues/{league_id}/leaderboard` - Gets fantasy team rankings (✅ works)
2. `/api/leagues/{league_id}/stats` - Gets player/team statistics (❌ 500 error)

The stats are displayed in a separate section on the leaderboard page showing:
- Top performers (best batsman, bowler, fielder)
- Best performing RL team
- Top 25 players by fantasy points

## Solution

### Option 1: Use rl_team String Field (Recommended)
Replace `Player.team_id` with `Player.rl_team` and remove FK-based team lookups.

**Changes needed:**
1. Query `Player.rl_team` instead of `Player.team_id` (line 422)
2. Use `rl_team` directly instead of looking up Team.name (lines 484, 499, 511, 518)
3. Aggregate by `rl_team` string instead of `cricket_team_id` (lines 467, 523-526)
4. Find best team using `rl_team` aggregation (lines 528-538)

### Option 2: Disable Team-Based Stats
If team-level statistics aren't needed:
- Remove `cricket_team_id` from query
- Set `team_name` to "Unknown" or player's club name
- Remove `best_team` calculation
- Only show player-level stats

## Recommended Fix

**Use rl_team field** since:
- It exists in production
- Provides meaningful team grouping (ACC 1, ACC 2, etc.)
- Matches the actual schema
- No database migration needed

## Code Changes Required

### 1. Update Query (line 417-427)
```python
# BEFORE
player_fantasy_data = db.query(
    FantasyTeamPlayer.player_id,
    FantasyTeamPlayer.total_points,
    FantasyTeamPlayer.fantasy_team_id,
    Player.name,
    Player.team_id  # ❌
).join(...)

# AFTER
player_fantasy_data = db.query(
    FantasyTeamPlayer.player_id,
    FantasyTeamPlayer.total_points,
    FantasyTeamPlayer.fantasy_team_id,
    Player.name,
    Player.rl_team  # ✅
).join(...)
```

### 2. Update Unpacking (line 471)
```python
# BEFORE
player_id, total_points, fantasy_team_id, player_name, cricket_team_id = pfd

# AFTER
player_id, total_points, fantasy_team_id, player_name, rl_team = pfd
```

### 3. Update Team Name Lookups (lines 484, 499, 511, 518)
```python
# BEFORE
'team_name': db.query(Team.name).filter(Team.id == cricket_team_id).scalar() if cricket_team_id else 'Unknown'

# AFTER
'team_name': rl_team if rl_team else 'Unknown'
```

### 4. Update Aggregation (lines 467, 523-526)
```python
# BEFORE
cricket_team_points = {}  # cricket team_id -> total points
...
if cricket_team_id:
    if cricket_team_id not in cricket_team_points:
        cricket_team_points[cricket_team_id] = 0
    cricket_team_points[cricket_team_id] += (total_points or 0)

# AFTER
rl_team_points = {}  # rl_team string -> total points
...
if rl_team:
    if rl_team not in rl_team_points:
        rl_team_points[rl_team] = 0
    rl_team_points[rl_team] += (total_points or 0)
```

### 5. Update Best Team (lines 528-538)
```python
# BEFORE
best_team = None
if cricket_team_points:
    best_team_id = max(cricket_team_points, key=cricket_team_points.get)
    team = db.query(Team).filter(Team.id == best_team_id).first()
    if team:
        best_team = {
            'team_name': team.name,
            'total_points': cricket_team_points[best_team_id],
            'player_count': sum(1 for pfd in player_fantasy_data if pfd[4] == best_team_id)
        }

# AFTER
best_team = None
if rl_team_points:
    best_rl_team = max(rl_team_points, key=rl_team_points.get)
    best_team = {
        'team_name': best_rl_team,
        'total_points': rl_team_points[best_rl_team],
        'player_count': sum(1 for pfd in player_fantasy_data if pfd[4] == best_rl_team)
    }
```

## Testing Plan

After fix:
1. ✅ Request `/api/leagues/{league_id}/stats` should return 200
2. ✅ Response should include all expected fields
3. ✅ `team_name` should show RL team names (e.g., "ACC 1", "ACC 2")
4. ✅ `best_team` should aggregate by RL team
5. ✅ `top_players` should show top 25 players by fantasy points
6. ✅ Frontend leaderboard page should display stats section

## Priority

**HIGH** - This is blocking the leaderboard page from displaying important statistics that users expect to see.
