#!/usr/bin/env python3
"""
Test Multiple 2025 Scorecards
==============================
Test the scraper with multiple real 2025 scorecard URLs.
"""

import asyncio
import json
from kncb_html_scraper import KNCBMatchCentreScraper

# Real 2025 scorecard URLs from Week 1 and Week 2
TEST_MATCHES = [
    {
        'match_id': 7324739,
        'url': 'https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194',
        'description': 'ACC 1 vs HBS (Week 1)'
    },
    {
        'match_id': 7331235,
        'url': 'https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394',
        'description': 'Kampong 1 vs ACC 1 (Week 1)'
    },
    {
        'match_id': 7331321,
        'url': 'https://matchcentre.kncb.nl/match/134453-7331321/scorecard/?period=2852372',
        'description': 'VRA 4 vs ACC 2 (Week 1)'
    },
]

async def test_multiple_scorecards():
    """Test parsing multiple 2025 scorecards"""

    print("\n" + "=" * 80)
    print("🏏 TESTING MULTIPLE 2025 SCORECARDS")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    results = []

    for test_match in TEST_MATCHES:
        print(f"\n{'='*80}")
        print(f"📋 {test_match['description']}")
        print(f"{'='*80}")
        print(f"URL: {test_match['url']}")
        print()

        match_id = test_match['match_id']

        # Scrape scorecard
        scorecard = await scraper.scrape_match_scorecard(match_id)

        if scorecard:
            print(f"✅ Scorecard scraped successfully!")

            # Extract player stats
            players = scraper.extract_player_stats(scorecard, club_name="ACC", tier="tier2")

            print(f"📊 Extracted {len(players)} player performances")

            # Show top performers
            if players:
                top_batting = sorted(players, key=lambda x: x.get('batting', {}).get('runs', 0), reverse=True)[:3]
                top_bowling = sorted(players, key=lambda x: x.get('bowling', {}).get('wickets', 0), reverse=True)[:3]

                print("\n🏏 Top 3 Batting:")
                for i, player in enumerate(top_batting, 1):
                    batting = player.get('batting', {})
                    if batting.get('runs', 0) > 0:
                        print(f"   {i}. {player['player_name']}: {batting['runs']}r ({batting.get('balls_faced', 0)}b) "
                              f"- {player['fantasy_points']} pts")

                print("\n🎯 Top 3 Bowling:")
                for i, player in enumerate(top_bowling, 1):
                    bowling = player.get('bowling', {})
                    if bowling.get('wickets', 0) > 0:
                        print(f"   {i}. {player['player_name']}: {bowling['wickets']}/{bowling.get('runs', 0)} "
                              f"in {bowling.get('overs', 0)}ov - {player['fantasy_points']} pts")

            results.append({
                'match_id': match_id,
                'description': test_match['description'],
                'success': True,
                'players_found': len(players),
                'total_fantasy_points': sum(p['fantasy_points'] for p in players)
            })

        else:
            print(f"❌ Failed to scrape scorecard")
            results.append({
                'match_id': match_id,
                'description': test_match['description'],
                'success': False
            })

        # Rate limit
        await asyncio.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\n✅ Successfully scraped: {successful}/{total} matches")

    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {result['description']}")
        if result['success']:
            print(f"   Players: {result['players_found']}")
            print(f"   Total fantasy points: {result['total_fantasy_points']}")

    print("\n" + "=" * 80)

    if successful == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n📝 Next steps:")
        print("1. Deploy updated scraper to production")
        print("2. Create database integration function")
        print("3. Set up weekly automation for 2026 season")
    else:
        print("⚠️  Some tests failed - review logs above")

    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(test_multiple_scorecards())
