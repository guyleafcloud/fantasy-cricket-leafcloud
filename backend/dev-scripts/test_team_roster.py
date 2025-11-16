#!/usr/bin/env python3
"""
Test if we can get full team rosters from API
This would allow us to load ALL players in a club upfront
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_team_roster():
    """Test getting team roster with all players"""

    print("🏏 Testing Team Roster Endpoint")
    print("=" * 70)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = await context.new_page()

    try:
        # Step 1: Get a grade
        print("\n1️⃣ Getting Topklasse grade...")
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/134453/grades/?apiid=1002&seasonId=19",
            wait_until='domcontentloaded'
        )

        json_text = await page.evaluate('document.body.textContent')
        grades = json.loads(json_text)

        topklasse = next((g for g in grades if 'Topklasse' in g.get('grade_name', '')), grades[0])
        grade_id = topklasse['grade_id']
        print(f"   ✅ Found {topklasse['grade_name']} (ID: {grade_id})")

        # Step 2: Get teams in this grade
        print(f"\n2️⃣ Getting teams in {topklasse['grade_name']}...")
        response = await page.goto(
            f"https://api.resultsvault.co.uk/rv/134453/grades/{grade_id}/?apiid=1002&seasonId=19",
            wait_until='domcontentloaded'
        )

        json_text = await page.evaluate('document.body.textContent')
        grade_data = json.loads(json_text)

        teams = grade_data.get('teams', [])
        print(f"   ✅ Found {len(teams)} teams")

        if teams:
            # Try to get roster for first 3 teams
            for team in teams[:3]:
                team_id = team.get('team_id')
                club_name = team.get('club_name', 'Unknown')

                print(f"\n3️⃣ Testing roster for {club_name} (team_id: {team_id})...")

                # Try roster endpoint
                roster_url = f"https://api.resultsvault.co.uk/rv/team/{team_id}/roster/?apiid=1002"

                try:
                    response = await page.goto(roster_url, wait_until='domcontentloaded', timeout=10000)
                    print(f"   Status: {response.status}")

                    if response.status == 200:
                        json_text = await page.evaluate('document.body.textContent')

                        try:
                            roster = json.loads(json_text)

                            if isinstance(roster, list) and len(roster) > 0:
                                print(f"   ✅ GOT ROSTER! {len(roster)} players")

                                # Show first 3 players
                                print(f"\n   👥 Sample players:")
                                for player in roster[:3]:
                                    print(f"      - {player.get('person_name', 'Unknown')}")
                                    print(f"        ID: {player.get('person_id')}")
                                    print(f"        Keys: {list(player.keys())[:5]}")

                                # Save full roster
                                with open(f'team_roster_{team_id}.json', 'w') as f:
                                    json.dump(roster, f, indent=2)
                                print(f"   💾 Saved to team_roster_{team_id}.json")

                                print("\n" + "=" * 70)
                                print("✅ ROSTER ENDPOINT WORKS!")
                                print("\n💡 We CAN load all players in a club upfront!")
                                print(f"   Format: /rv/team/{{team_id}}/roster/")

                                await browser.close()
                                await playwright.stop()
                                return True
                            else:
                                print(f"   ⚠️  Empty or invalid roster data")
                        except json.JSONDecodeError as e:
                            print(f"   ❌ JSON decode error: {e}")
                            # Show raw response
                            print(f"   Response: {json_text[:200]}")
                    else:
                        print(f"   ❌ Failed with status {response.status}")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue

            print("\n" + "=" * 70)
            print("⚠️  Roster endpoint doesn't work or returns empty data")
            print("\n💡 Fallback: Discover players incrementally from matches")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    await browser.close()
    await playwright.stop()
    return False


if __name__ == "__main__":
    asyncio.run(test_team_roster())
