# Scraper Usage Guide - Mock vs Production Modes

## Overview
The KNCB scraper now supports two operating modes:
- **PRODUCTION** - Real KNCB API (live match data)
- **MOCK** - Test server (simulated match data)

This allows full testing of the scraper workflow without depending on real matches.

## Quick Start

### Using Mock Mode (Testing)
```python
from scraper_config import get_scraper_config, ScraperMode
from kncb_html_scraper import KNCBMatchCentreScraper

# Get mock configuration
config = get_scraper_config(ScraperMode.MOCK)

# Initialize scraper
scraper = KNCBMatchCentreScraper(config=config)

# Use normally
matches = await scraper.get_recent_matches_for_club("VRA", days_back=30)
```

### Using Production Mode (Real Data)
```python
from scraper_config import get_scraper_config, ScraperMode
from kncb_html_scraper import KNCBMatchCentreScraper

# Get production configuration
config = get_scraper_config(ScraperMode.PRODUCTION)

# Initialize scraper
scraper = KNCBMatchCentreScraper(config=config)

# Use normally
matches = await scraper.get_recent_matches_for_club("VRA", days_back=7)
```

### Using Default Mode
```python
from kncb_html_scraper import KNCBMatchCentreScraper

# Default = production mode
scraper = KNCBMatchCentreScraper()

# Use normally
matches = await scraper.get_recent_matches_for_club("VRA", days_back=7)
```

## Using Environment Variables

Set the mode via environment variable:

```bash
# Use mock mode
export SCRAPER_MODE=mock

# Use production mode
export SCRAPER_MODE=production
```

Then in your code:
```python
from scraper_config import get_scraper_config
from kncb_html_scraper import KNCBMatchCentreScraper

# Auto-detect from environment
config = get_scraper_config()
scraper = KNCBMatchCentreScraper(config=config)
```

## Complete Example - Mock Mode

```python
#!/usr/bin/env python3
import asyncio
from scraper_config import get_scraper_config, ScraperMode
from kncb_html_scraper import KNCBMatchCentreScraper

async def scrape_test_data():
    # Initialize in mock mode
    config = get_scraper_config(ScraperMode.MOCK)
    scraper = KNCBMatchCentreScraper(config=config)

    # Fetch matches
    matches = await scraper.get_recent_matches_for_club(
        club_name="VRA",
        days_back=30,
        season_id=19
    )

    print(f"Found {len(matches)} matches")

    # Scrape first match
    if matches:
        match_id = matches[0]['match_id']
        scorecard = await scraper.scrape_match_scorecard(match_id)

        # Extract player stats
        tier = matches[0].get('tier', 'tier2')
        players = scraper.extract_player_stats(scorecard, "VRA", tier)

        print(f"Extracted {len(players)} players")

        # Show top performers
        players.sort(key=lambda p: p.get('fantasy_points', 0), reverse=True)
        for i, player in enumerate(players[:5]):
            name = player.get('name', 'Unknown')
            points = player.get('fantasy_points', 0)
            print(f"{i+1}. {name}: {points:.1f} pts")

if __name__ == "__main__":
    asyncio.run(scrape_test_data())
```

## Configuration Details

### Mock Mode
- **API URL**: `http://localhost:5001/rv`
- **Data Source**: Mock server (inside Docker container)
- **Match Data**: Randomly generated but realistic
- **Use Case**: Testing, beta testing, development

### Production Mode
- **API URL**: `https://api.resultsvault.co.uk/rv`
- **Data Source**: Real KNCB Match Centre API
- **Match Data**: Actual cricket matches
- **Use Case**: Live scoring, real leaderboards

## Mock Server Management

### Start Mock Server
```bash
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api /app/start_mock_server.sh
```

### Check Status
```bash
docker exec fantasy_cricket_api curl http://localhost:5001/health
```

### View Logs
```bash
docker exec fantasy_cricket_api tail -f /var/log/mock_kncb_server.log
```

### Stop Mock Server
```bash
docker exec fantasy_cricket_api /app/stop_mock_server.sh
```

## Testing the Configuration

Run the comprehensive test suite:
```bash
docker exec fantasy_cricket_api python3 /app/test_scraper_modes.py
```

This will:
1. Test mock mode with actual data fetching
2. Validate production configuration
3. Test default behavior

## Common Use Cases

### 1. Beta Testing
```python
# Use mock mode to simulate a season
config = get_scraper_config(ScraperMode.MOCK)
scraper = KNCBMatchCentreScraper(config=config)

# Generate weekly matches
for week in range(4):
    matches = await scraper.get_recent_matches_for_club("VRA")
    # Process and score...
```

### 2. Development
```python
# Test new features without hitting real API
import os
os.environ['SCRAPER_MODE'] = 'mock'

config = get_scraper_config()
scraper = KNCBMatchCentreScraper(config=config)
# Develop and test...
```

### 3. Production Scraping
```python
# Live match scoring
config = get_scraper_config(ScraperMode.PRODUCTION)
scraper = KNCBMatchCentreScraper(config=config)

# Scrape real matches
matches = await scraper.get_recent_matches_for_club("ACC", days_back=7)
```

## Backward Compatibility

The scraper maintains backward compatibility. Existing code without configuration will continue to work:

```python
# Old code - still works (defaults to production)
scraper = KNCBMatchCentreScraper()
matches = await scraper.get_recent_matches_for_club("VRA")
```

## Troubleshooting

**Mock server not responding:**
```bash
# Check if running
docker exec fantasy_cricket_api pgrep -f mock_kncb_server.py

# Restart if needed
docker exec fantasy_cricket_api /app/start_mock_server.sh
```

**"Module not found" errors:**
```bash
# Ensure files are in container
docker exec fantasy_cricket_api ls -la /app/scraper_config.py
docker exec fantasy_cricket_api ls -la /app/kncb_html_scraper.py
```

**Wrong mode being used:**
```python
# Check what mode you're in
print(f"Scraper mode: {scraper.mode}")
print(f"API URL: {scraper.kncb_api_url}")
```

## Next Steps

1. **Test with mock data** - Validate full workflow
2. **Run simulation** - Generate 4 weeks of matches
3. **Beta test** - Have users create teams with mock data
4. **Validate calculations** - Check points, leaderboards, multipliers
5. **Switch to production** - Use real KNCB data after validation

## Files Reference

- `scraper_config.py` - Configuration management
- `kncb_html_scraper.py` - Main scraper (now mode-aware)
- `mock_kncb_server.py` - Mock API server
- `test_scraper_modes.py` - Comprehensive test suite
- `test_scraper_with_mock.py` - Detailed integration test

## Support

**Check current status:**
```bash
docker exec fantasy_cricket_api python3 /app/test_mock_server_quick.py
```

**Validate scraper:**
```bash
docker exec fantasy_cricket_api python3 /app/test_scraper_modes.py
```
