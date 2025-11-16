#!/usr/bin/env python3
"""
Direct Scorecard Scraper
========================
Scrapes ACC player stats directly from scorecard pages.
Goes grade by grade through the 2025 season.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
import httpx
from bs4 import BeautifulSoup
import re

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScorecardScraper:
    """Scrape ACC players from scorecard pages"""

    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl"
        self.api_url = "https://api.resultsvault.co.uk/rv"
        self.entity_id = "134453"
        self.api_id = "1002"

        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()
        self.acc_teams_found = set()
        self.matches_scraped = 0

    async def scrape_all_grades(self, season_id: int = 17):
        """
        Scrape all grades for the season
        Season 17 = 2024 (completed)
        Season 19 = 2025 (future)
        """
        logger.info(f"🏏 Scraping ACC players from season {season_id}")
        logger.info(f"   Going grade by grade...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get all grades
            try:
                grades_url = f"{self.api_url}/{self.entity_id}/grades/?apiid={self.api_id}&seasonId={season_id}"
                response = await client.get(grades_url)

                if response.status_code == 200:
                    grades = response.json()
                    logger.info(f"✅ Found {len(grades)} grades")
                else:
                    logger.warning(f"⚠️  Grades API returned {response.status_code}")
                    grades = []
            except Exception as e:
                logger.warning(f"⚠️  Could not fetch grades: {e}")
                grades = []

            # Target grades to check
            target_names = ['Hoofdklasse', 'Topklasse', 'Tweede', 'Derde', 'Vierde', 'ZAMI', 'Youth', 'Junioren']

            for grade in grades:
                grade_name = grade.get('grade_name', '')
                grade_id = grade.get('grade_id')

                # Check if this is a grade we want
                if not any(target in grade_name for target in target_names):
                    continue

                logger.info(f"\n📊 Grade: {grade_name}")

                # Get matches for this grade
                await self._scrape_grade_matches(client, season_id, grade_id, grade_name)

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   Matches scraped: {self.matches_scraped}")
            logger.info(f"   Teams found: {sorted(self.acc_teams_found)}")
            logger.info(f"   Players found: {len(self.aggregator.players)}")

        return self.aggregator

    async def _scrape_grade_matches(self, client: httpx.AsyncClient, season_id: int, grade_id: int, grade_name: str):
        """Get all matches for a grade and scrape ACC ones"""

        try:
            # Get matches for this grade
            matches_url = f"{self.api_url}/{self.entity_id}/matches/"
            params = {
                'apiid': self.api_id,
                'seasonId': season_id,
                'gradeId': grade_id,
                'action': 'ors',
                'maxrecs': 500
            }

            response = await client.get(matches_url, params=params)

            if response.status_code != 200:
                logger.warning(f"   ⚠️  Matches API returned {response.status_code}")
                return

            matches = response.json()

            if not matches:
                logger.info(f"   No matches found")
                return

            logger.info(f"   Found {len(matches)} total matches")

            # Filter for ACC matches
            acc_matches = []
            for match in matches:
                home = match.get('home_club_name', '')
                away = match.get('away_club_name', '')

                if 'ACC' in home.upper() or 'ACC' in away.upper():
                    acc_matches.append(match)

            if not acc_matches:
                logger.info(f"   No ACC matches")
                return

            logger.info(f"   ✅ Found {len(acc_matches)} ACC matches")

            # Scrape each ACC match scorecard
            for i, match in enumerate(acc_matches, 1):
                match_id = match.get('match_id')
                home = match.get('home_club_name', '')
                away = match.get('away_club_name', '')

                logger.info(f"      {i}/{len(acc_matches)}: {home} vs {away}")

                # Scrape scorecard
                await self._scrape_scorecard(client, match_id, grade_name)

                # Rate limiting
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.warning(f"   ⚠️  Error: {e}")

    async def _scrape_scorecard(self, client: httpx.AsyncClient, match_id: int, grade_name: str):
        """Scrape a single scorecard page"""

        try:
            # Try to get scorecard via API first
            scorecard_url = f"{self.api_url}/match/{match_id}/?apiid={self.api_id}"
            response = await client.get(scorecard_url)

            if response.status_code == 200:
                scorecard_data = response.json()
                await self._parse_scorecard_api(scorecard_data, match_id, grade_name)
                self.matches_scraped += 1
                return

            # If API fails, try HTML
            html_url = f"{self.base_url}/match/{match_id}/scorecard/"
            response = await client.get(html_url)

            if response.status_code == 200:
                await self._parse_scorecard_html(response.text, match_id, grade_name)
                self.matches_scraped += 1
                return

        except Exception as e:
            logger.debug(f"         Error scraping {match_id}: {e}")

    async def _parse_scorecard_api(self, data: Dict, match_id: int, grade_name: str):
        """Parse scorecard from API JSON"""

        try:
            innings_list = data.get('Innings', [])

            # Find ACC team
            acc_team = None
            for innings in innings_list:
                team_name = innings.get('BattingTeam', '')
                if 'ACC' in team_name.upper():
                    acc_team = team_name
                    self.acc_teams_found.add(team_name)
                    break

            if not acc_team:
                return

            logger.info(f"         ✅ {acc_team}")

            # Extract batting
            for innings in innings_list:
                if innings.get('BattingTeam') == acc_team:
                    for bat in innings.get('Bat', []):
                        player_name = bat.get('Batsman', {}).get('PlayerName', '')
                        if not player_name:
                            continue

                        runs = bat.get('Runs', 0)
                        balls = bat.get('Balls', 0)
                        fours = bat.get('Fours', 0)
                        sixes = bat.get('Sixes', 0)

                        perf = {
                            'player_name': player_name,
                            'team': acc_team,
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

            # Extract bowling
            for innings in innings_list:
                # Bowling is against the other team
                if innings.get('BattingTeam') != acc_team:
                    for bowl in innings.get('Bowl', []):
                        player_name = bowl.get('Bowler', {}).get('PlayerName', '')
                        if not player_name:
                            continue

                        # Check if this bowler is from ACC team
                        # (API might not specify, so we add anyone)

                        wickets = bowl.get('Wickets', 0)
                        overs = bowl.get('Overs', 0.0)
                        runs_conceded = bowl.get('Runs', 0)
                        maidens = bowl.get('Maidens', 0)

                        if wickets > 0 or overs > 0:
                            perf = {
                                'player_name': player_name,
                                'team': acc_team,
                                'match_date': datetime.now().isoformat(),
                                'runs': 0,
                                'balls_faced': 0,
                                'fours': 0,
                                'sixes': 0,
                                'wickets': wickets,
                                'overs': overs,
                                'runs_conceded': runs_conceded,
                                'maidens': maidens,
                                'catches': 0,
                                'stumpings': 0,
                                'run_outs': 0,
                            }
                            self.aggregator.add_match_performance(perf)

        except Exception as e:
            logger.debug(f"         Parse error: {e}")

    async def _parse_scorecard_html(self, html: str, match_id: int, grade_name: str):
        """Parse scorecard from HTML page"""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find ACC team
            acc_team = None
            text = soup.get_text()
            team_pattern = r'(ACC[^<>"]*(?:1|2|3|4|5|6|ZAMI|Youth|U19|U17)?)'
            matches = re.findall(team_pattern, text)

            for match in matches:
                clean = match.strip()
                if 3 < len(clean) < 50:
                    acc_team = clean
                    self.acc_teams_found.add(clean)
                    break

            if not acc_team:
                return

            logger.info(f"         ✅ {acc_team}")

            # Find all tables
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    cell_texts = [c.get_text().strip() for c in cells]
                    player_name = cell_texts[0]

                    # Skip invalid
                    if not player_name or len(player_name) < 3:
                        continue
                    if any(word in player_name.lower() for word in ['batsman', 'bowler', 'total', 'extras', 'byes']):
                        continue

                    # Extract stats
                    runs = 0
                    balls = 0
                    wickets = 0
                    overs = 0.0

                    for i, text in enumerate(cell_texts[1:], 1):
                        if text.isdigit():
                            num = int(text)
                            if i <= 3 and num < 250:
                                runs = max(runs, num)
                            if i == 2:
                                balls = num

                        # Bowling figures
                        if '/' in text or '-' in text:
                            parts = re.split(r'[/-]', text)
                            if len(parts) == 2 and parts[0].isdigit():
                                wickets = int(parts[0])

                        # Overs
                        if '.' in text and len(text) < 6:
                            try:
                                overs = float(text)
                            except:
                                pass

                    if runs > 0 or wickets > 0 or balls > 0:
                        perf = {
                            'player_name': player_name,
                            'team': acc_team,
                            'match_date': datetime.now().isoformat(),
                            'runs': runs,
                            'balls_faced': balls,
                            'fours': 0,
                            'sixes': 0,
                            'wickets': wickets,
                            'overs': overs,
                            'runs_conceded': 0,
                            'maidens': 0,
                            'catches': 0,
                            'stumpings': 0,
                            'run_outs': 0,
                        }
                        self.aggregator.add_match_performance(perf)

        except Exception as e:
            logger.debug(f"         HTML parse error: {e}")

    def generate_roster(self, output_file: str) -> Dict:
        """Generate roster"""
        logger.info(f"\n📝 Generating roster...")
        logger.info(f"   Total players: {len(self.aggregator.players)}")

        if len(self.aggregator.players) == 0:
            return {
                "club": "ACC",
                "season": "2024/2025",
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
            "season": "2024/2025",
            "created_at": datetime.now().isoformat(),
            "notes": "Real ACC players scraped from KNCB scorecards",
            "total_players": len(results),
            "teams_found": sorted(list(self.acc_teams_found)),
            "players": []
        }

        for i, (stats, value, justification) in enumerate(results):
            team_name = player_team_map[stats.player_name]

            player_entry = {
                "player_id": f"acc_2024_real_{i+1:03d}",
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
    print("\n🏏 ACC Scorecard Scraper")
    print("=" * 80)
    print("Scraping ACC players from scorecards, grade by grade...")
    print()

    scraper = ScorecardScraper()

    try:
        # Scrape season 17 (2024 - completed season with data)
        await scraper.scrape_all_grades(season_id=17)

        roster = scraper.generate_roster('rosters/acc_2024_real_players.json')

        print("\n✅ Complete!")
        print(f"   Matches scraped: {scraper.matches_scraped}")
        print(f"   Players found: {len(roster.get('players', []))}")
        print(f"   Teams: {', '.join(roster.get('teams_found', []))}")

        # Show top 10
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
