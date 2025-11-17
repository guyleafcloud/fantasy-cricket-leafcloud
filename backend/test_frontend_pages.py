#!/usr/bin/env python3
"""
Comprehensive Frontend Pages Test
Test all frontend routes for accessibility and errors
"""

import requests
import json

FRONTEND_URL = "https://fantcric.fun"

# All frontend routes discovered from page.tsx files
ROUTES = [
    "/",
    "/login",
    "/register",
    "/dashboard",
    "/how-to-play",
    "/calculator",
    "/leagues",
    "/teams",
    "/admin",
    "/admin/seasons",
    "/admin/leagues",
    "/admin/roster",
    "/admin/users",
]

# Routes that need dynamic IDs (will test structure but expect redirects/errors)
DYNAMIC_ROUTES = [
    "/admin/seasons/test-id",
    "/admin/leagues/test-id",
    "/leagues/test-id/leaderboard",
    "/teams/test-id",
    "/teams/test-id/build",
]

class FrontendPageTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test_route(self, route):
        """Test a single route"""
        url = f"{FRONTEND_URL}{route}"

        try:
            response = requests.get(url, timeout=10, allow_redirects=True)

            # Check for server errors
            if response.status_code >= 500:
                return {
                    "status": "ERROR",
                    "code": response.status_code,
                    "url": url
                }
            # Check for React/Next.js errors in HTML
            elif "Application error" in response.text or "Error:" in response.text[:1000]:
                return {
                    "status": "REACT_ERROR",
                    "code": response.status_code,
                    "url": url
                }
            else:
                return {
                    "status": "OK",
                    "code": response.status_code,
                    "url": url
                }

        except requests.exceptions.Timeout:
            return {"status": "TIMEOUT", "url": url}
        except Exception as e:
            return {"status": "EXCEPTION", "error": str(e), "url": url}

    def test_all(self):
        """Test all frontend routes"""
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE FRONTEND TEST - {len(ROUTES) + len(DYNAMIC_ROUTES)} ROUTES")
        print(f"{'='*80}\n")

        all_routes = ROUTES + DYNAMIC_ROUTES
        results_by_status = {
            "OK": [],
            "ERROR": [],
            "REACT_ERROR": [],
            "TIMEOUT": [],
            "EXCEPTION": []
        }

        for i, route in enumerate(all_routes, 1):
            result = self.test_route(route)

            if result:
                status = result['status']
                results_by_status[status].append(result)

                # Print progress
                status_symbol = {
                    "OK": "✅",
                    "ERROR": "❌",
                    "REACT_ERROR": "⚠️",
                    "TIMEOUT": "⏱️",
                    "EXCEPTION": "💥"
                }.get(status, "❓")

                code_info = f" ({result.get('code', 'N/A')})" if 'code' in result else ""
                route_display = f"{route[:50]:50s}" if len(route) <= 50 else f"{route[:47]}..."
                print(f"{status_symbol} [{i:2d}/{len(all_routes)}] {route_display} {code_info}")

        # Summary
        print(f"\n{'='*80}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"✅ OK (accessible):      {len(results_by_status['OK'])}")
        print(f"❌ SERVER ERRORS (500+): {len(results_by_status['ERROR'])}")
        print(f"⚠️  REACT ERRORS:        {len(results_by_status['REACT_ERROR'])}")
        print(f"⏱️  TIMEOUTS:            {len(results_by_status['TIMEOUT'])}")
        print(f"💥 EXCEPTIONS:          {len(results_by_status['EXCEPTION'])}")

        # Show errors in detail
        if results_by_status['ERROR']:
            print(f"\n{'='*80}")
            print(f"❌ SERVER ERRORS (500+)")
            print(f"{'='*80}")
            for item in results_by_status['ERROR']:
                print(f"\n  {item['url']}")
                print(f"  Status: {item['code']}")

        if results_by_status['REACT_ERROR']:
            print(f"\n{'='*80}")
            print(f"⚠️  REACT/APPLICATION ERRORS")
            print(f"{'='*80}")
            for item in results_by_status['REACT_ERROR']:
                print(f"\n  {item['url']}")
                print(f"  Status: {item['code']}")

        print(f"\n{'='*80}")

        # Save results
        with open('/tmp/frontend_test_results.json', 'w') as f:
            json.dump(results_by_status, f, indent=2)
        print(f"Detailed results saved to: /tmp/frontend_test_results.json")

        return len(results_by_status['ERROR']) + len(results_by_status['REACT_ERROR'])

if __name__ == "__main__":
    tester = FrontendPageTester()
    exit_code = tester.test_all()
    exit(exit_code)
