# 🎯 Player Value System

## Overview

The **Player Value Calculator** determines how much each player costs to add to a fantasy team (€20-€50 range). Values are based on **2025 season performance** relative to other players in their club.

---

## 🧮 How It Works

### Performance Score (0-100 points)

Each player gets a score based on their contributions:

#### **Batting (0-40 points)**
- **Runs scored** (0-15 pts): 500+ runs = 15 pts
- **Batting average** (0-10 pts): 40+ average = 10 pts
- **Strike rate** (0-10 pts): 150+ strike rate = 10 pts
- **Milestones** (0-5 pts): Hundreds (2 pts each), Fifties (1 pt each)

#### **Bowling (0-40 points)**
- **Wickets taken** (0-15 pts): 40+ wickets = 15 pts
- **Economy rate** (0-10 pts): 3.0 economy = 10 pts (lower is better)
- **Bowling average** (0-10 pts): 15 average = 10 pts (lower is better)
- **Milestones** (0-5 pts): 5-wicket hauls (2 pts), Maidens (0.5 pts)

#### **Fielding (0-10 points)**
- **Catches** (0-5 pts): 20+ catches = 5 pts
- **Run outs/Stumpings** (0-5 pts): 10+ dismissals = 5 pts

#### **All-rounder Bonus (0-10 points)**
- Players who score 8+ in BOTH batting and bowling get a bonus
- Rewards versatility and balance

---

### Tier Adjustment

Players in lower tiers get a **value boost** because they're likely to dominate if playing at a higher level:

| Tier | Multiplier | Reasoning |
|------|-----------|-----------|
| 1st Team | 1.0x | Baseline (playing at highest level) |
| 2nd Team | 1.1x | +10% bonus (undervalued talent) |
| 3rd Team | 1.2x | +20% bonus (likely to move up) |
| 4th Team | 1.25x | +25% bonus |
| Social | 1.3x | +30% bonus (hidden gems) |

**Example:**
- Player A: 50 pts in 1st team → Value based on 50 pts
- Player B: 50 pts in 2nd team → Value based on 55 pts (50 × 1.1)

This creates interesting decisions: *Do I pick the proven 1st team player or the rising 2nd team star?*

---

### Consistency Score (-5 to +5 points)

Measures how reliable a player is across matches:

| Coefficient of Variation | Score | Description |
|-------------------------|-------|-------------|
| < 0.5 | +5 | Very consistent |
| 0.5 - 0.75 | +2.5 | Consistent |
| 0.75 - 1.25 | 0 | Average |
| 1.25 - 1.5 | -2.5 | Inconsistent |
| > 1.5 | -5 | Very inconsistent |

**Why it matters:** A player who scores 30 points every match is more valuable than one who scores 60, 0, 60, 0.

---

### Value Assignment (€20-€50)

Final scores are converted to prices using **percentile ranking**:

| Percentile | Value Range | Player Type |
|-----------|-------------|-------------|
| Top 10% | €45-€50 | Superstars (Rohit Sharma level) |
| Top 25% | €40-€45 | Premium players |
| Top 50% | €35-€40 | Solid performers |
| Bottom 50% | €30-€35 | Average players |
| Bottom 25% | €20-€30 | Budget options |

This ensures:
- ✅ **Relative pricing** - Values reflect how good they are vs teammates
- ✅ **Scarcity** - Only a few expensive players per club
- ✅ **Budget decisions** - Can't afford all the stars

---

## 📊 Example Calculations

### Example 1: All-Rounder (Boris Gorlee)

**Stats:**
- 450 runs @ 37.5 avg, SR 125
- 18 wickets @ 22.5 avg, ER 4.5
- 6 catches
- 1st team

**Calculation:**
```
Batting score: 25.5 pts
Bowling score: 30.0 pts
Fielding score: 3.0 pts
All-rounder bonus: 6.6 pts (contributes in both)
-------------------
Performance: 65.1 pts
Tier multiplier: 1.0x (1st team)
Final score: 65.1 pts

Percentile: Top 30%
Value: €40.0
```

**Why €40?** Balanced contributor in batting and bowling, consistent performer.

---

### Example 2: Pure Batsman (Sikander Zulfiqar)

**Stats:**
- 520 runs @ 52.0 avg, SR 140
- 2 wickets (occasional bowler)
- 4 catches
- 1st team

**Calculation:**
```
Batting score: 40.5 pts
Bowling score: 3.0 pts
Fielding score: 2.0 pts
All-rounder bonus: 0 pts (not balanced)
-------------------
Performance: 45.5 pts
Tier multiplier: 1.0x (1st team)
Final score: 45.5 pts

Percentile: Top 50%
Value: €30.0
```

**Why €30?** Great batsman but one-dimensional, less valuable than all-rounders.

---

### Example 3: Lower Tier Gem (Shariz Ahmad)

**Stats:**
- 180 runs @ 22.5 avg, SR 90
- 15 wickets @ 18.0 avg, ER 3.8
- 3 catches
- **2nd team**

**Calculation:**
```
Batting score: 15.0 pts
Bowling score: 32.0 pts
Fielding score: 1.5 pts
All-rounder bonus: 2.0 pts
-------------------
Performance: 50.5 pts
Tier multiplier: 1.1x (2nd team bonus!)
Adjusted score: 55.6 pts

Percentile: Top 40%
Value: €35.0
```

**Why €35?** Gets a boost for being in 2nd team - could dominate if moved to 1st team!

---

## 🔧 Admin Usage

### 1. Calculate Values for a Club

```bash
POST /api/admin/calculate-values/ACC?season_year=2025
Authorization: Bearer {admin_token}
```

This will:
1. Load all ACC players
2. Calculate their performance scores
3. Apply tier adjustments
4. Rank them against each other
5. Assign values (€20-€50)
6. Store values in database

### 2. View Value Breakdown

```bash
GET /api/admin/player-value-breakdown/{player_id}
Authorization: Bearer {admin_token}
```

Returns detailed justification showing:
- Performance breakdown (batting/bowling/fielding)
- Tier adjustments
- Consistency score
- Final value with reasoning

### 3. Manual Adjustments

After calculation, you can still manually adjust:

```bash
PATCH /api/admin/players/{player_id}/value
{
  "new_value": 42.5,
  "reason": "Undervalued by algorithm - key player"
}
```

The system tracks:
- Old value
- New value
- Who made the change
- Why they changed it

---

## 🎮 Impact on Game Balance

### Budget Constraint (€500)

With values ranging €20-€50:
- **Can't buy all stars**: Top players (€45-50) × 11 = €495-550
- **Need budget players**: Mix of €45 stars and €25 rookies
- **Trade-offs**: 3 superstars + 12 average OR 2 superstars + 13 good players

### Squad Building Strategy

**Option A: Star-Heavy (Risky)**
```
3 players @ €45 = €135
5 players @ €35 = €175
7 players @ €25 = €175
---
Total: €485 (15 players)
```

**Option B: Balanced (Safe)**
```
1 player @ €50 = €50
4 players @ €40 = €160
6 players @ €35 = €210
4 players @ €25 = €100
---
Total: €520... wait, over budget!
Adjust to: 4×€35, 6×€30, 4×€25 = €500
```

### Tier Strategy

Smart managers will:
- ✅ **Scout 2nd/3rd team players** (€35 value for €30 performance)
- ✅ **Watch for promotions** (if 2nd team player moves to 1st, their value skyrockets)
- ✅ **Balance team tiers** (mix of 1st and 2nd team players)

---

## 🔄 When Values Change

### During Season Setup (Now)
- Load 2025 legacy rosters
- Calculate initial values
- Admin can review and tweak

### Mid-Season (Later Feature)
- Weekly performance affects current season value
- Algorithm runs after each scrape
- Values update for next week's transfers

---

## 💡 Key Design Decisions

### Why €20-€50 range?
- Wide enough for meaningful differences
- Narrow enough to need budget management
- Easy mental math (€500 budget ÷ €30 avg ≈ 16 players)

### Why relative pricing?
- Boris worth €40 in ACC might only be €30 in VRA (different competition level)
- Ensures each club has stars, not just one dominant club
- Creates interesting cross-club comparisons

### Why tier multipliers?
- Rewards spotting undervalued talent
- Creates dynamic: "2nd team player playing well > 1st team player slumping"
- Realistic: Lower tier players often become stars

### Why all-rounder bonus?
- Reflects real cricket value (versatility is king)
- Encourages balanced team building
- Penalizes one-dimensional players

---

## 📈 Future Enhancements

### Phase 1 (Current)
✅ Calculate from 2025 legacy data
✅ Admin can manually adjust
✅ Transparent justifications

### Phase 2 (Next)
- [ ] Live updates based on current season
- [ ] Value trends (rising/falling)
- [ ] Predicted values for next week

### Phase 3 (Advanced)
- [ ] Machine learning model
- [ ] Historical value tracking
- [ ] Market demand (popular players cost more)
- [ ] Injury/form adjustments

---

## 🧪 Testing the Calculator

Run the calculator in test mode:

```bash
cd backend
python3 player_value_calculator.py
```

This will show:
- Sample player calculations
- Performance breakdowns
- Value justifications

---

## 📚 Files

- **`backend/player_value_calculator.py`** - Core algorithm (650 lines)
- **`backend/admin_endpoints.py`** - Admin endpoints (includes value calculation)
- **`PLAYER_VALUE_SYSTEM.md`** - This documentation

---

**The value system is now ready!** 🎯

Next steps:
1. Integrate with season setup workflow
2. Add UI for viewing/adjusting values
3. Connect to live scraping for mid-season updates
