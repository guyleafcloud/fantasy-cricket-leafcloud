#!/usr/bin/env python3
"""
Test Scraper with Mock and Production Modes
============================================
Demonstrates scraper working in both modes and validates configuration.
"""

import asyncio
import logging
from scraper_config import get_scraper_config, ScraperMode, print_config
from kncb_html_scraper import KNCBMatchCentreScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mock_mode():
    """Test scraper in mock mode"""
    print("\n" + "="*80)
    print("🧪 TEST 1: MOCK MODE (Test Data)")
    print("="*80)

    # Get mock configuration
    config = get_scraper_config(ScraperMode.MOCK)
    print_config(config)

    # Initialize scraper with mock config
    scraper = KNCBMatchCentreScraper(config=config)

    print("\n📋 Fetching matches from MOCK server...")
    try:
        matches = await scraper.get_recent_matches_for_club(
            club_name="VRA",
            days_back=30,
            season_id=19
        )

        if matches:
            print(f"✅ Found {len(matches)} mock matches")
            print(f"\n📊 Sample mock matches:")
            for i, match in enumerate(matches[:3]):
                home = match.get('home_club_name', 'Unknown')
                away = match.get('away_club_name', 'Unknown')
                grade = match.get('grade_name', 'Unknown')
                print(f"   {i+1}. {home} vs {away} - {grade}")

            # Test scraping one match
            if len(matches) > 0:
                match_id = matches[0].get('match_id')
                print(f"\n📥 Scraping mock scorecard for match {match_id}...")

                scorecard = await scraper.scrape_match_scorecard(match_id)
                if scorecard:
                    print(f"✅ Got mock scorecard")
                    print(f"   Innings: {len(scorecard.get('innings', []))}")

                    # Extract player stats
                    tier = matches[0].get('tier', 'tier2')
                    players = scraper.extract_player_stats(scorecard, "VRA", tier)

                    if players:
                        print(f"   Players extracted: {len(players)}")

                        # Show top scorer
                        players_sorted = sorted(
                            players,
                            key=lambda p: p.get('fantasy_points', 0),
                            reverse=True
                        )
                        if len(players_sorted) > 0:
                            top = players_sorted[0]
                            name = top.get('name', 'Unknown')
                            points = top.get('fantasy_points', 0)
                            print(f"   Top scorer: {name} - {points:.1f} pts")

            return True
        else:
            print("⚠️  No mock matches found")
            return False

    except Exception as e:
        print(f"❌ Error in mock mode: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_production_config():
    """Test production configuration (don't actually fetch data)"""
    print("\n" + "="*80)
    print("🌐 TEST 2: PRODUCTION MODE (Configuration Only)")
    print("="*80)

    # Get production configuration
    config = get_scraper_config(ScraperMode.PRODUCTION)
    print_config(config)

    # Initialize scraper with production config
    scraper = KNCBMatchCentreScraper(config=config)

    print("\n✅ Production scraper initialized")
    print(f"   API URL: {scraper.kncb_api_url}")
    print(f"   Match Centre: {scraper.matchcentre_url}")
    print("\n⚠️  Not fetching real data in this test")
    print("   Use this configuration when ready for production scraping")

    return True


def test_default_mode():
    """Test default initialization (should use production)"""
    print("\n" + "="*80)
    print("🔧 TEST 3: DEFAULT MODE (No config provided)")
    print("="*80)

    # Initialize without config (should default to production)
    scraper = KNCBMatchCentreScraper()

    print(f"✅ Scraper initialized in default mode")
    print(f"   Mode: {scraper.mode}")
    print(f"   API URL: {scraper.kncb_api_url}")

    if scraper.mode == "production":
        print("   ✅ Correctly defaulted to production mode")
        return True
    else:
        print("   ⚠️  Unexpected mode")
        return False


async def main():
    """Run all tests"""
    print("="*80)
    print("🧪 SCRAPER MODE CONFIGURATION TESTS")
    print("="*80)

    results = []

    # Test 1: Mock mode with actual data fetching
    result1 = await test_mock_mode()
    results.append(("Mock Mode", result1))

    # Test 2: Production configuration (no fetching)
    result2 = test_production_config()
    results.append(("Production Config", result2))

    # Test 3: Default mode
    result3 = test_default_mode()
    results.append(("Default Mode", result3))

    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("  1. Use mock mode for testing: config = get_scraper_config(ScraperMode.MOCK)")
        print("  2. Use production mode for real data: config = get_scraper_config(ScraperMode.PRODUCTION)")
        print("  3. Or set environment: export SCRAPER_MODE=mock")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
