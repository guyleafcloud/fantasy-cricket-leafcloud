# 🎭 League-Specific Dynamic Multipliers

## Overview

The fantasy cricket platform uses a sophisticated **league-specific dynamic multiplier system** that ensures fair competition within each league while allowing different leagues to have independent player valuations.

### Key Concept

**The same player can have different multipliers (and thus different fantasy points) in different leagues!**

This reflects the reality that a player's relative value depends on the context of the league they're in. A "strong" player in one league might be "average" in another league with more stars.

---

## How It Works

### 1. Initial Multiplier Capture (League Confirmation)

When an admin confirms a league (status: `draft` → `active`):

```
POST /api/admin/leagues/{league_id}/confirm
```

The system:
1. ✅ Validates roster meets squad requirements
2. ✅ Freezes all league rules (can't be edited)
3. ✅ Captures **current multipliers** for all roster players
4. ✅ Stores in `League.multipliers_snapshot` as JSON

**Example snapshot:**
```json
{
  "player_uuid_1": 1.0,
  "player_uuid_2": 0.85,
  "player_uuid_3": 1.25,
  ...
}
```

**Important:** This is the **STARTING POINT**, not frozen forever!

### 2. Weekly Drift Adjustment (Every Monday 2 AM)

An automated Celery task runs every Monday at 2 AM:

```python
# celery_tasks.py -> adjust_multipliers_weekly()
```

For each active/locked league:

1. **Query roster players** from `LeagueRoster` table
2. **Calculate season points** for each player (filtered by `league_id`)
3. **Compute statistics** relative to THIS league's roster:
   - Min points
   - Median points (reference point)
   - Max points
4. **Calculate target multiplier** for each player:
   - Below median → multiplier 1.0-5.0 (easier to get points)
   - At median → multiplier 1.0 (neutral)
   - Above median → multiplier 1.0-0.69 (harder to get points)
5. **Apply 15% drift** toward target:
   ```python
   new_multiplier = old_multiplier * 0.85 + target_multiplier * 0.15
   ```
6. **Update league's snapshot** with new values

### 3. Fantasy Team Points Calculation

When calculating a fantasy team's total points:

```python
# fantasy_team_points_service.py -> calculate_player_points_for_team()
```

For each player in the team:

1. **Get team's league_id** from `FantasyTeam` table
2. **Fetch league's multipliers_snapshot**
3. **Get league-specific multiplier** for this player
4. **Recalculate points**:
   ```python
   for performance in player_performances:
       points += performance.base_fantasy_points * league_multiplier
   ```
5. **Apply captain/vice-captain bonuses**

Result: Different leagues see different total points!

---

## Multiplier Scale

### Range

| Value | Meaning | Effect |
|-------|---------|--------|
| **5.0** | Weakest in league | Points × 5 (massive boost) |
| **3.0** | Below average | Points × 3 |
| **1.0** | Median/Average | No change |
| **0.85** | Above average | Points × 0.85 |
| **0.69** | Star player | Points × 0.69 (30% reduction) |

### Calculation Formula

Based on player's season points relative to league median:

```python
if player_score <= median_score:
    # Below median: interpolate from 5.0 (worst) to 1.0 (median)
    ratio = (player_score - min_score) / (median_score - min_score)
    multiplier = 5.0 - (ratio * 4.0)
else:
    # Above median: interpolate from 1.0 (median) to 0.69 (best)
    ratio = (player_score - median_score) / (max_score - median_score)
    multiplier = 1.0 - (ratio * 0.31)
```

### Drift Rate

- **15% per week** toward current season performance
- Prevents sudden jumps
- Allows gradual adjustment over season
- Configurable in `rules-set-1.py`:
  ```python
  FANTASY_RULES = {
      'player_multipliers': {
          'weekly_adjustment_max': 0.15,  # 15% drift rate
          'min': 0.69,
          'max': 5.0,
          'neutral': 1.0
      }
  }
  ```

---

## Real-World Example

### Scenario Setup

**League A: "Premier Division"**
- Roster: 30 players including many high scorers
- Season points distribution:
  - Min: 50 pts
  - Median: 120 pts
  - Max: 200 pts

**League B: "Community League"**
- Roster: 30 different players with fewer stars
- Season points distribution:
  - Min: 30 pts
  - Median: 80 pts
  - Max: 140 pts

**Player X:**
- Season points: 100 pts
- Latest match: 50 base points

### Week 1 - Initial Multipliers

Both leagues confirm with multiplier = 1.0 for Player X.

**League A:**
- Player X points: 100 pts
- League median: 120 pts
- **Below median** → target multiplier ≈ 1.2

**League B:**
- Player X points: 100 pts
- League median: 80 pts
- **Above median** → target multiplier ≈ 0.85

### Week 2 - After First Drift

After weekly adjustment (15% drift):

**League A:**
```
new_mult = 1.0 * 0.85 + 1.2 * 0.15
         = 0.85 + 0.18
         = 1.03
```
Player X match points: 50 × 1.03 = **51.5 pts**

**League B:**
```
new_mult = 1.0 * 0.85 + 0.85 * 0.15
         = 0.85 + 0.1275
         = 0.98
```
Player X match points: 50 × 0.98 = **49 pts**

### Week 10 - After Multiple Drifts

Assuming Player X maintains 100 pts performance:

**League A:** multiplier ≈ 1.18 → match points = 50 × 1.18 = **59 pts**
**League B:** multiplier ≈ 0.87 → match points = 50 × 0.87 = **43.5 pts**

**Same performance, 15.5 point difference!** This is correct because Player X is "below average" in League A but "above average" in League B.

---

## Why League-Specific?

### Problem with Global Multipliers

If all leagues shared the same multipliers:

- ❌ Player value wouldn't reflect league context
- ❌ Leagues with weaker rosters would be unbalanced
- ❌ Star players would dominate every league equally
- ❌ No strategic depth in roster selection

### Solution: League-Specific Multipliers

With independent multipliers per league:

- ✅ Player value reflects position within league's roster
- ✅ Each league has its own competitive balance
- ✅ Same player can be "budget" in one league, "premium" in another
- ✅ More strategic depth in team selection

### Concrete Example

**Player A: Season average 150 pts**

In League 1 (casual players, median 100 pts):
- Well above median
- Multiplier: 0.75
- Fantasy points: Base × 0.75
- Strategy: "Premium pick, expensive but worth it"

In League 2 (competitive players, median 180 pts):
- Below median
- Multiplier: 1.15
- Fantasy points: Base × 1.15
- Strategy: "Budget-friendly, good value"

---

## Technical Implementation

### Database Schema

**Leagues Table:**
```sql
CREATE TABLE leagues (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    status VARCHAR(50),  -- draft, active, locked, completed

    -- Multiplier tracking
    multipliers_snapshot JSON,  -- {player_id: multiplier}
    multipliers_frozen_at TIMESTAMP,

    -- Frozen rules
    frozen_squad_size INTEGER,
    frozen_transfers_per_season INTEGER,
    ...
);
```

**Player Performances Table:**
```sql
CREATE TABLE player_performances (
    id VARCHAR(50) PRIMARY KEY,
    match_id VARCHAR(50),
    player_id VARCHAR(50),
    league_id VARCHAR(50),  -- NEW: enables league filtering

    -- Points tracking
    base_fantasy_points FLOAT,     -- Before multiplier
    multiplier_applied FLOAT,      -- Which multiplier was used
    fantasy_points FLOAT,          -- After multiplier (final)
    ...
);
```

### Code Structure

**1. Multiplier Adjuster** (`multiplier_adjuster.py`)
```python
class MultiplierAdjuster:
    def adjust_league_multipliers(self, db, league_id, dry_run=False):
        """Adjust multipliers for specific league"""
        # Get league's roster players
        # Calculate points filtered by league_id
        # Compute league-specific median
        # Apply 15% drift
        # Update league.multipliers_snapshot
```

**2. Fantasy Team Points** (`fantasy_team_points_service.py`)
```python
class FantasyTeamPointsService:
    def calculate_player_points_for_team(self, player_id, league_id, ...):
        """Calculate points using league-specific multiplier"""
        # Get league.multipliers_snapshot
        # Get league_multiplier for player
        # Recalculate: base_points * league_multiplier
```

**3. Weekly Task** (`celery_tasks.py`)
```python
@app.task
def adjust_multipliers_weekly():
    """Run every Monday 2 AM"""
    # Query all active/locked leagues
    for league in leagues:
        adjuster.adjust_league_multipliers(db, league.id)
```

### API Endpoints

**Confirm League (Admin Only):**
```bash
POST /api/admin/leagues/{league_id}/confirm
```

**Get League Status:**
```bash
GET /api/admin/leagues/{league_id}/status

Response:
{
  "multipliers_captured": 61,
  "multipliers_frozen_at": "2026-04-01T10:00:00Z",
  ...
}
```

**View Team Points (uses league multipliers automatically):**
```bash
GET /api/fantasy-teams/{team_id}/points

Response:
{
  "total_points": 1250.5,
  "player_breakdown": [
    {
      "player_name": "Player X",
      "points": 125.5,  // Already includes league multiplier
      "is_captain": true
    },
    ...
  ]
}
```

---

## Admin Operations

### Monitoring Multiplier Drift

**View current multipliers for a league:**

```python
from database_models import League
from database_setup import SessionLocal

db = SessionLocal()
league = db.query(League).filter_by(id='league_id').first()

print(f"League: {league.name}")
print(f"Last updated: {league.multipliers_frozen_at}")
print(f"Multipliers: {league.multipliers_snapshot}")
```

**Manually trigger drift (testing only):**

```python
from multiplier_adjuster import MultiplierAdjuster

adjuster = MultiplierAdjuster(drift_rate=0.15)
result = adjuster.adjust_league_multipliers(db, league_id='league_id')

print(f"Players adjusted: {result['players_changed']}")
print(f"Top changes: {result['top_changes'][:5]}")
```

### Troubleshooting

**Issue: Multipliers not updating**

Check Celery worker is running:
```bash
docker ps | grep worker
docker logs fantasy_cricket_worker
```

**Issue: All players have same multiplier**

Check league has sufficient performance data:
```sql
SELECT COUNT(*)
FROM player_performances pp
JOIN league_rosters lr ON pp.player_id = lr.player_id
WHERE lr.league_id = 'league_id';
```

**Issue: Multipliers seem wrong**

Verify median calculation:
```python
result = adjuster.adjust_league_multipliers(db, league_id, dry_run=True)
print(f"Score stats: {result['score_stats']}")
# Should show min, median, mean, max for league
```

---

## Configuration

### Adjust Drift Rate

Edit `rules-set-1.py`:

```python
FANTASY_RULES = {
    'player_multipliers': {
        'weekly_adjustment_max': 0.15,  # Change this (0.0-1.0)
        'min': 0.69,                     # Minimum multiplier
        'max': 5.0,                      # Maximum multiplier
        'neutral': 1.0                   # Median multiplier
    }
}
```

**Drift rate examples:**
- `0.05` (5%) = Very slow adjustment, more stability
- `0.15` (15%) = Moderate adjustment (current)
- `0.30` (30%) = Fast adjustment, responsive to changes
- `1.0` (100%) = Instant snap to target (not recommended)

### Adjust Multiplier Range

To make star players even cheaper:
```python
'min': 0.50,  # Instead of 0.69
```

To reduce advantage for weak players:
```python
'max': 3.0,  # Instead of 5.0
```

---

## Testing

### Test Script

Run comprehensive test:

```bash
docker exec fantasy_cricket_api python3 /app/test_league_specific_multipliers.py
```

This test:
1. Creates 2 test leagues with overlapping rosters
2. Processes match performances
3. Runs multiplier drift for each league
4. Verifies overlapping players have different multipliers
5. Tests fantasy team points calculation

### Manual Testing

1. **Create two leagues** with different rosters
2. **Confirm both leagues** to capture initial multipliers
3. **Process some matches** to create performance data
4. **Manually trigger drift** for both leagues
5. **Compare multipliers** for overlapping players:

```python
from database_models import League

league_a = db.query(League).filter_by(name='League A').first()
league_b = db.query(League).filter_by(name='League B').first()

player_id = 'uuid_of_overlapping_player'

mult_a = league_a.multipliers_snapshot.get(player_id)
mult_b = league_b.multipliers_snapshot.get(player_id)

print(f"Player multiplier in League A: {mult_a}")
print(f"Player multiplier in League B: {mult_b}")
print(f"Difference: {abs(mult_a - mult_b)}")
```

---

## FAQ

### Q: Do multipliers start at 1.0 for all players?

**A:** No! When a league is confirmed, it captures the **current** multiplier values from each player. If players already have varied multipliers (from previous seasons or calculations), those are used as the starting point.

### Q: Can I manually set a player's multiplier in a league?

**A:** Not directly via API. Multipliers are calculated automatically based on performance. However, you can:
1. Adjust the drift rate to change how fast they update
2. Adjust the min/max range in configuration
3. Modify `Player.multiplier` globally (affects NEW leagues only)

### Q: What happens if a player joins the league roster mid-season?

**A:** The player would need to be added to `LeagueRoster` table. On the next weekly drift, they'll get a multiplier calculated relative to their performance vs. the league median.

### Q: Can completed leagues still drift?

**A:** No. The weekly task only processes leagues with status `active` or `locked`. Completed leagues are skipped, preserving their final state.

### Q: What if a league has very few players?

**A:** The system still calculates median/min/max, but with fewer data points the distribution might be less meaningful. Recommended minimum: 15+ players per league roster.

### Q: Do transfers affect multipliers?

**A:** No. A player's multiplier in a league is based on their overall season performance within that league, regardless of which fantasy teams picked them or when.

---

## See Also

- [FANTASY_POINTS_RULES.md](FANTASY_POINTS_RULES.md) - Base points calculation
- [SEASON_SETUP_GUIDE.md](SEASON_SETUP_GUIDE.md) - League lifecycle workflow
- [multiplier_adjuster.py](multiplier_adjuster.py) - Implementation code
- [celery_tasks.py](celery_tasks.py) - Weekly automation
- [test_league_specific_multipliers.py](test_league_specific_multipliers.py) - Test suite

---

**Last Updated:** 2025-12-19
**Version:** 1.0
**Status:** ✅ Fully implemented and tested
