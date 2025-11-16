#!/usr/bin/env python3
"""
Test getting player data from match scorecards instead of person endpoint
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def test_match_approach():
    """Get player data by scraping match scorecards"""

    print("🏏 Testing Match Scorecard Approach")
    print("=" * 70)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = await context.new_page()

    # Step 1: Get a grade (competition)
    print("\n1️⃣ Getting Topklasse grade...")
    try:
        response = await page.goto(
            "https://api.resultsvault.co.uk/rv/134453/grades/?apiid=1002&seasonId=19",
            wait_until='domcontentloaded'
        )

        json_text = await page.evaluate('document.body.textContent')
        grades = json.loads(json_text)

        topklasse = next((g for g in grades if 'Topklasse' in g.get('grade_name', '')), None)

        if topklasse:
            grade_id = topklasse['grade_id']
            print(f"   ✅ Found Topklasse (ID: {grade_id})")

            # Step 2: Get teams in this grade
            print(f"\n2️⃣ Getting teams in Topklasse...")
            response = await page.goto(
                f"https://api.resultsvault.co.uk/rv/134453/grades/{grade_id}/?apiid=1002&seasonId=19",
                wait_until='domcontentloaded'
            )

            json_text = await page.evaluate('document.body.textContent')
            grade_data = json.loads(json_text)

            teams = grade_data.get('teams', [])
            print(f"   ✅ Found {len(teams)} teams")

            if teams:
                # Show first team
                first_team = teams[0]
                print(f"   📍 First team: {first_team.get('club_name', 'Unknown')}")

                team_id = first_team.get('team_id')

                if team_id:
                    # Step 3: Get team roster
                    print(f"\n3️⃣ Getting roster for team {team_id}...")
                    response = await page.goto(
                        f"https://api.resultsvault.co.uk/rv/team/{team_id}/roster/?apiid=1002",
                        wait_until='domcontentloaded'
                    )

                    print(f"   Status: {response.status}")

                    if response.status == 200:
                        json_text = await page.evaluate('document.body.textContent')
                        roster = json.loads(json_text)
                        print(f"   ✅ Found {len(roster) if isinstance(roster, list) else 'N/A'} players")

                        if roster and isinstance(roster, list) and len(roster) > 0:
                            # Save roster
                            with open('team_roster.json', 'w') as f:
                                json.dump(roster, f, indent=2)
                            print(f"   💾 Saved to team_roster.json")

                            # Show first player
                            first_player = roster[0]
                            print(f"\n   👤 First player:")
                            for key, value in list(first_player.items())[:8]:
                                print(f"      {key}: {value}")
                    else:
                        print(f"   ❌ Failed with status {response.status}")

            # Step 4: Get matches
            print(f"\n4️⃣ Getting recent matches for Topklasse...")
            response = await page.goto(
                f"https://api.resultsvault.co.uk/rv/134453/matches/?apiid=1002&seasonId=19&gradeId={grade_id}&action=ors&maxrecs=10",
                wait_until='domcontentloaded'
            )

            json_text = await page.evaluate('document.body.textContent')
            matches = json.loads(json_text)

            print(f"   ✅ Found {len(matches) if isinstance(matches, list) else 0} matches")

            if matches and isinstance(matches, list) and len(matches) > 0:
                # Get first completed match
                completed_match = next((m for m in matches if m.get('match_status') == 'C'), matches[0])
                match_id = completed_match.get('match_id')

                print(f"   📍 Match ID: {match_id}")
                print(f"   📅 Date: {completed_match.get('match_date_time', 'Unknown')}")

                # Step 5: Get match scorecard
                print(f"\n5️⃣ Getting scorecard for match {match_id}...")
                response = await page.goto(
                    f"https://api.resultsvault.co.uk/rv/match/{match_id}/?apiid=1002",
                    wait_until='domcontentloaded'
                )

                print(f"   Status: {response.status}")

                if response.status == 200:
                    json_text = await page.evaluate('document.body.textContent')
                    scorecard = json.loads(json_text)

                    print(f"   ✅ Got scorecard!")

                    # Save scorecard
                    with open('match_scorecard.json', 'w') as f:
                        json.dump(scorecard, f, indent=2)
                    print(f"   💾 Saved to match_scorecard.json")

                    # Check if it has player data
                    print(f"\n   📊 Scorecard structure:")
                    print(f"      Keys: {list(scorecard.keys())[:10]}")

                    # Look for batting/bowling data
                    if 'innings' in scorecard:
                        innings = scorecard['innings']
                        print(f"      Innings count: {len(innings) if isinstance(innings, list) else 'N/A'}")

                        if innings and len(innings) > 0:
                            first_innings = innings[0]
                            print(f"      First innings keys: {list(first_innings.keys())[:10]}")

                            if 'batting' in first_innings:
                                batting = first_innings['batting']
                                print(f"      Batters: {len(batting) if isinstance(batting, list) else 'N/A'}")

                                if batting and len(batting) > 0:
                                    first_batter = batting[0]
                                    print(f"\n      🏏 First batter:")
                                    for key, value in list(first_batter.items())[:8]:
                                        print(f"         {key}: {value}")
                else:
                    print(f"   ❌ Failed with status {response.status}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    await browser.close()
    await playwright.stop()

    print("\n" + "=" * 70)
    print("✅ Match approach test complete!")
    print("\n💡 Strategy: Build player stats from match scorecards")
    print("   1. Get competitions/grades")
    print("   2. Get teams in each grade")
    print("   3. Get matches for each grade")
    print("   4. Extract player stats from each match scorecard")
    print("   5. Aggregate stats to build player season totals")


if __name__ == "__main__":
    asyncio.run(test_match_approach())
