#!/usr/bin/env python3
"""
Weekly Stats Updater
====================
Runs every Monday to update player stats from their Match Centre profile pages.
Reads the legacy database and updates stats for all players with Match Centre IDs.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeeklyStatsUpdater:
    """Update player stats from Match Centre profile pages"""

    def __init__(self, database_file: str, season_id: str = "19"):
        self.database_file = database_file
        self.season_id = season_id  # 19 = 2025, will be 20 for 2026
        self.database = None
        self.updated_players = []
        self.failed_players = []

    def load_database(self):
        """Load the legacy database"""
        logger.info(f"📥 Loading database from {self.database_file}")

        with open(self.database_file, 'r') as f:
            self.database = json.load(f)

        total = len(self.database.get('players', []))
        with_ids = sum(1 for p in self.database['players'] if p.get('matchcentre_id'))

        logger.info(f"   Total players: {total}")
        logger.info(f"   Players with Match Centre IDs: {with_ids}")

        if with_ids == 0:
            logger.warning("⚠️  No players have Match Centre IDs!")

    async def update_all_players(self):
        """Update stats for all players with Match Centre IDs"""

        logger.info(f"\n🔄 Starting weekly update for season {self.season_id}")
        logger.info(f"   {datetime.now().strftime('%A, %B %d, %Y')}")
        print()

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)

        try:
            players_to_update = [p for p in self.database['players'] if p.get('matchcentre_id')]

            for i, player in enumerate(players_to_update, 1):
                logger.info(f"📊 {i}/{len(players_to_update)}: {player['name']}")

                page = await browser.new_page()
                try:
                    updated_stats = await self._fetch_player_stats(page, player)

                    if updated_stats:
                        # Update player stats in database
                        player['stats'] = updated_stats
                        player['last_updated'] = datetime.now().isoformat()
                        self.updated_players.append(player['name'])
                        logger.info(f"   ✅ Updated")
                    else:
                        self.failed_players.append(player['name'])
                        logger.warning(f"   ⚠️  Failed to update")

                finally:
                    await page.close()

                # Rate limiting
                await asyncio.sleep(1)

        finally:
            await browser.close()
            await playwright.stop()

        logger.info(f"\n✅ Update complete!")
        logger.info(f"   Successfully updated: {len(self.updated_players)}")
        logger.info(f"   Failed: {len(self.failed_players)}")

    async def _fetch_player_stats(self, page, player: Dict) -> Dict:
        """Fetch updated stats from player's Match Centre profile"""

        matchcentre_id = player['matchcentre_id']
        url = f"https://matchcentre.kncb.nl/player/{matchcentre_id}/{self.season_id}/"

        try:
            # Load player profile
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            # Get page text
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')

            # Extract season summary stats
            # Look for patterns like:
            # "340 TOTAL RUNS"
            # "34.00 BATTING AVERAGE"
            # "109* HIGHEST SCORE"
            # "0 WICKETS"

            stats = {
                "matches": 0,
                "runs": 0,
                "batting_avg": 0.0,
                "strike_rate": 0.0,
                "wickets": 0,
                "bowling_avg": 0.0,
                "economy": 0.0,
                "catches": 0,
                "run_outs": 0
            }

            for i, line in enumerate(lines):
                line = line.strip()

                # Look for "CURRENT SEASON (X MATCHES)"
                if 'CURRENT SEASON' in line and 'MATCHES' in line:
                    match = re.search(r'(\d+)\s+MATCHES', line)
                    if match:
                        stats['matches'] = int(match.group(1))

                # Total runs
                if 'TOTAL RUNS' in line:
                    # Previous line should be the number
                    if i > 0 and lines[i-1].strip().isdigit():
                        stats['runs'] = int(lines[i-1].strip())

                # Batting average
                if 'BATTING AVERAGE' in line:
                    if i > 0:
                        try:
                            stats['batting_avg'] = float(lines[i-1].strip())
                        except:
                            pass

                # Wickets
                if line == 'WICKETS':
                    if i > 0 and lines[i-1].strip().isdigit():
                        stats['wickets'] = int(lines[i-1].strip())

                # Bowling average
                if 'BOWLING AVERAGE' in line:
                    if i > 0:
                        try:
                            avg_str = lines[i-1].strip()
                            if avg_str != '-':
                                stats['bowling_avg'] = float(avg_str)
                        except:
                            pass

            # Count matches from match-by-match table
            match_count = 0
            for line in lines:
                # Look for match entries (they have patterns like "vs" or specific team names)
                if ' vs ' in line.lower():
                    match_count += 1

            if match_count > 0:
                stats['matches'] = match_count // 2  # Each match appears twice (home and away)

            logger.info(f"      Matches: {stats['matches']}, Runs: {stats['runs']}, Wickets: {stats['wickets']}")

            return stats

        except Exception as e:
            logger.error(f"      Error fetching stats: {e}")
            return None

    def save_database(self, output_file: str = None):
        """Save updated database"""

        if output_file is None:
            output_file = self.database_file

        self.database['last_updated'] = datetime.now().isoformat()
        self.database['season_id'] = self.season_id

        with open(output_file, 'w') as f:
            json.dump(self.database, f, indent=2)

        logger.info(f"\n💾 Updated database saved to {output_file}")

    def recalculate_values(self):
        """Recalculate fantasy values based on updated stats"""

        logger.info(f"\n💰 Recalculating fantasy values...")

        from player_value_calculator import PlayerValueCalculator, PlayerStats

        calculator = PlayerValueCalculator()

        # Group players by team
        from collections import defaultdict
        teams = defaultdict(list)

        for player in self.database['players']:
            team_name = player['team_name']
            teams[team_name].append(player)

        # Recalculate values per team
        all_results = []

        for team_name, team_players in teams.items():
            player_stats = []

            for player in team_players:
                stats = PlayerStats(
                    player_name=player['name'],
                    club=player['club'],
                    matches_played=player['stats']['matches'],
                    total_runs=player['stats']['runs'],
                    batting_average=player['stats']['batting_avg'],
                    strike_rate=player['stats']['strike_rate'],
                    total_wickets=player['stats']['wickets'],
                    bowling_average=player['stats']['bowling_avg'],
                    economy_rate=player['stats']['economy'],
                    catches=player['stats']['catches'],
                    run_outs=player['stats']['run_outs'],
                    team_level=player['team_level']
                )
                player_stats.append((player, stats))

            # Calculate values for this team
            stats_only = [s for _, s in player_stats]
            results = calculator.calculate_team_values_per_team(
                stats_only,
                team_name_getter=lambda p: team_name
            )

            # Update player values
            for (player, _), (_, value, _) in zip(player_stats, results):
                player['fantasy_value'] = round(value, 1)

        # Sort by value
        self.database['players'].sort(key=lambda x: x['fantasy_value'], reverse=True)

        logger.info(f"   ✅ Fantasy values recalculated")


async def main():
    print("\n" + "=" * 80)
    print("🏏 ACC WEEKLY STATS UPDATER")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print("=" * 80)
    print()

    # Configuration
    database_file = 'rosters/acc_legacy_database.json'
    season_id = "19"  # Update to "20" for 2026 season

    try:
        updater = WeeklyStatsUpdater(database_file, season_id)
        updater.load_database()

        print()
        await updater.update_all_players()

        print()
        updater.recalculate_values()

        print()
        updater.save_database()

        print()
        print("=" * 80)
        print("✅ WEEKLY UPDATE COMPLETE!")
        print("=" * 80)
        print(f"   Players updated: {len(updater.updated_players)}")
        print(f"   Failed updates: {len(updater.failed_players)}")

        if updater.failed_players:
            print(f"\n⚠️  Failed players:")
            for name in updater.failed_players[:10]:
                print(f"   - {name}")

        print()
        print("💡 Database has been updated with latest season stats")
        print("=" * 80)

    except FileNotFoundError:
        logger.error(f"❌ Database file not found: {database_file}")
        logger.error("   Run build_acc_legacy_database.py first!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
