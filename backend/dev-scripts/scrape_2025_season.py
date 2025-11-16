#!/usr/bin/env python3
"""
2025 Season Archiver
====================
Scrapes complete 2025 season data for ACC to build accurate legacy roster.

This script:
1. Scrapes all ACC matches from 2025 season (April-September)
2. Extracts every player who appeared
3. Aggregates their complete season statistics
4. Generates a complete legacy roster JSON
5. Calculates initial fantasy values

Usage:
    python3 scrape_2025_season.py --club ACC --output rosters/acc_2025_complete.json
"""

import asyncio
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import sys

# Import our existing modules
from kncb_html_scraper import KNCBMatchCentreScraper
from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Season2025Archiver:
    """
    Archive complete 2025 season data for a club
    """

    def __init__(self, club: str):
        self.club = club
        self.scraper = KNCBMatchCentreScraper()
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

    async def scrape_full_season(self, days_back: int = 180) -> Dict:
        """
        Scrape all matches for the club going back specified days

        Args:
            days_back: How many days to look back (default 180 for full season)

        Returns:
            Dictionary with all match data and player performances
        """
        logger.info(f"🏏 Scraping 2025 season for {self.club}")
        logger.info(f"   Looking back {days_back} days (approx April-September 2025)")

        try:
            # Scrape matches
            result = await self.scraper.scrape_weekly_update(
                clubs=[self.club],
                days_back=days_back
            )

            matches_found = len(result.get('matches', []))
            logger.info(f"✅ Found {matches_found} matches for {self.club}")

            return result

        except Exception as e:
            logger.error(f"❌ Error scraping season: {e}")
            raise

    def aggregate_players(self, scrape_result: Dict) -> PlayerSeasonAggregator:
        """
        Aggregate all player performances into season totals

        Args:
            scrape_result: Output from scraper

        Returns:
            Aggregator with all player data
        """
        logger.info(f"\n📊 Aggregating player statistics...")

        matches = scrape_result.get('matches', [])

        for match in matches:
            for performance in match.get('player_performances', []):
                # Add to aggregator
                self.aggregator.add_match_performance(performance)

        total_players = len(self.aggregator.players)
        logger.info(f"✅ Aggregated stats for {total_players} players")

        return self.aggregator

    def calculate_player_values(self) -> Dict[str, tuple]:
        """
        Calculate fantasy values for all players

        Returns:
            Dict mapping player_id to (value, justification)
        """
        logger.info(f"\n💰 Calculating player values...")

        # Convert aggregator data to PlayerStats format
        player_stats_list = []

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
                team_level=player_data.get('team_level', '1st'),
                # TODO: Add match-by-match performances for consistency
                match_performances=None
            )
            player_stats_list.append((player_id, stats))

        # Calculate values with relative comparison
        stats_only = [stats for _, stats in player_stats_list]
        results = self.value_calculator.calculate_team_values(stats_only)

        # Map back to player IDs
        value_map = {}
        for i, (player_id, _) in enumerate(player_stats_list):
            _, value, justification = results[i]
            value_map[player_id] = (value, justification)

        logger.info(f"✅ Calculated values for {len(value_map)} players")

        return value_map

    def generate_legacy_roster(
        self,
        values: Dict[str, tuple],
        output_file: str
    ) -> Dict:
        """
        Generate complete legacy roster JSON

        Args:
            values: Player values from calculator
            output_file: Where to save the roster

        Returns:
            Complete roster dictionary
        """
        logger.info(f"\n📝 Generating legacy roster...")

        roster = {
            "club": self.club,
            "season": "2025",
            "created_at": datetime.now().isoformat(),
            "notes": f"Complete {self.club} roster from 2025 season",
            "total_players": len(self.aggregator.players),
            "players": []
        }

        # Add each player with their stats and value
        for player_id, player_data in self.aggregator.players.items():
            value, justification = values.get(player_id, (25.0, "Default value"))

            player_entry = {
                "player_id": player_id,
                "name": player_data['player_name'],
                "club": player_data['club'],
                "team_level": player_data.get('team_level', '1st'),
                "fantasy_value": round(value, 1),
                "stats": {
                    "matches": player_data['matches_played'],
                    "runs": player_data['season_totals']['runs'],
                    "batting_avg": round(player_data['averages']['batting_average'], 2),
                    "strike_rate": round(player_data['averages']['strike_rate'], 2),
                    "wickets": player_data['season_totals']['wickets'],
                    "bowling_avg": round(player_data['averages']['bowling_average'], 2),
                    "economy": round(player_data['averages']['economy_rate'], 2),
                    "catches": player_data['season_totals']['catches'],
                    "run_outs": player_data['season_totals']['run_outs'],
                    "fantasy_points": player_data['season_totals']['fantasy_points']
                },
                "value_justification": justification.split('\n')[0]  # First line only
            }

            roster['players'].append(player_entry)

        # Sort by value (highest first)
        roster['players'].sort(key=lambda x: x['fantasy_value'], reverse=True)

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(roster, f, indent=2)

        logger.info(f"✅ Saved roster to {output_file}")
        logger.info(f"   Total players: {len(roster['players'])}")

        return roster

    def print_summary(self, roster: Dict):
        """Print summary statistics"""
        players = roster['players']

        print("\n" + "=" * 80)
        print(f"🏏 {self.club} 2025 Season Complete Roster")
        print("=" * 80)
        print(f"\nTotal Players: {len(players)}")
        print(f"Season: {roster['season']}")
        print(f"\n📊 Value Distribution:")

        # Count by price range
        ranges = {
            "€45-50 (Superstars)": sum(1 for p in players if p['fantasy_value'] >= 45),
            "€40-45 (Premium)": sum(1 for p in players if 40 <= p['fantasy_value'] < 45),
            "€35-40 (Solid)": sum(1 for p in players if 35 <= p['fantasy_value'] < 40),
            "€30-35 (Average)": sum(1 for p in players if 30 <= p['fantasy_value'] < 35),
            "€20-30 (Budget)": sum(1 for p in players if p['fantasy_value'] < 30),
        }

        for range_name, count in ranges.items():
            print(f"   {range_name}: {count} players")

        print(f"\n🌟 Top 10 Most Valuable Players:")
        for i, player in enumerate(players[:10], 1):
            print(f"   {i:2d}. {player['name']:<25} €{player['fantasy_value']:.1f}")
            print(f"       {player['stats']['runs']} runs, {player['stats']['wickets']} wickets, {player['stats']['matches']} matches")

        print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(description='Scrape 2025 season and build complete roster')
    parser.add_argument('--club', default='ACC', help='Club name (default: ACC)')
    parser.add_argument('--days-back', type=int, default=180, help='Days to look back (default: 180)')
    parser.add_argument('--output', default='rosters/acc_2025_complete.json', help='Output file path')

    args = parser.parse_args()

    print(f"\n🏏 2025 Season Archiver")
    print(f"   Club: {args.club}")
    print(f"   Period: Last {args.days_back} days")
    print(f"   Output: {args.output}")
    print()

    try:
        # Create archiver
        archiver = Season2025Archiver(args.club)

        # Step 1: Scrape all matches
        scrape_result = await archiver.scrape_full_season(days_back=args.days_back)

        # Step 2: Aggregate player stats
        archiver.aggregate_players(scrape_result)

        # Step 3: Calculate values
        values = archiver.calculate_player_values()

        # Step 4: Generate roster
        roster = archiver.generate_legacy_roster(values, args.output)

        # Step 5: Print summary
        archiver.print_summary(roster)

        print(f"\n✅ Complete! Roster saved to {args.output}")
        print(f"   You can now use this roster for 2026 season setup")

    except Exception as e:
        logger.error(f"\n❌ Failed to archive season: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
