#!/usr/bin/env python3
"""
Test Runner for Scraper Tests
==============================
Runs all scraper tests and provides a summary report.

Usage:
    python tests/run_tests.py
    python tests/run_tests.py --verbose
    python tests/run_tests.py --test test_fantasy_points_calculation
"""

import sys
import subprocess
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header():
    """Print test header"""
    print()
    print("=" * 80)
    print(f"{BLUE}🏏 KNCB SCRAPER TEST SUITE{RESET}")
    print("=" * 80)
    print()
    print("Testing Components:")
    print("  ✓ Tier determination")
    print("  ✓ Fantasy points calculation")
    print("  ✓ API response parsing")
    print("  ✓ HTML fallback parsing")
    print("  ✓ Player stats extraction")
    print("  ✓ Match finding")
    print("  ✓ Full integration flow")
    print()
    print("=" * 80)
    print()


def run_tests(verbose=False, specific_test=None):
    """Run the test suite"""

    print_header()

    # Build pytest command
    cmd = ['pytest', 'tests/test_scraper_with_mocks.py']

    if verbose:
        cmd.append('-v')
        cmd.append('-s')
    else:
        cmd.append('-v')

    if specific_test:
        cmd.append(f'-k {specific_test}')

    cmd.extend(['--tb=short', '--color=yes'])

    # Run tests
    print(f"{YELLOW}Running tests...{RESET}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    print()
    print("=" * 80)

    if result.returncode == 0:
        print(f"{GREEN}✅ ALL TESTS PASSED!{RESET}")
        print()
        print("Your scraper logic is working correctly!")
        print("Next steps:")
        print("  1. Test with real match data (see test_with_real_data.py)")
        print("  2. Integrate with database")
        print("  3. Test full pipeline with sample season data")
    else:
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")
        print()
        print("Please check the output above for details.")

    print("=" * 80)
    print()

    return result.returncode


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Run scraper tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', '-t', type=str, help='Run specific test')

    args = parser.parse_args()

    return run_tests(verbose=args.verbose, specific_test=args.test)


if __name__ == '__main__':
    sys.exit(main())
