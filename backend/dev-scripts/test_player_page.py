#!/usr/bin/env python3
"""
Test Player Profile Page Scraping
==================================
Test if we can access player profile pages and extract player IDs.
"""

import asyncio
from playwright.async_api import async_playwright


async def test_player_page():
    """Test scraping a player profile page"""

    # Test URL provided by user
    test_url = "https://matchcentre.kncb.nl/player/11332933/19/"

    print(f"🏏 Testing player profile page")
    print(f"   URL: {test_url}")
    print(f"   Player ID: 11332933")
    print(f"   Season: 19")
    print()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Load the player page
        print("📥 Loading page...")
        await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)

        # Wait for content to render
        print("⏳ Waiting for React to render...")
        await asyncio.sleep(5)

        # Get page title
        title = await page.title()
        print(f"✅ Page loaded: {title}")
        print()

        # Get visible page text
        page_text = await page.inner_text('body')
        lines = page_text.split('\n')

        print(f"📄 Page has {len(lines)} lines of text")
        print()

        # Look for player name
        print("🔍 Looking for player information...")
        if 'ALIM' in page_text:
            print("   ✅ Found player name 'ALIM' on page")

        # Look for stats
        if 'runs' in page_text.lower() or 'wickets' in page_text.lower():
            print("   ✅ Found stats (runs/wickets)")

        if 'matches' in page_text.lower():
            print("   ✅ Found match information")

        print()
        print("📋 First 100 lines of page text:")
        for i, line in enumerate(lines[:100], 1):
            stripped = line.strip()
            if stripped:
                print(f"   {i}: {stripped}")

        print()
        print("💡 Extracting player ID from URL structure...")
        # URL format: https://matchcentre.kncb.nl/player/{PLAYER_ID}/{SEASON}/
        parts = test_url.rstrip('/').split('/')
        if 'player' in parts:
            player_idx = parts.index('player')
            if len(parts) > player_idx + 1:
                player_id = parts[player_idx + 1]
                season = parts[player_idx + 2] if len(parts) > player_idx + 2 else None
                print(f"   Player ID: {player_id}")
                print(f"   Season: {season}")

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
    asyncio.run(test_player_page())
