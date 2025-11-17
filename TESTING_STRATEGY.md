# Fantasy Cricket - Beta Testing Strategy

## Overview
Comprehensive testing plan to validate scraper, points calculation, and simulate real-world beta test with actual user teams.

---

## Phase 1: Scraper Testing
**Goal**: Verify KNCB data scraping works correctly and reliably

### 1.1 Unit Tests
- **File**: `backend/test_scraper_flow.py` (if exists) or create new
- **What to test**:
  - ✅ Match data extraction from KNCB website
  - ✅ Player performance parsing (batting, bowling, fielding)
  - ✅ Handle edge cases (DNB, injured, rain-affected matches)
  - ✅ Data validation (no negative runs, valid overs format)

### 1.2 Integration Tests
- **Test real match IDs** from recent KNCB games
- **Verify**:
  - Match scorecards parse correctly
  - Player stats extracted accurately
  - All fielding events captured (catches, run-outs, stumpings)

### 1.3 Scraper Checklist
```bash
# Test the scraper
cd backend
python3 kncb_scraper.py --match-id <RECENT_MATCH_ID> --verbose
```

**Expected Output**:
- Valid JSON with all player performances
- No missing critical stats
- Proper error handling for incomplete data

---

## Phase 2: Points Calculation Testing
**Goal**: Ensure fantasy points are calculated correctly per rules-set-1

### 2.1 Rules Validation
- **File**: `backend/rules-set-1.py`
- **Current rules** (updated tiered system):

  **BATTING:**
  - Runs 1-30: 1.0 pts/run
  - Runs 31-49: 1.25 pts/run
  - Runs 50-99: 1.5 pts/run
  - Runs 100+: 1.75 pts/run
  - Multiplier: Run points × (SR / 100)
  - Fifty bonus: +8 pts
  - Century bonus: +16 pts
  - Duck penalty: -2 pts

  **BOWLING:**
  - Wickets 1-2: 15 pts each
  - Wickets 3-4: 20 pts each
  - Wickets 5-10: 30 pts each
  - Multiplier: Wicket points × (6.0 / ER)
  - Maiden: +15 pts each
  - 5-wicket haul: +8 pts

  **FIELDING:**
  - Catch: +15 pts
  - Stumping: +15 pts
  - Run-out: +6 pts
  - Wicketkeeper catch: 2x (30 pts)

### 2.2 Test Scenarios
- **File**: `backend/test_new_points_rules.py`
- **Test cases** (already defined):
  1. ✅ Explosive innings (SR 184)
  2. ✅ Anchor innings (SR 45 - slow)
  3. ✅ Economical bowling with maidens
  4. ✅ Expensive bowling (ER 8.0)
  5. ✅ Boundaries without bonus
  6. ✅ Maiden masterclass
  7. ✅ Match-winning century

```bash
# Run points tests
python3 backend/test_new_points_rules.py
```

**Expected**: All 7 scenarios pass with exact point calculations

### 2.3 Frontend Calculator Test
- **URL**: https://fantcric.fun/calculator
- **Manual test**:
  - Enter test performance data
  - Verify calculation matches backend
  - Check tiered points apply correctly
  - Verify rules-set-1.json loads properly

---

## Phase 3: Simulation Testing
**Goal**: Simulate multiple weeks of cricket to test system dynamics

### 3.1 Month Simulation
- **File**: `backend/simulate_month_of_play.py`
- **What it does**:
  - Simulates 4 weeks of matches
  - Generates realistic performances based on player quality
  - Updates player stats after each match
  - Adjusts player multipliers weekly (15% max drift)
  - Tracks player progression

```bash
# Run simulation (dry-run first)
cd backend
python3 simulate_month_of_play.py --weeks 4 --dry-run

# If looks good, run for real
python3 simulate_month_of_play.py --weeks 4
```

**Expected outputs**:
- ✅ 2-3 matches per player per week
- ✅ Realistic score distributions
- ✅ Multipliers adjust based on performance
- ✅ Top performers' multipliers decrease (handicap)
- ✅ Poor performers' multipliers increase (boost)

### 3.2 Validate Multiplier System
- Check multiplier drift stays within 15% per week
- Verify range: 0.69 (best) to 5.0 (worst)
- Ensure median player stays ~1.0

---

## Phase 4: Beta Test with Real Users
**Goal**: Test full game flow with actual beta testers and their teams

### 4.1 Beta Test Setup
**Prerequisites**:
1. ✅ 5-10 beta testers recruited
2. ✅ Each creates a fantasy team (11 players)
3. ✅ Teams submitted before test matches
4. ✅ One active league created for beta

### 4.2 Test Match Workflow

#### BEFORE MATCHES:
1. **Verify teams are valid**:
   ```sql
   SELECT team_id, owner_name, COUNT(*) as player_count
   FROM team_players
   GROUP BY team_id, owner_name;
   ```
   - Each team should have 11 players
   - Check captain/vice-captain assigned

2. **Note starting multipliers**:
   ```sql
   SELECT name, multiplier FROM players WHERE id IN (
     SELECT DISTINCT player_id FROM team_players
   );
   ```

#### DURING/AFTER MATCHES:
3. **Scrape match data**:
   ```bash
   python3 backend/kncb_scraper.py --match-ids <LIST_OF_MATCH_IDS>
   ```

4. **Calculate fantasy points**:
   ```bash
   python3 backend/calculate_fantasy_scores.py --round <ROUND_NUMBER>
   ```

5. **Update leaderboard**:
   ```bash
   curl https://api.fantcric.fun/api/leagues/<LEAGUE_ID>/leaderboard
   ```

### 4.3 Beta Test Checklist

**Week 1** (Baseline):
- [ ] All teams submitted
- [ ] Scrape 1 full round of matches
- [ ] Calculate points for all players
- [ ] Verify leaderboard updates
- [ ] Check team scores calculated correctly (including captain/VC multipliers)
- [ ] Get user feedback on accuracy

**Week 2** (Multiplier Test):
- [ ] Run multiplier adjustment script
- [ ] Verify top performers get handicap (multiplier decreases)
- [ ] Verify poor performers get boost (multiplier increases)
- [ ] Check no player exceeds 15% weekly drift
- [ ] Scrape next round
- [ ] Recalculate with new multipliers
- [ ] Verify scores feel balanced

**Week 3** (Edge Cases):
- [ ] Test player injury/DNB scenarios
- [ ] Test rain-affected matches
- [ ] Test tie/no result scenarios
- [ ] Verify transfer system (if implemented)

**Week 4** (Full Season):
- [ ] Final multiplier adjustments
- [ ] Calculate season winner
- [ ] Generate season statistics
- [ ] Export data for analysis

### 4.4 Monitoring & Metrics

**Track these metrics**:
1. **Accuracy**: % of scraped matches with correct data
2. **Completeness**: % of player performances captured
3. **Balance**: Score distribution across teams
   - No single team dominating by >50%
   - Multiplier system creating parity
4. **Performance**: API response times <500ms
5. **User satisfaction**: Feedback from beta testers

**Dashboard queries**:
```sql
-- Top scorers this round
SELECT tp.player_id, p.name, SUM(mp.fantasy_points) as total_points
FROM team_players tp
JOIN players p ON tp.player_id = p.id
JOIN match_performances mp ON p.id = mp.player_id
WHERE mp.round_number = <CURRENT_ROUND>
GROUP BY tp.player_id, p.name
ORDER BY total_points DESC
LIMIT 20;

-- Team rankings
SELECT t.id, t.name, t.owner_name, SUM(mp.fantasy_points) as total_points
FROM teams t
JOIN team_players tp ON t.id = tp.team_id
JOIN match_performances mp ON tp.player_id = mp.player_id
WHERE t.league_id = <BETA_LEAGUE_ID>
GROUP BY t.id, t.name, t.owner_name
ORDER BY total_points DESC;

-- Multiplier distribution
SELECT
  CASE
    WHEN multiplier < 0.8 THEN 'Elite (< 0.8)'
    WHEN multiplier < 1.0 THEN 'Strong (0.8-1.0)'
    WHEN multiplier < 1.5 THEN 'Average (1.0-1.5)'
    WHEN multiplier < 3.0 THEN 'Weak (1.5-3.0)'
    ELSE 'Very Weak (3.0+)'
  END as category,
  COUNT(*) as player_count
FROM players
GROUP BY category
ORDER BY MIN(multiplier);
```

---

## Phase 5: Issues & Bug Tracking

### Common Issues to Watch For:
1. **Scraper failures**:
   - KNCB website changes
   - Timeout issues
   - Malformed HTML

2. **Points calculation errors**:
   - Tier boundaries not applied correctly
   - SR/ER multipliers wrong
   - Wicketkeeper bonus not applying

3. **Multiplier drift**:
   - Exceeding 15% weekly change
   - Players hitting min/max bounds (0.69/5.0)
   - Median not staying ~1.0

4. **Performance issues**:
   - Slow leaderboard loading
   - Database locks during calculation
   - Frontend calculator not loading rules

### Debug Commands:
```bash
# Check recent scraper runs
docker logs fantasy_cricket_worker --tail 100

# Verify rules file
curl https://fantcric.fun/rules-set-1.json | jq

# Check API health
curl https://api.fantcric.fun/health

# Database connection
docker exec -it fantasy_cricket_db psql -U fantasy_user -d fantasy_cricket
```

---

## Phase 6: Go/No-Go Decision

### Criteria for Public Launch:
- [ ] 95%+ scraper success rate over 2 weeks
- [ ] 100% points calculation accuracy (all test scenarios pass)
- [ ] Multiplier system converging properly (no runaway values)
- [ ] Zero critical bugs in beta test
- [ ] Positive feedback from all beta testers
- [ ] API performance <500ms 95th percentile
- [ ] Frontend calculator matches backend exactly
- [ ] Mobile experience acceptable

### If Not Ready:
- Extend beta test by 2 more weeks
- Focus on fixing identified issues
- Add more automated tests
- Recruit more beta testers for edge cases

---

## Next Steps

1. **Immediate** (This Week):
   - [ ] Run `test_new_points_rules.py` - verify all 7 scenarios pass
   - [ ] Test frontend calculator at /calculator
   - [ ] Run `simulate_month_of_play.py --dry-run` - check for errors

2. **Beta Prep** (Next Week):
   - [ ] Recruit 5-10 beta testers
   - [ ] Create beta league in database
   - [ ] Send beta testers team creation instructions
   - [ ] Schedule first test match round

3. **Beta Test** (Weeks 3-6):
   - [ ] Run full 4-week beta test following Phase 4 checklist
   - [ ] Collect feedback and metrics
   - [ ] Fix bugs as they arise
   - [ ] Document any rule changes needed

4. **Launch Decision** (Week 7):
   - [ ] Review all metrics
   - [ ] Make Go/No-Go decision
   - [ ] If Go: Plan public launch
   - [ ] If No-Go: Extend beta and iterate
