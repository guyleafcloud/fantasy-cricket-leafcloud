#!/usr/bin/env python3
"""
Test Player Links on Scorecard
===============================
Check if player names on scorecard pages are clickable links with player IDs.
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def test_player_links():
    """Test if scorecard has player ID links"""

    test_url = "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194"

    print(f"🏏 Testing player links on scorecard")
    print(f"   URL: {test_url}")
    print()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Load the scorecard
        print("📥 Loading scorecard...")
        await page.goto(test_url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(5)

        print("✅ Page loaded")
        print()

        # Look for all links on the page
        print("🔍 Looking for player profile links...")
        all_links = await page.query_selector_all('a')

        player_links = []
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()

                if href and '/player/' in href:
                    # This is a player link!
                    player_links.append({
                        'text': text.strip() if text else '',
                        'href': href
                    })
            except:
                continue

        print(f"   Found {len(player_links)} player profile links")
        print()

        if player_links:
            print("📋 Player links found:")
            for i, link in enumerate(player_links[:20], 1):  # Show first 20
                # Extract player ID from URL
                match = re.search(r'/player/(\d+)/', link['href'])
                player_id = match.group(1) if match else 'unknown'

                print(f"   {i:2d}. {link['text']:<30} ID: {player_id}")
                print(f"       {link['href']}")

            if len(player_links) > 20:
                print(f"   ... and {len(player_links) - 20} more")
        else:
            print("   ⚠️  No player profile links found")
            print()
            print("   Looking for player names as plain text...")

            # Get page HTML
            content = await page.content()

            # Look for "I ALIM" in the HTML
            if 'I ALIM' in content or 'ALIM' in content:
                print("   ✅ Found player name 'I ALIM' or 'ALIM' in HTML")

                # Try to find the surrounding HTML structure
                pattern = r'<[^>]*>(I ALIM|ALIM)[^<]*</[^>]*>'
                matches = re.findall(pattern, content)
                if matches:
                    print(f"   Found {len(matches)} HTML elements containing ALIM")

        print()
        print("💡 Strategy for extracting player IDs:")
        if player_links:
            print("   ✅ BEST: Player names are clickable links with IDs!")
            print("   We can extract player IDs directly from scorecard links.")
        else:
            print("   ⚠️  FALLBACK: Player names are plain text without links")
            print("   We'll need to match player names to IDs using:")
            print("   1. Build a name->ID mapping from all discovered players")
            print("   2. Use fuzzy matching to handle name variations")
            print("   3. Or search for players by name on KNCB")

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
    asyncio.run(test_player_links())
