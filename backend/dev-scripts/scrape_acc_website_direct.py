#!/usr/bin/env python3
"""
Direct Website Scraper for ACC Players
======================================
Scrapes ACC player data by directly navigating the KNCB Match Centre website.
No API - just raw HTML scraping.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict
from playwright.async_api import async_playwright
import re

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ACCWebsiteScraper:
    """Scrapes ACC players by navigating the actual website"""

    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl"
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        self.acc_teams_found = set()
        self.matches_scraped = 0

    async def scrape_acc_teams_from_website(self):
        """
        Scrape by directly navigating the website
        """
        logger.info("🏏 Scraping ACC players directly from website")
        logger.info("   Looking for ACC teams in 2025 season...")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Visible browser helps with debugging
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Start at the KNCB match centre
            logger.info("📥 Loading KNCB Match Centre...")
            await page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)

            # Try to find "Clubs" or "Teams" section
            logger.info("🔍 Looking for clubs/teams section...")

            # Look for links that might lead to clubs
            clubs_link = await page.query_selector('a[href*="club"], a[href*="teams"], a:has-text("Clubs"), a:has-text("Teams")')
            if clubs_link:
                logger.info("   Found clubs link, clicking...")
                await clubs_link.click()
                await asyncio.sleep(2)

            # Search for ACC
            logger.info("🔍 Searching for ACC...")

            # Try to find search box
            search_box = await page.query_selector('input[type="search"], input[type="text"], input[name*="search"]')
            if search_box:
                logger.info("   Found search box, typing 'ACC'...")
                await search_box.fill('ACC')
                await asyncio.sleep(1)
                await search_box.press('Enter')
                await asyncio.sleep(2)

            # Alternative: Look for ACC in links on current page
            logger.info("🔍 Scanning page for ACC mentions...")
            page_content = await page.content()

            # Find all links with ACC
            links = await page.query_selector_all('a')
            acc_links = []

            for link in links:
                try:
                    text = await link.text_content()
                    href = await link.get_attribute('href')

                    if text and 'ACC' in text.upper() and href:
                        acc_links.append({
                            'text': text.strip(),
                            'href': href
                        })
                        logger.info(f"   Found: {text.strip()} -> {href}")
                except:
                    continue

            if not acc_links:
                logger.warning("⚠️  No ACC links found. Trying direct URL approach...")

                # Try direct approach - search for ACC club page
                possible_urls = [
                    f"{self.base_url}/club/ACC",
                    f"{self.base_url}/clubs/ACC",
                    f"{self.base_url}/team/ACC",
                ]

                for url in possible_urls:
                    try:
                        logger.info(f"   Trying: {url}")
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                        if response.status == 200:
                            logger.info(f"   ✅ Found ACC page at {url}")
                            await asyncio.sleep(2)

                            # Now scrape matches from this page
                            await self._scrape_acc_matches_from_page(page)
                            break
                    except Exception as e:
                        logger.debug(f"   {url} failed: {e}")
                        continue
            else:
                # Follow the first ACC link
                logger.info(f"\n✅ Found {len(acc_links)} ACC links")

                for acc_link in acc_links[:5]:  # Check first 5
                    try:
                        href = acc_link['href']
                        if not href.startswith('http'):
                            href = self.base_url + href

                        logger.info(f"\n📊 Checking: {acc_link['text']}")
                        await page.goto(href, wait_until='domcontentloaded', timeout=15000)
                        await asyncio.sleep(2)

                        # Scrape matches from this page
                        await self._scrape_acc_matches_from_page(page)

                    except Exception as e:
                        logger.warning(f"   ⚠️  Error: {e}")
                        continue

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   Matches scraped: {self.matches_scraped}")
            logger.info(f"   ACC teams found: {len(self.acc_teams_found)}")
            logger.info(f"   Players found: {len(self.aggregator.players)}")

        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

        return self.aggregator

    async def _scrape_acc_matches_from_page(self, page):
        """
        Scrape matches from the current page
        """
        try:
            # Look for match links
            logger.info("   🔍 Looking for matches...")

            # Find all links that look like matches
            links = await page.query_selector_all('a[href*="match"]')
            match_links = []

            for link in links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()

                    if href and 'match' in href.lower():
                        if not href.startswith('http'):
                            href = self.base_url + href
                        match_links.append({
                            'text': text.strip() if text else '',
                            'href': href
                        })
                except:
                    continue

            logger.info(f"   Found {len(match_links)} potential match links")

            # Visit each match
            for i, match_link in enumerate(match_links[:50], 1):  # Limit to 50 matches
                try:
                    logger.info(f"   📋 Match {i}/{min(len(match_links), 50)}: {match_link['text']}")

                    await page.goto(match_link['href'], wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(1)

                    # Scrape this match's scorecard
                    await self._scrape_match_scorecard(page)
                    self.matches_scraped += 1

                    # Go back
                    await page.go_back(wait_until='domcontentloaded', timeout=10000)
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"      ⚠️  Could not scrape match: {e}")
                    continue

        except Exception as e:
            logger.warning(f"   ⚠️  Error scraping matches: {e}")

    async def _scrape_match_scorecard(self, page):
        """
        Scrape player data from a match scorecard page
        """
        try:
            # Get team names
            teams = await page.query_selector_all('.team-name, .club-name, h2, h3')
            team_names = []
            for team in teams[:2]:
                try:
                    name = await team.text_content()
                    if name and len(name.strip()) > 0:
                        team_names.append(name.strip())
                except:
                    continue

            # Check if this is an ACC match
            acc_team = None
            for team_name in team_names:
                if 'ACC' in team_name.upper():
                    acc_team = team_name
                    self.acc_teams_found.add(team_name)
                    break

            if not acc_team:
                return

            logger.info(f"      ✅ ACC team: {acc_team}")

            # Find batting tables
            tables = await page.query_selector_all('table')

            for table in tables:
                try:
                    # Get all rows
                    rows = await table.query_selector_all('tr')

                    for row in rows:
                        try:
                            cells = await row.query_selector_all('td, th')
                            if len(cells) < 3:
                                continue

                            # Try to extract player name and stats
                            player_name = None
                            runs = 0
                            wickets = 0

                            for i, cell in enumerate(cells):
                                text = await cell.text_content()
                                text = text.strip()

                                # First column is usually player name
                                if i == 0 and len(text) > 2 and not text.isdigit():
                                    player_name = text

                                # Look for runs (numbers)
                                if text.isdigit() and i > 0:
                                    num = int(text)
                                    if num < 200:  # Reasonable runs
                                        runs = max(runs, num)

                                # Look for wickets (format like "2/34")
                                if '/' in text:
                                    parts = text.split('/')
                                    if parts[0].isdigit():
                                        wickets = int(parts[0])

                            if player_name:
                                # Add to aggregator
                                perf = {
                                    'player_name': player_name,
                                    'team': acc_team,
                                    'match_date': datetime.now().isoformat(),
                                    'runs': runs,
                                    'balls_faced': 0,
                                    'fours': 0,
                                    'sixes': 0,
                                    'wickets': wickets,
                                    'overs': 0.0,
                                    'runs_conceded': 0,
                                    'maidens': 0,
                                    'catches': 0,
                                    'stumpings': 0,
                                    'run_outs': 0,
                                }
                                self.aggregator.add_match_performance(perf)

                        except Exception as e:
                            continue

                except Exception as e:
                    continue

        except Exception as e:
            logger.debug(f"      Error parsing scorecard: {e}")

    def generate_roster(self, output_file: str) -> Dict:
        """Generate roster from scraped data"""
        logger.info(f"\n📝 Generating roster from scraped data...")
        logger.info(f"   Total players found: {len(self.aggregator.players)}")

        if len(self.aggregator.players) == 0:
            logger.warning("⚠️  No players found!")
            return {
                "club": "ACC",
                "season": "2025",
                "total_players": 0,
                "players": []
            }

        # Convert to PlayerStats format
        player_stats_list = []
        player_team_map = {}

        for player_id, player_data in self.aggregator.players.items():
            stats = PlayerStats(
                player_name=player_data['player_name'],
                club=player_data['club'],
                matches_played=player_data['matches_played'],
                total_runs=player_data['season_totals']['runs'],
                batting_average=player_data['averages']['batting_average'],
                strike_rate=player_data['averages']['strike_rate'],
                total_wickets=player_data['season_totals']['wickets'],
                bowling_average=player_data['averages']['bowling_average'],
                economy_rate=player_data['averages']['economy_rate'],
                catches=player_data['season_totals']['catches'],
                run_outs=player_data['season_totals']['run_outs'],
                team_level='hoofdklasse'  # Default
            )
            player_stats_list.append(stats)
            player_team_map[stats.player_name] = player_data.get('team', 'ACC 1')

        # Calculate values per team
        logger.info(f"💰 Calculating fantasy values...")
        results = self.value_calculator.calculate_team_values_per_team(
            player_stats_list,
            team_name_getter=lambda p: player_team_map[p.player_name]
        )

        # Build roster
        roster = {
            "club": "ACC",
            "season": "2025",
            "created_at": datetime.now().isoformat(),
            "notes": "Real ACC players scraped from KNCB Match Centre website",
            "total_players": len(results),
            "teams_found": sorted(list(self.acc_teams_found)),
            "players": []
        }

        for i, (stats, value, justification) in enumerate(results):
            team_name = player_team_map[stats.player_name]

            player_entry = {
                "player_id": f"acc_2025_web_{i+1:03d}",
                "name": stats.player_name,
                "club": "ACC",
                "team_name": team_name,
                "fantasy_value": round(value, 1),
                "stats": {
                    "matches": stats.matches_played,
                    "runs": stats.total_runs,
                    "batting_avg": round(stats.batting_average, 2),
                    "strike_rate": round(stats.strike_rate, 2),
                    "wickets": stats.total_wickets,
                    "bowling_avg": round(stats.bowling_average, 2),
                    "economy": round(stats.economy_rate, 2),
                    "catches": stats.catches,
                    "run_outs": stats.run_outs
                }
            }
            roster['players'].append(player_entry)

        # Sort by value
        roster['players'].sort(key=lambda x: x['fantasy_value'], reverse=True)

        # Save
        with open(output_file, 'w') as f:
            json.dump(roster, f, indent=2)

        logger.info(f"✅ Roster saved to {output_file}")
        return roster


async def main():
    print("\n🏏 ACC Website Scraper (Direct HTML)")
    print("=" * 80)
    print("Navigating KNCB Match Centre website to find ACC players...")
    print()

    scraper = ACCWebsiteScraper()

    try:
        # Scrape from website
        await scraper.scrape_acc_teams_from_website()

        # Generate roster
        roster = scraper.generate_roster('rosters/acc_2025_website_scraped.json')

        print("\n✅ Complete!")
        print(f"   Matches scraped: {scraper.matches_scraped}")
        print(f"   Players found: {len(roster.get('players', []))}")
        print(f"   Teams found: {', '.join(roster.get('teams_found', []))}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
