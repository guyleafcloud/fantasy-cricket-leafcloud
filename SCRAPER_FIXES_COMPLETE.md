# KNCB Scraper Fixes - Complete ✅

**Date:** 2025-11-20
**Status:** ✅ DEPLOYED TO PRODUCTION

---

## Summary

The KNCB scraper has been **successfully fixed and tested** with real 2025 scorecard URLs. All tests passed and the updated scraper is now deployed to production.

---

## What Was Fixed

### 1. Primary Scraping Method Changed ✅

**Before:** API-first with HTML fallback
**After:** HTML text parsing primary, API fallback (likely blocked anyway)

**Why:** API returns 401 even with Referer header. HTML text parsing is more reliable.

### 2. Fixed Scorecard URL Format ✅

**Before:**
```python
url = f"{self.matchcentre_url}/match/{match_id}"
# Wrong: https://matchcentre.kncb.nl/match/7324739
```

**After:**
```python
url = f"{self.matchcentre_url}/match/{self.entity_id}-{match_id}/scorecard/"
# Correct: https://matchcentre.kncb.nl/match/134453-7324739/scorecard/
```

### 3. Integrated Text Parser from dev-scripts ✅

Copied working text parser methods from `dev-scripts/parse_scorecard.py`:
- `_parse_batting_section()` - Parses vertical text layout for batting stats
- `_parse_bowling_section()` - Parses vertical text layout for bowling stats

**Handles React-rendered content:**
- No HTML tables - extracts plain text
- No CSS selectors - parses text lines directly
- Vertical layout - each stat on separate line

---

## Test Results

### Local Tests (3 matches):
```
✅ ACC 1 vs HBS (Week 1)
   - 19 players extracted
   - 308 total fantasy points

✅ Kampong 1 vs ACC 1 (Week 1)
   - 19 players extracted
   - 251 total fantasy points

✅ VRA 4 vs ACC 2 (Week 1)
   - 21 players extracted
   - 231 total fantasy points

🎉 ALL TESTS PASSED: 3/3 matches
```

### Production Server Test:
```bash
docker exec fantasy_cricket_api python3 -c "test scraper"

✅ Scraper works on production!
📊 Extracted 19 players
💯 Total fantasy points: 308
```

---

## How It Works Now

### 1. Scorecard Scraping Flow

```python
async def scrape_match_scorecard(match_id):
    # PRIMARY: HTML text parsing
    scorecard = await _scrape_scorecard_html(page, match_id)

    if scorecard:
        return scorecard  # ✅ Success (most common)

    # FALLBACK: Try API with Referer (likely fails)
    await page.set_extra_http_headers({'Referer': 'https://matchcentre.kncb.nl/'})
    response = await page.goto(f"{api_url}/match/{match_id}/")

    if response.status == 200:
        return json.loads(response)  # Unlikely but try anyway
    else:
        return None  # Failed both methods
```

### 2. Text Parsing Strategy

**Batting Section (7 lines per player):**
```
M BOENDERMAKER       # Player name
b A Sehgal           # Dismissal
11                   # Runs
24                   # Balls
1                    # Fours
0                    # Sixes
45.83                # Strike rate
```

**Bowling Section (7 lines per bowler):**
```
A Sehgal             # Bowler name
8                    # Overs
1                    # Maidens
32                   # Runs
3                    # Wickets
0                    # No balls
2                    # Wides
```

Parser walks through lines, identifies sections by "BATTING" and "BOWLING" headers, then extracts 7-line blocks for each player.

### 3. Fantasy Points Calculation

Uses centralized `rules-set-1.py` with tiered system:

**Batting:**
- Tiered runs: 1-30 (1.0), 31-49 (1.25), 50-99 (1.5), 100+ (1.75 pts/run)
- Boundaries: +1 per four, +2 per six

**Bowling:**
- Tiered wickets: 1-2 (15), 3-4 (20), 5-10 (30 pts each)
- Maidens: 15 points

**Fielding:**
- Catches: 8 points (16 if wicketkeeper)
- Stumpings: 12 points
- Run outs: 6 points

---

## Files Changed

### Updated:
- `backend/kncb_html_scraper.py` - Main scraper with text parsing

### Created for Testing:
- `backend/test_2025_scorecard.py` - Single scorecard test
- `backend/test_multiple_scorecards.py` - Multiple scorecard test

### Documentation:
- `SCRAPER_INFRASTRUCTURE_ANALYSIS.md` - Complete technical analysis
- `SCRAPER_FIXES_COMPLETE.md` - This file

---

## What Still Works

All existing functionality intact:

✅ **Match Discovery**
```python
matches = await scraper.get_recent_matches_for_club("ACC", days_back=7, season_id=19)
```

✅ **Weekly Scraping**
```python
results = await scraper.scrape_weekly_update(["ACC", "VRA"], days_back=7)
```

✅ **Fantasy Points Calculation**
- Uses `rules-set-1.py`
- All tiered rules applied correctly

✅ **Configuration System**
- Production/mock modes
- Environment variable support

---

## Next Steps for 2026 Season

### Phase 1: Database Integration (TODO)

Create `backend/store_performances.py`:

```python
def store_weekly_performances(results: Dict, league_id: str, round_number: int):
    """Store scraped performances in player_performances table"""

    for perf in results['performances']:
        # 1. Match player by name to database
        player = find_player(perf['player_name'], perf['club'])

        # 2. Store performance
        performance = PlayerPerformance(
            player_id=player.id,
            league_id=league_id,
            round_number=round_number,
            runs=perf['batting'].get('runs', 0),
            wickets=perf['bowling'].get('wickets', 0),
            # ... all stats
            fantasy_points=perf['fantasy_points']
        )

        session.add(performance)

    session.commit()
```

### Phase 2: Weekly Automation (April 2026)

Create `backend/scrape_weekly.sh`:

```bash
#!/bin/bash
# Weekly scraping - runs every Monday at 9 AM

cd /app
python3 <<EOF
import asyncio
from kncb_html_scraper import KNCBMatchCentreScraper
from store_performances import store_weekly_performances

async def main():
    scraper = KNCBMatchCentreScraper()

    # Scrape last 7 days for configured clubs
    clubs = ["ACC", "VRA", "ZAMI", "Kampong", "HBS"]
    results = await scraper.scrape_weekly_update(clubs, days_back=7)

    # Store in database
    for league in get_active_leagues():
        store_weekly_performances(results, league.id, current_round())

    print(f"✅ Processed {results['total_performances']} performances")

asyncio.run(main())
EOF
```

**Cron job:**
```bash
0 9 * * 1 /app/scrape_weekly.sh >> /var/log/scraper.log 2>&1
```

### Phase 3: Monitoring (Ongoing)

- Log scraping results to `/var/log/scraper.log`
- Alert if scraper fails for 2+ consecutive weeks
- Monitor for KNCB website structure changes

---

## Key Technical Details

### Why HTML Parsing Works

1. **Public pages** - No authentication needed
2. **Text content** - Always available even if React changes
3. **Consistent format** - KNCB uses standardized scorecard layout
4. **Reliable** - Doesn't depend on API or CSS classes

### Why API Likely Fails

1. **IP-based blocking** - Server IPs may be flagged
2. **Rate limiting** - API has request limits
3. **Authentication** - Referer header helps but may not be enough
4. **Bot detection** - Even with stealth, API can detect automation

### Fallback Strategy

HTML text parsing is **primary** because:
- More reliable than API
- Harder to block (public pages)
- Doesn't require authentication
- React rendering doesn't affect text content

API is **fallback** because:
- Nice to have if it works
- Returns structured JSON (easier to parse)
- But we don't depend on it

---

## How to Use for 2026

### Manual Scraping (Test/Debug)

```python
import asyncio
from kncb_html_scraper import KNCBMatchCentreScraper

async def test():
    scraper = KNCBMatchCentreScraper()

    # Get recent matches for ACC
    matches = await scraper.get_recent_matches_for_club("ACC", days_back=7, season_id=20)

    for match in matches:
        # Scrape scorecard
        scorecard = await scraper.scrape_match_scorecard(match['match_id'])

        # Extract player stats with fantasy points
        players = scraper.extract_player_stats(scorecard, "ACC", "tier2")

        for player in players:
            print(f"{player['player_name']}: {player['fantasy_points']} pts")

asyncio.run(test())
```

### Production Scraping (Weekly)

```bash
# On server, run weekly scraping script
/app/scrape_weekly.sh

# Or manually trigger via Docker
docker exec fantasy_cricket_api python3 /app/scrape_weekly.sh
```

---

## Verification Checklist

- [x] Scraper works locally with 2025 URLs
- [x] Scraper works on production server
- [x] Multiple matches tested (3/3 passed)
- [x] Fantasy points calculated correctly
- [x] Text parser handles all stat types
- [x] Deployment successful
- [ ] Database integration created (TODO)
- [ ] Weekly automation configured (TODO - April 2026)

---

## Support & Troubleshooting

### If Scraper Fails

1. **Check URL format:**
   - Must be: `https://matchcentre.kncb.nl/match/134453-{match_id}/scorecard/`
   - Not: `https://matchcentre.kncb.nl/match/{match_id}`

2. **Check page structure:**
   - Look for "BATTING" and "BOWLING" headers in text
   - Verify vertical layout (7 lines per player)

3. **Check Playwright:**
   - Ensure browsers installed: `playwright install chromium`
   - Check headless mode works on server

4. **Check logs:**
   ```bash
   docker logs fantasy_cricket_api | grep scraper
   ```

### If KNCB Changes Website

1. **Inspect page text:**
   ```python
   page_text = await page.inner_text('body')
   print(page_text)  # See actual text structure
   ```

2. **Adjust parsers:**
   - Modify `_parse_batting_section()` if format changes
   - Modify `_parse_bowling_section()` if format changes

3. **Test with recent URL:**
   ```bash
   python3 test_2025_scorecard.py
   ```

---

## Conclusion

✅ **Scraper is working and deployed**
✅ **Tested with real 2025 scorecards**
✅ **Production-ready for 2026 season**

**Remaining work:**
1. Create database integration (before season starts)
2. Set up weekly automation (April 2026)
3. Monitor for website changes (ongoing)

The infrastructure is solid and ready for the 2026 season!

---

**Last Updated:** 2025-11-20
**Tested By:** Claude Code
**Status:** ✅ PRODUCTION READY
