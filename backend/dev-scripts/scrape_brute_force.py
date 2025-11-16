#!/usr/bin/env python3
"""
Brute Force Match Scraper
=========================
Just tries match IDs sequentially: match/1, match/2, match/3...
Scrapes any ACC matches found.
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


class BruteForceMatchScraper:
    """Brute force scrape matches by ID"""

    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl"
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        self.acc_teams_found = set()
        self.matches_scraped = 0
        self.acc_matches_found = 0

    async def scrape_matches_by_id(self, start_id: int = 1, end_id: int = 10000):
        """
        Brute force: try every match ID from start_id to end_id
        """
        logger.info(f"🏏 Brute force scraping matches {start_id} to {end_id}")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        checked = 0
        errors = 0

        try:
            for match_id in range(start_id, end_id + 1):
                try:
                    url = f"{self.base_url}/match/{match_id}"

                    # Try to load the page
                    try:
                        response = await page.goto(url, wait_until='networkidle', timeout=10000)
                    except Exception as e:
                        errors += 1
                        if match_id % 100 == 0:
                            logger.info(f"   Progress: {match_id}/{end_id} (checked: {checked}, errors: {errors}, ACC found: {self.acc_matches_found})")
                        continue

                    checked += 1

                    # Check response
                    if response.status != 200:
                        if match_id % 100 == 0:
                            logger.info(f"   Progress: {match_id}/{end_id} (checked: {checked}, errors: {errors}, ACC found: {self.acc_matches_found})")
                        continue

                    # Get page content
                    await asyncio.sleep(0.5)  # Let page render
                    content = await page.content()

                    # Check if this is an ACC match
                    if 'ACC' not in content:
                        if match_id % 50 == 0:
                            logger.info(f"   Progress: {match_id}/{end_id} (checked: {checked}, errors: {errors}, ACC found: {self.acc_matches_found})")
                        continue

                    # Found an ACC match!
                    logger.info(f"\n   ✅ Match {match_id} - ACC match found! URL: {url}")
                    self.acc_matches_found += 1

                    # Scrape it
                    await self._scrape_match_page(page, match_id)
                    self.matches_scraped += 1

                    # Rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    errors += 1
                    if match_id % 100 == 0:
                        logger.info(f"   Progress: {match_id}/{end_id} (checked: {checked}, errors: {errors}, ACC found: {self.acc_matches_found})")
                        logger.debug(f"   Error at {match_id}: {e}")
                    continue

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   ACC matches found: {self.acc_matches_found}")
            logger.info(f"   Matches scraped: {self.matches_scraped}")
            logger.info(f"   Teams found: {sorted(self.acc_teams_found)}")
            logger.info(f"   Players found: {len(self.aggregator.players)}")

        finally:
            await browser.close()
            await playwright.stop()

        return self.aggregator

    async def _scrape_match_page(self, page, match_id):
        """Scrape player data from match page"""
        try:
            # Get all text content
            content = await page.content()

            # Find team names with ACC
            team_pattern = r'(ACC[^<>"]*(?:1|2|3|4|5|6|ZAMI|Youth|U19|U17)?[^<>"]*)'
            teams = re.findall(team_pattern, content)

            acc_team = None
            for team in teams:
                clean_team = team.strip()
                if len(clean_team) > 3 and len(clean_team) < 50:
                    acc_team = clean_team
                    self.acc_teams_found.add(clean_team)
                    break

            if not acc_team:
                acc_team = "ACC 1"  # Default
                self.acc_teams_found.add(acc_team)

            logger.info(f"      Team: {acc_team}")

            # Find all tables (batting/bowling scorecards)
            tables = await page.query_selector_all('table')

            players_found = 0

            for table in tables:
                rows = await table.query_selector_all('tr')

                for row in rows:
                    try:
                        cells = await row.query_selector_all('td, th')
                        if len(cells) < 2:
                            continue

                        # Get all cell texts
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            cell_texts.append(text.strip() if text else '')

                        # First cell is usually player name
                        player_name = cell_texts[0]

                        # Skip headers and empty rows
                        if not player_name or len(player_name) < 3:
                            continue
                        if any(word in player_name.lower() for word in ['batsman', 'bowler', 'fielder', 'total', 'extras', 'byes', 'leg']):
                            continue
                        if player_name.isdigit():
                            continue

                        # Try to extract stats
                        runs = 0
                        balls_faced = 0
                        fours = 0
                        sixes = 0
                        wickets = 0
                        overs = 0.0
                        runs_conceded = 0
                        maidens = 0

                        # Look through cells for numbers
                        for i, text in enumerate(cell_texts[1:], 1):
                            # Runs (just a number)
                            if text.isdigit() and i <= 3:
                                num = int(text)
                                if num < 250:  # Reasonable runs
                                    runs = max(runs, num)

                            # Balls faced
                            if text.isdigit() and i == 2:
                                balls_faced = int(text)

                            # Fours, sixes (small numbers)
                            if text.isdigit() and i > 2:
                                num = int(text)
                                if num < 30:
                                    if i == 3:
                                        fours = num
                                    elif i == 4:
                                        sixes = num

                            # Bowling figures: "3/45" or "3-45"
                            if '/' in text or '-' in text:
                                parts = re.split(r'[/-]', text)
                                if len(parts) == 2:
                                    if parts[0].isdigit():
                                        wickets = int(parts[0])
                                    if parts[1].isdigit():
                                        runs_conceded = int(parts[1])

                            # Overs: "10.2" or "10"
                            if '.' in text and len(text) < 6:
                                try:
                                    overs = float(text)
                                except:
                                    pass

                        # Add player performance
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
                                'maidens': maidens,
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
            logger.warning(f"      Error scraping match {match_id}: {e}")

    def generate_roster(self, output_file: str) -> Dict:
        """Generate roster from scraped data"""
        logger.info(f"\n📝 Generating roster...")
        logger.info(f"   Total players: {len(self.aggregator.players)}")

        if len(self.aggregator.players) == 0:
            logger.warning("⚠️  No players found!")
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
            "notes": "Real ACC players scraped from KNCB Match Centre (brute force)",
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
        """Map team name to level code"""
        team_upper = team_name.upper()

        if 'ACC 1' in team_upper or ('ACC' in team_upper and '1' in team_upper):
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
    print("\n🏏 Brute Force Match Scraper")
    print("=" * 80)
    print("Trying match IDs sequentially to find ACC matches...")
    print()

    # You can adjust these ranges
    start = int(input("Start match ID (default 1): ") or "1")
    end = int(input("End match ID (default 5000): ") or "5000")

    scraper = BruteForceMatchScraper()

    try:
        await scraper.scrape_matches_by_id(start_id=start, end_id=end)

        roster = scraper.generate_roster('rosters/acc_2025_brute_force.json')

        print("\n✅ Complete!")
        print(f"   ACC matches found: {scraper.acc_matches_found}")
        print(f"   Players found: {len(roster.get('players', []))}")
        print(f"   Teams: {', '.join(roster.get('teams_found', []))}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
