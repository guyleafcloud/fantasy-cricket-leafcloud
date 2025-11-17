# Player Multiplier Calculation System
**Fantasy Cricket Platform - Reverse Handicap System**

## 📋 Overview

The multiplier system creates competitive balance by **handicapping strong players** and **boosting weak players**:
- **Lower multiplier (0.69)** = Best real-life players = Fantasy points REDUCED
- **Neutral multiplier (1.0)** = Median performers = No change
- **Higher multiplier (5.0)** = Weakest players = Fantasy points BOOSTED

This ensures strong players cost more fantasy budget, while weak players become valuable picks.

---

## 🧮 Calculation Process

### Step 1: Calculate Season Fantasy Points

For each player, sum their total fantasy points from the season using the tiered system:

**Batting Points:**
- Tier 1 (1-30 runs): 1.0 pt/run
- Tier 2 (31-49 runs): 1.25 pt/run
- Tier 3 (50-99 runs): 1.5 pt/run
- Tier 4 (100+ runs): 1.75 pt/run
- Multiply by (Strike Rate / 100)
- Bonuses: 50 runs (+8), 100 runs (+16)
- Duck penalty: -2 points

**Bowling Points:**
- Tier 1 (1-2 wickets): 15 pts each
- Tier 2 (3-4 wickets): 20 pts each
- Tier 3 (5-10 wickets): 30 pts each
- Multiply by (6.0 / Economy Rate)
- Maiden overs: +15 pts each
- 5-wicket haul: +8 bonus

**Fielding Points:**
- Catch: +4 pts
- Run out: +6 pts
- Stumping: +6 pts
- Wicketkeeper: 2× catch points

---

### Step 2: Calculate League Statistics

Once all players have fantasy point totals:

```python
player_scores = [player1_points, player2_points, ..., player_n_points]

min_score = min(player_scores)        # Weakest player
median_score = median(player_scores)  # Middle value (50th percentile)
max_score = max(player_scores)        # Strongest player
```

---

### Step 3: Calculate Target Multiplier

Linear interpolation based on position relative to median:

```python
def calculate_multiplier(player_score, min_score, median_score, max_score):
    """
    Multiplier Scale:
    - Below median (weaker): 1.0 to 5.0 (linear)
    - At median: 1.0
    - Above median (stronger): 1.0 to 0.69 (linear)
    """

    if player_score <= median_score:
        # BELOW MEDIAN: Interpolate from 5.0 (min_score) to 1.0 (median)
        ratio = (player_score - min_score) / (median_score - min_score)
        return 5.0 - (ratio * 4.0)  # 5.0 → 1.0

    else:
        # ABOVE MEDIAN: Interpolate from 1.0 (median) to 0.69 (max_score)
        ratio = (player_score - median_score) / (max_score - median_score)
        return 1.0 - (ratio * 0.31)  # 1.0 → 0.69
```

**Visual Representation:**

```
Fantasy Points:  [Min=0]  ←  [Median]  →  [Max=1500]
Multiplier:      5.00     →    1.00    ←    0.69
                (Weak)       (Average)    (Strong)
```

**Example Calculations:**

| Player Score | Position | Multiplier | Explanation |
|--------------|----------|------------|-------------|
| 0 pts | Minimum | 5.00 | Weakest - full 5× boost |
| 500 pts | Below median | 2.50 | Halfway between min and median |
| 750 pts | Median | 1.00 | Neutral - no adjustment |
| 1000 pts | Above median | 0.85 | Strong - 15% handicap |
| 1500 pts | Maximum | 0.69 | Best - maximum 31% handicap |

---

### Step 4: Weekly Drift Adjustment (15% max)

For **weekly updates** (not initial calculation), multipliers drift gradually toward targets:

```python
def apply_weekly_drift(old_multiplier, target_multiplier, drift_rate=0.15):
    """
    Gradually adjust multiplier toward target
    Maximum 15% movement per week
    """
    new_multiplier = old_multiplier * (1 - drift_rate) + target_multiplier * drift_rate
    return round(new_multiplier, 2)
```

**Example:**
- Old multiplier: 2.50
- Target multiplier: 0.80 (player improved significantly)
- New multiplier: `2.50 × 0.85 + 0.80 × 0.15 = 2.245` → **2.25**
- Change: -0.25 (10% reduction)

This prevents sudden jumps and creates strategic opportunities to pick improving players early.

---

## 🚀 Usage: Generate Initial Multipliers for New Season

### Prerequisites

1. Collect season stats for all players (from scorecards/match data)
2. Format as JSON with player stats (see format below)

### Input Format

Create a JSON file with this structure:

```json
{
  "season": "2026",
  "club": "ACC",
  "players": [
    {
      "name": "PlayerName",
      "team": "ACC 1",
      "role": "BATSMAN",
      "tier": "HOOFDKLASSE",
      "stats": {
        "runs": 450,
        "balls_faced": 380,
        "wickets": 0,
        "overs": 0.0,
        "runs_conceded": 0,
        "maidens": 0,
        "catches": 5,
        "run_outs": 1,
        "stumpings": 0
      }
    }
  ]
}
```

### Run the Script

```bash
cd backend
python3 generate_initial_multipliers.py season_2026_stats.json
```

### Output

The script will:
1. Calculate fantasy points for each player
2. Calculate league statistics (min, median, max)
3. Generate multipliers (0.69-5.00) using linear interpolation
4. Save results to `season_2026_stats_with_multipliers.json`
5. Display top/bottom 10 players

**Example Output:**

```
======================================================================
🎯 GENERATING INITIAL PLAYER MULTIPLIERS FROM SEASON STATS
======================================================================

📂 Loading player data from: season_2026_stats.json
   Found 513 players

🔢 Calculating season fantasy points for all players...

📊 Calculating league statistics...
   Minimum:     0.00 points
   Median:    648.46 points
   Mean:      667.74 points
   Maximum:  1374.02 points

⚖️  Calculating multipliers for all players...

🏆 TOP 10 PLAYERS (Lowest Multipliers - Best Performers):
Rank  Name                          Team        Points    Multiplier
----------------------------------------------------------------------
1     AyaanBarve                    U17         1374.0    0.69
2     MandeepSingh                  ACC 3       1234.2    0.75
...

💾 Saving results to: season_2026_stats_with_multipliers.json

✅ MULTIPLIER GENERATION COMPLETE!
```

---

## 📊 Example Calculation Walkthrough

Let's calculate multipliers for 4 players:

### Input Data

| Player | Role | Runs | Wickets | Catches |
|--------|------|------|---------|---------|
| Alice | ALL_ROUNDER | 456 (SR 117) | 18 (ER 5.17) | 8 |
| Bob | ALL_ROUNDER | 389 (SR 125) | 15 (ER 5.13) | 6 |
| Charlie | BATSMAN | 45 (SR 67) | 0 | 2 |
| Diana | BOWLER | 0 | 0 | 0 |

### Step 1: Calculate Fantasy Points

**Alice:**
- Batting: (50×1.0 + 49×1.25 + 357×1.5) × 1.17 = 765 pts
- Bowling: (2×15 + 2×20 + 14×30) × (6/5.17) = 609 pts
- Fielding: 8×4 = 32 pts
- **Total: 1374 pts**

**Bob:**
- Batting: (50×1.0 + 49×1.25 + 290×1.5) × 1.25 = 662 pts
- Bowling: (2×15 + 2×20 + 11×30) × (6/5.13) = 534 pts
- Fielding: 6×4 = 24 pts
- **Total: 1234 pts**

**Charlie:**
- Batting: 45×1.0 × 0.67 = 30 pts
- Fielding: 2×4 = 8 pts
- **Total: 63 pts**

**Diana:**
- **Total: 0 pts**

### Step 2: League Stats

```
Min: 0 pts (Diana)
Median: (63 + 1234) / 2 = 648.5 pts
Max: 1374 pts (Alice)
```

### Step 3: Calculate Multipliers

**Alice (1374 pts - above median):**
```
ratio = (1374 - 648.5) / (1374 - 648.5) = 1.0
multiplier = 1.0 - (1.0 × 0.31) = 0.69
```

**Bob (1234 pts - above median):**
```
ratio = (1234 - 648.5) / (1374 - 648.5) = 0.806
multiplier = 1.0 - (0.806 × 0.31) = 0.75
```

**Charlie (63 pts - below median):**
```
ratio = (63 - 0) / (648.5 - 0) = 0.097
multiplier = 5.0 - (0.097 × 4.0) = 4.61
```

**Diana (0 pts - no stats):**
```
multiplier = 1.0 (neutral for players with no data)
```

### Final Results

| Player | Fantasy Points | Multiplier | Impact |
|--------|---------------|------------|--------|
| Alice | 1374 | 0.69 | Best player - 31% handicap |
| Bob | 1234 | 0.75 | Strong - 25% handicap |
| Charlie | 63 | 4.61 | Weak - 361% boost |
| Diana | 0 | 1.00 | No data - neutral |

---

## 🔄 Weekly Drift Example

After Week 1, Charlie improves significantly:

**Before:**
- Charlie fantasy points: 63 pts
- Charlie multiplier: 4.61

**After Week 1:**
- Charlie fantasy points: 680 pts (moved to median!)
- Target multiplier: 1.0
- New multiplier: `4.61 × 0.85 + 1.0 × 0.15 = 4.07`
- Change: -0.54 (11.7% reduction)

Over 6 weeks of consistent median performance, Charlie would gradually reach 1.0 multiplier.

---

## 📁 Files

- `backend/generate_initial_multipliers.py` - Script to generate multipliers from stats
- `backend/multiplier_adjuster.py` - Weekly drift adjustment class
- `backend/rules-set-1.py` - Centralized rules and constants
- `backend/example_season_stats.json` - Input format example

---

## ⚙️ Configuration

All multiplier settings are centralized in `rules-set-1.py`:

```python
'player_multipliers': {
    'min': 0.69,      # Best players (maximum handicap)
    'neutral': 1.0,   # Median performers
    'max': 5.0,       # Weakest players (maximum boost)
    'weekly_adjustment_max': 0.15,  # 15% drift rate
}
```

---

## 🎯 Summary

1. **Initial Calculation**: Use `generate_initial_multipliers.py` with season stats
2. **Weekly Updates**: Use `multiplier_adjuster.py` with 15% drift rate
3. **Result**: Balanced fantasy game where weak players become valuable picks
4. **Strategic Depth**: Pick improving players early before multipliers drift down

The system ensures **competitive balance** while rewarding users who identify improving players before their multipliers adjust.
