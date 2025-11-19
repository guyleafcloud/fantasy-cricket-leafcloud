# STATS ENDPOINT FIX - EXECUTIVE SUMMARY

## Current Problem

**Error:** `Postgres error: "m.league_id does not exist"`

**Location:** `/api/leagues/{league_id}/stats` endpoint at line 444 in main.py

**Impact:** Leaderboard page cannot display player statistics

---

## Root Cause (One Sentence)

The code filters player performances by `m.league_id`, but the `matches` table does NOT have a `league_id` column.

---

## Why This Happened

The Match table has:
- `season_id` (FK to seasons)
- `club_id` (FK to clubs)

But NO `league_id` column.

The League table is linked to Season + Club, not directly to Matches.

---

## The Correct Data Path

```
League (has season_id + club_id)
    ↓
Match (has season_id + club_id)
    ↓
PlayerPerformance (has match_id)
    ↓
Player (has rl_team)
```

To find matches for a league: Match on (season_id, club_id)

---

## The Fix (2 Changes)

### Change 1: Add League Lookup (Line ~400)

```python
# Get league info to find season_id and club_id
league = db.query(League).filter(League.id == league_id).first()
if not league:
    return {
        "best_batsman": None,
        "best_bowler": None,
        "best_fielder": None,
        "best_team": None,
        "top_players": []
    }
```

### Change 2: Fix Query (Line ~434-446)

**FROM THIS:**
```sql
WHERE m.league_id = :league_id
```

**TO THIS:**
```sql
WHERE m.season_id = :season_id AND m.club_id = :club_id
```

And pass season_id and club_id from the league object:

```python
perf_results = db.execute(perf_query, {
    'season_id': league.season_id,
    'club_id': league.club_id
})
```

---

## Complete Fixed Code Block

Replace lines 434-448 with:

```python
# Get league to find season and club
league = db.query(League).filter(League.id == league_id).first()
if not league:
    return {
        "best_batsman": None,
        "best_bowler": None,
        "best_fielder": None,
        "best_team": None,
        "top_players": []
    }

# Query player_performances table directly with raw SQL
perf_query = text("""
    SELECT pp.player_id,
           SUM(pp.runs) as total_runs,
           SUM(pp.wickets) as total_wickets,
           SUM(pp.catches) as total_catches,
           SUM(pp.balls_faced) as total_balls,
           SUM(pp.overs_bowled) as total_overs,
           SUM(pp.runs_conceded) as total_runs_conceded
    FROM player_performances pp
    JOIN matches m ON pp.match_id = m.id
    WHERE m.season_id = :season_id AND m.club_id = :club_id
    GROUP BY pp.player_id
""")

perf_results = db.execute(perf_query, {
    'season_id': league.season_id,
    'club_id': league.club_id
})
```

---

## File to Modify

**File:** `/Users/guypa/Github/fantasy-cricket-leafcloud/backend/main.py`

**Lines:** 389-448 (get_league_stats function)

**Estimated changes:** 20 lines

---

## Testing

After fix, test:

1. Call `/api/leagues/{league_id}/stats` with a valid league_id
2. Should return valid JSON (not 500 error)
3. Check leaderboard page loads
4. Verify stats display correctly

---

## Why This Is Safe

- No database schema changes
- No model changes needed
- Just fixing query logic
- Isolated to stats endpoint only
- One-way fix (can't break other endpoints)

---

## Previous Related Fixes

- Commit 27e1ae3: Fixed `Player.team_id` → `Player.rl_team` ✅
- Commit 3f21f21: Partially fixed query but missed the WHERE clause ⚠️

---

## Status

**Analysis:** Complete (see STATS_ENDPOINT_ANALYSIS.md for full details)

**Recommended Fix:** Implement changes described above

**Risk Level:** LOW

---

## Next Steps

1. Apply changes to main.py
2. Test on dev environment
3. Commit with message: "Fix stats endpoint - use season_id + club_id instead of league_id"
4. Deploy to production
5. Verify leaderboard works

