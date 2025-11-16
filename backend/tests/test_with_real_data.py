#!/usr/bin/env python3
"""
Test Scraper with Real Match Data
==================================
This script tests the scraper against REAL matchcentre data
to validate that:

1. Scorecard finding works correctly
2. Data extraction is accurate
3. Fantasy points calculation matches expectations
4. Player matching works

This is a SAFE test - it only reads data, doesn't write to database.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from kncb_html_scraper import KNCBMatchCentreScraper


async def test_single_known_match():
    """
    Test with a single known match to verify scraper works end-to-end

    This will:
    1. Fetch a real scorecard
    2. Extract player stats
    3. Calculate fantasy points
    4. Display results for verification
    """

    print("\n" + "=" * 80)
    print("🏏 TESTING WITH REAL MATCH DATA")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    # Test with a known match ID (you can change this)
    # This should be a recent completed match
    test_match_id = 7254567  # Replace with a real match ID

    print(f"📡 Fetching scorecard for match {test_match_id}...")
    print()

    scorecard = await scraper.scrape_match_scorecard(test_match_id)

    if not scorecard:
        print("❌ Failed to fetch scorecard")
        print()
        print("Possible reasons:")
        print("  - Match ID doesn't exist")
        print("  - Match is not completed yet")
        print("  - Network issues")
        print()
        return False

    print("✅ Scorecard fetched successfully!")
    print()

    # Save raw scorecard for inspection
    with open('test_real_scorecard.json', 'w') as f:
        json.dump(scorecard, f, indent=2)

    print("💾 Raw scorecard saved to: test_real_scorecard.json")
    print()

    # Extract player stats
    print("📊 Extracting player stats...")
    players = scraper.extract_player_stats(scorecard, 'TEST CLUB', 'tier1')

    if not players:
        print("⚠️  No players extracted from scorecard")
        return False

    print(f"✅ Extracted {len(players)} player performances")
    print()

    # Display top performers
    print("=" * 80)
    print("🌟 TOP PERFORMERS")
    print("=" * 80)
    print()

    # Sort by fantasy points
    top_players = sorted(players, key=lambda p: p['fantasy_points'], reverse=True)[:10]

    for i, player in enumerate(top_players, 1):
        name = player['player_name']
        points = player['fantasy_points']

        print(f"{i}. {name} - {points} points")

        # Show breakdown
        batting = player.get('batting', {})
        if batting and batting.get('runs', 0) > 0:
            runs = batting.get('runs', 0)
            balls = batting.get('balls_faced', 0)
            fours = batting.get('fours', 0)
            sixes = batting.get('sixes', 0)
            print(f"   Batting: {runs}({balls}) [{fours}x4, {sixes}x6]")

        bowling = player.get('bowling', {})
        if bowling and bowling.get('wickets', 0) > 0:
            wickets = bowling.get('wickets', 0)
            runs = bowling.get('runs_conceded', 0)
            overs = bowling.get('overs', 0)
            maidens = bowling.get('maidens', 0)
            print(f"   Bowling: {wickets}/{runs} ({overs} ov, {maidens}M)")

        fielding = player.get('fielding', {})
        if fielding:
            catches = fielding.get('catches', 0)
            if catches > 0:
                print(f"   Fielding: {catches} catches")

        print()

    # Save results
    results = {
        'match_id': test_match_id,
        'scraped_at': datetime.now().isoformat(),
        'total_players': len(players),
        'players': players
    }

    with open('test_real_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 80)
    print("💾 Full results saved to: test_real_results.json")
    print("=" * 80)
    print()

    return True


async def test_recent_matches_for_club(club_name='ACC', days_back=7):
    """
    Test fetching recent matches for a club

    This validates:
    1. Match finding works correctly
    2. Can locate scorecards
    3. Date filtering works
    """

    print("\n" + "=" * 80)
    print(f"🏏 TESTING MATCH FINDING FOR {club_name}")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    print(f"📡 Searching for {club_name} matches in last {days_back} days...")
    print()

    matches = await scraper.get_recent_matches_for_club(club_name, days_back=days_back)

    if not matches:
        print(f"⚠️  No matches found for {club_name} in last {days_back} days")
        print()
        print("This could mean:")
        print("  - Club name is incorrect")
        print("  - No matches in this period (off-season?)")
        print("  - Increase days_back parameter")
        print()
        return False

    print(f"✅ Found {len(matches)} matches!")
    print()

    # Display matches
    print("📋 MATCHES FOUND:")
    print("=" * 80)
    print()

    for i, match in enumerate(matches, 1):
        home = match.get('home_club_name')
        away = match.get('away_club_name')
        date = match.get('match_date_time', '')[:10]
        grade = match.get('grade_name', 'Unknown')
        tier = match.get('tier', 'Unknown')
        match_id = match.get('match_id')

        print(f"{i}. {home} vs {away}")
        print(f"   Date: {date}")
        print(f"   Grade: {grade} (Tier: {tier})")
        print(f"   Match ID: {match_id}")
        print()

    # Save match list
    with open('test_matches_found.json', 'w') as f:
        json.dump(matches, f, indent=2)

    print("💾 Match list saved to: test_matches_found.json")
    print("=" * 80)
    print()

    return True


async def main():
    """Run real data tests"""

    print("\n" + "=" * 80)
    print("🧪 SCRAPER REAL DATA TEST SUITE")
    print("=" * 80)
    print()
    print("This will test the scraper against REAL matchcentre data.")
    print("No database writes - read-only testing.")
    print()
    print("=" * 80)

    # Ask user what to test
    print()
    print("Options:")
    print("1. Test single match (fast, detailed)")
    print("2. Test finding recent matches for club")
    print("3. Both")
    print()

    try:
        choice = input("Choose option (1/2/3): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nDefaulting to option 3 (both tests)")
        choice = '3'

    print()

    if choice in ['1', '3']:
        success = await test_single_known_match()
        if not success:
            print("⚠️  Single match test had issues - check output above")

    if choice in ['2', '3']:
        success = await test_recent_matches_for_club('ACC', days_back=14)
        if not success:
            print("⚠️  Match finding test had issues - check output above")

    print("\n" + "=" * 80)
    print("✅ TESTING COMPLETE")
    print("=" * 80)
    print()
    print("Review the output files:")
    print("  - test_real_scorecard.json (raw API response)")
    print("  - test_real_results.json (processed player data)")
    print("  - test_matches_found.json (match list)")
    print()
    print("=" * 80)
    print()


if __name__ == '__main__':
    asyncio.run(main())
