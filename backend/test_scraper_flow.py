#!/usr/bin/env python3
"""
Test Scraper Flow
=================
Quick test to verify the scraper can find recent ACC matches
and extract player performance data.
"""

import asyncio
import json
import logging
from datetime import datetime
from kncb_html_scraper import KNCBMatchCentreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_recent_matches():
    """Test scraping recent ACC matches"""

    print("\n" + "=" * 80)
    print("🏏 TESTING ACC MATCH SCRAPER")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    try:
        logger.info("📡 Scraping ACC matches from last 7 days...")

        result = await scraper.scrape_weekly_update(
            clubs=['ACC'],
            days_back=7
        )

        matches = result.get('matches', [])

        print()
        print("=" * 80)
        print(f"✅ SCRAPE COMPLETE")
        print("=" * 80)
        print(f"   Matches found: {len(matches)}")
        print()

        if matches:
            print("📋 MATCH SUMMARY:")
            print()

            for i, match in enumerate(matches[:3], 1):  # Show first 3
                print(f"   {i}. {match.get('match_title', 'Unknown')}")
                print(f"      Date: {match.get('match_date', 'Unknown')}")
                print(f"      URL: {match.get('scorecard_url', 'Unknown')}")
                print(f"      Players found: {len(match.get('player_performances', []))}")
                print()

                # Show sample players
                perfs = match.get('player_performances', [])[:5]
                if perfs:
                    print(f"      Sample player performances:")
                    for perf in perfs:
                        name = perf.get('player_name', 'Unknown')
                        club = perf.get('club', 'Unknown')
                        runs = perf.get('runs', 0)
                        wickets = perf.get('wickets', 0)
                        print(f"         - {name} ({club}): {runs} runs, {wickets} wkts")
                    print()

        else:
            print("⚠️  No matches found in last 7 days")
            print("   This might be off-season or no recent matches")
            print()

        # Save result to file for inspection
        output_file = 'test_scraper_output.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print("=" * 80)
        print(f"💾 Full output saved to: {output_file}")
        print("=" * 80)
        print()

        return result

    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_recent_matches())
