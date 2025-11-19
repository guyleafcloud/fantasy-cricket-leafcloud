#!/usr/bin/env python3
"""
Phase 1a: Mock Server Test
Test complete scraper pipeline with controlled mock data
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set mock mode
os.environ['SCRAPER_MODE'] = 'mock'

from kncb_html_scraper import KNCBMatchCentreScraper
from scraper_config import get_scraper_config, ScraperMode
from database import SessionLocal
from database_models import Player

async def test_mock_server():
    print("="*70)
    print("PHASE 1A: MOCK SERVER TEST")
    print("="*70)
    print("\n✅ Testing with MOCK server (controlled data)\n")

    # Verify mock server is running
    import requests
    try:
        response = requests.get('http://localhost:5001/health', timeout=2)
        health = response.json()
        print(f"🟢 Mock server health check:")
        print(f"   Status: {health.get('status')}")
        print(f"   Message: {health.get('message')}\n")
    except Exception as e:
        print(f"❌ Mock server not responding: {e}")
        print(f"   Start it with: python3 mock_kncb_server.py")
        return False

    # Initialize scraper in mock mode
    config = get_scraper_config(ScraperMode.MOCK)
    scraper = KNCBMatchCentreScraper(config=config)

    # Test scraping
    print(f"{'='*70}")
    print("STEP 1: SCRAPING MOCK DATA")
    print('='*70)

    try:
        # Scrape weekly update for ACC
        print(f"\n📥 Calling scrape_weekly_update(clubs=['ACC'], days_back=7)...")

        results = await scraper.scrape_weekly_update(clubs=['ACC'], days_back=7)

        print(f"\n✅ Scraping complete!")
        print(f"   Total performances: {results.get('total_performances', 0)}")
        print(f"   Clubs scraped: {', '.join(results.get('clubs', []))}")
        print(f"   Scraped at: {results.get('scraped_at')}")

        performances = results.get('performances', [])

        if len(performances) == 0:
            print(f"\n❌ No performances extracted from mock server")
            return False

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Analyze performances
    print(f"\n{'='*70}")
    print("STEP 2: ANALYZING PERFORMANCES")
    print('='*70)

    total_runs = sum(p.get('batting', {}).get('runs', 0) for p in performances)
    total_wickets = sum(p.get('bowling', {}).get('wickets', 0) for p in performances)
    total_catches = sum(p.get('fielding', {}).get('catches', 0) for p in performances)
    total_points = sum(p.get('fantasy_points', 0) for p in performances)

    print(f"\n   Aggregated stats:")
    print(f"   - Total runs: {total_runs}")
    print(f"   - Total wickets: {total_wickets}")
    print(f"   - Total catches: {total_catches}")
    print(f"   - Total fantasy points: {total_points:.1f}")

    # Group by player
    player_totals = {}
    for perf in performances:
        player_id = perf.get('player_id', 'unknown')
        player_name = perf.get('player_name', 'Unknown')

        if player_id not in player_totals:
            player_totals[player_id] = {
                'name': player_name,
                'matches': 0,
                'total_points': 0,
                'total_runs': 0,
                'total_wickets': 0
            }

        player_totals[player_id]['matches'] += 1
        player_totals[player_id]['total_points'] += perf.get('fantasy_points', 0)
        player_totals[player_id]['total_runs'] += perf.get('batting', {}).get('runs', 0)
        player_totals[player_id]['total_wickets'] += perf.get('bowling', {}).get('wickets', 0)

    print(f"\n   Unique players: {len(player_totals)}")

    # Show top 5 performers
    sorted_players = sorted(player_totals.values(),
                           key=lambda x: x['total_points'],
                           reverse=True)

    print(f"\n   Top 5 Performers:")
    for i, player in enumerate(sorted_players[:5], 1):
        print(f"   {i}. {player['name']:25s} - {player['total_points']:6.1f} pts "
              f"({player['matches']} matches, R:{player['total_runs']}, W:{player['total_wickets']})")

    # Test player matching
    print(f"\n{'='*70}")
    print("STEP 3: DATABASE PLAYER MATCHING")
    print('='*70)

    try:
        db = SessionLocal()
        all_players = db.query(Player).all()
        db.close()

        print(f"\n   Database has {len(all_players)} players")

        # Simple name matching test
        matched = 0
        for perf in performances[:10]:  # Test first 10
            player_name = perf.get('player_name', '')
            normalized = player_name.lower().replace(' ', '').replace('.', '')

            for db_player in all_players:
                db_normalized = db_player.name.lower().replace(' ', '').replace('.', '')
                if normalized in db_normalized or db_normalized in normalized:
                    matched += 1
                    break

        print(f"   Sample matching (first 10): {matched}/10 matched")

    except Exception as e:
        print(f"   ⚠️  Database matching skipped: {e}")

    # Test points calculation
    print(f"\n{'='*70}")
    print("STEP 4: POINTS CALCULATION VALIDATION")
    print('='*70)

    # Pick one performance and verify calculation
    if performances:
        sample = performances[0]
        print(f"\n   Sample performance (manual verification):")
        print(f"   Player: {sample.get('player_name')}")
        print(f"   Batting: {sample.get('batting', {}).get('runs', 0)} runs, "
              f"{sample.get('batting', {}).get('balls_faced', 0)} balls")
        print(f"   Bowling: {sample.get('bowling', {}).get('wickets', 0)} wickets, "
              f"{sample.get('bowling', {}).get('overs_bowled', 0)} overs")
        print(f"   Fielding: {sample.get('fielding', {}).get('catches', 0)} catches")
        print(f"   Fantasy Points: {sample.get('fantasy_points', 0):.2f}")

        # Check if rules-set-1.py was used
        breakdown = sample.get('points_breakdown', {})
        if breakdown:
            print(f"\n   Points breakdown:")
            for category, points in breakdown.items():
                if isinstance(points, dict):
                    print(f"   - {category.capitalize()}: {points.get('total', 0):.1f}")

    # Success criteria
    print(f"\n{'='*70}")
    print("SUCCESS CRITERIA")
    print('='*70)

    criteria = [
        ("Mock server responding", True),
        ("Scraper completed without errors", results.get('total_performances', 0) > 0),
        ("10+ performances extracted", len(performances) >= 10),
        ("Players have fantasy points", total_points > 0),
        ("Fantasy points > 0 for sample", performances[0].get('fantasy_points', 0) > 0 if performances else False),
    ]

    all_passed = True
    for criterion, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
        if not passed:
            all_passed = False

    print(f"\n{'='*70}")
    if all_passed:
        print("✅ PHASE 1A: PASSED")
        print("   Mock server pipeline working correctly")
        print("   Ready to proceed to Phase 1b (Real API test)")
    else:
        print("❌ PHASE 1A: FAILED")
        print("   Fix issues before proceeding")
    print('='*70)

    return all_passed

if __name__ == "__main__":
    print("\n🏏 Starting Phase 1a: Mock Server Test\n")

    try:
        result = asyncio.run(test_mock_server())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
