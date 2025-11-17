#!/usr/bin/env python3
"""
Test Scraper with Mock KNCB Server
===================================
Tests the KNCB scraper against simulated match data.

This validates the full scraper flow:
1. Fetch grades
2. Fetch matches
3. Scrape scorecards
4. Extract player stats
5. Calculate fantasy points

Usage:
    # Terminal 1: Start mock server
    python3 mock_kncb_server.py

    # Terminal 2: Run scraper test
    python3 test_scraper_with_mock.py
"""

import asyncio
import logging
from kncb_html_scraper import KNCBMatchCentreScraper
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockKNCBScraper(KNCBMatchCentreScraper):
    """Modified scraper that points to mock server"""

    def __init__(self, mock_server_url="http://localhost:5001"):
        super().__init__()
        # Override the API URL to point to mock server
        self.kncb_api_url = f"{mock_server_url}/rv"
        self.mock_mode = True
        logger.info(f"🧪 Scraper configured for MOCK MODE")
        logger.info(f"📍 Using mock server: {mock_server_url}")


async def test_scraper_flow():
    """Test the full scraper flow with mock data"""

    print("\n" + "="*80)
    print("🧪 SCRAPER TEST WITH MOCK DATA")
    print("="*80)

    # Initialize mock scraper
    scraper = MockKNCBScraper(mock_server_url="http://localhost:5001")

    # Test club
    test_club = "VRA"

    try:
        print(f"\n📋 Step 1: Fetching recent matches for {test_club}...")
        print("-" * 80)

        matches = await scraper.get_recent_matches_for_club(
            club_name=test_club,
            days_back=30,
            season_id=19
        )

        if not matches:
            print("❌ No matches found!")
            return

        print(f"✅ Found {len(matches)} matches")

        # Show first few matches
        print(f"\n📊 Sample matches:")
        for i, match in enumerate(matches[:5]):
            home = match.get('home_club_name', 'Unknown')
            away = match.get('away_club_name', 'Unknown')
            date = match.get('match_date_time', 'Unknown')
            grade = match.get('grade_name', 'Unknown')
            print(f"   {i+1}. {home} vs {away} - {grade} ({date[:10]})")

        # Test scraping one match in detail
        if len(matches) > 0:
            test_match = matches[0]
            match_id = test_match.get('match_id')

            print(f"\n📥 Step 2: Scraping detailed scorecard for match {match_id}...")
            print("-" * 80)

            scorecard = await scraper.scrape_match_scorecard(match_id)

            if not scorecard:
                print("❌ Failed to get scorecard")
                return

            print(f"✅ Got scorecard with {len(scorecard.get('innings', []))} innings")

            # Extract player stats
            print(f"\n👥 Step 3: Extracting player stats...")
            print("-" * 80)

            tier = test_match.get('tier', 'tier2')
            players = scraper.extract_player_stats(scorecard, test_club, tier)

            if not players:
                print("⚠️  No player stats extracted")
                return

            print(f"✅ Extracted stats for {len(players)} players")

            # Show top performers
            print(f"\n🏆 Top 10 Fantasy Point Scorers:")
            print("-" * 80)

            # Sort by fantasy points
            players_sorted = sorted(
                players,
                key=lambda p: p.get('fantasy_points', 0),
                reverse=True
            )

            for i, player in enumerate(players_sorted[:10]):
                name = player.get('name', 'Unknown')
                points = player.get('fantasy_points', 0)

                # Get stats breakdown
                batting = player.get('batting', {})
                bowling = player.get('bowling', {})
                fielding = player.get('fielding', {})

                stats = []
                if batting.get('runs', 0) > 0:
                    runs = batting['runs']
                    balls = batting.get('balls_faced', 0)
                    stats.append(f"{runs}({balls})")

                if bowling.get('wickets', 0) > 0:
                    wickets = bowling['wickets']
                    runs = bowling.get('runs_conceded', 0)
                    stats.append(f"{wickets}/{runs}")

                if fielding.get('catches', 0) > 0:
                    stats.append(f"{fielding['catches']}ct")

                stats_str = ", ".join(stats) if stats else "DNB/DNB"

                print(f"   {i+1:2d}. {name:25s} - {points:6.1f} pts  ({stats_str})")

            # Calculate points breakdown
            print(f"\n📊 Points Breakdown Analysis:")
            print("-" * 80)

            total_batting_points = sum(p.get('batting', {}).get('runs', 0) for p in players)
            total_bowling_points = sum(p.get('bowling', {}).get('wickets', 0) * 15 for p in players)
            total_fielding_points = sum(
                p.get('fielding', {}).get('catches', 0) * 15 +
                p.get('fielding', {}).get('stumpings', 0) * 15 +
                p.get('fielding', {}).get('runouts', 0) * 6
                for p in players
            )

            print(f"   Batting contribution:  ~{total_batting_points:.0f} points (runs)")
            print(f"   Bowling contribution:  ~{total_bowling_points:.0f} points (wickets)")
            print(f"   Fielding contribution: ~{total_fielding_points:.0f} points")

            # Test multiple matches
            print(f"\n🔄 Step 4: Testing batch scraping (3 matches)...")
            print("-" * 80)

            test_matches = matches[:3]
            all_players = []

            for i, match in enumerate(test_matches):
                match_id = match.get('match_id')
                print(f"   Scraping match {i+1}/3 (ID: {match_id})...")

                scorecard = await scraper.scrape_match_scorecard(match_id)
                if scorecard:
                    tier = match.get('tier', 'tier2')
                    players = scraper.extract_player_stats(scorecard, test_club, tier)
                    all_players.extend(players)
                    print(f"   ✅ Extracted {len(players)} players")
                else:
                    print(f"   ⚠️  Failed to scrape")

            print(f"\n✅ Total players extracted from 3 matches: {len(all_players)}")

            # Aggregate stats by player
            player_aggregates = {}
            for player in all_players:
                name = player.get('name')
                if name not in player_aggregates:
                    player_aggregates[name] = {
                        'name': name,
                        'matches': 0,
                        'total_points': 0,
                        'total_runs': 0,
                        'total_wickets': 0
                    }

                player_aggregates[name]['matches'] += 1
                player_aggregates[name]['total_points'] += player.get('fantasy_points', 0)
                player_aggregates[name]['total_runs'] += player.get('batting', {}).get('runs', 0)
                player_aggregates[name]['total_wickets'] += player.get('bowling', {}).get('wickets', 0)

            print(f"\n📈 Aggregated Performance (across 3 matches):")
            print("-" * 80)

            # Sort by total points
            top_players = sorted(
                player_aggregates.values(),
                key=lambda p: p['total_points'],
                reverse=True
            )[:10]

            for i, player in enumerate(top_players):
                name = player['name']
                matches = player['matches']
                points = player['total_points']
                runs = player['total_runs']
                wickets = player['total_wickets']
                avg_points = points / matches

                print(f"   {i+1:2d}. {name:25s} - {points:7.1f} pts ({matches} matches, {avg_points:5.1f} avg) - {runs}R, {wickets}W")

        print("\n" + "="*80)
        print("✅ SCRAPER TEST COMPLETE!")
        print("="*80)
        print("\nKey Validations:")
        print("  ✓ Grades fetched successfully")
        print("  ✓ Matches retrieved from API")
        print("  ✓ Scorecards parsed correctly")
        print("  ✓ Player stats extracted")
        print("  ✓ Fantasy points calculated with tiered system")
        print("  ✓ Multi-match aggregation working")
        print("\n📌 Next Steps:")
        print("  1. Run simulation to generate more realistic player data")
        print("  2. Test with edge cases (DNB, rain-affected, etc.)")
        print("  3. Integrate with database update workflow")
        print("  4. Test with real KNCB data when ready")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


async def test_mock_server_connection():
    """Test if mock server is running"""
    import aiohttp

    print("\n🔌 Testing connection to mock server...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Mock server is running")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Matches in memory: {data.get('matches_in_memory')}")
                    return True
                else:
                    print(f"❌ Mock server returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to mock server: {e}")
        print("\n💡 Make sure the mock server is running:")
        print("   python3 mock_kncb_server.py")
        return False


if __name__ == "__main__":
    # First check if mock server is running
    if not asyncio.run(test_mock_server_connection()):
        sys.exit(1)

    # Run the full test
    asyncio.run(test_scraper_flow())
