# Mock KNCB Server - Production Deployment

## Status
✅ **DEPLOYED** on fantcric.fun (inside `fantasy_cricket_api` container)

The mock server is running on **port 5001** inside the Docker container.

## Quick Commands

### Start the Mock Server
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api /app/start_mock_server.sh
```

### Stop the Mock Server
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api /app/stop_mock_server.sh
```

### Check Status
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api curl http://localhost:5001/health
```

### View Logs
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api tail -f /var/log/mock_kncb_server.log
```

### Run Quick Test
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api python3 /app/test_mock_server_quick.py
```

## API Endpoints

The mock server provides these endpoints (accessible only inside the container):

```
http://localhost:5001/health
http://localhost:5001/rv/{entity_id}/grades/?apiid={api_id}&seasonId={season_id}
http://localhost:5001/rv/{entity_id}/matches/?apiid={api_id}&seasonId={season_id}&gradeId={grade_id}
http://localhost:5001/rv/match/{match_id}/?apiid={api_id}
```

## Using with the Scraper

To test the scraper with mock data, modify the scraper to use localhost:5001 instead of api.resultsvault.co.uk:

```python
from kncb_html_scraper import KNCBMatchCentreScraper

class MockKNCBScraper(KNCBMatchCentreScraper):
    def __init__(self):
        super().__init__()
        # Override the API URL to point to mock server
        self.kncb_api_url = "http://localhost:5001/rv"
```

## What It Generates

- **5 grades/leagues** (Hoofdklasse, Topklasse, Eerste Klasse, etc.)
- **10-20 matches per grade** with random clubs
- **Realistic player stats**:
  - Batting: Runs 0-100, SR 50-200, boundaries calculated
  - Bowling: Wickets 0-5, ER 3-9, maidens 0-3
  - Fielding: Catches, stumpings, run-outs
- **Fantasy points calculated** using tiered system from rules-set-1.py

## Beta Testing Workflow

1. **Start mock server** (already running)
2. **Generate simulated season** - Server generates matches on demand
3. **Beta testers create teams** - Use simulated player data
4. **Run weekly "matches"** - Generate new scorecards each week
5. **Calculate fantasy scores** - Scraper processes mock matches
6. **Update leaderboards** - Full scoring workflow tested

## Production vs Testing

### For Testing (Mock Data)
- Use mock server at `localhost:5001`
- Data is random but realistic
- No rate limiting, instant results
- Perfect for beta testing

### For Production (Real KNCB Data)
- Use real API at `api.resultsvault.co.uk`
- Actual match data from KNCB
- Subject to rate limits
- Use after beta testing complete

## File Locations

All files are in the `fantasy_cricket_api` container:

```
/app/mock_kncb_server.py          - Main server code
/app/test_mock_server_quick.py    - Quick validation test
/app/test_scraper_with_mock.py    - Full scraper integration test
/app/start_mock_server.sh         - Start script
/app/stop_mock_server.sh          - Stop script
/var/log/mock_kncb_server.log     - Server logs
```

## Troubleshooting

**Server not responding:**
```bash
# Check if running
docker exec fantasy_cricket_api pgrep -f mock_kncb_server.py

# Restart
docker exec fantasy_cricket_api /app/stop_mock_server.sh
docker exec fantasy_cricket_api /app/start_mock_server.sh
```

**Check logs for errors:**
```bash
docker exec fantasy_cricket_api tail -100 /var/log/mock_kncb_server.log
```

**Test connectivity:**
```bash
docker exec fantasy_cricket_api python3 /app/test_mock_server_quick.py
```

## Next Steps

1. ✅ Mock server deployed and running
2. ✅ All endpoints tested and working
3. ⏭️ Configure scraper to use mock data
4. ⏭️ Generate simulated season (4-8 weeks)
5. ⏭️ Test full workflow with beta testers' fantasy teams
6. ⏭️ Validate points calculation and leaderboards
7. ⏭️ Switch to real KNCB data after validation

## Notes

- Mock server runs inside the Docker container, not exposed externally
- Only accessible from within the container (perfect for testing)
- Generates new random matches each time you query (simulates different weeks)
- 19 matches currently in memory (will grow as you query different grades)
