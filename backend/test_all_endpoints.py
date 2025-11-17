#!/usr/bin/env python3
"""
Comprehensive API Endpoint Test
Test ALL 64 endpoints systematically
"""

import requests
import json
import time

API_URL = "https://api.fantcric.fun"
ADMIN_EMAIL = "admin@fantcric.fun"
ADMIN_PASSWORD = "FantasyTest2025!"

class ComprehensiveEndpointTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.token = None

    def login(self):
        """Get admin token"""
        try:
            response = requests.post(
                f"{API_URL}/api/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD,
                    "turnstile_token": "test_token"
                },
                timeout=10
            )

            if response.status_code == 429:
                time.sleep(2)
                response = requests.post(
                    f"{API_URL}/api/auth/login",
                    json={
                        "email": ADMIN_EMAIL,
                        "password": ADMIN_PASSWORD,
                        "turnstile_token": "test_token"
                    },
                    timeout=10
                )

            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print(f"✅ Logged in successfully")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_endpoint(self, method, path, requires_auth=True, params=None):
        """Test a single endpoint"""
        url = f"{API_URL}{path}"

        headers = {}
        if requires_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Replace path parameters with test values
        url = url.replace("{season_id}", "2808d60f-bf55-4114-aa2e-16ba7511b4bd")
        url = url.replace("{club_id}", "625f1c55-6d5b-40a9-be1d-8f7abe6fa00e")
        url = url.replace("{team_id}", "test-team-id")
        url = url.replace("{player_id}", "test-player-id")
        url = url.replace("{league_id}", "d2510a16-a78f-4991-97ec-a44fe8eafe78")
        url = url.replace("{user_id}", "test-user-id")
        url = url.replace("{transfer_id}", "test-transfer-id")
        url = url.replace("{club_name}", "ACC")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=headers, json={}, timeout=5)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json={}, timeout=5)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json={}, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=5)
            else:
                return None

            # Consider these status codes as "not broken"
            # 200/201 = success
            # 400/401/403/404 = client errors (expected for test data)
            # 422 = validation error (expected for empty POST data)
            # 500/502/503 = SERVER errors (actual problems)

            if response.status_code >= 500:
                return {
                    "status": "ERROR",
                    "code": response.status_code,
                    "response": response.text[:200]
                }
            else:
                return {
                    "status": "OK",
                    "code": response.status_code
                }

        except requests.exceptions.Timeout:
            return {"status": "TIMEOUT"}
        except Exception as e:
            return {"status": "EXCEPTION", "error": str(e)}

    def test_all(self):
        """Test all endpoints"""
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE ENDPOINT TEST - ALL 64 ENDPOINTS")
        print(f"{'='*80}\n")

        # Load endpoints
        with open('/tmp/all_endpoints.json', 'r') as f:
            endpoints = json.load(f)

        # Try to login, but continue even if it fails (will test public endpoints)
        has_auth = self.login()
        if not has_auth:
            print("⚠️  Login failed - will test public endpoints without auth")
            print("   (Authenticated endpoints will return 401/403 instead of being fully tested)\n")

        print(f"\nTesting {len(endpoints)} endpoints...\n")

        results_by_status = {
            "OK": [],
            "ERROR": [],
            "TIMEOUT": [],
            "EXCEPTION": []
        }

        for i, endpoint in enumerate(endpoints, 1):
            method = endpoint['method']
            path = endpoint['path']

            # Determine if endpoint needs auth
            requires_auth = '/admin' in path or '/user' in path or '/auth/me' in path

            result = self.test_endpoint(method, path, requires_auth)

            if result:
                status = result['status']
                results_by_status[status].append({
                    'method': method,
                    'path': path,
                    'result': result
                })

                # Print progress
                status_symbol = {
                    "OK": "✅",
                    "ERROR": "❌",
                    "TIMEOUT": "⏱️",
                    "EXCEPTION": "💥"
                }.get(status, "❓")

                code_info = f" ({result.get('code', 'N/A')})" if 'code' in result else ""
                print(f"{status_symbol} [{i:2d}/64] {method:7s} {path[:60]:60s}{code_info}")

            time.sleep(0.1)  # Rate limiting

        # Summary
        print(f"\n{'='*80}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"✅ OK (no 500 errors):  {len(results_by_status['OK'])}")
        print(f"❌ SERVER ERRORS (500+): {len(results_by_status['ERROR'])}")
        print(f"⏱️  TIMEOUTS:            {len(results_by_status['TIMEOUT'])}")
        print(f"💥 EXCEPTIONS:          {len(results_by_status['EXCEPTION'])}")

        # Show server errors in detail
        if results_by_status['ERROR']:
            print(f"\n{'='*80}")
            print(f"❌ SERVER ERRORS (500+) - REQUIRES ATTENTION")
            print(f"{'='*80}")
            for item in results_by_status['ERROR']:
                print(f"\n{item['method']:7s} {item['path']}")
                print(f"  Status: {item['result']['code']}")
                print(f"  Response: {item['result'].get('response', 'N/A')[:150]}")

        # Show exceptions
        if results_by_status['EXCEPTION']:
            print(f"\n{'='*80}")
            print(f"💥 EXCEPTIONS")
            print(f"{'='*80}")
            for item in results_by_status['EXCEPTION']:
                print(f"\n{item['method']:7s} {item['path']}")
                print(f"  Error: {item['result'].get('error', 'N/A')}")

        print(f"\n{'='*80}")

        # Save detailed results
        with open('/tmp/endpoint_test_results.json', 'w') as f:
            json.dump(results_by_status, f, indent=2)
        print(f"Detailed results saved to: /tmp/endpoint_test_results.json")

        return len(results_by_status['ERROR']) + len(results_by_status['EXCEPTION'])

if __name__ == "__main__":
    tester = ComprehensiveEndpointTester()
    exit_code = tester.test_all()
    exit(exit_code)
