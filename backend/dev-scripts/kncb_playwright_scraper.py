#!/usr/bin/env python3
"""
KNCB Player Data Scraper - Playwright Edition
==============================================
Autonomous server-side scraper using real browser to bypass bot detection.

This scraper:
- Uses Playwright headless browser (indistinguishable from human)
- Scrapes player data that the API blocks
- Runs autonomously on server (no laptop needed)
- Calculates fantasy points from performance data
- Integrates with Celery for scheduled updates
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from playwright.async_api import async_playwright, Browser, Page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNCBPlaywrightScraper:
    """Scrapes KNCB player data using Playwright browser automation"""

    def __init__(self):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.matchcentre_url = "https://matchcentre.kncb.nl"
        self.api_id = "1002"
        self.kncb_entity_id = "134453"

        # Fantasy points configuration
        self.points_config = {
            'batting': {
                'run': 1,
                'four': 1,
                'six': 2,
                'fifty': 8,
                'century': 16,
                'duck_penalty': -2
            },
            'bowling': {
                'wicket': 12,
                'maiden': 4,
                'five_wicket_haul': 8
            },
            'fielding': {
                'catch': 4,
                'stumping': 6,
                'runout': 6
            }
        }

        # Tier multipliers
        self.tier_multipliers = {
            'tier1': 1.2,
            'tier2': 1.0,
            'tier3': 0.8,
            'social': 0.4,
            'youth': 0.6,
            'ladies': 0.9
        }

    async def create_browser(self) -> Browser:
        """Create a stealthy browser instance"""
        playwright = await async_playwright().start()

        # Launch browser with stealth settings
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        return browser

    async def create_page(self, browser: Browser) -> Page:
        """Create a page with realistic browser context"""
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-GB',
            timezone_id='Europe/Amsterdam',
        )

        page = await context.new_page()

        # Add extra stealth
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return page

    async def fetch_player_data_via_api(self, person_id: int) -> Optional[Dict]:
        """
        Fetch player data using browser to access the API
        This bypasses IP-based blocking by using real browser
        """
        browser = await self.create_browser()
        page = await self.create_page(browser)

        try:
            # Go directly to the API endpoint
            api_url = f"{self.base_url}/personseason/{person_id}/?apiid={self.api_id}"
            logger.info(f"📥 Fetching player {person_id} via browser: {api_url}")

            response = await page.goto(api_url, wait_until='domcontentloaded', timeout=60000)

            if response and response.status == 200:
                # Extract JSON from page
                # The API returns JSON, extract it from the <pre> tag or body
                json_text = await page.evaluate('document.body.textContent')
                data = json.loads(json_text)

                logger.info(f"✅ Successfully fetched player: {data.get('person_name', 'Unknown')}")
                return data
            else:
                status = response.status if response else 'No response'
                logger.error(f"❌ Failed with status {status}")
                return None

        except Exception as e:
            logger.error(f"❌ Error fetching player data: {e}")
            return None
        finally:
            await browser.close()

    async def scrape_player_from_html(self, person_id: int) -> Optional[Dict]:
        """
        Fallback: Scrape player data directly from HTML pages
        Used if API still fails even with browser
        """
        browser = await self.create_browser()
        page = await self.create_page(browser)

        try:
            # Navigate to player profile page
            player_url = f"{self.matchcentre_url}/player/{person_id}"
            logger.info(f"🔍 Scraping player HTML: {player_url}")

            await page.goto(player_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(1)

            # Extract player data from HTML
            player_data = await page.evaluate("""() => {
                // Extract player name
                const nameEl = document.querySelector('h1.player-name, .player-header h1');
                const name = nameEl ? nameEl.textContent.trim() : null;

                // Extract stats tables
                const statsRows = Array.from(document.querySelectorAll('.stats-table tr'));
                const stats = {};

                statsRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const label = cells[0].textContent.trim();
                        const value = cells[1].textContent.trim();
                        stats[label] = value;
                    }
                });

                return {
                    person_name: name,
                    stats: stats,
                    scraped_at: new Date().toISOString()
                };
            }""")

            if player_data.get('person_name'):
                logger.info(f"✅ Scraped player: {player_data['person_name']}")
                return player_data
            else:
                logger.error("❌ Could not extract player data from HTML")
                return None

        except Exception as e:
            logger.error(f"❌ Error scraping HTML: {e}")
            return None
        finally:
            await browser.close()

    async def fetch_player_data(self, person_id: int, use_html_fallback: bool = True) -> Optional[Dict]:
        """
        Fetch player data with automatic fallback
        1. Try API via browser (primary)
        2. Fall back to HTML scraping (if enabled)
        """
        # Try API first
        data = await self.fetch_player_data_via_api(person_id)

        if data:
            return data

        # Fallback to HTML scraping
        if use_html_fallback:
            logger.info("🔄 API failed, trying HTML scraping...")
            return await self.scrape_player_from_html(person_id)

        return None

    def calculate_fantasy_points(self, player_performance: Dict, tier: str = 'tier2') -> int:
        """
        Calculate fantasy points from player performance data

        Args:
            player_performance: Dict containing batting, bowling, fielding stats
            tier: Competition tier for multiplier

        Returns:
            Total fantasy points
        """
        points = 0

        # Batting points
        if 'batting' in player_performance:
            bat = player_performance['batting']
            runs = bat.get('runs', 0)
            points += runs * self.points_config['batting']['run']
            points += bat.get('fours', 0) * self.points_config['batting']['four']
            points += bat.get('sixes', 0) * self.points_config['batting']['six']

            # Milestones
            if runs >= 100:
                points += self.points_config['batting']['century']
            elif runs >= 50:
                points += self.points_config['batting']['fifty']
            elif runs == 0 and bat.get('balls_faced', 0) > 0:
                points += self.points_config['batting']['duck_penalty']

        # Bowling points
        if 'bowling' in player_performance:
            bowl = player_performance['bowling']
            wickets = bowl.get('wickets', 0)
            points += wickets * self.points_config['bowling']['wicket']
            points += bowl.get('maidens', 0) * self.points_config['bowling']['maiden']

            if wickets >= 5:
                points += self.points_config['bowling']['five_wicket_haul']

        # Fielding points
        if 'fielding' in player_performance:
            field = player_performance['fielding']
            points += field.get('catches', 0) * self.points_config['fielding']['catch']
            points += field.get('stumpings', 0) * self.points_config['fielding']['stumping']
            points += field.get('runouts', 0) * self.points_config['fielding']['runout']

        # Apply tier multiplier
        multiplier = self.tier_multipliers.get(tier, 1.0)
        final_points = int(points * multiplier)

        logger.info(f"💯 Base points: {points}, Tier: {tier} ({multiplier}x), Final: {final_points}")

        return max(0, final_points)

    def parse_player_season(self, player_data: Dict) -> Dict:
        """
        Parse player season data into structured format for fantasy points

        Args:
            player_data: Raw player data from API or scraper

        Returns:
            Parsed data with fantasy points per match
        """
        parsed = {
            'person_id': player_data.get('person_id'),
            'person_name': player_data.get('person_name'),
            'season_id': player_data.get('season_id'),
            'matches': [],
            'total_fantasy_points': 0
        }

        # Parse match performances
        matches = player_data.get('matches', [])

        for match in matches:
            performance = {
                'match_id': match.get('match_id'),
                'match_date': match.get('match_date'),
                'opponent': match.get('opponent'),
                'tier': match.get('tier', 'tier2'),
                'batting': {},
                'bowling': {},
                'fielding': {}
            }

            # Extract batting stats
            if 'batting' in match:
                performance['batting'] = {
                    'runs': match['batting'].get('runs', 0),
                    'balls_faced': match['batting'].get('balls_faced', 0),
                    'fours': match['batting'].get('fours', 0),
                    'sixes': match['batting'].get('sixes', 0),
                }

            # Extract bowling stats
            if 'bowling' in match:
                performance['bowling'] = {
                    'wickets': match['bowling'].get('wickets', 0),
                    'runs_conceded': match['bowling'].get('runs', 0),
                    'overs': match['bowling'].get('overs', 0),
                    'maidens': match['bowling'].get('maidens', 0),
                }

            # Extract fielding stats
            if 'fielding' in match:
                performance['fielding'] = {
                    'catches': match['fielding'].get('catches', 0),
                    'stumpings': match['fielding'].get('stumpings', 0),
                    'runouts': match['fielding'].get('runouts', 0),
                }

            # Calculate fantasy points for this match
            fantasy_points = self.calculate_fantasy_points(
                performance,
                tier=performance['tier']
            )

            performance['fantasy_points'] = fantasy_points
            parsed['matches'].append(performance)
            parsed['total_fantasy_points'] += fantasy_points

        return parsed

    async def scrape_team_players(self, club_name: str, season_id: int = 19) -> List[Dict]:
        """
        Scrape all players from a specific club
        Used for weekly batch updates
        """
        browser = await self.create_browser()
        page = await self.create_page(browser)

        try:
            # Search for the club
            search_url = f"{self.matchcentre_url}/search?q={club_name.replace(' ', '+')}"
            await page.goto(search_url, wait_until='networkidle')

            # Extract player links
            player_links = await page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href*="/player/"]'));
                return links.map(link => ({
                    url: link.href,
                    name: link.textContent.trim(),
                    person_id: link.href.match(/\\/player\\/(\\d+)/)?.[1]
                }));
            }""")

            logger.info(f"✅ Found {len(player_links)} players for {club_name}")
            return player_links

        except Exception as e:
            logger.error(f"❌ Error scraping team players: {e}")
            return []
        finally:
            await browser.close()


# =============================================================================
# TESTING
# =============================================================================

async def test_scraper():
    """Test the Playwright scraper with Sean Walsh"""

    print("🏏 Testing KNCB Playwright Scraper")
    print("=" * 70)

    scraper = KNCBPlaywrightScraper()

    # Test with Sean Walsh (person_id: 11190879)
    print("\n📥 Testing with Sean Walsh (11190879)...")

    player_data = await scraper.fetch_player_data(11190879)

    if player_data:
        print(f"\n✅ Successfully fetched player data!")
        print(f"👤 Name: {player_data.get('person_name', 'Unknown')}")
        print(f"🔑 Data keys: {list(player_data.keys())}")

        # Save raw data
        with open('sean_walsh_playwright.json', 'w') as f:
            json.dump(player_data, f, indent=2)
        print(f"💾 Raw data saved to sean_walsh_playwright.json")

        # Parse and calculate fantasy points
        print("\n💯 Calculating fantasy points...")
        parsed_data = scraper.parse_player_season(player_data)

        print(f"\n📊 Season Summary:")
        print(f"   Matches played: {len(parsed_data['matches'])}")
        print(f"   Total fantasy points: {parsed_data['total_fantasy_points']}")

        if parsed_data['matches']:
            print(f"\n🎯 Recent matches:")
            for match in parsed_data['matches'][:5]:
                print(f"   - {match.get('match_date', 'N/A')}: {match['fantasy_points']} points")

        # Save parsed data
        with open('sean_walsh_fantasy_points.json', 'w') as f:
            json.dump(parsed_data, f, indent=2)
        print(f"\n💾 Fantasy points saved to sean_walsh_fantasy_points.json")

        print("\n" + "=" * 70)
        print("✅ Scraper Working Successfully!")
        print("\n📝 Next steps:")
        print("1. Integrate with database models")
        print("2. Add to Celery scheduled tasks")
        print("3. Configure weekly scraping for your clubs")

    else:
        print("\n❌ Scraper failed to fetch data")
        print("\n📝 Troubleshooting:")
        print("1. Install Playwright: pip install playwright")
        print("2. Install browsers: playwright install chromium")
        print("3. Check if match centre is accessible")


if __name__ == "__main__":
    asyncio.run(test_scraper())
