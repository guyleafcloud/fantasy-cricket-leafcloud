#!/usr/bin/env python3
"""
Test Scorecard Parser
=====================
Test scraping a known historical ACC scorecard to verify:
1. Can extract player performances
2. Can match players to database
3. Data format is correct for points calculation
"""

import asyncio
import json
import os
import psycopg2
from kncb_html_scraper import KNCBMatchCentreScraper

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')
ACC_CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276'

# Test with a known historical scorecard
TEST_SCORECARD_URL = "https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921"


def normalize_name(name):
    """Normalize player name for matching"""
    return name.replace(' ', '').replace('-', '').lower()


async def test_scorecard_parsing():
    """Test parsing a single scorecard"""

    print("\n" + "=" * 80)
    print("🏏 TESTING SCORECARD PARSER")
    print("=" * 80)
    print(f"Test URL: {TEST_SCORECARD_URL}")
    print("=" * 80)
    print()

    scraper = KNCBMatchCentreScraper()

    # Parse the scorecard
    print("📡 Fetching and parsing scorecard...")
    match_data = await scraper.scrape_single_match(TEST_SCORECARD_URL)

    if not match_data:
        print("❌ Failed to parse scorecard")
        return

    print(f"✅ Scorecard parsed successfully")
    print()

    # Display match info
    print("📋 MATCH INFORMATION:")
    print(f"   Title: {match_data.get('match_title', 'Unknown')}")
    print(f"   Date: {match_data.get('match_date', 'Unknown')}")
    print(f"   Players found: {len(match_data.get('player_performances', []))}")
    print()

    # Display player performances
    performances = match_data.get('player_performances', [])
    if performances:
        print("👥 PLAYER PERFORMANCES:")
        print()
        for i, perf in enumerate(performances[:10], 1):  # Show first 10
            name = perf.get('player_name', 'Unknown')
            club = perf.get('club', 'Unknown')
            runs = perf.get('runs', 0)
            balls_faced = perf.get('balls_faced', 0)
            fours = perf.get('fours', 0)
            sixes = perf.get('sixes', 0)
            wickets = perf.get('wickets', 0)
            overs = perf.get('overs_bowled', 0)
            runs_conceded = perf.get('runs_conceded', 0)
            catches = perf.get('catches', 0)
            run_outs = perf.get('run_outs', 0)

            print(f"   {i}. {name} ({club})")
            if runs > 0 or balls_faced > 0:
                print(f"      Batting: {runs} runs off {balls_faced} balls ({fours}x4, {sixes}x6)")
            if wickets > 0 or overs > 0:
                print(f"      Bowling: {wickets} wkts, {runs_conceded} runs in {overs} overs")
            if catches > 0 or run_outs > 0:
                print(f"      Fielding: {catches} catches, {run_outs} run outs")
            print()
    print()

    # Now try to match players to database
    print("🔍 MATCHING PLAYERS TO DATABASE:")
    print()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Get all ACC players
        cursor.execute("""
            SELECT id, name, player_type
            FROM players
            WHERE club_id = %s
        """, (ACC_CLUB_ID,))

        db_players = {normalize_name(row[1]): row for row in cursor.fetchall()}

        matched = 0
        unmatched = []

        for perf in performances:
            player_name = perf.get('player_name', '')
            norm_name = normalize_name(player_name)

            if norm_name in db_players:
                matched += 1
                db_id, db_name, db_type = db_players[norm_name]
                print(f"   ✅ {player_name} → {db_name} ({db_type})")
            else:
                unmatched.append(player_name)

        print()
        print("=" * 80)
        print("MATCH RESULTS:")
        print("=" * 80)
        print(f"   Total performances: {len(performances)}")
        print(f"   Matched to database: {matched}")
        print(f"   Unmatched: {len(unmatched)}")

        if unmatched:
            print()
            print("   Unmatched players:")
            for name in unmatched[:10]:
                print(f"      - {name}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")

    print()
    print("=" * 80)

    # Save result
    with open('test_scorecard_output.json', 'w') as f:
        json.dump(match_data, f, indent=2)

    print(f"💾 Full scorecard data saved to: test_scorecard_output.json")
    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(test_scorecard_parsing())
