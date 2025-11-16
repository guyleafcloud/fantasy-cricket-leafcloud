#!/usr/bin/env python3
"""
Complete ACC Scraper - 2025 Season
==================================
Scrapes all ACC teams from KNCB Match Centre with player IDs.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
from playwright.async_api import async_playwright

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Grade URLs for all ACC teams in 2025 season
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


class CompleteScraper:
    """Complete scraper with player ID extraction"""

    def __init__(self):
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        self.acc_teams_found = set()
        self.matches_scraped = 0
        self.scorecards_processed = 0

        # Store player IDs (name -> matchcentre_id)
        self.player_ids = {}

        # Store match URLs per grade (for resumability)
        self.match_urls_by_grade = {}

    async def scrape_all_grades(self, browser):
        """Scrape all grade pages to find ACC matches"""
        logger.info("🏏 Starting complete ACC scraper for 2025 season")
        logger.info(f"   Grades to check: {len(GRADE_PAGES)}")
        print()

        for grade_name, grade_url in GRADE_PAGES.items():
            logger.info(f"📊 {grade_name}")
            logger.info(f"   URL: {grade_url}")

            match_urls = await self._find_matches_in_grade(browser, grade_name, grade_url)
            self.match_urls_by_grade[grade_name] = match_urls

            logger.info(f"   Found {len(match_urls)} potential ACC matches")

            # Scrape each match
            if match_urls:
                await self._scrape_matches(browser, grade_name, match_urls)

            print()

        logger.info(f"✅ All grades scraped!")
        logger.info(f"   Total scorecards processed: {self.scorecards_processed}")
        logger.info(f"   ACC matches found: {self.matches_scraped}")
        logger.info(f"   Unique players: {len(self.aggregator.players)}")
        logger.info(f"   Teams found: {sorted(self.acc_teams_found)}")

    async def _find_matches_in_grade(self, browser, grade_name: str, grade_url: str) -> List[str]:
        """Find all match URLs in a grade page"""
        page = await browser.new_page()
        match_urls = []

        try:
            # Load grade page
            logger.info(f"   Loading page...")
            await page.goto(grade_url, wait_until='domcontentloaded', timeout=60000)

            # Wait longer and scroll to trigger lazy loading
            logger.info(f"   Waiting for content to load (15s)...")
            await asyncio.sleep(10)

            # Scroll down to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)

            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)

            # Get page text to see what's actually visible
            page_text = await page.inner_text('body')
            logger.info(f"   Page has {len(page_text)} characters of text")

            # Find all links with /match/ in them
            links = await page.query_selector_all('a')
            logger.info(f"   Found {len(links)} total links on page")

            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if href and '/match/' in href and '/scorecard' not in href:
                        # Convert to full URL
                        if not href.startswith('http'):
                            href = 'https://matchcentre.kncb.nl' + href

                        # Avoid duplicates
                        if href not in match_urls:
                            match_urls.append(href)
                except:
                    continue

        except Exception as e:
            logger.warning(f"   ⚠️  Error loading grade page: {e}")
        finally:
            await page.close()

        return match_urls

    async def _scrape_matches(self, browser, grade_name: str, match_urls: List[str]):
        """Scrape all matches for a grade"""

        for i, match_url in enumerate(match_urls, 1):
            try:
                logger.info(f"   Match {i}/{len(match_urls)}")

                # Check if it's an ACC match first
                page = await browser.new_page()

                try:
                    await page.goto(match_url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(2)

                    content = await page.content()

                    # Check if ACC is in this match
                    if 'ACC' not in content:
                        await page.close()
                        continue

                    logger.info(f"      ✅ ACC match found")

                    # Build scorecard URL
                    match_id = match_url.split('/match/')[-1].rstrip('/')
                    scorecard_url = f"https://matchcentre.kncb.nl/match/{match_id}/scorecard/"

                    # Scrape the scorecard
                    await self._scrape_scorecard(page, scorecard_url, grade_name)

                except Exception as e:
                    logger.debug(f"      Error: {e}")
                finally:
                    await page.close()

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.debug(f"   Error with match {i}: {e}")
                continue

    async def _scrape_scorecard(self, page, scorecard_url: str, grade_name: str):
        """Scrape a single scorecard with player IDs"""

        try:
            # Navigate to scorecard
            await page.goto(scorecard_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            # Extract player IDs from links
            player_links = await page.query_selector_all('a[href*="/player/"]')
            player_id_map = {}  # name -> (id, full_name)

            for link in player_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()

                    if href and text:
                        # Extract player ID from URL: /player/{ID}/19/
                        match = re.search(r'/player/(\d+)/', href)
                        if match:
                            player_id = match.group(1)
                            full_name = text.strip()

                            # Store both full name and abbreviated version
                            player_id_map[full_name] = (player_id, full_name)

                            # Also store abbreviated name (e.g., "IrfanAlim" -> "I ALIM")
                            if full_name:
                                # Extract initials + last name
                                words = full_name.split()
                                if len(words) >= 2:
                                    abbreviated = f"{words[0][0]} {' '.join(words[1:])}"
                                    player_id_map[abbreviated.upper()] = (player_id, full_name)
                except:
                    continue

            # Get page content for team identification
            content = await page.content()

            # Find ACC team name
            acc_team = None
            team_pattern = r'(ACC[^<>\"]*(?:1|2|3|4|5|6|ZAMI|U\d+)?[^<>\"]*)'
            teams = re.findall(team_pattern, content)

            for team in teams:
                clean = team.strip()
                if 3 < len(clean) < 50 and 'ACC' in clean:
                    # Clean up the team name (remove scores like "114/10")
                    clean = re.sub(r'\s+\d+/\d+', '', clean)
                    acc_team = clean
                    self.acc_teams_found.add(clean)
                    break

            if not acc_team:
                return

            logger.info(f"         Team: {acc_team}")
            logger.info(f"         Player IDs found: {len(player_id_map)}")

            # Get visible text for stats
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')

            # Parse batting and bowling sections
            players_found = 0

            for i, line in enumerate(lines):
                # Look for batting section
                if line.strip() == 'BATTING':
                    players_found += await self._parse_batting_section(
                        lines, i, acc_team, player_id_map
                    )

                # Look for bowling section (for ACC players bowling)
                elif line.strip() == 'BOWLING':
                    players_found += await self._parse_bowling_section(
                        lines, i, acc_team, player_id_map
                    )

            if players_found > 0:
                logger.info(f"         ✅ {players_found} player performances recorded")
                self.scorecards_processed += 1
                self.matches_scraped += 1

        except Exception as e:
            logger.debug(f"         Error scraping scorecard: {e}")

    async def _parse_batting_section(
        self,
        lines: List[str],
        start_idx: int,
        team: str,
        player_id_map: Dict[str, Tuple[str, str]]
    ) -> int:
        """Parse batting section and record performances"""

        players_found = 0
        i = start_idx + 1

        # Skip headers
        while i < len(lines) and lines[i].strip() in ['BATTING', 'R', 'B', '4', '6', 'SR', '']:
            i += 1

        # Parse players (7 lines per player: name, dismissal, R, B, 4, 6, SR)
        while i < len(lines) - 6:
            if lines[i].strip() in ['BOWLING', 'FIELDING', '']:
                break

            player_name = lines[i].strip()

            if not player_name or len(player_name) < 3:
                i += 1
                continue

            # Skip headers
            if player_name in ['R', 'B', '4', '6', 'SR', 'BATTING']:
                i += 1
                continue

            if player_name.replace('.', '').isdigit():
                i += 1
                continue

            # Try to parse stats
            try:
                dismissal = lines[i + 1].strip()
                runs = int(lines[i + 2].strip()) if lines[i + 2].strip().isdigit() else 0
                balls = int(lines[i + 3].strip()) if lines[i + 3].strip().isdigit() else 0
                fours = int(lines[i + 4].strip()) if lines[i + 4].strip().isdigit() else 0
                sixes = int(lines[i + 5].strip()) if lines[i + 5].strip().isdigit() else 0

                # Look up player ID
                player_id = None
                full_name = player_name

                for key, (pid, fname) in player_id_map.items():
                    if key.upper() == player_name.upper() or fname.upper() == player_name.upper():
                        player_id = pid
                        full_name = fname
                        break

                # Store player ID
                if player_id:
                    self.player_ids[full_name] = player_id

                # Add performance
                perf = {
                    'player_name': full_name,
                    'team': team,
                    'match_date': datetime.now().isoformat(),
                    'runs': runs,
                    'balls_faced': balls,
                    'fours': fours,
                    'sixes': sixes,
                    'wickets': 0,
                    'overs': 0.0,
                    'runs_conceded': 0,
                    'maidens': 0,
                    'catches': 0,
                    'stumpings': 0,
                    'run_outs': 0,
                }

                self.aggregator.add_match_performance(perf)
                players_found += 1

                i += 7

            except (ValueError, IndexError):
                i += 1

        return players_found

    async def _parse_bowling_section(
        self,
        lines: List[str],
        start_idx: int,
        team: str,
        player_id_map: Dict[str, Tuple[str, str]]
    ) -> int:
        """Parse bowling section for ACC players who bowled"""

        players_found = 0
        i = start_idx + 1

        # Skip headers
        while i < len(lines) and lines[i].strip() in ['BOWLING', 'O', 'M', 'R', 'W', 'NB', 'WD', '']:
            i += 1

        # Parse bowlers (7 lines: name, overs, maidens, runs, wickets, NB, WD)
        while i < len(lines) - 6:
            if lines[i].strip() in ['FIELDING', 'Players', ''] or 'Players' in lines[i]:
                break

            bowler_name = lines[i].strip()

            if not bowler_name or len(bowler_name) < 3:
                i += 1
                continue

            if bowler_name in ['O', 'M', 'R', 'W', 'NB', 'WD', 'BOWLING']:
                i += 1
                continue

            if bowler_name.replace('.', '').isdigit():
                i += 1
                continue

            # Check if this bowler is from ACC (not opponent)
            # Look up in player_id_map to see if they're in the ACC team
            is_acc_player = False
            player_id = None
            full_name = bowler_name

            for key, (pid, fname) in player_id_map.items():
                if key.upper() == bowler_name.upper() or fname.upper() == bowler_name.upper():
                    # Check if this player is in our ACC team by checking if we've seen them bat
                    player_id = pid
                    full_name = fname
                    is_acc_player = True
                    break

            if not is_acc_player:
                i += 7
                continue

            # Parse bowling stats
            try:
                overs_str = lines[i + 1].strip()
                maidens = int(lines[i + 2].strip()) if lines[i + 2].strip().isdigit() else 0
                runs = int(lines[i + 3].strip()) if lines[i + 3].strip().isdigit() else 0
                wickets = int(lines[i + 4].strip()) if lines[i + 4].strip().isdigit() else 0

                overs = float(overs_str) if overs_str.replace('.', '').isdigit() else 0.0

                # Store player ID
                if player_id:
                    self.player_ids[full_name] = player_id

                # Add bowling performance (will merge with batting if exists)
                perf = {
                    'player_name': full_name,
                    'team': team,
                    'match_date': datetime.now().isoformat(),
                    'runs': 0,
                    'balls_faced': 0,
                    'fours': 0,
                    'sixes': 0,
                    'wickets': wickets,
                    'overs': overs,
                    'runs_conceded': runs,
                    'maidens': maidens,
                    'catches': 0,
                    'stumpings': 0,
                    'run_outs': 0,
                }

                self.aggregator.add_match_performance(perf)
                players_found += 1

                i += 7

            except (ValueError, IndexError):
                i += 1

        return players_found

    def generate_roster(self, output_file: str) -> Dict:
        """Generate final roster with player IDs"""

        logger.info(f"\n📝 Generating complete roster...")
        logger.info(f"   Total unique players: {len(self.aggregator.players)}")
        logger.info(f"   Players with Match Centre IDs: {len(self.player_ids)}")

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

        # Calculate fantasy values per team
        logger.info(f"💰 Calculating fantasy values per team...")
        results = self.value_calculator.calculate_team_values_per_team(
            player_stats_list,
            team_name_getter=lambda p: player_team_map[p.player_name]
        )

        # Build roster
        roster = {
            "club": "ACC",
            "season": "2025",
            "created_at": datetime.now().isoformat(),
            "notes": "Complete ACC roster scraped from KNCB Match Centre 2025 season with player IDs",
            "total_players": len(results),
            "teams_found": sorted(list(self.acc_teams_found)),
            "players": []
        }

        for i, (stats, value, justification) in enumerate(results):
            team_name = player_team_map[stats.player_name]

            # Get Match Centre ID
            matchcentre_id = self.player_ids.get(stats.player_name, None)
            matchcentre_url = f"https://matchcentre.kncb.nl/player/{matchcentre_id}/19/" if matchcentre_id else None

            player_entry = {
                "player_id": f"acc_2025_{i+1:03d}",
                "name": stats.player_name,
                "club": "ACC",
                "team_name": team_name,
                "team_level": stats.team_level,
                "fantasy_value": round(value, 1),
                "matchcentre_id": matchcentre_id,
                "matchcentre_url": matchcentre_url,
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

        # Print summary by team
        print()
        logger.info("📊 Players per team:")
        team_counts = defaultdict(int)
        for player in roster['players']:
            team_counts[player['team_name']] += 1

        for team, count in sorted(team_counts.items()):
            logger.info(f"   {team}: {count} players")

        return roster

    def _determine_team_level(self, team_name: str) -> str:
        """Map team name to level code"""
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
    print("\n" + "=" * 80)
    print("🏏 COMPLETE ACC SCRAPER - 2025 SEASON")
    print("=" * 80)
    print("This will scrape ALL ACC teams from KNCB Match Centre")
    print("Including player names, Match Centre IDs, and full season stats")
    print()
    print("⏱️  This may take 30-60 minutes depending on the number of matches")
    print("=" * 80)
    print()

    scraper = CompleteScraper()

    # Start Playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    try:
        await scraper.scrape_all_grades(browser)

        # Generate roster
        roster = scraper.generate_roster('rosters/acc_2025_complete.json')

        print()
        print("=" * 80)
        print("✅ SCRAPING COMPLETE!")
        print("=" * 80)
        print(f"   Scorecards processed: {scraper.scorecards_processed}")
        print(f"   ACC matches found: {scraper.matches_scraped}")
        print(f"   Total players: {len(roster.get('players', []))}")
        print(f"   Players with IDs: {len(scraper.player_ids)}")
        print(f"   Teams: {', '.join(roster.get('teams_found', []))}")
        print()

        if roster.get('players'):
            print("🌟 Top 20 players by fantasy value:")
            for i, p in enumerate(roster['players'][:20], 1):
                mc_id = f"[{p['matchcentre_id']}]" if p['matchcentre_id'] else "[no ID]"
                print(f"   {i:2d}. {p['name']:<30} ({p['team_name']:<15}) €{p['fantasy_value']:>5.1f} {mc_id}")

        print()
        print(f"💾 Roster saved to: rosters/acc_2025_complete.json")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        print("   Saving partial results...")
        roster = scraper.generate_roster('rosters/acc_2025_partial.json')
        print(f"   Partial roster saved with {len(roster.get('players', []))} players")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
