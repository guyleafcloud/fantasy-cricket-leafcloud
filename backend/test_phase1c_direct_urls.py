#!/usr/bin/env python3
"""
Phase 1c: Direct URL Scraper
Scrape your 18 specific scorecard URLs directly to validate 2025 format
"""
import asyncio
import sys
import re
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util
import sys

# Import rules-set-1.py (has hyphens, can't use normal import)
spec = importlib.util.spec_from_file_location("rules_set_1", "rules-set-1.py")
rules_module = importlib.util.module_from_spec(spec)
sys.modules["rules_set_1"] = rules_module
spec.loader.exec_module(rules_module)
calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

# Your provided URLs
WEEK1_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394",
    "https://matchcentre.kncb.nl/match/134453-7336247/scorecard/?period=2880895",
    "https://matchcentre.kncb.nl/match/134453-7323305/scorecard/?period=2904132",
    "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194",
    "https://matchcentre.kncb.nl/match/134453-7329152/scorecard/?period=2912677",
    "https://matchcentre.kncb.nl/match/134453-7326066/scorecard/?period=2850306",
    "https://matchcentre.kncb.nl/match/134453-7332092/scorecard/?period=2843768",
    "https://matchcentre.kncb.nl/match/134453-7324743/scorecard/?period=2883358",
    "https://matchcentre.kncb.nl/match/134453-7324797/scorecard/?period=2883096",
]

WEEK2_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7336254/scorecard/?period=2911963",
    "https://matchcentre.kncb.nl/match/134453-7331237/scorecard/?period=2912048",
    "https://matchcentre.kncb.nl/match/134453-7329153/scorecard/?period=2943897",
    "https://matchcentre.kncb.nl/match/134453-7332269/scorecard/?period=2905571",
    "https://matchcentre.kncb.nl/match/134453-7326162/scorecard/?period=2882990",
    "https://matchcentre.kncb.nl/match/134453-7324749/scorecard/?period=2946803",
    "https://matchcentre.kncb.nl/match/134453-7323338/scorecard/?period=3100381",
    "https://matchcentre.kncb.nl/match/134453-7323364/scorecard/?period=2883312",
    "https://matchcentre.kncb.nl/match/134453-7330958/scorecard/?period=2971631",
]

async def scrape_scorecard_url(browser, url):
    """
    Scrape a single scorecard URL directly using Playwright
    """
    page = await browser.new_page()

    try:
        print(f"   📥 Fetching: {url}")

        # Navigate to the scorecard
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Wait for scorecard to load
        await page.wait_for_selector('body', timeout=10000)

        # Extract match info from page
        try:
            match_title = await page.text_content('h1, .match-title, .game-header')
            match_title = match_title.strip() if match_title else "Unknown Match"
        except:
            match_title = "Unknown Match"

        # Try to get the scorecard data
        # The KNCB matchcentre typically loads data via JavaScript/API
        # We'll try to intercept the API call or parse the rendered HTML

        # Option 1: Try to find JSON data in page
        json_data = None
        try:
            # Look for __NEXT_DATA__ or similar JSON embedded in page
            script_content = await page.inner_text('script#__NEXT_DATA__')
            if script_content:
                import json
                json_data = json.loads(script_content)
        except:
            pass

        # Option 2: Parse HTML tables directly
        batting_data = []
        bowling_data = []

        try:
            # Find batting tables
            batting_rows = await page.query_selector_all('table.batting tbody tr, .batting-card tbody tr, [data-testid="batting-table"] tbody tr')

            for row in batting_rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        # Typical format: Player Name | Runs | Balls | 4s | 6s | SR
                        player_name = await cells[0].inner_text()
                        runs = await cells[1].inner_text()
                        balls = await cells[2].inner_text() if len(cells) > 2 else "0"

                        # Clean and parse
                        player_name = player_name.strip()
                        runs = re.search(r'\d+', runs)
                        balls = re.search(r'\d+', balls)

                        if player_name and runs:
                            batting_data.append({
                                'player_name': player_name,
                                'runs': int(runs.group()),
                                'balls_faced': int(balls.group()) if balls else 0,
                                'is_out': 'not out' not in player_name.lower()
                            })
                except Exception as e:
                    continue

            # Find bowling tables
            bowling_rows = await page.query_selector_all('table.bowling tbody tr, .bowling-card tbody tr, [data-testid="bowling-table"] tbody tr')

            for row in bowling_rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 4:
                        # Typical format: Player Name | Overs | Maidens | Runs | Wickets
                        player_name = await cells[0].inner_text()
                        overs = await cells[1].inner_text()
                        maidens = await cells[2].inner_text() if len(cells) > 2 else "0"
                        runs_conceded = await cells[3].inner_text() if len(cells) > 3 else "0"
                        wickets = await cells[4].inner_text() if len(cells) > 4 else "0"

                        # Clean and parse
                        player_name = player_name.strip()
                        overs_match = re.search(r'[\d.]+', overs)
                        wickets_match = re.search(r'\d+', wickets)

                        if player_name and overs_match:
                            bowling_data.append({
                                'player_name': player_name,
                                'overs_bowled': float(overs_match.group()),
                                'maidens': int(re.search(r'\d+', maidens).group()) if re.search(r'\d+', maidens) else 0,
                                'runs_conceded': int(re.search(r'\d+', runs_conceded).group()) if re.search(r'\d+', runs_conceded) else 0,
                                'wickets': int(wickets_match.group()) if wickets_match else 0
                            })
                except Exception as e:
                    continue

        except Exception as e:
            print(f"      ⚠️  HTML parsing error: {e}")

        # Combine batting and bowling data
        all_players = {}

        for bat in batting_data:
            player_name = bat['player_name']
            all_players[player_name] = {
                'player_name': player_name,
                'batting': {
                    'runs': bat['runs'],
                    'balls_faced': bat['balls_faced'],
                    'is_out': bat['is_out']
                },
                'bowling': {'wickets': 0, 'overs_bowled': 0, 'maidens': 0, 'runs_conceded': 0},
                'fielding': {'catches': 0, 'stumpings': 0, 'run_outs': 0}
            }

        for bowl in bowling_data:
            player_name = bowl['player_name']
            if player_name not in all_players:
                all_players[player_name] = {
                    'player_name': player_name,
                    'batting': {'runs': 0, 'balls_faced': 0, 'is_out': False},
                    'bowling': {'wickets': 0, 'overs_bowled': 0, 'maidens': 0, 'runs_conceded': 0},
                    'fielding': {'catches': 0, 'stumpings': 0, 'run_outs': 0}
                }

            all_players[player_name]['bowling'] = {
                'wickets': bowl['wickets'],
                'overs_bowled': bowl['overs_bowled'],
                'maidens': bowl['maidens'],
                'runs_conceded': bowl['runs_conceded']
            }

        # Calculate fantasy points for each player
        performances = []
        for player_name, stats in all_players.items():
            fantasy_points = calculate_total_fantasy_points(
                stats['batting'],
                stats['bowling'],
                stats['fielding']
            )

            performances.append({
                'player_name': player_name,
                'batting': stats['batting'],
                'bowling': stats['bowling'],
                'fielding': stats['fielding'],
                'fantasy_points': fantasy_points
            })

        await page.close()

        return {
            'url': url,
            'match_title': match_title,
            'success': len(performances) > 0,
            'performances': performances,
            'total_players': len(performances)
        }

    except Exception as e:
        print(f"      ❌ Error: {e}")
        await page.close()
        return {
            'url': url,
            'match_title': 'Error',
            'success': False,
            'performances': [],
            'total_players': 0,
            'error': str(e)
        }

async def test_direct_urls():
    print("="*70)
    print("PHASE 1C: DIRECT URL SCRAPER")
    print("="*70)
    print("\n📋 Testing your 18 specific scorecard URLs\n")

    all_urls = WEEK1_URLS + WEEK2_URLS

    print(f"URLs to test:")
    print(f"   Week 1: {len(WEEK1_URLS)} matches")
    print(f"   Week 2: {len(WEEK2_URLS)} matches")
    print(f"   Total: {len(all_urls)} matches\n")

    # Start Playwright
    async with async_playwright() as p:
        print(f"🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)

        # Test Week 1 URLs
        print(f"\n{'='*70}")
        print("WEEK 1 MATCHES")
        print('='*70)

        week1_results = []
        for i, url in enumerate(WEEK1_URLS, 1):
            print(f"\n[{i}/{len(WEEK1_URLS)}]")
            result = await scrape_scorecard_url(browser, url)
            week1_results.append(result)

            if result['success']:
                print(f"   ✅ Success: {result['total_players']} players, "
                      f"{sum(p['fantasy_points'] for p in result['performances']):.1f} total points")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

        # Test Week 2 URLs
        print(f"\n{'='*70}")
        print("WEEK 2 MATCHES")
        print('='*70)

        week2_results = []
        for i, url in enumerate(WEEK2_URLS, 1):
            print(f"\n[{i}/{len(WEEK2_URLS)}]")
            result = await scrape_scorecard_url(browser, url)
            week2_results.append(result)

            if result['success']:
                print(f"   ✅ Success: {result['total_players']} players, "
                      f"{sum(p['fantasy_points'] for p in result['performances']):.1f} total points")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

        await browser.close()

        # Summary
        all_results = week1_results + week2_results
        successful = [r for r in all_results if r['success']]
        failed = [r for r in all_results if not r['success']]

        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)

        print(f"\n   Successful: {len(successful)}/{len(all_results)}")
        print(f"   Failed: {len(failed)}/{len(all_results)}")

        if successful:
            total_players = sum(r['total_players'] for r in successful)
            total_performances = sum(len(r['performances']) for r in successful)
            total_points = sum(sum(p['fantasy_points'] for p in r['performances']) for r in successful)

            print(f"\n   Total players extracted: {total_players}")
            print(f"   Total performances: {total_performances}")
            print(f"   Total fantasy points: {total_points:.1f}")

            # Show top performers
            all_performances = []
            for result in successful:
                all_performances.extend(result['performances'])

            sorted_performers = sorted(all_performances,
                                     key=lambda x: x['fantasy_points'],
                                     reverse=True)

            print(f"\n   Top 10 Performers Across All Matches:")
            for i, perf in enumerate(sorted_performers[:10], 1):
                print(f"   {i:2d}. {perf['player_name']:25s} - {perf['fantasy_points']:6.1f} pts "
                      f"(R:{perf['batting']['runs']}, W:{perf['bowling']['wickets']})")

        if failed:
            print(f"\n   ⚠️  Failed URLs:")
            for result in failed[:5]:
                print(f"      - {result['url']}")
            if len(failed) > 5:
                print(f"      ... and {len(failed) - 5} more")

        # Success criteria
        print(f"\n{'='*70}")
        print("SUCCESS CRITERIA")
        print('='*70)

        success_rate = len(successful) / len(all_results) * 100 if all_results else 0

        criteria = [
            ("At least 50% URLs scraped", success_rate >= 50),
            ("Players extracted", total_players > 0 if successful else False),
            ("Fantasy points calculated", total_points > 0 if successful else False),
            ("2025 format parseable", len(successful) > 0),
        ]

        all_passed = True
        for criterion, passed in criteria:
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}")
            if not passed:
                all_passed = False

        print(f"\n{'='*70}")
        if all_passed:
            print("✅ PHASE 1C: PASSED")
            print(f"   Successfully scraped {len(successful)}/{len(all_results)} URLs")
            print("   2025 scorecard format validated!")
            print("   Ready to proceed to Phase 2")
        else:
            print("❌ PHASE 1C: FAILED")
            print("   Need to investigate URL scraping issues")
        print('='*70)

        return all_passed

if __name__ == "__main__":
    print("\n🏏 Starting Phase 1c: Direct URL Scraper\n")
    print("⏱️  This may take 3-5 minutes (18 URLs)...\n")

    try:
        result = asyncio.run(test_direct_urls())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
