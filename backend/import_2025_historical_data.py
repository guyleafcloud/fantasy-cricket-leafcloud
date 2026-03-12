#!/usr/bin/env python3
"""
Import 2025 Historical Data
============================
Import real 2025 scorecard data for validation and testing.

This script:
1. Scrapes 136 real 2025 matches (full season, all ACC teams)
2. Matches players to database
3. Calculates fantasy points
4. Generates validation report
5. Optionally stores in database

Purpose: Validate the entire system works with real data before 2026 season.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kncb_html_scraper import KNCBMatchCentreScraper
from scorecard_player_matcher import ScorecardPlayerMatcher
from acc_2025_matches import ALL_2025_MATCHES, MATCH_COUNTS, TOTAL_MATCHES

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# =============================================================================
# IMPORT LOGIC
# =============================================================================

async def import_historical_matches(save_to_db: bool = False) -> Dict:
    """
    Import and validate all 2025 matches

    Args:
        save_to_db: If True, save to database. If False, just validate.

    Returns:
        Validation report dict
    """

    print("="*80)
    print("📚 IMPORTING 2025 HISTORICAL DATA")
    print("="*80)
    print(f"Total matches: {TOTAL_MATCHES}")
    print(f"Team breakdown:")
    for team, count in MATCH_COUNTS.items():
        print(f"   {team}: {count} matches")
    print(f"Save to database: {save_to_db}")
    print("="*80)
    print()

    session = Session()
    scraper = KNCBMatchCentreScraper()
    matcher = ScorecardPlayerMatcher(session)

    # Results tracking
    results = {
        'total_matches': TOTAL_MATCHES,
        'successful_scrapes': 0,
        'failed_scrapes': 0,
        'total_players_extracted': 0,
        'total_players_matched': 0,
        'total_players_unmatched': 0,
        'match_rate': 0.0,
        'matches': [],
        'all_unmatched_players': [],
        'team_stats': {},  # Track stats per team
        'errors': []
    }

    try:
        for idx, match_info in enumerate(ALL_2025_MATCHES, 1):
            match_id = match_info['match_id']
            team = match_info['team']

            print(f"\n{'='*80}")
            print(f"📋 Match {idx}/{TOTAL_MATCHES}: {team}")
            print(f"   ID: {match_id}")
            print(f"{'='*80}")

            # Scrape scorecard
            print(f"   📥 Scraping scorecard...")
            scorecard = await scraper.scrape_match_scorecard(match_id)

            if not scorecard:
                print(f"   ❌ Failed to scrape")
                results['failed_scrapes'] += 1
                results['errors'].append(f"Failed to scrape match {match_id}: {team}")
                continue

            results['successful_scrapes'] += 1

            # Extract players - determine tier based on team name
            tier = "tier2"  # Default
            if "U13" in team or "U15" in team or "U17" in team:
                tier = "youth"
            elif "ZAMI" in team:
                tier = "women"

            players = scraper.extract_player_stats(scorecard, "ACC", tier)
            print(f"   ✅ Extracted {len(players)} players")
            results['total_players_extracted'] += len(players)

            # Match players to database
            match_results = []
            matched_count = 0
            unmatched_players = []

            for player_data in players:
                scraped_name = player_data['player_name']

                # Try to match
                db_player = matcher.match_player(scraped_name, club_filter="ACC")

                if db_player:
                    matched_count += 1
                    match_results.append({
                        'scraped_name': scraped_name,
                        'matched': True,
                        'db_name': db_player['name'],
                        'db_id': db_player['id'],
                        'fantasy_points': player_data['fantasy_points'],
                        'stats': {
                            'runs': player_data.get('batting', {}).get('runs', 0),
                            'wickets': player_data.get('bowling', {}).get('wickets', 0),
                            'catches': player_data.get('fielding', {}).get('catches', 0)
                        }
                    })
                else:
                    unmatched_players.append(scraped_name)
                    match_results.append({
                        'scraped_name': scraped_name,
                        'matched': False,
                        'fantasy_points': player_data['fantasy_points'],
                        'stats': {
                            'runs': player_data.get('batting', {}).get('runs', 0),
                            'wickets': player_data.get('bowling', {}).get('wickets', 0),
                            'catches': player_data.get('fielding', {}).get('catches', 0)
                        }
                    })

            results['total_players_matched'] += matched_count
            results['total_players_unmatched'] += len(unmatched_players)
            results['all_unmatched_players'].extend(unmatched_players)

            # Track stats per team
            if team not in results['team_stats']:
                results['team_stats'][team] = {
                    'matches': 0,
                    'players_extracted': 0,
                    'players_matched': 0,
                    'players_unmatched': 0
                }

            results['team_stats'][team]['matches'] += 1
            results['team_stats'][team]['players_extracted'] += len(players)
            results['team_stats'][team]['players_matched'] += matched_count
            results['team_stats'][team]['players_unmatched'] += len(unmatched_players)

            match_rate = (matched_count / len(players) * 100) if players else 0
            print(f"   👥 Matched: {matched_count}/{len(players)} ({match_rate:.1f}%)")

            if unmatched_players:
                print(f"   ⚠️  Unmatched: {', '.join(unmatched_players)}")

            # Store match result
            results['matches'].append({
                'match_id': match_id,
                'team': team,
                'success': True,
                'players_extracted': len(players),
                'players_matched': matched_count,
                'players_unmatched': len(unmatched_players),
                'match_rate': match_rate,
                'unmatched_names': unmatched_players,
                'player_results': match_results
            })

            # Rate limiting - 2 seconds between requests
            await asyncio.sleep(2)

        # Calculate overall stats
        if results['total_players_extracted'] > 0:
            results['match_rate'] = (
                results['total_players_matched'] / results['total_players_extracted'] * 100
            )

        # Generate summary report
        print_summary_report(results)

        # Save detailed report
        save_report(results)

        # Optionally save to database
        if save_to_db:
            print("\n💾 Saving to database...")
            # TODO: Implement database storage
            print("   ⚠️  Database storage not yet implemented")

        return results

    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
        return results
    finally:
        session.close()


def print_summary_report(results: Dict):
    """Print summary validation report"""

    print("\n" + "="*80)
    print("📊 VALIDATION REPORT")
    print("="*80)

    print(f"\n🏏 SCRAPING RESULTS:")
    print(f"   Total matches: {results['total_matches']}")
    print(f"   Successful: {results['successful_scrapes']}")
    print(f"   Failed: {results['failed_scrapes']}")
    print(f"   Success rate: {results['successful_scrapes']/results['total_matches']*100:.1f}%")

    print(f"\n👥 PLAYER MATCHING:")
    print(f"   Total players extracted: {results['total_players_extracted']}")
    print(f"   Matched to database: {results['total_players_matched']}")
    print(f"   Unmatched: {results['total_players_unmatched']}")
    print(f"   Overall match rate: {results['match_rate']:.1f}%")

    # Team-level breakdown
    if results.get('team_stats'):
        print(f"\n📋 MATCH RATE BY TEAM:")
        for team in sorted(results['team_stats'].keys()):
            stats = results['team_stats'][team]
            team_rate = (stats['players_matched'] / stats['players_extracted'] * 100) if stats['players_extracted'] > 0 else 0
            print(f"   {team:12} {team_rate:5.1f}% ({stats['players_matched']:3}/{stats['players_extracted']:3} players, {stats['matches']:2} matches)")

    if results['all_unmatched_players']:
        # Count unique unmatched players
        unique_unmatched = list(set(results['all_unmatched_players']))
        print(f"\n⚠️  UNIQUE UNMATCHED PLAYERS ({len(unique_unmatched)}):")
        for name in sorted(unique_unmatched):
            count = results['all_unmatched_players'].count(name)
            print(f"   - {name} (appeared in {count} match{'es' if count > 1 else ''})")

    if results['errors']:
        print(f"\n❌ ERRORS ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   - {error}")

    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80)


def save_report(results: Dict):
    """Save detailed report to JSON file"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'2025_historical_import_report_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed report saved to: {filename}")


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import 2025 historical data for validation'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to database (default: just validate)'
    )

    args = parser.parse_args()

    result = asyncio.run(import_historical_matches(save_to_db=args.save))

    if result['failed_scrapes'] == 0 and result['match_rate'] > 70:
        print("\n✅ Validation successful!")
        return 0
    else:
        print("\n⚠️  Validation completed with issues")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
