#!/usr/bin/env python3
"""
Test local scorecard implementation on production.
Tests a few sample players to verify the system is working.
"""

import sys
import logging
from database import get_db
from database_models import Player
from multiplier_calculator import calculate_roster_multipliers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_few_players():
    """Test local scorecard calculation with a few players"""
    db = next(get_db())

    try:
        # Get a few active players from ACC 1
        test_players = db.query(Player).filter(
            Player.is_active == True,
            Player.rl_team == 'ACC 1'
        ).limit(5).all()

        if not test_players:
            logger.error("No active players found in ACC 1")
            return False

        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Local Scorecard Implementation (Production)")
        logger.info(f"{'='*80}\n")

        logger.info(f"Found {len(test_players)} test players from ACC 1:")
        for player in test_players:
            logger.info(f"  - {player.name} (Current multiplier: {player.multiplier})")

        # Calculate multipliers for these players
        logger.info(f"\nCalculating multipliers (should use local scorecards)...")

        player_ids = [p.id for p in test_players]

        multipliers, metadata = calculate_roster_multipliers(
            db,
            player_ids,
            scrape_missing=False  # Don't scrape web if local data fails
        )

        logger.info(f"\n{'='*80}")
        logger.info(f"RESULTS")
        logger.info(f"{'='*80}\n")

        logger.info(f"Metadata:")
        logger.info(f"  Total players: {metadata.get('total_players', 0)}")
        logger.info(f"  Players with data: {metadata.get('players_with_data', 0)}")
        logger.info(f"  Players without data: {metadata.get('players_without_data', 0)}")

        if metadata.get('players_with_data', 0) > 0:
            logger.info(f"  Median score: {metadata.get('median_score', 0):.2f}")
            logger.info(f"  Min score: {metadata.get('min_score', 0):.2f}")
            logger.info(f"  Max score: {metadata.get('max_score', 0):.2f}")

        logger.info(f"\nPlayer Results:")
        for player_id in player_ids:
            player = db.query(Player).filter(Player.id == player_id).first()
            multiplier = multipliers.get(player_id, 1.0)
            points = player.prev_season_fantasy_points if player else None
            logger.info(f"  {player.name if player else player_id}:")
            logger.info(f"    Multiplier: {multiplier:.2f}")
            if points is not None:
                logger.info(f"    Prev season points: {points:.2f}")
            else:
                logger.info(f"    Prev season points: None")

        success = metadata.get('players_with_data', 0) > 0

        if success:
            logger.info(f"\n✅ TEST PASSED - Local scorecards are working!")
        else:
            logger.warning(f"\n⚠️  No players found in local scorecards")
            logger.warning(f"   This might mean the scorecards don't contain these players")
            logger.warning(f"   Or the player name matching needs adjustment")

        return success

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_few_players()
    sys.exit(0 if success else 1)
