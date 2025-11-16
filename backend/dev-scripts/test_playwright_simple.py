#!/usr/bin/env python3
"""
Simple test to verify Playwright can access the API
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_api_access():
    """Test if Playwright can access KNCB API"""

    print("🧪 Testing Playwright API Access")
    print("=" * 70)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = await context.new_page()

    # Test 1: Entity info
    print("\n1️⃣ Testing entity endpoint...")
    try:
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/134453/?apiid=1002",
            wait_until='domcontentloaded',
            timeout=30000
        )
        print(f"   Status: {response.status}")

        if response.status == 200:
            json_text = await page.evaluate('document.body.textContent')
            data = json.loads(json_text)
            print(f"   ✅ Entity: {data.get('entity_name', 'Unknown')}")
        else:
            print(f"   ❌ Failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Grades
    print("\n2️⃣ Testing grades endpoint...")
    try:
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/134453/grades/?apiid=1002&seasonId=19",
            wait_until='domcontentloaded',
            timeout=30000
        )
        print(f"   Status: {response.status}")

        if response.status == 200:
            json_text = await page.evaluate('document.body.textContent')
            data = json.loads(json_text)
            print(f"   ✅ Found {len(data)} competitions")
        else:
            print(f"   ❌ Failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Person endpoint (Sean Walsh)
    print("\n3️⃣ Testing person endpoint (Sean Walsh 11190879)...")
    try:
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/personseason/11190879/?apiid=1002",
            wait_until='domcontentloaded',
            timeout=30000
        )
        print(f"   Status: {response.status}")

        if response.status == 200:
            json_text = await page.evaluate('document.body.textContent')
            data = json.loads(json_text)
            print(f"   ✅ Person: {data.get('person_name', 'Unknown')}")
            print(f"   📊 Keys: {list(data.keys())[:10]}")

            # Save full data
            with open('sean_walsh_playwright_success.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"   💾 Saved to sean_walsh_playwright_success.json")
        else:
            print(f"   ❌ Failed with status {response.status}")
            # Try to get error details
            try:
                body = await page.content()
                print(f"   Response preview: {body[:200]}")
            except:
                pass
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Try alternative person endpoint format
    print("\n4️⃣ Testing alternative person format...")
    try:
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/person/11190879/?apiid=1002",
            wait_until='domcontentloaded',
            timeout=30000
        )
        print(f"   Status: {response.status}")

        if response.status == 200:
            json_text = await page.evaluate('document.body.textContent')
            data = json.loads(json_text)
            print(f"   ✅ Person: {data.get('person_name', 'Unknown')}")
        else:
            print(f"   ❌ Failed with status {response.status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    await browser.close()
    await playwright.stop()

    print("\n" + "=" * 70)
    print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(test_api_access())
