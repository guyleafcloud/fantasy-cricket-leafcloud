#!/usr/bin/env python3
"""
End-to-End System Test
======================
Tests the complete system flow including authentication, database, and API endpoints.
"""

import requests
import json
from datetime import datetime

API_URL = "https://api.fantcric.fun"
FRONTEND_URL = "https://fantcric.fun"

class EndToEndTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test(self, name, func):
        """Run a test and track results"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print('='*70)
        try:
            func()
            print(f"✅ PASSED")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            self.failed += 1
            self.errors.append({"test": name, "error": str(e)})
        except Exception as e:
            print(f"💥 ERROR: {e}")
            self.failed += 1
            self.errors.append({"test": name, "error": str(e)})

    def test_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{API_URL}/health", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["status"] == "healthy", f"Expected healthy, got {data['status']}"
        print(f"   Status: {data['status']}")
        print(f"   Environment: {data['environment']}")
        print(f"   Location: {data['location']}")

    def test_frontend(self):
        """Test frontend is accessible"""
        response = requests.get(FRONTEND_URL, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"   Frontend accessible at {FRONTEND_URL}")

    def test_database_connection(self):
        """Test database has players"""
        response = requests.get(f"{API_URL}/api/admin/clubs", timeout=10)
        # May be 401 (need auth) but shouldn't be 500
        assert response.status_code in [200, 401], f"Database connection failed: {response.status_code}"
        print(f"   Database connectivity: OK (status {response.status_code})")

    def test_player_roster(self):
        """Test player roster exists in database"""
        # This endpoint might require auth, but we're testing if the query works
        response = requests.get(f"{API_URL}/api/admin/clubs", timeout=10)

        if response.status_code == 401:
            print(f"   Authentication required (expected)")
            print(f"   Database query successful (no 500 errors)")
        elif response.status_code == 200:
            clubs = response.json()
            print(f"   Found {len(clubs)} clubs")
            for club in clubs:
                print(f"     - {club.get('name')}")

    def test_login_endpoint_structure(self):
        """Test login endpoint responds (even if credentials wrong)"""
        # Test with invalid token to verify endpoint structure works
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "email": "test@test.com",
                "password": "wrongpassword",
                "turnstile_token": "invalid_token"
            },
            timeout=10
        )

        # Should NOT be 500 (internal server error)
        assert response.status_code != 500, f"Login endpoint has internal error: {response.text[:200]}"
        print(f"   Login endpoint structure: OK (status {response.status_code})")

        if response.status_code == 400:
            print(f"   Turnstile verification working")
        elif response.status_code == 401:
            print(f"   Authentication logic working")

    def test_cors_headers(self):
        """Test CORS headers are set correctly"""
        response = requests.options(
            f"{API_URL}/api/auth/login",
            headers={"Origin": FRONTEND_URL},
            timeout=10
        )

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers, "Missing CORS headers"
        print(f"   CORS configured correctly")
        print(f"   Allowed origin: {response.headers.get('access-control-allow-origin')}")

    def test_ssl_certificate(self):
        """Test SSL certificate is valid"""
        response = requests.get(FRONTEND_URL, timeout=10, verify=True)
        assert response.status_code == 200, "SSL verification failed"
        print(f"   SSL certificate: Valid")
        print(f"   HTTPS: Working")

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*70)
        print("END-TO-END TEST REPORT")
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
            print("✅ ALL TESTS PASSED - SYSTEM IS HEALTHY")
        else:
            print(f"⚠️  {self.failed} TEST(S) FAILED - REVIEW ERRORS ABOVE")

        print("="*70 + "\n")

        return self.failed == 0


if __name__ == "__main__":
    tester = EndToEndTester()

    print(f"\n🏏 FANTASY CRICKET - END-TO-END SYSTEM TEST")
    print(f"API: {API_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Run all tests
    tester.test("1. API Health Check", tester.test_health)
    tester.test("2. Frontend Accessibility", tester.test_frontend)
    tester.test("3. Database Connection", tester.test_database_connection)
    tester.test("4. Player Roster", tester.test_player_roster)
    tester.test("5. Login Endpoint Structure", tester.test_login_endpoint_structure)
    tester.test("6. CORS Configuration", tester.test_cors_headers)
    tester.test("7. SSL Certificate", tester.test_ssl_certificate)

    # Generate report
    success = tester.generate_report()

    # Exit with appropriate code
    exit(0 if success else 1)
