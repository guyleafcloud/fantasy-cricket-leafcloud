# Leaderboard Stats 500 Error - Root Cause Analysis

**Date:** 2025-11-19
**Issue:** `/api/leagues/{league_id}/stats` returns 500 error on production
**Impact:** Leaderboard page cannot display top 25 players and league statistics

---

## ROOT CAUSE

**Error in Logs:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column "overs" does not exist
LINE 7: SUM(overs) as total_overs,
```

**Location:** `backend/main.py` line 440

**Problem:** The SQL query references a column named `overs` but the actual database column is named `overs_bowled`.

---

## DETAILED ANALYSIS

### Database Schema vs Query Mismatch

**PlayerPerformance Model** (`backend/database_models.py` line 481):
```python
class PlayerPerformance(Base):
    __tablename__ = "player_performances"

    # Bowling stats
    overs_bowled = Column(Float, default=0.0)  # ✅ Actual column name
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    bowling_economy = Column(Float, nullable=True)
```

**Broken Query** (`backend/main.py` lines 434-445):
```python
perf_query = text("""
    SELECT player_id,
           SUM(runs) as total_runs,
           SUM(wickets) as total_wickets,
           SUM(catches) as total_catches,
           SUM(balls_faced) as total_balls,
           SUM(overs) as total_overs,              # ❌ WRONG: should be overs_bowled
           SUM(runs_conceded) as total_runs_conceded
    FROM player_performances
    WHERE league_id = :league_id
    GROUP BY player_id
""")
```

---

## ADDITIONAL ISSUE

### Missing league_id Column

The query also filters by `league_id`:
```python
WHERE league_id = :league_id
```

But the `player_performances` table **does NOT have a league_id column**. It has:
- `match_id` (FK to matches table)
- `player_id` (FK to players table)

To get league_id, we need to join through the matches table:
```sql
FROM player_performances pp
JOIN matches m ON pp.match_id = m.id
WHERE m.league_id = :league_id
```

---

## THE FIX

### Required Changes to `backend/main.py` lines 434-445:

```python
# BEFORE (BROKEN)
perf_query = text("""
    SELECT player_id,
           SUM(runs) as total_runs,
           SUM(wickets) as total_wickets,
           SUM(catches) as total_catches,
           SUM(balls_faced) as total_balls,
           SUM(overs) as total_overs,                    # ❌ Wrong column name
           SUM(runs_conceded) as total_runs_conceded
    FROM player_performances
    WHERE league_id = :league_id                         # ❌ Column doesn't exist
    GROUP BY player_id
""")

# AFTER (FIXED)
perf_query = text("""
    SELECT pp.player_id,
           SUM(pp.runs) as total_runs,
           SUM(pp.wickets) as total_wickets,
           SUM(pp.catches) as total_catches,
           SUM(pp.balls_faced) as total_balls,
           SUM(pp.overs_bowled) as total_overs,          # ✅ Correct column name
           SUM(pp.runs_conceded) as total_runs_conceded
    FROM player_performances pp
    JOIN matches m ON pp.match_id = m.id                 # ✅ Join to get league_id
    WHERE m.league_id = :league_id                       # ✅ Filter by league
    GROUP BY pp.player_id
""")
```

---

## PREVIOUS FIX STATUS

The investigation found that the **previous fix for `Player.team_id` → `Player.rl_team` was successfully applied** (commit 27e1ae3). That fix is working correctly.

However, this separate issue with the `overs` column name was not caught because:
1. It's a different part of the same endpoint
2. It only fails at runtime when data exists in player_performances table
3. Testing may not have included actual performance data

---

## VERIFICATION CHECKLIST

After applying the fix:

1. ✅ Check that `overs_bowled` is the correct column name in database
2. ✅ Verify match-to-league join is correct
3. ✅ Test endpoint with empty player_performances (should return nulls)
4. ✅ Test endpoint with actual performance data (should aggregate correctly)
5. ✅ Verify frontend displays stats properly

---

## FILES TO MODIFY

**File:** `/Users/guypa/Github/fantasy-cricket-leafcloud/backend/main.py`

**Line 440:** Change `SUM(overs)` to `SUM(pp.overs_bowled)`

**Lines 434-445:** Add join to matches table and use table aliases

---

## DEPLOYMENT STEPS

1. Make code changes to main.py
2. Test locally if possible
3. Commit and push changes
4. Pull on production server
5. Rebuild backend container: `docker-compose up -d --build fantasy_cricket_api`
6. Test endpoint: `curl https://fantcric.fun/api/leagues/{league_id}/stats`
7. Verify leaderboard page loads without errors

---

## EXPECTED RESULT

After fix, the `/api/leagues/{league_id}/stats` endpoint should return:

```json
{
  "best_batsman": null,           // null if no performances yet
  "best_bowler": null,
  "best_fielder": null,
  "best_team": {
    "team_name": "ACC 1",
    "total_points": 0,
    "player_count": 45
  },
  "top_players": [
    {
      "player_name": "Player Name",
      "team_name": "ACC 1",
      "total_points": 0.0
    },
    // ... up to 25 players
  ]
}
```

All point values will be 0 until actual match data is scraped and processed.

---

## PRIORITY

**HIGH** - This is blocking the leaderboard page from displaying properly.
