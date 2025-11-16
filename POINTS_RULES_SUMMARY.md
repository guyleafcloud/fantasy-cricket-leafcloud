# Fantasy Cricket Points Rules - DEFINITIVE VERSION

## Base Fantasy Points Calculation

### Batting
- **Every run**: +1 point (base)
- **Strike Rate Multiplier**: Run points × (Strike Rate / 100)
  - SR 100 = 1.0x (no change)
  - SR 150 = 1.5x (50% bonus)
  - SR 200 = 2.0x (double points)
  - SR 50 = 0.5x (half points)
  - Example: 50 runs at SR 150 = 50 × 1.5 = 75 points
- **Fifty (50+ runs)**: +8 points
- **Century (100+ runs)**: +16 points
- **Duck (0 runs, dismissed)**: -2 points
- **NO boundary bonuses** - Fours and sixes count as runs only, no extra points

### Bowling
- **Every wicket**: +12 points (base)
- **Economy Rate Multiplier**: Wicket points × (6 / Economy Rate)
  - ER 6.0 = 1.0x (no change)
  - ER 4.0 = 1.5x (50% bonus)
  - ER 3.0 = 2.0x (double points)
  - ER 8.0 = 0.75x (25% penalty)
  - Example: 3 wickets at ER 4.0 = 36 × 1.5 = 54 points
- **Maiden over**: +25 points each (HIGH VALUE!)
- **5 wicket haul**: +8 points

### Fielding
- **Catch**: +4 points
- **Stumping**: +6 points
- **Run out**: +6 points

## Player Value Multiplier System

After calculating base fantasy points, they are multiplied by the player's **personal performance multiplier**:

- **Multiplier range**: 0.69 to 5.00
- **0.69**: Best players (historical top performers)
- **1.00**: Median club performance
- **5.00**: Weakest players

### How Multipliers Work:
1. At season start, each player gets a multiplier based on previous season stats
2. Multiplier is calculated relative to their club's median performance
3. **Better historical performance = LOWER multiplier**
4. **Weaker historical performance = HIGHER multiplier**
5. Multipliers adjust by max 15% per week based on current performance

### Why This System?
- **Balances team building** - Star players "cost more" (lower multiplier)
- **Rewards picking overlooked players** - High multipliers can yield big points
- **Dynamic over season** - Recent form matters, multipliers drift toward current performance

## NO Tier/League Multipliers

**REMOVED**: Tier multipliers are NO LONGER applied.
- All performances scored equally regardless of league (Topklasse, Youth, Ladies, Social, etc.)
- League tier is only used for team identification and roster constraints
- A 50-run innings earns the same base points whether in Topklasse or ZAMI

## Leadership Multipliers (Team Selection Only)

These are applied in fantasy team scoring, NOT in the scraper:
- **Captain**: Points × 2.0
- **Vice-Captain**: Points × 1.5

## Final Points Formula

```
FINAL POINTS = (Base Fantasy Points) × (Player Multiplier 0.69-5.00) × (Captain/VC multiplier if applicable)
```

### Example:
Player scores 50 runs (SR 125) + 2 wickets (ER 6.0) + 1 maiden + 1 catch:
- Run points: 50 × 1.25 (SR multiplier) = 62.5
- Wicket points: 24 × 1.0 (ER multiplier) = 24
- Bonus points: 8 (fifty) + 25 (maiden) + 4 (catch) = 37
- **Base total: 62.5 + 24 + 37 = 123.5 points**
- Player multiplier: 0.85 (good historical performer)
- Result: 123.5 × 0.85 = **105 points**
- If Captain: 105 × 2.0 = **210 points** to fantasy team

---

## Files Status:
1. **kncb_html_scraper.py** ✅ (Updated with SR/ER multipliers)
2. **fantasy_points_calculator.py** ✅ (Updated with SR/ER multipliers)
3. **frontend/app/how-to-play/page.tsx** ⚠️ (Needs SR/ER multiplier explanation)
4. **frontend/components/PointsCalculator.tsx** ⚠️ (Needs SR/ER multiplier implementation)
