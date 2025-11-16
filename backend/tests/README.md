# Scraper Testing Suite

Comprehensive testing framework for validating the KNCB Match Centre scraper logic without hitting the live site.

## 🎯 What's Included

### 1. **Mocked Tests** (`test_scraper_with_mocks.py`)
Tests scraper logic using fixture data - NO network calls to live site.

**Tests:**
- ✅ Tier determination (Topklasse → tier1, etc.)
- ✅ Fantasy points calculation (runs, wickets, catches, bonuses)
- ✅ API response parsing
- ✅ HTML fallback parsing
- ✅ Player stats extraction
- ✅ Match finding
- ✅ Full integration flow

**Run:**
```bash
python3 -m pytest tests/test_scraper_with_mocks.py -v
```

### 2. **Player Deduplication Tests** (`test_player_matcher.py`)
Tests player matching across multiple teams/grades.

**Tests:**
- ✅ Name normalization (handles "Jan de Vries", "J. de Vries", "de Vries, Jan")
- ✅ Fuzzy name matching
- ✅ Player ID matching
- ✅ Stats aggregation across multiple matches
- ✅ Database player matching

**Run:**
```bash
python3 -m pytest tests/test_player_matcher.py -v
```

### 3. **Real Data Test Script** (`test_with_real_data.py`)
Tests with ACTUAL matchcentre data (read-only, safe).

**Run:**
```bash
python3 tests/test_with_real_data.py
```

### 4. **Demo Scripts**

**Player Deduplication Demo:**
```bash
python3 demo_player_deduplication.py
```

Shows how the system handles a player who plays in:
- ACC 1 (tier2)
- U17 Competition (youth)
- ZAMI Social (social)

All in the same week!

## 📁 Fixture Files

Located in `tests/fixtures/`:

- `grades_response.json` - Sample grades API response
- `matches_response.json` - Sample matches API response
- `scorecard_api_response.json` - Sample scorecard with full player stats
- `scorecard_html.html` - Sample HTML scorecard page
- `multi_grade_player_scenario.json` - Player in multiple grades

## 🔑 Key Features Tested

### 1. Player Deduplication
The system correctly handles:
- Player appearing in multiple grades (ACC 1 + U17 + ZAMI)
- Name variations ("Jan de Vries" vs "J. de Vries")
- With and without player IDs
- Points aggregation across all matches

### 2. Fantasy Points Calculation
Validates:
- Run scoring (1 point/run)
- Boundaries (4s = 1pt, 6s = 2pts)
- Milestones (50 = 8pts, 100 = 16pts)
- Duck penalty (-2pts)
- Wickets (12pts each)
- 5-wicket haul bonus (8pts)
- Maidens (4pts)
- Catches (4pts), Stumpings (6pts), Run-outs (6pts)
- Tier multipliers applied correctly

### 3. Scorecard Finding
Tests:
- API endpoint access
- HTML fallback when API fails
- Date filtering
- Club name matching
- Grade/tier determination

## 🚀 Quick Start

### Install Dependencies
```bash
pip3 install pytest pytest-asyncio
```

### Run All Tests
```bash
# Mocked tests (fast)
python3 -m pytest tests/test_scraper_with_mocks.py -v

# Player matcher tests
python3 -m pytest tests/test_player_matcher.py -v

# Run everything
python3 -m pytest tests/ -v
```

### Run Test Runner
```bash
python3 tests/run_tests.py
```

## 📊 Test Results

**Scraper Tests:** 10/10 passing ✅
**Player Matcher Tests:** 8/8 passing ✅

## 🧪 Testing Scenarios

### Scenario 1: Player in Multiple Grades
**Problem:** Jan plays in ACC 1, U17, and ZAMI in same week. How do we track this?

**Solution:**
1. Scraper extracts all performances with player_id when available
2. PlayerMatcher deduplicates by ID
3. Aggregates total points: tier2 + youth + social
4. Updates single player record in database

**Result:**
- 3 match records
- 1 player record with aggregated stats
- Correct points: 84 (tier2) + 60 (youth) + 17 (social) = 161 total

### Scenario 2: Name Variations
**Problem:** Same player appears as "Jan de Vries" and "J. de Vries"

**Solution:**
- Match by player_id first (most reliable)
- Fuzzy name matching fallback
- Normalization: "jandevries" vs "jdevries" (85% similarity)

### Scenario 3: New Players
**Problem:** Player not in database yet

**Solution:**
- Returns in `unmatched_players` list
- Admin can review and add to database
- Next week will match correctly

## 🔧 Customization

### Adjust Name Similarity Threshold
```python
# In player_matcher.py
matcher = PlayerMatcher()
matcher.name_similarity_threshold = 0.80  # Default: 0.85
```

### Change Points Configuration
```python
# In kncb_html_scraper.py
scraper.points_config['batting']['run'] = 2  # 2 points per run
scraper.points_config['bowling']['wicket'] = 15  # 15 points per wicket
```

### Add New Fixtures
1. Capture real API response from matchcentre
2. Save as JSON in `tests/fixtures/`
3. Create test using the fixture

## 📝 Next Steps

### For Testing with Real Data:
1. **Capture real scorecards:**
   ```bash
   python3 tests/test_with_real_data.py
   ```

2. **Review extracted data:**
   - Check `test_real_scorecard.json`
   - Verify player names match database
   - Confirm fantasy points look correct

3. **Dry-run database update:**
   - Process data with PlayerMatcher
   - Generate SQL preview
   - Review before executing

### For Production:
1. **Integrate with database:**
   - Connect to PostgreSQL
   - Implement transaction handling
   - Add error recovery

2. **Set up automation:**
   - Celery scheduled task
   - Weekly scrape on Monday morning
   - Email notifications for issues

3. **Monitor:**
   - Log all matches processed
   - Track unmatched players
   - Alert on parsing errors

## ⚠️ Important Notes

### Player Matching
- **Always prefer player_id** when available (most reliable)
- Fuzzy name matching is fallback only
- New players require manual review
- Consider: "Jan Smith" at ACC ≠ "Jan Smith" at VRA

### Tier Multipliers
- tier1 (Topklasse/Hoofdklasse): 1.2x
- tier2 (Eerste/Tweede): 1.0x
- tier3 (Derde/Vierde): 0.8x
- social (ZAMI/ZOMI): 0.4x
- youth (U13-U17): 0.6x
- ladies: 0.9x

### Edge Cases Handled
- ✅ Duck (0 runs, > 0 balls): -2 points
- ✅ Not out batsman: No penalty
- ✅ DNB (Did Not Bat): 0 points
- ✅ Player bowling and fielding in same innings
- ✅ Player in multiple matches same day

## 🐛 Troubleshooting

### Tests Fail with Import Error
```bash
# Make sure you're in backend directory
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend

# Install dependencies
pip3 install pytest pytest-asyncio playwright
```

### Fixture Dates Out of Range
```bash
# Update fixture dates in tests/fixtures/matches_response.json
# Use recent dates (last 30 days)
```

### Real Data Test Fails
- Check match_id exists and is completed
- Verify network connection
- Ensure matchcentre site is accessible

## 📚 Documentation

- **Scraper:** `kncb_html_scraper.py`
- **Player Matcher:** `player_matcher.py`
- **Tests:** `tests/`
- **Fixtures:** `tests/fixtures/`
- **Demo:** `demo_player_deduplication.py`

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD)
2. Add fixtures for edge cases
3. Update this README
4. Run full test suite

## ✅ Test Checklist

Before deploying:
- [ ] All mocked tests pass
- [ ] Player matcher tests pass
- [ ] Tested with real match data
- [ ] Verified player deduplication works
- [ ] Checked fantasy points calculations
- [ ] Reviewed unmatched players list
- [ ] Dry-run database updates look correct
- [ ] Beta testers can see updated points
