#!/usr/bin/env python3
"""
Month-Long Play Simulation
===========================
Simulates 4 weeks of cricket matches to test:
1. Player stats updating from match performances
2. Multiplier adjustments with 15% weekly drift
3. How player values shift based on performance

Usage:
    python3 simulate_month_of_play.py [--dry-run] [--weeks 4]
"""

import sys
import os
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from database_models import Player, Club
from multiplier_adjuster import MultiplierAdjuster
from fantasy_points_calculator import FantasyPointsCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonthSimulator:
    """Simulates a month of cricket matches with multiplier adjustments"""

    def __init__(self, db: Session, num_weeks: int = 4):
        self.db = db
        self.num_weeks = num_weeks
        self.calculator = FantasyPointsCalculator()
        self.adjuster = MultiplierAdjuster(drift_rate=0.15)
        self.simulation_log = []

    def generate_realistic_match_performance(
        self,
        player: Player,
        quality_factor: float
    ) -> Dict:
        """
        Generate realistic match performance based on player quality

        Args:
            player: Player object
            quality_factor: 0.0 to 1.0 (0.0 = poor form, 1.0 = excellent form)

        Returns:
            Dictionary with match performance stats
        """
        performance = {
            'runs': 0,
            'balls_faced': 0,
            'fours': 0,
            'sixes': 0,
            'is_out': False,
            'wickets': 0,
            'overs_bowled': 0.0,
            'runs_conceded': 0,
            'maidens': 0,
            'catches': 0,
            'run_outs': 0,
            'stumpings': 0
        }

        # Batting performance (weighted by quality)
        batting_chance = random.random()
        if batting_chance < 0.7:  # 70% chance to bat
            # Runs: quality affects max runs
            max_runs = int(120 * quality_factor + 10)
            performance['runs'] = random.randint(0, max_runs)

            if performance['runs'] > 0:
                # Strike rate varies
                strike_rate = random.uniform(60, 180) * (0.7 + quality_factor * 0.6)
                performance['balls_faced'] = max(1, int(performance['runs'] / (strike_rate / 100)))

                # Boundaries based on runs and strike rate
                if performance['runs'] > 20:
                    performance['fours'] = int(performance['runs'] * random.uniform(0.15, 0.25))
                    performance['sixes'] = int(performance['runs'] * random.uniform(0.05, 0.15))

                # Chance of getting out
                performance['is_out'] = random.random() < 0.6

        # Bowling performance (weighted by quality)
        bowling_chance = random.random()
        if bowling_chance < 0.5:  # 50% chance to bowl
            # Overs: typically 2-10 overs
            performance['overs_bowled'] = round(random.uniform(2.0, 10.0), 1)

            # Wickets: quality affects wicket-taking
            max_wickets = 5 if quality_factor > 0.6 else 3
            performance['wickets'] = random.choices(
                [0, 1, 2, 3, 4, 5],
                weights=[30, 35, 20, 10, 4, 1]
            )[0]
            if performance['wickets'] > max_wickets:
                performance['wickets'] = max_wickets

            # Economy rate: better players have better economy
            base_economy = 6.0 - (quality_factor * 2.0)  # 4.0 to 6.0
            economy = random.gauss(base_economy, 1.5)
            performance['runs_conceded'] = int(performance['overs_bowled'] * max(2.0, economy))

            # Maidens: rare but possible
            if quality_factor > 0.5:
                performance['maidens'] = random.choices([0, 1, 2], weights=[70, 25, 5])[0]

        # Fielding (everyone can field)
        fielding_quality = 0.5 + (quality_factor * 0.5)
        if random.random() < 0.3 * fielding_quality:
            performance['catches'] = random.choices([0, 1, 2], weights=[40, 50, 10])[0]
        if random.random() < 0.1 * fielding_quality:
            performance['run_outs'] = 1

        return performance

    def update_player_stats(self, player: Player, performance: Dict):
        """Update player's season stats with new performance"""
        # Initialize stats dict if None
        if not player.stats:
            player.stats = {}

        # Ensure all required fields exist (handle existing players with partial stats)
        required_fields = {
            'total_runs': 0,
            'total_balls_faced': 0,
            'total_fours': 0,
            'total_sixes': 0,
            'total_wickets': 0,
            'total_overs': 0.0,
            'total_runs_conceded': 0,
            'total_maidens': 0,
            'total_catches': 0,
            'total_run_outs': 0,
            'total_stumpings': 0,
            'matches_played': 0
        }

        for field, default_value in required_fields.items():
            if field not in player.stats:
                player.stats[field] = default_value

        # Add performance to cumulative stats
        player.stats['total_runs'] += performance['runs']
        player.stats['total_balls_faced'] += performance['balls_faced']
        player.stats['total_fours'] += performance['fours']
        player.stats['total_sixes'] += performance['sixes']
        player.stats['total_wickets'] += performance['wickets']
        player.stats['total_overs'] += performance['overs_bowled']
        player.stats['total_runs_conceded'] += performance['runs_conceded']
        player.stats['total_maidens'] += performance['maidens']
        player.stats['total_catches'] += performance['catches']
        player.stats['total_run_outs'] += performance['run_outs']
        player.stats['total_stumpings'] += performance['stumpings']
        player.stats['matches_played'] += 1

        # Mark the stats field as modified for SQLAlchemy to detect JSONB changes
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(player, 'stats')

    def simulate_week(self, week_num: int) -> Dict:
        """Simulate one week of matches for all players"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📅 WEEK {week_num} - Simulating matches...")
        logger.info(f"{'='*70}\n")

        # Get all players
        players = self.db.query(Player).all()
        logger.info(f"   Simulating matches for {len(players)} players")

        week_performances = []

        for player in players:
            # Each player has 2-3 matches per week
            num_matches = random.randint(2, 3)

            # Player quality based on current multiplier (inverted - lower multiplier = better)
            # Multiplier range: 0.69 (best) to 5.0 (worst)
            quality_factor = max(0.0, min(1.0, (5.0 - player.multiplier) / 4.31))

            for match_num in range(num_matches):
                # Generate performance
                performance = self.generate_realistic_match_performance(player, quality_factor)

                # Calculate fantasy points for this match
                points = self.calculator.calculate_total_points(**performance)

                # Update cumulative stats
                self.update_player_stats(player, performance)

                week_performances.append({
                    'player_name': player.name,
                    'player_id': player.id,
                    'match_num': match_num + 1,
                    'performance': performance,
                    'points': points['grand_total']
                })

        self.db.commit()

        # Calculate total points for the week
        total_points = sum(p['points'] for p in week_performances)
        avg_points = total_points / len(week_performances) if week_performances else 0

        logger.info(f"   ✅ Week {week_num} complete!")
        logger.info(f"      Total matches simulated: {len(week_performances)}")
        logger.info(f"      Total fantasy points: {total_points:.2f}")
        logger.info(f"      Average points per match: {avg_points:.2f}")

        return {
            'week': week_num,
            'performances': week_performances,
            'total_points': total_points,
            'avg_points': avg_points
        }

    def track_player_changes(self, week_num: int) -> List[Dict]:
        """Track player multiplier and stats before adjustment"""
        players = self.db.query(Player).all()

        tracked = []
        for player in players:
            season_points = self.adjuster.calculate_player_season_points(player)
            tracked.append({
                'week': week_num,
                'player_name': player.name,
                'player_id': player.id,
                'multiplier_before': player.multiplier,
                'season_points': season_points,
                'total_runs': player.stats.get('total_runs', 0) if player.stats else 0,
                'total_wickets': player.stats.get('total_wickets', 0) if player.stats else 0,
                'matches_played': player.stats.get('matches_played', 0) if player.stats else 0
            })

        return tracked

    def adjust_multipliers(self, week_num: int, before_data: List[Dict]) -> Dict:
        """Run multiplier adjustment and track changes"""
        logger.info(f"\n🎯 Adjusting multipliers after Week {week_num}...")

        result = self.adjuster.adjust_multipliers(self.db, dry_run=False)

        logger.info(f"   Players adjusted: {result['players_changed']}")
        logger.info(f"   Score distribution:")
        logger.info(f"      Min: {result['score_stats']['min']:.2f}")
        logger.info(f"      Median: {result['score_stats']['median']:.2f}")
        logger.info(f"      Max: {result['score_stats']['max']:.2f}")

        # Track changes
        if result['top_changes']:
            logger.info(f"\n   📊 Top 5 multiplier changes:")
            for i, change in enumerate(result['top_changes'][:5], 1):
                direction = "↑" if change['change'] > 0 else "↓"
                logger.info(
                    f"      {i}. {change['player_name']}: "
                    f"{change['old_multiplier']:.2f} → {change['new_multiplier']:.2f} "
                    f"({direction}{abs(change['change']):.2f}) "
                    f"[{change['score']:.0f} pts]"
                )

        return result

    def run_simulation(self) -> Dict:
        """Run full month simulation"""
        logger.info(f"\n{'#'*70}")
        logger.info(f"🏏 STARTING MONTH-LONG SIMULATION ({self.num_weeks} weeks)")
        logger.info(f"{'#'*70}\n")

        simulation_results = {
            'weeks': [],
            'adjustments': [],
            'player_progression': {}
        }

        # Get initial player states
        players = self.db.query(Player).all()
        logger.info(f"📋 Initial state: {len(players)} players")
        logger.info(f"   Multiplier range: {min(p.multiplier for p in players):.2f} - {max(p.multiplier for p in players):.2f}\n")

        # Run simulation for each week
        for week_num in range(1, self.num_weeks + 1):
            # Track before adjustment
            before_data = self.track_player_changes(week_num)

            # Simulate matches
            week_results = self.simulate_week(week_num)
            simulation_results['weeks'].append(week_results)

            # Adjust multipliers
            adjustment_results = self.adjust_multipliers(week_num, before_data)
            simulation_results['adjustments'].append(adjustment_results)

            # Track player progression
            players = self.db.query(Player).all()
            for player in players:
                if player.id not in simulation_results['player_progression']:
                    simulation_results['player_progression'][player.id] = {
                        'player_name': player.name,
                        'weekly_data': []
                    }

                season_points = self.adjuster.calculate_player_season_points(player)
                simulation_results['player_progression'][player.id]['weekly_data'].append({
                    'week': week_num,
                    'multiplier': player.multiplier,
                    'season_points': season_points,
                    'matches_played': player.stats.get('matches_played', 0) if player.stats else 0
                })

        # Generate summary report
        self.generate_summary_report(simulation_results)

        return simulation_results

    def generate_summary_report(self, results: Dict):
        """Generate comprehensive summary report"""
        logger.info(f"\n{'#'*70}")
        logger.info(f"📊 SIMULATION SUMMARY REPORT")
        logger.info(f"{'#'*70}\n")

        # Overall stats
        total_matches = sum(len(week['performances']) for week in results['weeks'])
        total_points = sum(week['total_points'] for week in results['weeks'])

        logger.info(f"📈 Overall Statistics:")
        logger.info(f"   Total weeks simulated: {self.num_weeks}")
        logger.info(f"   Total matches: {total_matches}")
        logger.info(f"   Total fantasy points: {total_points:.2f}")
        logger.info(f"   Average points per match: {total_points / total_matches:.2f}")

        # Find players with biggest changes
        logger.info(f"\n🎯 Biggest Multiplier Changes (Start → End):")

        biggest_changes = []
        for player_id, data in results['player_progression'].items():
            if len(data['weekly_data']) >= 2:
                start = data['weekly_data'][0]
                end = data['weekly_data'][-1]
                change = end['multiplier'] - start['multiplier']

                biggest_changes.append({
                    'player_name': data['player_name'],
                    'start_multiplier': start['multiplier'],
                    'end_multiplier': end['multiplier'],
                    'change': change,
                    'start_points': start['season_points'],
                    'end_points': end['season_points'],
                    'matches_played': end['matches_played']
                })

        # Sort by absolute change
        biggest_changes.sort(key=lambda x: abs(x['change']), reverse=True)

        logger.info(f"\n   Top 10 Improved (Lower Multiplier = Better):")
        for i, player in enumerate([p for p in biggest_changes if p['change'] < 0][:10], 1):
            logger.info(
                f"   {i:2d}. {player['player_name']:30s} "
                f"{player['start_multiplier']:.2f} → {player['end_multiplier']:.2f} "
                f"(↓{abs(player['change']):.2f}) "
                f"[{player['end_points']:.0f} pts, {player['matches_played']} matches]"
            )

        logger.info(f"\n   Top 10 Declined (Higher Multiplier = Worse):")
        for i, player in enumerate([p for p in biggest_changes if p['change'] > 0][:10], 1):
            logger.info(
                f"   {i:2d}. {player['player_name']:30s} "
                f"{player['start_multiplier']:.2f} → {player['end_multiplier']:.2f} "
                f"(↑{player['change']:.2f}) "
                f"[{player['end_points']:.0f} pts, {player['matches_played']} matches]"
            )

        logger.info(f"\n{'#'*70}")
        logger.info(f"✅ SIMULATION COMPLETE!")
        logger.info(f"{'#'*70}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Simulate month of cricket play')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to simulate')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')

    args = parser.parse_args()

    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE - No changes will be committed\n")

    # Create database session
    db = SessionLocal()

    try:
        # Run simulation
        simulator = MonthSimulator(db, num_weeks=args.weeks)
        results = simulator.run_simulation()

        if args.dry_run:
            db.rollback()
            logger.info("⚠️  Changes rolled back (dry run)")
        else:
            logger.info("✅ All changes committed to database")

    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
