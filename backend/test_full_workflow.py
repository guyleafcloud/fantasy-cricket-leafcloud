#!/usr/bin/env python3
"""
Comprehensive Workflow Test
Test all critical endpoints end-to-end
"""

import requests
import json
from datetime import datetime

API_URL = "https://api.fantcric.fun"
ADMIN_EMAIL = "admin@fantcric.fun"
ADMIN_PASSWORD = "FantasyTest2025!"

class WorkflowTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.token = None
        self.season_id = None
        self.club_id = None

    def test(self, name, func):
        """Run a test and track results"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print('='*70)
        try:
            result = func()
            print(f"✅ PASSED")
            self.passed += 1
            return result
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.errors.append({"test": name, "error": str(e)})
            return None
        except Exception as e:
            print(f"💥 ERROR: {e}")
            self.failed += 1
            self.errors.append({"test": name, "error": str(e)})
            return None

    def test_login(self):
        """Test admin login"""
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "turnstile_token": "dummy_token_for_testing"
            },
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 429:
            print(f"   Rate limited - waiting...")
            import time
            time.sleep(2)
            response = requests.post(
                f"{API_URL}/api/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD,
                    "turnstile_token": "dummy_token_for_testing"
                },
                timeout=10
            )

        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text[:200]}"

        data = response.json()
        self.token = data["access_token"]
        print(f"   Logged in successfully")
        print(f"   Token: {self.token[:20]}...")
        return self.token

    def test_get_seasons(self):
        """Test getting seasons"""
        response = requests.get(
            f"{API_URL}/api/admin/seasons",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )

        assert response.status_code == 200, f"Get seasons failed: {response.status_code} - {response.text[:200]}"

        data = response.json()
        seasons = data.get("seasons", [])
        print(f"   Found {len(seasons)} season(s)")

        if seasons:
            self.season_id = seasons[0]["id"]
            print(f"   Using season: {seasons[0]['name']} ({self.season_id})")
        else:
            raise AssertionError("No seasons found in database")

        return seasons

    def test_get_clubs(self):
        """Test getting clubs"""
        response = requests.get(
            f"{API_URL}/api/admin/clubs",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )

        assert response.status_code == 200, f"Get clubs failed: {response.status_code} - {response.text[:500]}"

        data = response.json()
        clubs = data.get("clubs", [])
        print(f"   Found {len(clubs)} club(s)")

        if clubs:
            self.club_id = clubs[0]["id"]
            print(f"   Using club: {clubs[0]['name']} ({self.club_id})")
            print(f"   Players: {clubs[0].get('players_count', 0)}")
        else:
            raise AssertionError("No clubs found in database")

        return clubs

    def test_get_players(self):
        """Test getting players for a club"""
        response = requests.get(
            f"{API_URL}/api/admin/clubs/{self.club_id}/players",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )

        assert response.status_code == 200, f"Get players failed: {response.status_code} - {response.text[:200]}"

        data = response.json()
        players = data.get("players", [])
        print(f"   Found {len(players)} player(s)")

        if players:
            print(f"   Sample player: {players[0].get('name')} - RL Team: {players[0].get('rl_team')} - Multiplier: {players[0].get('multiplier')}")

        return players

    def test_create_league(self):
        """Test creating a league"""
        league_data = {
            "season_id": self.season_id,
            "club_id": self.club_id,
            "name": f"Test League {datetime.now().strftime('%H:%M:%S')}",
            "description": "Test league created by automated workflow test",
            "squad_size": 11,
            "transfers_per_season": 4,
            "require_from_each_team": True,
            "is_public": True,
            "max_participants": 100
        }

        print(f"   Creating league with data:")
        print(f"     Season ID: {self.season_id}")
        print(f"     Club ID: {self.club_id}")
        print(f"     Name: {league_data['name']}")

        response = requests.post(
            f"{API_URL}/api/admin/leagues",
            headers={"Authorization": f"Bearer {self.token}"},
            json=league_data,
            timeout=10
        )

        print(f"   Response status: {response.status_code}")

        if response.status_code != 201:
            print(f"   Response body: {response.text[:1000]}")

        assert response.status_code == 201, f"Create league failed: {response.status_code} - {response.text[:500]}"

        data = response.json()
        league = data.get("league", {})
        print(f"   League created: {league.get('name')}")
        print(f"   League code: {league.get('league_code')}")
        print(f"   League ID: {league.get('id')}")

        return league

    def test_get_leagues(self):
        """Test getting leagues"""
        response = requests.get(
            f"{API_URL}/api/admin/leagues",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )

        assert response.status_code == 200, f"Get leagues failed: {response.status_code} - {response.text[:200]}"

        data = response.json()
        leagues = data.get("leagues", [])
        print(f"   Found {len(leagues)} league(s)")

        for league in leagues[-3:]:  # Show last 3 leagues
            print(f"   - {league.get('name')} (Code: {league.get('league_code')})")

        return leagues

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*70)
        print("WORKFLOW TEST REPORT")
        print("="*70)
        print(f"Tests Run: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")

        if self.failed > 0:
            print(f"\n🔴 FAILURES:")
            for error in self.errors:
                print(f"\n  {error['test']}:")
                print(f"    {error['error']}")

        print("\n" + "="*70)

        if self.failed == 0:
            print("✅ ALL TESTS PASSED - WORKFLOW IS HEALTHY")
        else:
            print(f"⚠️  {self.failed} TEST(S) FAILED - REVIEW ERRORS ABOVE")

        print("="*70 + "\n")

        return self.failed == 0


if __name__ == "__main__":
    tester = WorkflowTester()

    print(f"\n🏏 FANTASY CRICKET - FULL WORKFLOW TEST")
    print(f"API: {API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Run all tests in sequence
    tester.test("1. Admin Login", tester.test_login)
    tester.test("2. Get Seasons", tester.test_get_seasons)
    tester.test("3. Get Clubs", tester.test_get_clubs)
    tester.test("4. Get Players", tester.test_get_players)
    tester.test("5. Create League", tester.test_create_league)
    tester.test("6. Get Leagues", tester.test_get_leagues)

    # Generate report
    success = tester.generate_report()

    # Exit with appropriate code
    exit(0 if success else 1)
