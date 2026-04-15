#!/usr/bin/env python3
"""
Pre-calculate Player Statistics from Local Scorecards
======================================================
One-time script to parse all 136 local scorecards and generate player_stats_2025.json

This script:
1. Reads all scorecard files from mock_data/scorecards_2026/by_match_id/
2. Uses Playwright to render React SPA HTML
3. Extracts player stats using existing kncb_html_scraper logic
4. Matches player names to database using scorecard_player_matcher
5. Aggregates total fantasy points per player
6. Stores results in mock_data/player_stats_2025.json

Run this once to generate the pre-calculated stats file.
For 2026 season, we'll run this weekly as new scorecards arrive.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict
from database import get_db
from scorecard_player_matcher import ScorecardPlayerMatcher
from kncb_html_scraper import KNCBMatchCentreScraper
from scraper_config import get_scraper_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def parse_scorecard_with_playwright(scraper, match_id: int, team: str):
    """
    Use Playwright via mock server to render and parse scorecard

    The HTML files are React SPAs that need JavaScript execution.
    We use the mock server to serve them and Playwright to render them.

    Returns:
        List of player stats dicts with fantasy_points calculated
    """
    try:
        # Use the scraper to fetch and parse the scorecard from mock server
        # The mock server will serve our local file
        scorecard_result = await scraper.scrape_match_scorecard(match_id)

        if not scorecard_result:
            logger.warning(f"Match {match_id}: No scorecard data returned")
            return []

        # Extract player stats using the scraper's built-in extraction
        player_stats = scraper.extract_player_stats(
            scorecard_result,
            club_name='ACC',  # All our scorecards are ACC matches
            tier=None  # Will be inferred from team name
        )

        logger.debug(f"Match {match_id}: Extracted {len(player_stats)} players")
        return player_stats

    except Exception as e:
        logger.error(f"Match {match_id}: Error parsing with Playwright: {e}")
        return []


async def process_all_scorecards():
    """
    Process all local scorecards and generate player_stats_2025.json
    """
    logger.info("="*80)
    logger.info("PRE-CALCULATING PLAYER STATS FROM LOCAL SCORECARDS")
    logger.info("="*80)

    # Setup paths
    backend_dir = Path(__file__).parent
    scorecards_dir = backend_dir / "mock_data" / "scorecards_2026" / "by_match_id"
    output_file = backend_dir / "mock_data" / "player_stats_2025.json"

    if not scorecards_dir.exists():
        logger.error(f"Scorecards directory not found: {scorecards_dir}")
        return False

    # Get database session
    db = next(get_db())

    try:
        # Initialize matcher
        matcher = ScorecardPlayerMatcher(db)

        # Initialize scraper in MOCK mode
        os.environ['SCRAPER_MODE'] = 'mock'
        config = get_scraper_config()
        scraper = KNCBMatchCentreScraper(config)
        logger.info(f"Scraper initialized: {config.mode} mode, base URL: {config.base_url}")

        # Get all scorecard files
        scorecard_files = sorted(list(scorecards_dir.glob("*.json")))
        logger.info(f"\nFound {len(scorecard_files)} scorecard files")

        # Track player stats: player_id -> {name, matches, total_points, performances}
        player_stats: Dict[str, dict] = {}

        # Track unmatched players for debugging
        unmatched_names = set()

        # Process each scorecard
        for i, scorecard_file in enumerate(scorecard_files, 1):
            try:
                logger.info(f"\n[{i}/{len(scorecard_files)}] Processing {scorecard_file.name}...")

                # Load scorecard
                with open(scorecard_file, 'r') as f:
                    scorecard_data = json.load(f)

                match_id = scorecard_data['match_id']
                team = scorecard_data.get('team', 'Unknown')
                html = scorecard_data['scorecard_html']

                # Parse scorecard using Playwright via mock server
                player_performances = await parse_scorecard_with_playwright(scraper, match_id, team)

                if not player_performances:
                    logger.warning(f"  No player data extracted from match {match_id}")
                    continue

                logger.info(f"  Extracted {len(player_performances)} player performances")

                # Match each player to database
                for perf in player_performances:
                    scorecard_name = perf.get('name', '').strip()
                    fantasy_points = perf.get('fantasy_points', 0.0)

                    if not scorecard_name:
                        continue

                    # Try to match to database player
                    matched_player = matcher.match_player(
                        scorecard_name,
                        club_filter='ACC',  # All our scorecards are ACC
                        team_filter=team if team != 'Unknown' else None
                    )

                    if matched_player:
                        player_id = matched_player['id']
                        player_name = matched_player['name']

                        # Initialize player stats if not exists
                        if player_id not in player_stats:
                            player_stats[player_id] = {
                                'player_id': player_id,
                                'name': player_name,
                                'team': matched_player.get('team_name', 'Unknown'),
                                'role': matched_player.get('player_type', 'Unknown'),
                                'matches': 0,
                                'total_points': 0.0,
                                'performances': []
                            }

                        # Add performance
                        player_stats[player_id]['matches'] += 1
                        player_stats[player_id]['total_points'] += fantasy_points
                        player_stats[player_id]['performances'].append({
                            'match_id': match_id,
                            'team': team,
                            'fantasy_points': fantasy_points,
                            'scorecard_name': scorecard_name,
                            'batting': perf.get('batting', {}),
                            'bowling': perf.get('bowling', {}),
                            'fielding': perf.get('fielding', {})
                        })

                        logger.debug(f"    ✅ {scorecard_name} → {player_name}: {fantasy_points:.2f} pts")
                    else:
                        unmatched_names.add(scorecard_name)
                        logger.debug(f"    ⚠️  {scorecard_name}: No match found")

            except Exception as e:
                logger.error(f"  Error processing {scorecard_file.name}: {e}")
                continue

        # Generate summary
        logger.info("\n" + "="*80)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*80)

        logger.info(f"\n📊 Statistics:")
        logger.info(f"  Scorecards processed: {len(scorecard_files)}")
        logger.info(f"  Players matched: {len(player_stats)}")
        logger.info(f"  Unmatched names: {len(unmatched_names)}")

        if unmatched_names:
            logger.info(f"\n⚠️  Unmatched player names ({len(unmatched_names)}):")
            for name in sorted(list(unmatched_names))[:20]:
                logger.info(f"    - {name}")
            if len(unmatched_names) > 20:
                logger.info(f"    ... and {len(unmatched_names) - 20} more")

        # Show top performers
        if player_stats:
            sorted_players = sorted(
                player_stats.values(),
                key=lambda p: p['total_points'],
                reverse=True
            )

            logger.info(f"\n🏆 Top 10 Performers (2025 Season):")
            for i, player in enumerate(sorted_players[:10], 1):
                logger.info(
                    f"  {i:2d}. {player['name']:25s} - "
                    f"{player['total_points']:6.1f} pts in {player['matches']:2d} matches "
                    f"({player['total_points']/player['matches']:.1f} avg)"
                )

        # Save to file
        output_data = {
            'generated_at': '2026-03-20',  # Will be updated when run
            'season': 2025,
            'total_scorecards': len(scorecard_files),
            'total_players': len(player_stats),
            'unmatched_count': len(unmatched_names),
            'unmatched_names': sorted(list(unmatched_names)),
            'players': list(player_stats.values())
        }

        logger.info(f"\n💾 Saving results to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"✅ Successfully saved stats for {len(player_stats)} players")

        return True

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return False
    finally:
        db.close()


def main():
    """Run the pre-calculation"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success = loop.run_until_complete(process_all_scorecards())
        return 0 if success else 1
    finally:
        loop.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
