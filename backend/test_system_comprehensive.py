#!/usr/bin/env python3
"""
Comprehensive system test - Admin and User flows
"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "https://api.fantcric.fun"
ADMIN_EMAIL = "admin@fantcric.fun"
ADMIN_PASSWORD = "FantasyTest2025!"

class SystemTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.season_id = None
        self.league_id = None
        self.issues = []

    def log_issue(self, section, message, details=None):
        """Log an issue found during testing"""
        issue = {
            "section": section,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(issue)
        print(f"❌ [{section}] {message}")
        if details:
            print(f"   Details: {details}")

    def log_success(self, section, message):
        """Log successful test"""
        print(f"✅ [{section}] {message}")

    def test_admin_login(self):
        """Test admin authentication"""
        print("\n" + "="*70)
        print("1. TESTING ADMIN LOGIN")
        print("="*70)

        try:
            # Note: Turnstile will fail but we're testing if endpoint works
            response = requests.post(
                f"{API_URL}/api/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD,
                    "turnstile_token": "test_token"
                },
                timeout=10
            )

            if response.status_code == 400:
                # Expected: Turnstile verification fails
                self.log_issue("Admin Login", "Turnstile verification required",
                             "Cannot test admin endpoints without Turnstile bypass")
                return False
            elif response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_success("Admin Login", f"Logged in as {data['user']['email']}")
                return True
            else:
                self.log_issue("Admin Login", f"Unexpected status {response.status_code}",
                             response.text[:200])
                return False

        except Exception as e:
            self.log_issue("Admin Login", f"Request failed: {str(e)}")
            return False

    def test_get_seasons(self):
        """Test retrieving seasons"""
        print("\n" + "="*70)
        print("2. TESTING GET SEASONS")
        print("="*70)

        try:
            response = requests.get(
                f"{API_URL}/api/admin/seasons",
                headers={"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {},
                timeout=10
            )

            if response.status_code == 401:
                self.log_issue("Get Seasons", "Authentication required",
                             "Need valid admin token")
                return False
            elif response.status_code == 200:
                seasons = response.json()
                self.log_success("Get Seasons", f"Retrieved {len(seasons)} season(s)")
                for s in seasons:
                    print(f"   - {s.get('year')}: {s.get('name')} (active: {s.get('is_active')})")
                return True
            else:
                self.log_issue("Get Seasons", f"Status {response.status_code}", response.text[:200])
                return False

        except Exception as e:
            self.log_issue("Get Seasons", f"Request failed: {str(e)}")
            return False

    def test_get_clubs(self):
        """Test retrieving clubs"""
        print("\n" + "="*70)
        print("3. TESTING GET CLUBS")
        print("="*70)

        try:
            response = requests.get(
                f"{API_URL}/api/admin/clubs",
                headers={"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {},
                timeout=10
            )

            if response.status_code == 401:
                self.log_issue("Get Clubs", "Authentication required")
                return False
            elif response.status_code == 200:
                clubs = response.json()
                self.log_success("Get Clubs", f"Retrieved {len(clubs)} club(s)")
                for c in clubs:
                    print(f"   - {c.get('name')} (tier: {c.get('tier')})")
                return True
            else:
                self.log_issue("Get Clubs", f"Status {response.status_code}", response.text[:200])
                return False

        except Exception as e:
            self.log_issue("Get Clubs", f"Request failed: {str(e)}")
            return False

    def test_get_players(self):
        """Test retrieving players"""
        print("\n" + "="*70)
        print("4. TESTING GET PLAYERS")
        print("="*70)

        try:
            # Get ACC club ID first
            clubs_response = requests.get(f"{API_URL}/api/admin/clubs", timeout=10)
            if clubs_response.status_code != 200:
                self.log_issue("Get Players", "Cannot get clubs list")
                return False

            clubs = clubs_response.json()
            acc_club = next((c for c in clubs if c['name'] == 'ACC'), None)

            if not acc_club:
                self.log_issue("Get Players", "ACC club not found")
                return False

            # Get players for ACC
            response = requests.get(
                f"{API_URL}/api/admin/clubs/{acc_club['id']}/players",
                headers={"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {},
                timeout=10
            )

            if response.status_code == 401:
                self.log_issue("Get Players", "Authentication required")
                return False
            elif response.status_code == 200:
                players = response.json()
                self.log_success("Get Players", f"Retrieved {len(players)} ACC player(s)")

                # Check player structure
                if len(players) > 0:
                    sample = players[0]
                    required_fields = ['id', 'name', 'role', 'tier', 'multiplier']
                    missing = [f for f in required_fields if f not in sample]
                    if missing:
                        self.log_issue("Get Players", f"Missing fields in player: {missing}")
                    else:
                        print(f"   Sample: {sample['name']} - {sample['role']} - multiplier: {sample.get('multiplier')}")

                # Check multiplier distribution
                with_mult = [p for p in players if p.get('multiplier') is not None]
                print(f"   Players with multiplier: {len(with_mult)}/{len(players)}")

                if len(with_mult) > 0:
                    mults = [p['multiplier'] for p in with_mult]
                    print(f"   Multiplier range: {min(mults):.2f} - {max(mults):.2f}")
                    print(f"   Average: {sum(mults)/len(mults):.2f}")

                return True
            else:
                self.log_issue("Get Players", f"Status {response.status_code}", response.text[:200])
                return False

        except Exception as e:
            self.log_issue("Get Players", f"Request failed: {str(e)}")
            return False

    def test_create_season(self):
        """Test creating a new season"""
        print("\n" + "="*70)
        print("5. TESTING CREATE SEASON")
        print("="*70)

        if not self.admin_token:
            self.log_issue("Create Season", "No admin token available")
            return False

        try:
            season_data = {
                "year": "2026",
                "name": "Topklasse 2026",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=180)).isoformat(),
                "description": "Test season for 2026",
                "is_active": False,
                "registration_open": True,
                "scraping_enabled": False
            }

            response = requests.post(
                f"{API_URL}/api/admin/seasons",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=season_data,
                timeout=10
            )

            if response.status_code == 201:
                season = response.json()
                self.season_id = season.get('id')
                self.log_success("Create Season", f"Created season {season.get('year')}: {season.get('name')}")
                return True
            else:
                self.log_issue("Create Season", f"Status {response.status_code}", response.text[:200])
                return False

        except Exception as e:
            self.log_issue("Create Season", f"Request failed: {str(e)}")
            return False

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST REPORT")
        print("="*70)
        print(f"\nTotal Issues Found: {len(self.issues)}")

        if len(self.issues) == 0:
            print("✅ All tests passed!")
        else:
            print("\n📋 Issues Summary:")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. [{issue['section']}] {issue['message']}")
                if issue['details']:
                    print(f"   {issue['details']}")

        print("\n" + "="*70)

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n🏏 FANTASY CRICKET COMPREHENSIVE SYSTEM TEST")
        print(f"API: {API_URL}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Run tests
        self.test_admin_login()
        self.test_get_seasons()
        self.test_get_clubs()
        self.test_get_players()

        if self.admin_token:
            self.test_create_season()

        # Generate report
        self.generate_report()

        return len(self.issues)


if __name__ == "__main__":
    tester = SystemTester()
    num_issues = tester.run_all_tests()
    exit(num_issues)
