#!/usr/bin/env python3
"""
Quick Test for Mock KNCB Server
================================
Simple synchronous test to verify mock server is working.
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    print("🔌 Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data.get('status')}")
        print(f"   Matches in memory: {data.get('matches_in_memory')}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_grades():
    """Test grades endpoint"""
    print("\n📋 Testing /grades endpoint...")
    response = requests.get(f"{BASE_URL}/rv/134453/grades/?apiid=1002&seasonId=19")
    if response.status_code == 200:
        grades = response.json()
        print(f"✅ Got {len(grades)} grades")
        for grade in grades:
            print(f"   - {grade['grade_name']} (ID: {grade['grade_id']})")
        return True
    else:
        print(f"❌ Grades request failed: {response.status_code}")
        return False

def test_matches():
    """Test matches endpoint"""
    print("\n📊 Testing /matches endpoint...")
    response = requests.get(
        f"{BASE_URL}/rv/134453/matches/?apiid=1002&seasonId=19&gradeId=1"
    )
    if response.status_code == 200:
        matches = response.json()
        print(f"✅ Got {len(matches)} matches for Hoofdklasse")
        if len(matches) > 0:
            match = matches[0]
            print(f"   Sample match:")
            print(f"   - {match['home_club_name']} vs {match['away_club_name']}")
            print(f"   - Date: {match['match_date_time'][:10]}")
            print(f"   - Match ID: {match['match_id']}")
            return match['match_id']
        return True
    else:
        print(f"❌ Matches request failed: {response.status_code}")
        return False

def test_scorecard(match_id):
    """Test scorecard endpoint"""
    print(f"\n📥 Testing /match/{match_id} endpoint...")
    response = requests.get(f"{BASE_URL}/rv/match/{match_id}/?apiid=1002")
    if response.status_code == 200:
        scorecard = response.json()
        print(f"✅ Got scorecard for match {match_id}")
        print(f"   {scorecard['home_club']} vs {scorecard['away_club']}")
        print(f"   Innings: {len(scorecard.get('innings', []))}")

        # Show sample batting
        if scorecard.get('innings') and len(scorecard['innings']) > 0:
            first_innings = scorecard['innings'][0]
            batting = first_innings.get('batting', [])
            print(f"   Batters in first innings: {len(batting)}")
            if len(batting) > 0:
                top_scorer = max(batting, key=lambda b: b.get('runs', 0))
                print(f"   Top scorer: {top_scorer['player_name']} - {top_scorer['runs']}({top_scorer['balls_faced']})")

        return True
    else:
        print(f"❌ Scorecard request failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("="*80)
    print("🧪 MOCK KNCB SERVER - QUICK TEST")
    print("="*80)

    # Run tests
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        exit(1)

    if not test_grades():
        print("\n❌ Grades test failed")
        exit(1)

    match_id = test_matches()
    if not match_id:
        print("\n❌ Matches test failed")
        exit(1)

    if not test_scorecard(match_id):
        print("\n❌ Scorecard test failed")
        exit(1)

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print("\nMock server is working correctly and ready for scraper testing.")
    print("Next steps:")
    print("  1. Run full scraper test: python3 test_scraper_with_mock.py")
    print("  2. Configure scraper to use mock URL for testing")
    print("  3. Generate simulated season data")
