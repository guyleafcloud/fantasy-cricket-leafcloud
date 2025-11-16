#!/usr/bin/env python3
"""
Scrape ACC Matches from Matches Page
====================================
Goes to ACC club page, clicks "Matches", scrapes all match links
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from playwright.async_api import async_playwright
import re

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ACCMatchesPageScraper:
    """Scrape matches from ACC matches page"""

    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl"
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        self.acc_teams_found = set()
        self.matches_scraped = 0

    async def scrape_acc_matches(self):
        """
        Go to ACC matches page and scrape all matches
        """
        logger.info("🏏 Scraping ACC matches from matches page")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Go to ACC club page
            logger.info("📥 Loading ACC club page...")
            await page.goto(f"{self.base_url}/club/ACC", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Click on "Matches" or "Fixtures"
            logger.info("🔍 Looking for Matches link...")
            matches_link = await page.query_selector('a[href*="matches"], a:has-text("Fixtures"), a:has-text("FIXTURES")')

            if matches_link:
                logger.info("   Found Matches link, clicking...")
                await matches_link.click()
                await asyncio.sleep(3)
            else:
                # Try direct URL
                logger.info("   Trying direct matches URL...")
                await page.goto(f"{self.base_url}/club/ACC/matches/", wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

            # Now scrape all match links
            logger.info("📋 Finding all match links...")
            match_links = []

            # Look for links with /match/ in them
            all_links = await page.query_selector_all('a')

            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    if href and '/match/' in href:
                        if not href.startswith('http'):
                            href = self.base_url + href

                        text = await link.text_content()
                        match_links.append({
                            'url': href,
                            'text': text.strip() if text else ''
                        })
                except:
                    continue

            # Remove duplicates
            unique_urls = {}
            for m in match_links:
                unique_urls[m['url']] = m
            match_links = list(unique_urls.values())

            logger.info(f"   Found {len(match_links)} unique match links")

            # Scrape each match
            for i, match in enumerate(match_links, 1):
                try:
                    logger.info(f"\n   📋 Match {i}/{len(match_links)}: {match['text']}")
                    logger.info(f"      URL: {match['url']}")

                    await page.goto(match['url'], wait_until='networkidle', timeout=15000)
                    await asyncio.sleep(1)

                    # Scrape this match
                    await self._scrape_match_page(page)
                    self.matches_scraped += 1

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"      ⚠️  Error: {e}")
                    continue

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   Matches scraped: {self.matches_scraped}")
            logger.info(f"   Teams found: {sorted(self.acc_teams_found)}")
            logger.info(f"   Players found: {len(self.aggregator.players)}")

        finally:
            await browser.close()
            await playwright.stop()

        return self.aggregator

    async def _scrape_match_page(self, page):
        """Scrape player data from match page"""
        try:
            content = await page.content()

            # Find ACC team name
            team_pattern = r'(ACC[^<>"]*(?:1|2|3|4|5|6|ZAMI|Youth|U19|U17)?[^<>"]*)'
            teams = re.findall(team_pattern, content)

            acc_team = None
            for team in teams:
                clean_team = team.strip()
                if 3 < len(clean_team) < 50:
                    acc_team = clean_team
                    self.acc_teams_found.add(clean_team)
                    break

            if not acc_team:
                acc_team = "ACC 1"
                self.acc_teams_found.add(acc_team)

            logger.info(f"      Team: {acc_team}")

            # Find all tables
            tables = await page.query_selector_all('table')
            players_found = 0

            for table in tables:
                rows = await table.query_selector_all('tr')

                for row in rows:
                    try:
                        cells = await row.query_selector_all('td, th')
                        if len(cells) < 2:
                            continue

                        # Get cell texts
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            cell_texts.append(text.strip() if text else '')

                        player_name = cell_texts[0]

                        # Skip invalid names
                        if not player_name or len(player_name) < 3:
                            continue
                        if any(word in player_name.lower() for word in ['batsman', 'bowler', 'fielder', 'total', 'extras', 'byes', 'leg', 'wides', 'no balls']):
                            continue
                        if player_name.isdigit():
                            continue

                        # Extract stats
                        runs = 0
                        balls_faced = 0
                        fours = 0
                        sixes = 0
                        wickets = 0
                        overs = 0.0
                        runs_conceded = 0

                        for i, text in enumerate(cell_texts[1:], 1):
                            # Runs
                            if text.isdigit() and i <= 3:
                                num = int(text)
                                if num < 250:
                                    runs = max(runs, num)

                            # Balls
                            if text.isdigit() and i == 2:
                                balls_faced = int(text)

                            # Bowling figures
                            if '/' in text or '-' in text:
                                parts = re.split(r'[/-]', text)
                                if len(parts) == 2:
                                    if parts[0].isdigit():
                                        wickets = int(parts[0])
                                    if parts[1].isdigit():
                                        runs_conceded = int(parts[1])

                            # Overs
                            if '.' in text and len(text) < 6:
                                try:
                                    overs = float(text)
                                except:
                                    pass

                        # Add if has stats
                        if runs > 0 or wickets > 0 or balls_faced > 0:
                            perf = {
                                'player_name': player_name,
                                'team': acc_team,
                                'match_date': datetime.now().isoformat(),
                                'runs': runs,
                                'balls_faced': balls_faced,
                                'fours': fours,
                                'sixes': sixes,
                                'wickets': wickets,
                                'overs': overs,
                                'runs_conceded': runs_conceded,
                                'maidens': 0,
                                'catches': 0,
                                'stumpings': 0,
                                'run_outs': 0,
                            }
                            self.aggregator.add_match_performance(perf)
                            players_found += 1

                    except Exception as e:
                        continue

            logger.info(f"      Players: {players_found}")

        except Exception as e:
            logger.warning(f"      Error scraping: {e}")

    def generate_roster(self, output_file: str) -> Dict:
        """Generate roster"""
        logger.info(f"\n📝 Generating roster...")
        logger.info(f"   Total players: {len(self.aggregator.players)}")

        if len(self.aggregator.players) == 0:
            return {
                "club": "ACC",
                "season": "2025",
                "total_players": 0,
                "players": []
            }

        # Convert to PlayerStats
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
                team_level=self._determine_team_level(player_data.get('team', 'ACC 1'))
            )
            player_stats_list.append(stats)
            player_team_map[stats.player_name] = player_data.get('team', 'ACC 1')

        # Calculate values
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
            "notes": "Real ACC players scraped from KNCB Match Centre",
            "total_players": len(results),
            "teams_found": sorted(list(self.acc_teams_found)),
            "players": []
        }

        for i, (stats, value, justification) in enumerate(results):
            team_name = player_team_map[stats.player_name]

            player_entry = {
                "player_id": f"acc_2025_real_{i+1:03d}",
                "name": stats.player_name,
                "club": "ACC",
                "team_name": team_name,
                "team_level": stats.team_level,
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

    def _determine_team_level(self, team_name: str) -> str:
        """Map team name to level"""
        team_upper = team_name.upper()

        if 'ACC 1' in team_upper:
            return 'hoofdklasse'
        elif 'ACC 2' in team_upper:
            return 'tweede'
        elif 'ACC 3' in team_upper or 'ACC 4' in team_upper:
            return 'derde'
        elif 'ACC 5' in team_upper or 'ACC 6' in team_upper:
            return 'vierde'
        elif 'ZAMI' in team_upper:
            return 'zami'
        elif 'YOUTH' in team_upper or 'U19' in team_upper or 'U17' in team_upper:
            return 'youth'
        else:
            return 'hoofdklasse'


async def main():
    print("\n🏏 ACC Matches Page Scraper")
    print("=" * 80)

    scraper = ACCMatchesPageScraper()

    try:
        await scraper.scrape_acc_matches()
        roster = scraper.generate_roster('rosters/acc_2025_real_players.json')

        print("\n✅ Complete!")
        print(f"   Matches scraped: {scraper.matches_scraped}")
        print(f"   Players found: {len(roster.get('players', []))}")
        print(f"   Teams: {', '.join(roster.get('teams_found', []))}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
