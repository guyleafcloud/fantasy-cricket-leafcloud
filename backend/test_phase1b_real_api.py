#!/usr/bin/env python3
"""
Phase 1b: Real API Test
Test scraper with production KNCB API and real 2025 data
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Ensure production mode
os.environ['SCRAPER_MODE'] = 'production'

from kncb_html_scraper import KNCBMatchCentreScraper
from scraper_config import get_scraper_config, ScraperMode

# Your provided URLs to check against
WEEK1_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394",
    "https://matchcentre.kncb.nl/match/134453-7336247/scorecard/?period=2880895",
    "https://matchcentre.kncb.nl/match/134453-7323305/scorecard/?period=2904132",
    "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194",
    "https://matchcentre.kncb.nl/match/134453-7329152/scorecard/?period=2912677",
    "https://matchcentre.kncb.nl/match/134453-7326066/scorecard/?period=2850306",
    "https://matchcentre.kncb.nl/match/134453-7332092/scorecard/?period=2843768",
    "https://matchcentre.kncb.nl/match/134453-7324743/scorecard/?period=2883358",
    "https://matchcentre.kncb.nl/match/134453-7324797/scorecard/?period=2883096",
]

WEEK2_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7336254/scorecard/?period=2911963",
    "https://matchcentre.kncb.nl/match/134453-7331237/scorecard/?period=2912048",
    "https://matchcentre.kncb.nl/match/134453-7329153/scorecard/?period=2943897",
    "https://matchcentre.kncb.nl/match/134453-7332269/scorecard/?period=2905571",
    "https://matchcentre.kncb.nl/match/134453-7326162/scorecard/?period=2882990",
    "https://matchcentre.kncb.nl/match/134453-7324749/scorecard/?period=2946803",
    "https://matchcentre.kncb.nl/match/134453-7323338/scorecard/?period=3100381",
    "https://matchcentre.kncb.nl/match/134453-7323364/scorecard/?period=2883312",
    "https://matchcentre.kncb.nl/match/134453-7330958/scorecard/?period=2971631",
]

def extract_match_ids(urls):
    """Extract match IDs from URLs"""
    match_ids = []
    for url in urls:
        # Format: https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394
        parts = url.split('/')
        for part in parts:
            if '-' in part and part.startswith('134453'):
                match_ids.append(part)
                break
    return match_ids

async def test_real_api():
    print("="*70)
    print("PHASE 1B: REAL API TEST")
    print("="*70)
    print("\n🌐 Testing with PRODUCTION KNCB API (real 2025 data)\n")

    print("⚠️  WARNING: This will make real API requests to KNCB")
    print("   - May be rate-limited if too many requests")
    print("   - Will take longer than mock server")
    print("   - Tests actual 2025 scorecard format\n")

    # Extract match IDs from your URLs
    week1_match_ids = extract_match_ids(WEEK1_URLS)
    week2_match_ids = extract_match_ids(WEEK2_URLS)
    all_expected_matches = set(week1_match_ids + week2_match_ids)

    print(f"📋 Expected matches from your URLs:")
    print(f"   Week 1: {len(week1_match_ids)} matches")
    print(f"   Week 2: {len(week2_match_ids)} matches")
    print(f"   Total: {len(all_expected_matches)} unique matches\n")

    # Initialize scraper in production mode
    config = get_scraper_config(ScraperMode.PRODUCTION)
    scraper = KNCBMatchCentreScraper(config=config)

    # Test scraping
    print(f"{'='*70}")
    print("STEP 1: SCRAPING REAL KNCB API")
    print('='*70)

    try:
        # Scrape last 365 days (full 2025 season)
        print(f"\n📥 Calling scrape_weekly_update(clubs=['ACC'], days_back=365)...")
        print(f"   This will fetch ACC matches from entire 2025 season")
        print(f"   Estimated time: 2-5 minutes (checking many matches)...\n")

        start_time = datetime.now()
        results = await scraper.scrape_weekly_update(clubs=['ACC'], days_back=365)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Scraping complete! (took {duration:.1f} seconds)")
        print(f"   Total performances: {results.get('total_performances', 0)}")
        print(f"   Clubs scraped: {', '.join(results.get('clubs', []))}")
        print(f"   Scraped at: {results.get('scraped_at')}")

        performances = results.get('performances', [])

        if len(performances) == 0:
            print(f"\n⚠️  No performances extracted")
            print(f"   Possible reasons:")
            print(f"   - No ACC matches in last 14 days")
            print(f"   - API access issues")
            print(f"   - Wrong club name or entity ID")
            return False

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check which of your URLs were found
    print(f"\n{'='*70}")
    print("STEP 2: CHECKING YOUR PROVIDED URLS")
    print('='*70)

    scraped_match_ids = set()
    for perf in performances:
        match_id = perf.get('match_id')
        if match_id:
            # Convert to string format that matches URL format
            scraped_match_ids.add(str(match_id))

    # Also check matchcentre_id format
    for perf in performances:
        match_id = str(perf.get('match_id', ''))
        if match_id:
            # Try to match against expected formats
            for expected in all_expected_matches:
                if match_id in expected or expected.endswith(match_id):
                    scraped_match_ids.add(expected)

    found_matches = all_expected_matches.intersection(scraped_match_ids)
    missing_matches = all_expected_matches - scraped_match_ids

    print(f"\n   Your URLs matched: {len(found_matches)}/{len(all_expected_matches)}")

    if found_matches:
        print(f"\n   ✅ Found matches:")
        for match_id in sorted(found_matches):
            print(f"      - {match_id}")

    if missing_matches:
        print(f"\n   ⚠️  Not found (may be outside 14 day window):")
        for match_id in sorted(list(missing_matches)[:5]):
            print(f"      - {match_id}")
        if len(missing_matches) > 5:
            print(f"      ... and {len(missing_matches) - 5} more")

    # Analyze performances
    print(f"\n{'='*70}")
    print("STEP 3: ANALYZING PERFORMANCES")
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
        player_id = perf.get('player_id', perf.get('player_name', 'unknown'))
        player_name = perf.get('player_name', 'Unknown')

        if player_id not in player_totals:
            player_totals[player_id] = {
                'name': player_name,
                'matches': 0,
                'total_points': 0,
                'total_runs': 0,
                'total_wickets': 0,
                'total_catches': 0
            }

        player_totals[player_id]['matches'] += 1
        player_totals[player_id]['total_points'] += perf.get('fantasy_points', 0)
        player_totals[player_id]['total_runs'] += perf.get('batting', {}).get('runs', 0)
        player_totals[player_id]['total_wickets'] += perf.get('bowling', {}).get('wickets', 0)
        player_totals[player_id]['total_catches'] += perf.get('fielding', {}).get('catches', 0)

    print(f"\n   Unique players: {len(player_totals)}")

    # Show top 10 performers
    sorted_players = sorted(player_totals.values(),
                           key=lambda x: x['total_points'],
                           reverse=True)

    print(f"\n   Top 10 Performers (last 14 days):")
    for i, player in enumerate(sorted_players[:10], 1):
        print(f"   {i:2d}. {player['name']:25s} - {player['total_points']:6.1f} pts "
              f"(R:{player['total_runs']:3d}, W:{player['total_wickets']:2d}, C:{player['total_catches']:2d})")

    # Manual verification sample
    print(f"\n{'='*70}")
    print("STEP 4: MANUAL VERIFICATION SAMPLE")
    print('='*70)

    if performances and sorted_players:
        top_player = sorted_players[0]
        print(f"\n   🔍 Top performer to verify manually:")
        print(f"      Name: {top_player['name']}")
        print(f"      Matches: {top_player['matches']}")
        print(f"      Total runs: {top_player['total_runs']}")
        print(f"      Total wickets: {top_player['total_wickets']}")
        print(f"      Total catches: {top_player['total_catches']}")
        print(f"      Fantasy Points: {top_player['total_points']:.2f}")

        # Find one of their performances to show detail
        for perf in performances:
            if perf.get('player_name') == top_player['name']:
                print(f"\n   Sample match performance:")
                print(f"      Match ID: {perf.get('match_id')}")
                print(f"      Date: {perf.get('match_date')}")
                print(f"      Runs: {perf.get('batting', {}).get('runs', 0)} off {perf.get('batting', {}).get('balls_faced', 0)} balls")
                print(f"      Wickets: {perf.get('bowling', {}).get('wickets', 0)} in {perf.get('bowling', {}).get('overs_bowled', 0)} overs")
                print(f"      Points: {perf.get('fantasy_points', 0):.2f}")
                break

    # Success criteria
    print(f"\n{'='*70}")
    print("SUCCESS CRITERIA")
    print('='*70)

    criteria = [
        ("Real API responded", results.get('total_performances', 0) > 0),
        ("Performances extracted", len(performances) > 0),
        ("Players have fantasy points", total_points > 0),
        ("Multiple players found", len(player_totals) > 1),
        ("Realistic stats", total_runs > 0 and (total_wickets > 0 or total_catches > 0)),
    ]

    all_passed = True
    for criterion, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
        if not passed:
            all_passed = False

    # Additional insights
    print(f"\n{'='*70}")
    print("INSIGHTS & RECOMMENDATIONS")
    print('='*70)

    if len(found_matches) == 0:
        print(f"\n   ⚠️  None of your provided URLs were found")
        print(f"   Possible reasons:")
        print(f"   - Matches are older than 14 days")
        print(f"   - Try increasing days_back parameter")
        print(f"   - Match IDs may have different format in API")
    elif len(found_matches) < len(all_expected_matches):
        print(f"\n   ℹ️  Some matches not found ({len(missing_matches)} missing)")
        print(f"   - These may be outside the 14-day window")
        print(f"   - Week 1-2 URLs might be from earlier in season")
        print(f"   - Try: scrape_weekly_update(clubs=['ACC'], days_back=365)")
    else:
        print(f"\n   ✅ All your provided URLs found!")
        print(f"   - Scraper correctly captures 2025 format")
        print(f"   - Ready for full Week 1-2 testing")

    print(f"\n{'='*70}")
    if all_passed:
        print("✅ PHASE 1B: PASSED")
        print("   Real API integration working!")
        if len(found_matches) > 0:
            print("   Some of your URLs validated!")
        print("   Ready to proceed to Phase 1c (verify all URLs)")
    else:
        print("❌ PHASE 1B: FAILED")
        print("   Need to resolve API issues before proceeding")
    print('='*70)

    return all_passed

if __name__ == "__main__":
    print("\n🏏 Starting Phase 1b: Real API Test\n")
    print("⏱️  This may take 1-3 minutes (real API calls)...\n")

    try:
        result = asyncio.run(test_real_api())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
