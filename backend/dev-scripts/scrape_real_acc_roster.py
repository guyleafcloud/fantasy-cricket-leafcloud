#!/usr/bin/env python3
"""
Real ACC Roster Scraper
======================
Scrapes ACTUAL ACC players from all divisions on KNCB Match Centre.

Searches for ACC teams in:
- Hoofdklasse (ACC 1)
- Tweede Klasse (ACC 2)
- Derde Klasse (ACC 3, ACC 4)
- Vierde Klasse (ACC 5, ACC 6)
- ZAMI Klasse (ACC ZAMI 1, ACC ZAMI 2)
- Youth Leagues (ACC Youth U19, U17)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from collections import defaultdict

from kncb_html_scraper import KNCBMatchCentreScraper
from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ACCRosterScraper:
    """Scrapes real ACC players from all divisions"""

    # Map Dutch league names to our simplified codes
    LEAGUE_MAPPING = {
        "Hoofdklasse": "hoofdklasse",
        "Topklasse": "hoofdklasse",  # Alternative name
        "Tweede Klasse": "tweede",
        "Derde Klasse": "derde",
        "Vierde Klasse": "vierde",
        "ZAMI": "zami",
        "Youth": "youth",
    }

    def __init__(self):
        self.scraper = KNCBMatchCentreScraper()
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        # Track which teams we've found
        self.acc_teams_found = set()
        self.matches_by_team = defaultdict(list)

    async def scrape_all_acc_teams(self, season_id: int = 19, days_back: int = 365):
        """
        Scrape all ACC teams from all divisions

        Args:
            season_id: KNCB season ID (19 = 2025)
            days_back: How far back to search
        """
        logger.info(f"🏏 Scraping ALL ACC teams from 2025 season")
        logger.info(f"   Season ID: {season_id}")
        logger.info(f"   Looking back: {days_back} days")

        # Create browser
        browser = await self.scraper.create_browser()
        page = await browser.new_page()

        try:
            # Get all grades/divisions using KNCB API
            logger.info(f"🔍 Fetching grades for season {season_id}...")
            url = f"{self.scraper.kncb_api_url}/{self.scraper.entity_id}/grades/?apiid={self.scraper.api_id}&seasonId={season_id}"
            await page.goto(url, wait_until='domcontentloaded')

            json_text = await page.evaluate('document.body.textContent')
            grades = json.loads(json_text)

            logger.info(f"✅ Found {len(grades)} total divisions/grades")

            # Define which grades we want to check
            target_grades = [
                "Hoofdklasse",
                "Topklasse",
                "Tweede Klasse",
                "Derde Klasse",
                "Vierde Klasse",
                "ZAMI",
                "Junioren",  # Youth
                "Youth",
            ]

            # Check each grade for ACC teams
            for grade in grades:
                grade_name = grade.get('grade_name', '')

                # Check if this grade is one we're interested in
                should_check = any(target in grade_name for target in target_grades)

                if should_check:
                    logger.info(f"\n📊 Checking grade: {grade_name}")
                    await self._check_grade_for_acc(page, grade, season_id, days_back)

            logger.info(f"\n✅ Scraping complete!")
            logger.info(f"   ACC teams found: {len(self.acc_teams_found)}")
            logger.info(f"   Teams: {sorted(self.acc_teams_found)}")

        finally:
            await browser.close()

        return self.aggregator

    async def _check_grade_for_acc(self, page, grade: Dict, season_id: int, days_back: int):
        """Check a specific grade/division for ACC teams"""

        grade_name = grade.get('grade_name', '')
        grade_id = grade.get('grade_id')

        try:
            # Fetch matches for this grade using KNCB API
            matches_url = f"{self.scraper.kncb_api_url}/{self.scraper.entity_id}/matches/"
            params = f"?apiid={self.scraper.api_id}&seasonId={season_id}&gradeId={grade_id}&action=ors&maxrecs=200"

            await page.goto(matches_url + params, wait_until='domcontentloaded', timeout=10000)
            json_text = await page.evaluate('document.body.textContent')

            if not json_text.strip():
                return

            matches = json.loads(json_text)

            if not matches:
                return

            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            acc_matches_found = 0

            for match in matches:
                home_team = match.get('home_club_name', '')
                away_team = match.get('away_club_name', '')

                # Check if either team is ACC
                is_acc_match = False
                acc_team_name = None

                if 'ACC' in home_team.upper():
                    is_acc_match = True
                    acc_team_name = home_team
                    self.acc_teams_found.add(home_team)

                if 'ACC' in away_team.upper():
                    is_acc_match = True
                    acc_team_name = away_team
                    self.acc_teams_found.add(away_team)

                if is_acc_match:
                    # Check date
                    match_date_str = match.get('match_date_time', '')
                    try:
                        match_date = datetime.strptime(match_date_str.split('T')[0], '%Y-%m-%d')
                        if match_date < cutoff_date:
                            continue
                    except:
                        pass

                    acc_matches_found += 1

                    # Try to get detailed match data
                    match_id = match.get('match_id')
                    if match_id:
                        try:
                            # Use existing scraper method
                            scorecard = await self.scraper.scrape_match_scorecard(match_id)

                            if scorecard:
                                # Determine tier
                                tier = self.scraper._determine_tier(grade_name)

                                # Extract player stats for ACC team
                                players = self.scraper.extract_player_stats(scorecard, "ACC", tier)

                                # Add to aggregator
                                for player in players:
                                    # Build performance dict for aggregator
                                    perf = {
                                        'player_name': player['player_name'],
                                        'team': acc_team_name,
                                        'match_date': match_date_str,
                                        'runs': player.get('batting', {}).get('runs', 0),
                                        'balls_faced': player.get('batting', {}).get('balls_faced', 0),
                                        'fours': player.get('batting', {}).get('fours', 0),
                                        'sixes': player.get('batting', {}).get('sixes', 0),
                                        'wickets': player.get('bowling', {}).get('wickets', 0),
                                        'overs': player.get('bowling', {}).get('overs', 0.0),
                                        'runs_conceded': player.get('bowling', {}).get('runs_conceded', 0),
                                        'maidens': player.get('bowling', {}).get('maidens', 0),
                                        'catches': player.get('fielding', {}).get('catches', 0),
                                        'stumpings': player.get('fielding', {}).get('stumpings', 0),
                                        'run_outs': player.get('fielding', {}).get('runouts', 0),
                                    }
                                    self.aggregator.add_match_performance(perf)

                                logger.info(f"      ✅ Match {match_id}: {home_team} vs {away_team} - {len(players)} ACC players")

                        except Exception as e:
                            logger.warning(f"      ⚠️  Could not fetch match {match_id}: {e}")

                    # Rate limiting
                    await asyncio.sleep(0.5)

            if acc_matches_found > 0:
                logger.info(f"   ✅ Found {acc_matches_found} ACC matches in {grade_name}")

        except Exception as e:
            logger.warning(f"   ⚠️  Could not process grade {grade_name}: {e}")

    def generate_roster(self, output_file: str) -> Dict:
        """
        Generate roster from aggregated data

        Args:
            output_file: Where to save roster JSON

        Returns:
            Roster dictionary
        """
        logger.info(f"\n📝 Generating roster from scraped data...")
        logger.info(f"   Total players found: {len(self.aggregator.players)}")

        if len(self.aggregator.players) == 0:
            logger.warning("⚠️  No players found! Check if scraping worked.")
            return {
                "club": "ACC",
                "season": "2025",
                "total_players": 0,
                "players": []
            }

        # Convert to PlayerStats format
        player_stats_list = []
        player_team_map = {}  # Map player name to team name

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
        logger.info(f"   Total players: {len(roster['players'])}")

        return roster

    def _determine_team_level(self, team_name: str) -> str:
        """Map team name to level code"""
        team_upper = team_name.upper()

        if 'ACC 1' in team_upper or ('ACC' in team_upper and '1' in team_upper):
            return 'hoofdklasse'
        elif 'ACC 2' in team_upper:
            return 'tweede'
        elif 'ACC 3' in team_upper:
            return 'derde'
        elif 'ACC 4' in team_upper:
            return 'derde'
        elif 'ACC 5' in team_upper:
            return 'vierde'
        elif 'ACC 6' in team_upper:
            return 'vierde'
        elif 'ZAMI' in team_upper:
            return 'zami'
        elif 'YOUTH' in team_upper or 'U19' in team_upper or 'U17' in team_upper:
            return 'youth'
        else:
            return 'hoofdklasse'  # Default

    def print_summary(self, roster: Dict):
        """Print summary of scraped roster"""
        players = roster.get('players', [])

        print("\n" + "=" * 80)
        print(f"🏏 Real ACC Roster - Scraped from KNCB")
        print("=" * 80)
        print(f"\nTotal Players: {len(players)}")
        print(f"Teams Found: {', '.join(roster.get('teams_found', []))}")

        if len(players) > 0:
            print(f"\n🌟 Top 20 Players:")
            for i, player in enumerate(players[:20], 1):
                print(f"   {i:2d}. {player['name']:<30} {player['team_name']:<20} €{player['fantasy_value']:.1f}")

        print("\n" + "=" * 80)


async def main():
    print("\n🏏 Real ACC Roster Scraper")
    print("=" * 80)
    print("Searching for ACC teams in all Dutch cricket divisions...")
    print("NOTE: Scraping season 17 (2024) since 2025 hasn't started yet")
    print()

    scraper = ACCRosterScraper()

    try:
        # Scrape all ACC teams from 2024 season (season 17)
        # We'll use this data as baseline for 2025 season
        await scraper.scrape_all_acc_teams(
            season_id=17,  # 2024 season (has actual match data)
            days_back=365  # Full year
        )

        # Generate roster
        roster = scraper.generate_roster('rosters/acc_2024_real_players.json')

        # Print summary
        scraper.print_summary(roster)

        print("\n✅ Complete!")
        print(f"   Real ACC roster saved to rosters/acc_2024_real_players.json")
        print(f"   This will be used as baseline for 2025 season")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
