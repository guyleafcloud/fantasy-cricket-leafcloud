#!/usr/bin/env python3
"""
Debug Player Links
==================
Check what text is in player links vs what we extract from scorecard
"""

import asyncio
import re
from playwright.async_api import async_playwright


async def debug_links():
    """Debug player link extraction"""

    url = "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194"

    print("🔍 Debugging player link extraction")
    print(f"   URL: {url}")
    print()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Load scorecard
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(5)

        # Extract player links
        print("📋 Player links found on page:")
        print()

        player_links = await page.query_selector_all('a[href*="/player/"]')

        for i, link in enumerate(player_links, 1):
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()

                if href and text:
                    match = re.search(r'/player/(\d+)/', href)
                    if match:
                        player_id = match.group(1)
                        link_text = text.strip()

                        print(f"{i:2d}. Link text: '{link_text}'")
                        print(f"    Player ID: {player_id}")
                        print()
            except:
                continue

        # Now get scorecard text
        print("=" * 60)
        print("📊 Scorecard batting section (first 50 lines):")
        print()

        page_text = await page.inner_text('body')
        lines = page_text.split('\n')

        # Find batting section
        batting_start = None
        for i, line in enumerate(lines):
            if 'BATTING' in line.upper():
                batting_start = i
                break

        if batting_start:
            for i in range(batting_start, min(batting_start + 50, len(lines))):
                print(f"{i:3d}: {lines[i]}")

        print()
        print("⏸️  Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)

    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_links())
