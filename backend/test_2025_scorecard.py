#!/usr/bin/env python3
"""
Test 2025 Scorecard Parsing
============================
Test the existing scraper infrastructure with a real 2025 scorecard URL.
"""

import asyncio
import json
from kncb_html_scraper import KNCBMatchCentreScraper

# One of the real 2025 scorecard URLs from the user
TEST_URL = "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194"

async def test_2025_scorecard():
    """Test parsing a 2025 scorecard"""

    print("\n" + "=" * 80)
    print("🏏 TESTING 2025 SCORECARD PARSER")
    print("=" * 80)
    print(f"Test URL: {TEST_URL}")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    # Extract match ID from URL
    # URL format: https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194
    # Match ID is 7324739
    match_id = 7324739

    print(f"📡 Testing scraper.scrape_match_scorecard({match_id})...")
    print()

    # Test the main scraper method
    scorecard = await scraper.scrape_match_scorecard(match_id)

    if scorecard:
        print("✅ Scorecard scraped successfully!")
        print()
        print("📋 SCORECARD DATA STRUCTURE:")
        print(f"   Keys: {list(scorecard.keys())}")
        print()

        # Save raw scorecard
        with open('test_2025_scorecard_raw.json', 'w') as f:
            json.dump(scorecard, f, indent=2)
        print("💾 Raw scorecard saved to: test_2025_scorecard_raw.json")
        print()

        # Check innings data
        if 'innings' in scorecard:
            print(f"📊 Found {len(scorecard['innings'])} innings")
            for i, innings in enumerate(scorecard['innings'], 1):
                print(f"\n   Innings {i}:")
                print(f"      Batting entries: {len(innings.get('batting', []))}")
                print(f"      Bowling entries: {len(innings.get('bowling', []))}")
                print(f"      Fielding entries: {len(innings.get('fielding', []))}")

                # Show sample batting
                if innings.get('batting'):
                    print(f"\n      Sample batting (first 3):")
                    for batter in innings['batting'][:3]:
                        print(f"         - {batter}")

                # Show sample bowling
                if innings.get('bowling'):
                    print(f"\n      Sample bowling (first 3):")
                    for bowler in innings['bowling'][:3]:
                        print(f"         - {bowler}")

        # Test player stats extraction
        print("\n" + "=" * 80)
        print("🎯 TESTING extract_player_stats()")
        print("=" * 80)

        players = scraper.extract_player_stats(scorecard, club_name="ACC", tier="tier2")

        if players:
            print(f"\n✅ Extracted {len(players)} player performances")
            print()
            print("👥 Sample player performances (first 5):")
            for i, player in enumerate(players[:5], 1):
                print(f"\n   {i}. {player.get('player_name', 'Unknown')}")
                print(f"      Batting: {player.get('batting', {})}")
                print(f"      Bowling: {player.get('bowling', {})}")
                print(f"      Fielding: {player.get('fielding', {})}")
                print(f"      Fantasy points: {player.get('fantasy_points', 0)}")

            # Save processed players
            with open('test_2025_players_extracted.json', 'w') as f:
                json.dump(players, f, indent=2)
            print("\n💾 Extracted players saved to: test_2025_players_extracted.json")
        else:
            print("\n⚠️  No players extracted from scorecard")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)

    else:
        print("❌ Failed to scrape scorecard")
        print()
        print("🔍 TROUBLESHOOTING:")
        print("   1. Check if API endpoint is accessible")
        print("   2. Check if HTML fallback works")
        print("   3. Check if match ID is valid")


if __name__ == "__main__":
    asyncio.run(test_2025_scorecard())
