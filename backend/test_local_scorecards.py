#!/usr/bin/env python3
"""
Test script for local scorecard multiplier calculation.

This script tests the new _calculate_from_local_scorecards() function
to ensure it correctly reads and parses local scorecard files.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Database setup
from database import get_db
from database_models import Player
from multiplier_calculator import _calculate_from_local_scorecards, calculate_roster_multipliers
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_player():
    """Test local scorecard calculation for a single player"""
    db = next(get_db())

    try:
        # Get a few sample players from different teams
        test_players = db.query(Player).filter(
            Player.is_active == True,
            Player.rl_team.in_(['ACC 1', 'ACC 2', 'ACC 3'])
        ).limit(10).all()

        if not test_players:
            logger.error("No active players found in database")
            return

        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Local Scorecard Multiplier Calculation")
        logger.info(f"{'='*80}\n")

        results = []

        for player in test_players:
            logger.info(f"\nTesting player: {player.name} (Team: {player.rl_team})")
            logger.info(f"  Current multiplier: {player.multiplier}")
            logger.info(f"  Stored prev_season_fantasy_points: {player.prev_season_fantasy_points}")

            # Calculate from local scorecards
            points = _calculate_from_local_scorecards(db, player)

            if points is not None:
                results.append({
                    'name': player.name,
                    'team': player.rl_team,
                    'points': points,
                    'current_multiplier': player.multiplier
                })
                logger.info(f"  ✅ Calculated from local scorecards: {points:.2f} points")
            else:
                logger.info(f"  ⚠️  No local scorecard data found")

        # Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*80}\n")
        logger.info(f"Total players tested: {len(test_players)}")
        logger.info(f"Players with local data: {len(results)}")
        logger.info(f"Players without local data: {len(test_players) - len(results)}")

        if results:
            logger.info(f"\nPlayers found in local scorecards:")
            for r in results:
                logger.info(f"  - {r['name']} ({r['team']}): {r['points']:.2f} points")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        db.close()


def test_full_multiplier_calculation():
    """Test full multiplier calculation with local scorecards"""
    db = next(get_db())

    try:
        # Get some active players
        active_players = db.query(Player).filter(
            Player.is_active == True,
            Player.rl_team.in_(['ACC 1', 'ACC 2'])
        ).limit(20).all()

        if not active_players:
            logger.error("No active players found")
            return

        player_ids = [p.id for p in active_players]

        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Full Multiplier Calculation (with local scorecards)")
        logger.info(f"{'='*80}\n")
        logger.info(f"Calculating multipliers for {len(player_ids)} players...")

        # Calculate multipliers (should use local scorecards, not web scraping)
        multipliers, metadata = calculate_roster_multipliers(
            db,
            player_ids,
            scrape_missing=False  # Don't scrape web, only use local data
        )

        logger.info(f"\n{'='*80}")
        logger.info(f"CALCULATION RESULTS")
        logger.info(f"{'='*80}\n")
        logger.info(f"Total players: {metadata.get('total_players', 0)}")
        logger.info(f"Players with data: {metadata.get('players_with_data', 0)}")
        logger.info(f"Players without data: {metadata.get('players_without_data', 0)}")
        logger.info(f"Median score: {metadata.get('median_score', 0):.2f}")
        logger.info(f"Min score: {metadata.get('min_score', 0):.2f}")
        logger.info(f"Max score: {metadata.get('max_score', 0):.2f}")
        logger.info(f"Min multiplier: {metadata.get('min_multiplier', 0):.2f}")
        logger.info(f"Max multiplier: {metadata.get('max_multiplier', 0):.2f}")

        # Show some sample multipliers
        logger.info(f"\nSample multipliers:")
        for i, player_id in enumerate(list(multipliers.keys())[:10]):
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                logger.info(f"  - {player.name}: {multipliers[player_id]:.2f}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        db.close()


def check_scorecard_availability():
    """Check if local scorecards are available"""
    backend_dir = Path(__file__).parent
    scorecards_dir = backend_dir / "mock_data" / "scorecards_2026"

    logger.info(f"\n{'='*80}")
    logger.info(f"Checking Local Scorecard Availability")
    logger.info(f"{'='*80}\n")

    if not scorecards_dir.exists():
        logger.error(f"❌ Scorecards directory not found: {scorecards_dir}")
        return False

    logger.info(f"✅ Scorecards directory exists: {scorecards_dir}")

    # Check subdirectories
    by_match_id = scorecards_dir / "by_match_id"
    by_team = scorecards_dir / "by_team"
    by_week = scorecards_dir / "by_week"
    index_file = scorecards_dir / "index.json"

    if by_match_id.exists():
        match_files = list(by_match_id.glob("*.json"))
        logger.info(f"✅ by_match_id: {len(match_files)} match files")
    else:
        logger.warning(f"⚠️  by_match_id directory not found")

    if by_team.exists():
        team_files = list(by_team.glob("*.json"))
        logger.info(f"✅ by_team: {len(team_files)} team files")
    else:
        logger.warning(f"⚠️  by_team directory not found")

    if by_week.exists():
        week_files = list(by_week.glob("*.json"))
        logger.info(f"✅ by_week: {len(week_files)} week files")
    else:
        logger.warning(f"⚠️  by_week directory not found")

    if index_file.exists():
        logger.info(f"✅ index.json exists")
    else:
        logger.warning(f"⚠️  index.json not found")

    return True


if __name__ == "__main__":
    # Run tests
    check_scorecard_availability()
    test_single_player()
    # Uncomment to test full calculation:
    # test_full_multiplier_calculation()
