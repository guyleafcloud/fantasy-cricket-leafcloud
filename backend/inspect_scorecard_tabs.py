#!/usr/bin/env python3
"""
Inspect scorecard structure to find ACC team tabs
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_scorecard():
    playwright = await async_playwright().start()
    # Use actual Chrome instead of Chromium
    browser = await playwright.chromium.launch(channel='chrome', headless=False)
    page = await browser.new_page()

    print('Loading scorecard...')
    await page.goto('https://matchcentre.kncb.nl/match/3000178', wait_until='domcontentloaded', timeout=60000)
    print('Page loaded, waiting for React to render...')
    await asyncio.sleep(8)  # Wait for React to render

    print('\n=== Searching for elements containing "ACC" ===')
    # Get all elements
    all_elements = await page.query_selector_all('*')
    print(f'Total elements on page: {len(all_elements)}')

    acc_elements = []
    for elem in all_elements:
        try:
            text = await elem.text_content()
            if text and 'ACC' in text and len(text) < 200:
                tag = await elem.evaluate('el => el.tagName')
                classes = await elem.get_attribute('class') or ''
                acc_elements.append((tag, text.strip()[:100], classes[:50]))
        except:
            continue

    print(f'\nFound {len(acc_elements)} elements containing "ACC"')
    for tag, text, classes in acc_elements[:30]:
        print(f'  [{tag}] class="{classes}"')
        print(f'    Text: {text}')
        print()

    print('\n=== Looking for elements that might be clickable tabs ===')
    # Common React tab patterns
    selectors = [
        'button',
        '[role="tab"]',
        '[role="button"]',
        '.tab',
        '.nav-item',
        '.nav-link',
        '[class*="tab"]',
        '[class*="Tab"]',
        '[class*="button"]',
        '[class*="Button"]'
    ]

    for selector in selectors:
        elements = await page.query_selector_all(selector)
        if len(elements) > 0:
            print(f'\n{selector}: Found {len(elements)} elements')
            for elem in elements[:5]:
                try:
                    text = (await elem.text_content() or '').strip()
                    if text and len(text) < 100:
                        print(f'  - "{text}"')
                except:
                    pass

    print('\n=== Saving page screenshot ===')
    await page.screenshot(path='/Users/guypa/Github/fantasy-cricket-leafcloud/backend/scorecard_screenshot.png', full_page=True)
    print('Screenshot saved to scorecard_screenshot.png')

    print('\nKeeping browser open for 15 seconds for manual inspection...')
    await asyncio.sleep(15)

    await browser.close()
    await playwright.stop()

if __name__ == '__main__':
    asyncio.run(inspect_scorecard())
