#!/usr/bin/env python3
"""
Final ACC Scraper - Grade by Grade
==================================
Uses the exact grade URLs provided by user.
Loads each page with Playwright, finds match links, scrapes scorecards.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright
import re

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Grade URLs provided by user
GRADE_PAGES = {
    "Hoofdklasse (ACC 1)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=71375&season=19",
    "Tweede Klasse (ACC 2)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=73940&season=19",
    "Derde Klasse (ACC 3, 4)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=73941&season=19",
    "Vierde Klasse (ACC 5, 6)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=73942&season=19",
    "ZAMI (ACC ZAMI 1, 2)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=73943&season=19",
    "U17 (ACC U17)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=75943&season=19",
    "U15 (ACC U15)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=75913&season=19",
    "U13 (ACC U13)": "https://matchcentre.kncb.nl/matches/?entity=134453&grade=75914&season=19",
}


class ACCFinalScraper:
    """Final scraper using exact grade pages"""

    def __init__(self):
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()
        self.acc_teams_found = set()
        self.matches_scraped = 0

    async def scrape_all_grades(self):
        """Scrape all grade pages"""
        logger.info("🏏 Scraping ACC players from 2025 season")
        logger.info(f"   Checking {len(GRADE_PAGES)} grades...")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)

        try:
            for grade_name, grade_url in GRADE_PAGES.items():
                logger.info(f"\n📊 {grade_name}")
                logger.info(f"   URL: {grade_url}")

                await self._scrape_grade_page(browser, grade_name, grade_url)

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   Matches scraped: {self.matches_scraped}")
            logger.info(f"   Teams found: {sorted(self.acc_teams_found)}")
            logger.info(f"   Players found: {len(self.aggregator.players)}")

        finally:
            await browser.close()
            await playwright.stop()

        return self.aggregator

    async def _scrape_grade_page(self, browser, grade_name: str, grade_url: str):
        """Scrape a single grade page to find all matches"""

        page = await browser.new_page()

        try:
            # Load the grade page
            await page.goto(grade_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Let React render

            # Find all match links
            match_links = []
            links = await page.query_selector_all('a')

            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if href and '/match/' in href and 'scorecard' not in href:
                        # Convert to full URL if needed
                        if not href.startswith('http'):
                            href = 'https://matchcentre.kncb.nl' + href

                        # Avoid duplicates
                        if href not in match_links:
                            match_links.append(href)
                except:
                    continue

            logger.info(f"   Found {len(match_links)} matches")

            # Check each match for ACC
            acc_count = 0
            for i, match_url in enumerate(match_links, 1):
                try:
                    # Load match page first to check if it's ACC
                    await page.goto(match_url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)

                    content = await page.content()

                    # Check if ACC is in this match
                    if 'ACC' not in content:
                        continue

                    acc_count += 1
                    logger.info(f"      {i}/{len(match_links)}: ACC match found")

                    # Build scorecard URL
                    # Extract match ID from URL like: /match/134453-7336247/
                    match_id = match_url.split('/match/')[-1].rstrip('/')
                    scorecard_url = f"https://matchcentre.kncb.nl/match/{match_id}/scorecard/"

                    # Scrape the scorecard
                    await self._scrape_scorecard(page, scorecard_url, grade_name)

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.debug(f"         Error: {e}")
                    continue

            if acc_count > 0:
                logger.info(f"   ✅ Scraped {acc_count} ACC matches")

        except Exception as e:
            logger.warning(f"   ⚠️  Error scraping grade: {e}")
        finally:
            await page.close()

    async def _scrape_scorecard(self, page, scorecard_url: str, grade_name: str):
        """Scrape a scorecard page"""

        try:
            await page.goto(scorecard_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)  # Let it render

            # Get page content
            content = await page.content()

            # Find ACC team name
            acc_team = None
            team_pattern = r'(ACC[^<>"]*(?:1|2|3|4|5|6|ZAMI|U\d+)?[^<>"]*)'
            teams = re.findall(team_pattern, content)

            for team in teams:
                clean = team.strip()
                if 3 < len(clean) < 50 and 'ACC' in clean:
                    acc_team = clean
                    self.acc_teams_found.add(clean)
                    break

            if not acc_team:
                return

            logger.info(f"         Team: {acc_team}")

            # Find all tables on the page
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
                        if any(word in player_name.lower() for word in ['batsman', 'batsmen', 'bowler', 'total', 'extras', 'byes', 'leg', 'wides', 'no ball']):
                            continue
                        if player_name.isdigit():
                            continue
                        if player_name in ['DNB', 'Absent', 'Did not bat']:
                            continue

                        # Extract stats
                        runs = 0
                        balls = 0
                        fours = 0
                        sixes = 0
                        wickets = 0
                        overs = 0.0
                        runs_conceded = 0

                        for i, text in enumerate(cell_texts[1:], 1):
                            # Runs
                            if text.isdigit():
                                num = int(text)
                                if i <= 3 and num < 250:
                                    runs = max(runs, num)
                                if i == 2 and num < 200:
                                    balls = num
                                if i == 3 and num < 50:
                                    fours = num
                                if i == 4 and num < 30:
                                    sixes = num

                            # Bowling figures: "3/45" or "3-45"
                            if ('/' in text or '-' in text) and len(text) < 10:
                                parts = re.split(r'[/-]', text)
                                if len(parts) == 2:
                                    try:
                                        if parts[0].isdigit() and parts[1].isdigit():
                                            wickets = int(parts[0])
                                            runs_conceded = int(parts[1])
                                    except:
                                        pass

                            # Overs: "10.2"
                            if '.' in text and len(text) < 6:
                                try:
                                    o = float(text)
                                    if 0 < o < 50:
                                        overs = o
                                except:
                                    pass

                        # Add if has meaningful stats
                        if runs > 0 or wickets > 0 or balls > 0 or overs > 0:
                            perf = {
                                'player_name': player_name,
                                'team': acc_team,
                                'match_date': datetime.now().isoformat(),
                                'runs': runs,
                                'balls_faced': balls,
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

            if players_found > 0:
                logger.info(f"         Players: {players_found}")
                self.matches_scraped += 1

        except Exception as e:
            logger.debug(f"         Scorecard error: {e}")

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
            "notes": "Real ACC players scraped from KNCB Match Centre 2025 season",
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

        if 'ACC 1' in team_upper or 'ACC1' in team_upper:
            return 'hoofdklasse'
        elif 'ACC 2' in team_upper or 'ACC2' in team_upper:
            return 'tweede'
        elif 'ACC 3' in team_upper or 'ACC 4' in team_upper or 'ACC3' in team_upper or 'ACC4' in team_upper:
            return 'derde'
        elif 'ACC 5' in team_upper or 'ACC 6' in team_upper or 'ACC5' in team_upper or 'ACC6' in team_upper:
            return 'vierde'
        elif 'ZAMI' in team_upper:
            return 'zami'
        elif 'U17' in team_upper or 'U15' in team_upper or 'U13' in team_upper or 'YOUTH' in team_upper:
            return 'youth'
        else:
            return 'hoofdklasse'


async def main():
    print("\n🏏 Final ACC Scraper - 2025 Season")
    print("=" * 80)
    print("Scraping all ACC teams from grade pages...")
    print()

    scraper = ACCFinalScraper()

    try:
        await scraper.scrape_all_grades()
        roster = scraper.generate_roster('rosters/acc_2025_real_players.json')

        print("\n✅ Complete!")
        print(f"   Matches scraped: {scraper.matches_scraped}")
        print(f"   Players found: {len(roster.get('players', []))}")
        print(f"   Teams: {', '.join(roster.get('teams_found', []))}")

        if roster.get('players'):
            print(f"\n🌟 Top 10 players:")
            for i, p in enumerate(roster['players'][:10], 1):
                print(f"   {i:2d}. {p['name']:<30} ({p['team_name']}) - €{p['fantasy_value']:.1f}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
