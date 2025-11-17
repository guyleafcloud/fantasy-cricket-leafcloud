#!/usr/bin/env python3
"""
KNCB Match Centre HTML Scraper - Fully Autonomous
==================================================
Scrapes player data from public match centre pages.
No API authentication required - works 24/7 on server.

This is the BEST solution for autonomous operation because:
- No IP blocking (public pages)
- No API authentication needed
- Reliable and consistent
- Runs independently on server

Strategy:
1. Weekly: Scrape matches for configured clubs
2. Extract player stats from match scorecards
3. Calculate fantasy points per match
4. Aggregate season totals
5. Update database
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, Page
import json
import re

# Import centralized rules
try:
    from rules_set_1 import FANTASY_RULES, calculate_total_fantasy_points
except ImportError:
    # Fallback if module name has hyphens
    import importlib
    rules_module = importlib.import_module('rules-set-1')
    FANTASY_RULES = rules_module.FANTASY_RULES
    calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

# Import scraper configuration
try:
    from scraper_config import get_scraper_config, ScraperConfig, ScraperMode
except ImportError:
    # Fallback if config not available
    ScraperConfig = None
    ScraperMode = None
    get_scraper_config = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNCBMatchCentreScraper:
    """Autonomous scraper for KNCB match centre

    Supports both production (real KNCB API) and mock (test) modes.

    Usage:
        # Production mode (default)
        scraper = KNCBMatchCentreScraper()

        # Mock mode for testing
        from scraper_config import get_scraper_config, ScraperMode
        config = get_scraper_config(ScraperMode.MOCK)
        scraper = KNCBMatchCentreScraper(config=config)

        # Or use environment variable
        # export SCRAPER_MODE=mock
        config = get_scraper_config()  # Auto-detects from env
        scraper = KNCBMatchCentreScraper(config=config)
    """

    def __init__(self, config: 'ScraperConfig' = None):
        """
        Initialize scraper with optional configuration

        Args:
            config: ScraperConfig instance (optional)
                   If not provided, uses production settings
        """
        # Load configuration
        if config is None:
            # Default to production settings
            self.matchcentre_url = "https://matchcentre.kncb.nl"
            self.kncb_api_url = "https://api.resultsvault.co.uk/rv"
            self.api_id = "1002"
            self.entity_id = "134453"
            self.mode = "production"
            logger.info("🌐 Scraper initialized in PRODUCTION mode (real KNCB API)")
        else:
            # Use provided configuration
            self.matchcentre_url = config.matchcentre_url
            self.kncb_api_url = config.api_url
            self.api_id = config.api_id
            self.entity_id = config.entity_id
            self.mode = config.mode.value

            if config.is_mock():
                logger.info("🧪 Scraper initialized in MOCK mode (test data)")
                logger.info(f"   Mock API URL: {config.api_url}")
            else:
                logger.info("🌐 Scraper initialized in PRODUCTION mode (real KNCB API)")

        # Fantasy points configuration - imported from centralized rules-set-1.py
        self.rules = FANTASY_RULES

    async def create_browser(self) -> Browser:
        """Create browser instance"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        return browser

    async def get_recent_matches_for_club(
        self, club_name: str, days_back: int = 7, season_id: int = 19
    ) -> List[Dict]:
        """
        Get recent matches for a specific club using API (public endpoint)

        Args:
            club_name: Name of the club (e.g., "VRA", "ACC")
            days_back: How many days back to fetch matches
            season_id: Season ID

        Returns:
            List of match dictionaries with match_id, date, teams, etc.
        """
        browser = await self.create_browser()
        page = await browser.new_page()

        try:
            # Get all grades
            logger.info(f"🔍 Fetching grades for season {season_id}...")
            url = f"{self.kncb_api_url}/{self.entity_id}/grades/?apiid={self.api_id}&seasonId={season_id}"
            await page.goto(url, wait_until='domcontentloaded')

            json_text = await page.evaluate('document.body.textContent')
            grades = json.loads(json_text)

            logger.info(f"✅ Found {len(grades)} grades")

            all_matches = []

            # For each grade, get matches
            for grade in grades[:5]:  # Limit to top 5 grades for efficiency
                grade_id = grade.get('grade_id')
                grade_name = grade.get('grade_name', 'Unknown')

                logger.info(f"📊 Checking {grade_name}...")

                # Get matches for this grade
                matches_url = f"{self.kncb_api_url}/{self.entity_id}/matches/"
                params = f"?apiid={self.api_id}&seasonId={season_id}&gradeId={grade_id}&action=ors&maxrecs=100"

                try:
                    await page.goto(matches_url + params, wait_until='domcontentloaded', timeout=10000)
                    json_text = await page.evaluate('document.body.textContent')

                    if json_text.strip():
                        matches = json.loads(json_text)

                        # Filter matches for this club and date range
                        cutoff_date = datetime.now() - timedelta(days=days_back)

                        for match in matches:
                            home_team = match.get('home_club_name', '')
                            away_team = match.get('away_club_name', '')

                            # Check if club is in this match
                            if club_name.lower() in home_team.lower() or club_name.lower() in away_team.lower():
                                match_date_str = match.get('match_date_time', '')

                                # Parse date and filter
                                try:
                                    match_date = datetime.strptime(match_date_str.split('T')[0], '%Y-%m-%d')
                                    if match_date >= cutoff_date:
                                        match['grade_name'] = grade_name
                                        match['tier'] = self._determine_tier(grade_name)
                                        all_matches.append(match)
                                        logger.info(f"   ✅ Found match: {home_team} vs {away_team} on {match_date_str}")
                                except:
                                    pass

                except Exception as e:
                    logger.warning(f"   ⚠️  Could not fetch matches for {grade_name}: {e}")
                    continue

            logger.info(f"\n✅ Total matches found for {club_name}: {len(all_matches)}")
            return all_matches

        except Exception as e:
            logger.error(f"❌ Error fetching matches: {e}")
            return []
        finally:
            await browser.close()

    async def scrape_match_scorecard(self, match_id: int) -> Optional[Dict]:
        """
        Scrape full scorecard for a match

        Returns:
            Dict with innings, batting, bowling stats for all players
        """
        browser = await self.create_browser()
        page = await browser.new_page()

        try:
            # Try API endpoint first (works for scorecards)
            url = f"{self.kncb_api_url}/match/{match_id}/?apiid={self.api_id}"
            logger.info(f"📥 Fetching scorecard for match {match_id}...")

            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response.status == 200:
                json_text = await page.evaluate('document.body.textContent')
                scorecard = json.loads(json_text)

                logger.info(f"✅ Got scorecard for match {match_id}")
                return scorecard
            else:
                logger.warning(f"⚠️  Scorecard API returned {response.status}, trying HTML...")
                return await self._scrape_scorecard_html(page, match_id)

        except Exception as e:
            logger.error(f"❌ Error scraping scorecard: {e}")
            return None
        finally:
            await browser.close()

    async def _scrape_scorecard_html(self, page: Page, match_id: int) -> Optional[Dict]:
        """Fallback: Scrape scorecard from HTML"""
        try:
            # Navigate to match page
            url = f"{self.matchcentre_url}/match/{match_id}"
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Extract data using JavaScript
            scorecard = await page.evaluate("""() => {
                const data = {innings: []};

                // Find innings sections
                const inningsSections = document.querySelectorAll('.innings-section, [class*="innings"]');

                inningsSections.forEach(innings => {
                    const inningsData = {
                        batting: [],
                        bowling: []
                    };

                    // Extract batting data
                    const battingRows = innings.querySelectorAll('.batting-row, [class*="batting"] tr');
                    battingRows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 3) {
                            inningsData.batting.push({
                                player_name: cells[0]?.textContent.trim(),
                                dismissal: cells[1]?.textContent.trim(),
                                runs: parseInt(cells[2]?.textContent.trim()) || 0
                            });
                        }
                    });

                    // Extract bowling data
                    const bowlingRows = innings.querySelectorAll('.bowling-row, [class*="bowling"] tr');
                    bowlingRows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            inningsData.bowling.push({
                                player_name: cells[0]?.textContent.trim(),
                                figures: cells[1]?.textContent.trim()
                            });
                        }
                    });

                    if (inningsData.batting.length > 0 || inningsData.bowling.length > 0) {
                        data.innings.push(inningsData);
                    }
                });

                return data;
            }""")

            return scorecard if scorecard.get('innings') else None

        except Exception as e:
            logger.error(f"❌ HTML scraping failed: {e}")
            return None

    def extract_player_stats(self, scorecard: Dict, club_name: str, tier: str) -> List[Dict]:
        """
        Extract individual player stats from scorecard

        Returns:
            List of player performance dicts with fantasy points
        """
        players = []

        if not scorecard or 'innings' not in scorecard:
            return players

        for innings in scorecard['innings']:
            # Extract batting performances
            for batter in innings.get('batting', []):
                player_name = batter.get('player_name') or batter.get('person_name')
                if not player_name:
                    continue

                runs = batter.get('runs', 0)
                balls = batter.get('balls_faced', 0)
                fours = batter.get('fours', 0)
                sixes = batter.get('sixes', 0)

                performance = {
                    'player_name': player_name,
                    'player_id': batter.get('player_id') or batter.get('person_id'),
                    'club': club_name,
                    'tier': tier,
                    'batting': {
                        'runs': runs,
                        'balls_faced': balls,
                        'fours': fours,
                        'sixes': sixes
                    },
                    'bowling': {},
                    'fielding': {}
                }

                players.append(performance)

            # Extract bowling performances
            for bowler in innings.get('bowling', []):
                player_name = bowler.get('player_name') or bowler.get('person_name')
                if not player_name:
                    continue

                # Find existing player or create new
                player_perf = next((p for p in players if p['player_name'] == player_name), None)

                if not player_perf:
                    player_perf = {
                        'player_name': player_name,
                        'player_id': bowler.get('player_id') or bowler.get('person_id'),
                        'club': club_name,
                        'tier': tier,
                        'batting': {},
                        'bowling': {},
                        'fielding': {}
                    }
                    players.append(player_perf)

                player_perf['bowling'] = {
                    'wickets': bowler.get('wickets', 0),
                    'runs_conceded': bowler.get('runs', 0),
                    'overs': bowler.get('overs', 0.0),
                    'maidens': bowler.get('maidens', 0)
                }

            # Extract fielding (catches, stumpings, runouts)
            for fielder in innings.get('fielding', []):
                player_name = fielder.get('player_name') or fielder.get('person_name')
                if not player_name:
                    continue

                player_perf = next((p for p in players if p['player_name'] == player_name), None)

                if player_perf:
                    player_perf['fielding'] = {
                        'catches': fielder.get('catches', 0),
                        'stumpings': fielder.get('stumpings', 0),
                        'runouts': fielder.get('runouts', 0)
                    }

        # Calculate fantasy points for each player
        for player in players:
            player['fantasy_points'] = self._calculate_fantasy_points(player)

        return players

    def _calculate_fantasy_points(self, performance: Dict) -> int:
        """Calculate fantasy points for a single performance using centralized rules"""

        # Extract batting stats
        batting = performance.get('batting', {})
        runs = batting.get('runs', 0) if batting else 0
        balls_faced = batting.get('balls_faced', 0) if batting else 0
        is_out = batting.get('is_out', False) if batting else False

        # Extract bowling stats
        bowling = performance.get('bowling', {})
        wickets = bowling.get('wickets', 0) if bowling else 0
        maidens = bowling.get('maidens', 0) if bowling else 0
        runs_conceded = (bowling.get('runs_conceded', 0) or bowling.get('runs', 0)) if bowling else 0
        overs = bowling.get('overs', 0.0) if bowling else 0.0

        # Extract fielding stats
        fielding = performance.get('fielding', {})
        catches = fielding.get('catches', 0) if fielding else 0
        stumpings = fielding.get('stumpings', 0) if fielding else 0
        runouts = fielding.get('runouts', 0) if fielding else 0

        # Use centralized calculation function from rules-set-1.py
        result = calculate_total_fantasy_points(
            runs=runs,
            balls_faced=balls_faced,
            is_out=is_out,
            wickets=wickets,
            overs=overs,
            runs_conceded=runs_conceded,
            maidens=maidens,
            catches=catches,
            stumpings=stumpings,
            runouts=runouts,
            is_wicketkeeper=False  # Determined elsewhere in the system
        )

        return int(max(0, result['grand_total']))

    def _determine_tier(self, grade_name: str) -> str:
        """Determine tier from grade name"""
        name_lower = grade_name.lower()

        if any(x in name_lower for x in ['topklasse', 'hoofdklasse']):
            return 'tier1'
        elif any(x in name_lower for x in ['eerste', 'tweede']):
            return 'tier2'
        elif any(x in name_lower for x in ['derde', 'vierde']):
            return 'tier3'
        elif any(x in name_lower for x in ['zami', 'zomi']):
            return 'social'
        elif any(x in name_lower for x in ['u17', 'u15', 'u13', 'u11']):
            return 'youth'
        elif any(x in name_lower for x in ['vrouwen', 'women']):
            return 'ladies'

        return 'tier2'

    async def scrape_weekly_update(self, clubs: List[str], days_back: int = 7) -> Dict:
        """
        Main method: Scrape weekly updates for configured clubs

        Args:
            clubs: List of club names to scrape
            days_back: How many days back to fetch

        Returns:
            Dict with all player performances
        """
        logger.info(f"🏏 Starting weekly scrape for {len(clubs)} clubs")
        logger.info(f"📅 Fetching matches from last {days_back} days")

        all_player_stats = []

        for club in clubs:
            logger.info(f"\n🔍 Processing {club}...")

            # Get recent matches for this club
            matches = await self.get_recent_matches_for_club(club, days_back)

            for match in matches:
                match_id = match.get('match_id')
                tier = match.get('tier', 'tier2')

                # Scrape scorecard
                scorecard = await self.scrape_match_scorecard(match_id)

                if scorecard:
                    # Extract player stats
                    players = self.extract_player_stats(scorecard, club, tier)

                    # Add match metadata
                    for player in players:
                        player['match_id'] = match_id
                        player['match_date'] = match.get('match_date_time')
                        player['opponent'] = (
                            match.get('away_club_name')
                            if club.lower() in match.get('home_club_name', '').lower()
                            else match.get('home_club_name')
                        )

                    all_player_stats.extend(players)

                    logger.info(f"   ✅ Processed match {match_id}: {len(players)} players")

                # Rate limiting
                await asyncio.sleep(1)

        logger.info(f"\n✅ Scraping complete! Processed {len(all_player_stats)} player performances")

        return {
            'scraped_at': datetime.now().isoformat(),
            'clubs': clubs,
            'days_back': days_back,
            'total_performances': len(all_player_stats),
            'performances': all_player_stats
        }


# =============================================================================
# TESTING
# =============================================================================

async def test_scraper():
    """Test the scraper with a real club"""

    print("🏏 Testing KNCB HTML Scraper")
    print("=" * 70)

    scraper = KNCBMatchCentreScraper()

    # Test with VRA (a well-known club)
    test_clubs = ["VRA"]

    print(f"\n📥 Scraping recent matches for: {', '.join(test_clubs)}")
    print(f"📅 Looking back 14 days...")

    results = await scraper.scrape_weekly_update(test_clubs, days_back=14)

    print(f"\n✅ Scraping complete!")
    print(f"📊 Total performances: {results['total_performances']}")

    if results['performances']:
        # Save results
        with open('weekly_scrape_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to weekly_scrape_results.json")

        # Show sample
        print(f"\n🎯 Sample performances:")
        for perf in results['performances'][:5]:
            print(f"\n   👤 {perf['player_name']}")
            print(f"      Club: {perf['club']}")
            print(f"      Tier: {perf['tier']}")
            if perf.get('batting', {}).get('runs'):
                print(f"      Batting: {perf['batting']['runs']} runs")
            if perf.get('bowling', {}).get('wickets'):
                print(f"      Bowling: {perf['bowling']['wickets']} wickets")
            print(f"      Fantasy points: {perf['fantasy_points']}")

        print("\n" + "=" * 70)
        print("✅ SCRAPER WORKING!")
        print("\n📝 Next steps:")
        print("1. Add more clubs to configuration")
        print("2. Integrate with database")
        print("3. Set up Celery scheduled task")
        print("4. Configure weekly automation")

    else:
        print("\n⚠️  No matches found. Try:")
        print("1. Different club name")
        print("2. Increase days_back")
        print("3. Check if season is active")


if __name__ == "__main__":
    asyncio.run(test_scraper())
