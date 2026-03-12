#!/usr/bin/env python3
"""
Weekly Real Data Scraper
=========================
Scrapes actual KNCB match data and integrates with fantasy cricket system.

Replaces simulate_live_teams.py simulation with real scorecard data.

Usage:
    python3 scrape_weekly_real_data.py --round 1 --clubs ACC
    python3 scrape_weekly_real_data.py --round 2 --clubs ACC,VRA --days 7
    python3 scrape_weekly_real_data.py --round 3 --dry-run  # Test without saving
"""

import asyncio
import argparse
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Import our modules
from kncb_html_scraper import KNCBMatchCentreScraper
from scorecard_player_matcher import ScorecardPlayerMatcher

# Import rules (handle hyphenated module name)
try:
    from rules_set_1 import calculate_total_fantasy_points
except ImportError:
    import importlib
    rules_module = importlib.import_module('rules-set-1')
    calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

# Import simulation functions we'll reuse
from simulate_live_teams import (
    get_active_teams,
    get_team_players,
    update_team_scores_in_db,
    store_fantasy_team_player_totals
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# =============================================================================
# CORE SCRAPING LOGIC
# =============================================================================

async def scrape_and_store_performances(
    league_id: str,
    round_number: int,
    clubs: List[str] = None,
    days_back: int = 7,
    dry_run: bool = False
) -> Dict:
    """
    Main workflow: Scrape → Match → Store → Calculate

    Args:
        league_id: League to scrape for
        round_number: Round/week number
        clubs: List of club names to scrape (default: ["ACC"])
        days_back: How many days back to scrape
        dry_run: If True, don't write to database

    Returns:
        Dict with scraping results
    """
    if clubs is None:
        clubs = ["ACC"]

    logger.info("="*80)
    logger.info("🏏 WEEKLY REAL DATA SCRAPER")
    logger.info("="*80)
    logger.info(f"League: {league_id}")
    logger.info(f"Round: {round_number}")
    logger.info(f"Clubs: {', '.join(clubs)}")
    logger.info(f"Days back: {days_back}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("="*80)

    session = Session()
    scraper = KNCBMatchCentreScraper()
    matcher = ScorecardPlayerMatcher(session)

    try:
        all_performances = {}  # player_id -> performance data
        match_count = 0
        player_count = 0

        # 1. SCRAPE matches for each club
        for club_name in clubs:
            logger.info(f"\n🔍 Scraping matches for {club_name}...")

            matches = await scraper.get_recent_matches_for_club(
                club_name,
                days_back=days_back
            )

            logger.info(f"   Found {len(matches)} matches")

            for match_info in matches:
                match_id = match_info['match_id']

                # Check if already processed
                existing = session.execute(text("""
                    SELECT id FROM matches
                    WHERE matchcentre_id = :match_id
                      AND is_processed = true
                """), {'match_id': str(match_id)}).fetchone()

                if existing and not dry_run:
                    logger.info(f"   ⏭️  Match {match_id} already processed")
                    continue

                # Scrape scorecard
                logger.info(f"   📥 Scraping match {match_id}...")
                scorecard = await scraper.scrape_match_scorecard(match_id)

                if not scorecard:
                    logger.warning(f"   ❌ Failed to scrape match {match_id}")
                    continue

                # Extract players
                players = scraper.extract_player_stats(
                    scorecard,
                    club_name,
                    match_info.get('tier', 'tier2')
                )

                logger.info(f"   ✅ Extracted {len(players)} player performances")

                # Match players to database
                matched_count = 0
                for player_data in players:
                    scraped_name = player_data['player_name']

                    # Try to match to database
                    db_player = matcher.match_player(
                        scraped_name,
                        club_filter=club_name
                    )

                    if db_player:
                        player_id = db_player['id']

                        # Store or aggregate performance
                        if player_id in all_performances:
                            # Player played multiple matches - aggregate
                            all_performances[player_id]['performance'] = aggregate_performances(
                                all_performances[player_id]['performance'],
                                player_data
                            )
                            all_performances[player_id]['match_ids'].append(match_id)
                        else:
                            # New player this week
                            all_performances[player_id] = {
                                'performance': player_data,
                                'player_name': db_player['name'],
                                'club_name': club_name,
                                'is_wicket_keeper': db_player['is_wicket_keeper'],
                                'multiplier': db_player['multiplier'],
                                'match_ids': [match_id]
                            }

                        matched_count += 1
                    else:
                        logger.warning(f"      ⚠️  No DB match for '{scraped_name}'")

                logger.info(f"   Matched: {matched_count}/{len(players)} players")

                match_count += 1
                player_count += len(players)

                # Rate limiting
                await asyncio.sleep(1)

        logger.info(f"\n✅ Scraping complete!")
        logger.info(f"   Matches processed: {match_count}")
        logger.info(f"   Total performances: {player_count}")
        logger.info(f"   Unique players matched: {len(all_performances)}")

        # 2. STORE performances in database
        if not dry_run:
            stored_count = store_player_performances(
                all_performances,
                league_id,
                round_number,
                session
            )
            logger.info(f"   ✅ Stored {stored_count} performances")

            # 3. CALCULATE fantasy team scores
            teams = get_active_teams()
            logger.info(f"\n📊 Calculating scores for {len(teams)} fantasy teams...")

            all_team_scores = calculate_team_scores(
                teams,
                all_performances,
                session
            )

            # 4. UPDATE fantasy teams
            update_team_scores_in_db(all_team_scores)

            # 5. UPDATE fantasy team player totals
            store_fantasy_team_player_totals(all_team_scores, round_number)

            logger.info(f"\n✅ ALL UPDATES COMPLETE!")
        else:
            logger.info(f"\n🔍 DRY RUN - No database changes made")

        return {
            'success': True,
            'matches_processed': match_count,
            'total_performances': player_count,
            'unique_players': len(all_performances),
            'dry_run': dry_run
        }

    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        session.close()


def aggregate_performances(perf1: Dict, perf2: Dict) -> Dict:
    """Aggregate two performances (same player, different matches)"""

    # Aggregate batting
    batting1 = perf1.get('batting', {})
    batting2 = perf2.get('batting', {})

    aggregated_batting = {
        'runs': batting1.get('runs', 0) + batting2.get('runs', 0),
        'balls_faced': batting1.get('balls_faced', 0) + batting2.get('balls_faced', 0),
        'fours': batting1.get('fours', 0) + batting2.get('fours', 0),
        'sixes': batting1.get('sixes', 0) + batting2.get('sixes', 0),
    }

    # Aggregate bowling
    bowling1 = perf1.get('bowling', {})
    bowling2 = perf2.get('bowling', {})

    aggregated_bowling = {
        'wickets': bowling1.get('wickets', 0) + bowling2.get('wickets', 0),
        'overs': bowling1.get('overs', 0) + bowling2.get('overs', 0),
        'maidens': bowling1.get('maidens', 0) + bowling2.get('maidens', 0),
        'runs': bowling1.get('runs', 0) + bowling2.get('runs', 0),
    }

    # Aggregate fielding
    fielding1 = perf1.get('fielding', {})
    fielding2 = perf2.get('fielding', {})

    aggregated_fielding = {
        'catches': fielding1.get('catches', 0) + fielding2.get('catches', 0),
        'stumpings': fielding1.get('stumpings', 0) + fielding2.get('stumpings', 0),
        'runouts': fielding1.get('runouts', 0) + fielding2.get('runouts', 0),
    }

    # Recalculate fantasy points for aggregated stats
    result = calculate_total_fantasy_points(
        runs=aggregated_batting['runs'],
        balls_faced=aggregated_batting['balls_faced'],
        is_out=False,  # Can't determine for aggregated
        wickets=aggregated_bowling['wickets'],
        overs=aggregated_bowling['overs'],
        runs_conceded=aggregated_bowling['runs'],
        maidens=aggregated_bowling['maidens'],
        catches=aggregated_fielding['catches'],
        stumpings=aggregated_fielding['stumpings'],
        runouts=aggregated_fielding['runouts'],
        is_wicketkeeper=False  # Will be determined from DB
    )

    return {
        'player_name': perf1['player_name'],
        'batting': aggregated_batting,
        'bowling': aggregated_bowling,
        'fielding': aggregated_fielding,
        'fantasy_points': result['grand_total']
    }


def store_player_performances(
    all_performances: Dict,
    league_id: str,
    round_number: int,
    session: Session
) -> int:
    """
    Store all player performances in player_performances table

    Args:
        all_performances: Dict of player_id -> performance data
        league_id: League ID
        round_number: Round number
        session: Database session

    Returns:
        Number of performances stored
    """
    logger.info("\n💾 Storing player performances...")

    stored_count = 0

    for player_id, data in all_performances.items():
        perf = data['performance']
        multiplier = data['multiplier']
        is_wicket_keeper = data['is_wicket_keeper']

        # Get stats
        batting = perf.get('batting', {})
        bowling = perf.get('bowling', {})
        fielding = perf.get('fielding', {})

        # Calculate base fantasy points
        base_points = perf.get('fantasy_points', 0)

        # Apply player multiplier
        final_points = base_points * multiplier

        # Insert performance
        insert_query = text("""
            INSERT INTO player_performances (
                id, player_id, league_id, round_number,
                runs, balls_faced, is_out,
                wickets, overs_bowled, runs_conceded, maidens,
                catches, stumpings, run_outs,
                base_fantasy_points, multiplier_applied,
                captain_multiplier, final_fantasy_points,
                is_captain, is_vice_captain, is_wicket_keeper,
                match_date, created_at, updated_at
            ) VALUES (
                :id, :player_id, :league_id, :round_number,
                :runs, :balls_faced, false,
                :wickets, :overs, :runs_conceded, :maidens,
                :catches, :stumpings, :runouts,
                :base_points, :multiplier,
                1.0, :final_points,
                false, false, :is_wicket_keeper,
                NOW(), NOW(), NOW()
            )
            ON CONFLICT (player_id, league_id, round_number)
            WHERE league_id IS NOT NULL AND round_number IS NOT NULL
            DO UPDATE SET
                runs = EXCLUDED.runs,
                balls_faced = EXCLUDED.balls_faced,
                wickets = EXCLUDED.wickets,
                overs_bowled = EXCLUDED.overs_bowled,
                runs_conceded = EXCLUDED.runs_conceded,
                maidens = EXCLUDED.maidens,
                catches = EXCLUDED.catches,
                stumpings = EXCLUDED.stumpings,
                run_outs = EXCLUDED.run_outs,
                base_fantasy_points = EXCLUDED.base_fantasy_points,
                multiplier_applied = EXCLUDED.multiplier_applied,
                final_fantasy_points = EXCLUDED.final_fantasy_points,
                updated_at = NOW()
        """)

        session.execute(insert_query, {
            'id': str(uuid.uuid4()),
            'player_id': player_id,
            'league_id': league_id,
            'round_number': round_number,
            'runs': batting.get('runs', 0),
            'balls_faced': batting.get('balls_faced', 0),
            'wickets': bowling.get('wickets', 0),
            'overs': bowling.get('overs', 0.0),
            'runs_conceded': bowling.get('runs', 0),
            'maidens': bowling.get('maidens', 0),
            'catches': fielding.get('catches', 0),
            'stumpings': fielding.get('stumpings', 0),
            'runouts': fielding.get('runouts', 0),
            'base_points': base_points,
            'multiplier': multiplier,
            'final_points': final_points,
            'is_wicket_keeper': is_wicket_keeper
        })

        stored_count += 1

    session.commit()
    return stored_count


def calculate_team_scores(
    teams: List[Dict],
    all_performances: Dict,
    session: Session
) -> List[Dict]:
    """
    Calculate fantasy team scores from player performances

    Args:
        teams: List of fantasy teams
        all_performances: Dict of player_id -> performance data
        session: Database session

    Returns:
        List of team scores
    """
    all_team_scores = []

    for team in teams:
        team_id = team['team_id']
        team_players = get_team_players(team_id)

        team_total = 0.0
        player_scores = []

        for player in team_players:
            player_id = player['player_id']

            if player_id not in all_performances:
                # Player didn't play this week
                continue

            perf_data = all_performances[player_id]
            base_points = perf_data['performance'].get('fantasy_points', 0)
            player_multiplier = perf_data['multiplier']

            # Apply captain/VC multiplier
            if player['is_captain']:
                role_multiplier = 2.0
            elif player['is_vice_captain']:
                role_multiplier = 1.5
            else:
                role_multiplier = 1.0

            # Final points = base × player_multiplier × role_multiplier
            final_points = base_points * player_multiplier * role_multiplier

            team_total += final_points

            player_scores.append({
                'player_id': player_id,
                'player_name': player['name'],
                'base_points': base_points,
                'multiplier': player_multiplier,
                'role_multiplier': role_multiplier,
                'final_points': final_points,
                'is_captain': player['is_captain'],
                'is_vice_captain': player['is_vice_captain']
            })

        all_team_scores.append({
            'team': team,
            'total_points': team_total,
            'player_scores': player_scores
        })

    return all_team_scores


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape real KNCB match data for fantasy cricket'
    )
    parser.add_argument(
        '--round',
        type=int,
        required=True,
        help='Round/week number (e.g., 1, 2, 3)'
    )
    parser.add_argument(
        '--clubs',
        type=str,
        default='ACC',
        help='Comma-separated list of clubs (default: ACC)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='How many days back to scrape (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without saving to database'
    )

    args = parser.parse_args()

    # Parse clubs
    clubs = [c.strip() for c in args.clubs.split(',')]

    # Get active league
    session = Session()
    try:
        league = session.execute(text("""
            SELECT l.id, l.name
            FROM leagues l
            JOIN seasons s ON l.season_id = s.id
            WHERE s.is_active = true
            LIMIT 1
        """)).fetchone()

        if not league:
            logger.error("❌ No active league found")
            sys.exit(1)

        league_id = league[0]
        league_name = league[1]

        logger.info(f"🏆 League: {league_name} ({league_id})")

    finally:
        session.close()

    # Run scraper
    result = asyncio.run(scrape_and_store_performances(
        league_id=league_id,
        round_number=args.round,
        clubs=clubs,
        days_back=args.days,
        dry_run=args.dry_run
    ))

    if result['success']:
        logger.info("\n✅ SUCCESS!")
        sys.exit(0)
    else:
        logger.error(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
