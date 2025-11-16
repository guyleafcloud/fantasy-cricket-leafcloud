#!/usr/bin/env python3
"""
Test the correct reports endpoint for player data
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_reports_endpoint():
    """Test the rpt_plsml reports endpoint"""

    print("🏏 Testing Reports Endpoint for Player Data")
    print("=" * 70)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = await context.new_page()

    # Test with Sean Walsh
    player_id = "11190879"
    season_id = 19

    url = f"https://api.resultsvault.co.uk/rv/0/report/rpt_plsml/?apiid=1002&seasonid={season_id}&playerid={player_id}&sportid=1&sort=-DATE1"

    print(f"\n📥 Fetching Sean Walsh (ID: {player_id})...")
    print(f"🔗 URL: {url}")

    try:
        response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)

        print(f"   Status: {response.status}")

        if response.status == 200:
            json_text = await page.evaluate('document.body.textContent')
            data = json.loads(json_text)

            print(f"   ✅ SUCCESS!")
            print(f"\n   📊 Data structure:")
            print(f"      Keys: {list(data.keys())}")

            if 'data' in data:
                matches = data['data']
                print(f"      Matches: {len(matches)}")

                if matches and len(matches) > 0:
                    print(f"\n   🏏 First match data:")
                    first_match = matches[0]
                    print(f"      Keys: {list(first_match.keys())[:10]}")

                    # Check for items
                    if 'items' in first_match:
                        items = first_match['items']
                        print(f"      Items count: {len(items)}")

                        if items and len(items) > 0:
                            print(f"\n      📋 Sample items:")
                            for item in items[:10]:
                                print(f"         {item.get('id')}: {item.get('val')}")

            # Save full data
            with open('sean_walsh_reports_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n   💾 Full data saved to sean_walsh_reports_data.json")

            print("\n" + "=" * 70)
            print("✅ REPORTS ENDPOINT WORKS!")
            print("\n💡 This is the correct endpoint for player data!")
            print(f"   Format: /rv/0/report/rpt_plsml/")
            print(f"   Params: apiid, seasonid, playerid, sportid, sort")

        else:
            print(f"   ❌ Failed with status {response.status}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_reports_endpoint())
