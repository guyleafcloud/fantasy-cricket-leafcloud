#!/usr/bin/env python3
"""
Test Scorecard Scraping
=======================
Test if we can access and scrape a single scorecard page.
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_scorecard_scrape():
    """Test scraping a single scorecard"""

    # Test URL provided by user
    test_url = "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194"

    print(f"🏏 Testing scorecard scraping")
    print(f"   URL: {test_url}")
    print()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Load the scorecard page
        print("📥 Loading page...")
        await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)

        # Wait for content to render
        print("⏳ Waiting for React to render...")
        await asyncio.sleep(5)

        # Get page title to verify it loaded
        title = await page.title()
        print(f"✅ Page loaded: {title}")
        print()

        # Save page HTML for inspection
        content = await page.content()
        with open('scorecard_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("💾 Saved page HTML to scorecard_page.html")
        print()

        # Look for different selectors
        print("🔍 Looking for scorecard data structures...")

        # Try tables
        tables = await page.query_selector_all('table')
        print(f"   Tables: {len(tables)}")

        # Try divs with common cricket scorecard classes
        divs_scorecard = await page.query_selector_all('div[class*="scorecard"], div[class*="batting"], div[class*="bowling"]')
        print(f"   Scorecard divs: {len(divs_scorecard)}")

        # Try rows/items
        rows = await page.query_selector_all('div[class*="row"], div[class*="item"], li[class*="player"]')
        print(f"   Row/item divs: {len(rows)}")

        # Try any element with "player" in class
        player_elements = await page.query_selector_all('[class*="player"]')
        print(f"   Player elements: {len(player_elements)}")

        # Look for text content patterns
        print()
        print("📝 Searching for player-like patterns in text...")
        if 'wickets' in content.lower() or 'runs' in content.lower() or 'overs' in content.lower():
            print("   ✅ Found cricket terms (wickets/runs/overs) in page")

        print()

        # Try to extract visible text from the page
        print("📄 Extracting visible page text...")
        page_text = await page.inner_text('body')

        # Look for player names and stats patterns
        lines = page_text.split('\n')
        print(f"   Total lines: {len(lines)}")

        print()
        print("📋 First 50 lines of page text:")
        for i, line in enumerate(lines[:50], 1):
            stripped = line.strip()
            if stripped:
                print(f"   {i}: {stripped}")

        print()
        print("🔍 Searching for ACC team names...")
        if 'ACC' in content:
            print("   ✅ Found 'ACC' in page content")

            # Try to extract team name
            import re
            team_pattern = r'(ACC[^<>\"]*(?:1|2|3|4|5|6|ZAMI|U\d+)?[^<>\"]*)'
            teams = re.findall(team_pattern, content)

            if teams:
                unique_teams = list(set([t.strip() for t in teams if 3 < len(t.strip()) < 50]))
                print(f"   Found team names: {unique_teams[:5]}")
        else:
            print("   ⚠️  No 'ACC' found in page content")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n⏸️  Keeping browser open for 10 seconds so you can inspect...")
        await asyncio.sleep(10)
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_scorecard_scrape())
