# Mock KNCB Server for Scraper Testing

## Overview
This mock server simulates the KNCB Match Centre API, allowing you to test the scraper without depending on real matches. It generates realistic match data with proper statistics and serves it in the exact format the KNCB API provides.

## Files
- `mock_kncb_server.py` - Flask server that mimics KNCB API endpoints
- `test_scraper_with_mock.py` - Test script that runs the scraper against mock data

## Features
✅ Simulates realistic match data with proper statistics
✅ Generates batting, bowling, and fielding performances
✅ Serves data in exact KNCB API JSON format
✅ Allows testing full scraper workflow without real matches
✅ Perfect for beta testing and edge case validation

## Usage

### 1. Install dependencies
```bash
pip install flask flask-cors
```

### 2. Start the mock server
```bash
python3 mock_kncb_server.py
```

The server will run on `http://localhost:5001`

### 3. Run the scraper test (in another terminal)
```bash
python3 test_scraper_with_mock.py
```

## What Gets Tested

1. **Grade Fetching** - Retrieves list of leagues/divisions
2. **Match Listing** - Gets recent matches for a club
3. **Scorecard Scraping** - Fetches detailed match scorecards
4. **Player Stats Extraction** - Parses batting/bowling/fielding stats
5. **Points Calculation** - Calculates fantasy points with tiered system
6. **Multi-match Aggregation** - Tests player performance across multiple matches

## API Endpoints

The mock server provides these endpoints (matching KNCB API):

```
GET /rv/{entity_id}/grades/
    - Returns list of grades/leagues

GET /rv/{entity_id}/matches/?seasonId={id}&gradeId={id}
    - Returns list of matches for a grade

GET /rv/match/{match_id}/
    - Returns detailed scorecard for a match

GET /health
    - Health check endpoint
```

## Simulated Data

### Batting
- Runs: 0-100 (realistic distribution)
- Strike rates: 50-200
- Boundaries: Calculated from runs
- Dismissals: Various types (caught, bowled, lbw, etc.)

### Bowling
- Overs: 0-10
- Wickets: 0-5 (weighted toward 0-2)
- Economy rates: 3-9 runs per over
- Maidens: 0-3

### Fielding
- Catches: 0-3 per player
- Stumpings: 0-1 (rare)
- Run-outs: 0-1 (occasional)

## Example Output

```
🧪 SCRAPER TEST WITH MOCK DATA
================================================================================

📋 Step 1: Fetching recent matches for VRA...
✅ Found 15 matches

📊 Sample matches:
   1. VRA vs ACC - Hoofdklasse (2025-11-01)
   2. Quick Haag vs VRA - Topklasse (2025-10-28)
   3. VRA vs HCC - Eerste Klasse (2025-10-25)

📥 Step 2: Scraping detailed scorecard for match 100000...
✅ Got scorecard with 2 innings

👥 Step 3: Extracting player stats...
✅ Extracted stats for 22 players

🏆 Top 10 Fantasy Point Scorers:
   1. Jason Patel           - 207.1 pts  (85(46), 2ct)
   2. Michael Singh         - 160.1 pts  (3/22, 5M)
   3. David de Jong         - 119.5 pts  (45(32), 2/20, 1ct)
```

## Integration with Real System

Once testing is complete, you can easily switch back to real KNCB data:

```python
# For testing (mock)
scraper = MockKNCBScraper(mock_server_url="http://localhost:5001")

# For production (real KNCB)
scraper = KNCBMatchCentreScraper()
```

## Beta Testing Workflow

1. **Start mock server** on production or test environment
2. **Generate simulated season** - Create 4-8 weeks of matches
3. **Beta testers create teams** - Select players from simulated data
4. **Run weekly "matches"** - Generate new match results each week
5. **Calculate fantasy scores** - Run scraper against mock matches
6. **Update leaderboards** - Test full scoring workflow
7. **Validate multiplier adjustments** - Ensure handicap system works

## Edge Cases to Test

Add these scenarios to the mock server:

- [ ] DNB (Did Not Bat) - Player in team but didn't bat
- [ ] DNB (Did Not Bowl) - Player in team but didn't bowl
- [ ] Duck (0 runs dismissed) - Should get -2 penalty
- [ ] Century - Should get +16 bonus
- [ ] 5-wicket haul - Should get +8 bonus
- [ ] Wicketkeeper catches - Should get 2x multiplier
- [ ] Rain-affected match - Reduced overs
- [ ] Tie/No result - How to handle?

## Next Steps

1. Run initial test: `python3 test_scraper_with_mock.py`
2. Add more realistic player names from your database
3. Implement edge case scenarios
4. Create "season simulation" mode (generate 4+ weeks of matches)
5. Integrate with database update workflow
6. Test with beta testers' fantasy teams

## Troubleshooting

**"Cannot connect to mock server"**
- Make sure `mock_kncb_server.py` is running
- Check if port 5001 is available
- Try: `curl http://localhost:5001/health`

**"No matches found"**
- Check club name spelling (case-insensitive)
- Increase `days_back` parameter
- Mock server generates random matches each time

**"Fantasy points seem wrong"**
- Verify `rules-set-1.py` is being used
- Check tiered points calculation
- Run `test_tiered_points_system.py` to validate rules
