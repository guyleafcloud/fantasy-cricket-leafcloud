#!/usr/bin/env python3
"""
Phase 1: Single URL Smoke Test
Test that scraper can parse one 2025 scorecard correctly
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from kncb_html_scraper import KNCBMatchCentreScraper
from database import SessionLocal
from database_models import Player

# Test URL - Week 1, Match 1 (ACC team)
TEST_URL = "https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394"

async def test_single_url():
    print("="*70)
    print("PHASE 1: SINGLE URL SMOKE TEST")
    print("="*70)
    print(f"\nTest URL: {TEST_URL}\n")

    # Initialize scraper
    scraper = KNCBMatchCentreScraper()

    # Extract match ID from URL
    # Format: https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394
    # The match ID is the full "134453-7331235" format
    parts = TEST_URL.split('/')
    match_part = [p for p in parts if '-' in p and p != 'matchcentre.kncb.nl'][0]
    match_id = match_part  # Keep full format: "134453-7331235"

    print(f"📥 Extracting match ID: {match_id}")

    # Scrape the scorecard
    print(f"\n{'='*70}")
    print("STEP 1: SCRAPING SCORECARD")
    print('='*70)

    try:
        scorecard = await scraper.scrape_match_scorecard(match_id)

        if not scorecard:
            print("❌ Failed to scrape scorecard")
            return False

        print(f"✅ Scorecard scraped successfully")
        print(f"   Match: {scorecard.get('home_team', 'Unknown')} vs {scorecard.get('away_team', 'Unknown')}")
        print(f"   Date: {scorecard.get('match_date', 'Unknown')}")

        # Extract player performances
        player_performances = scorecard.get('player_performances', [])
        print(f"   Players: {len(player_performances)} performances extracted")

        if len(player_performances) == 0:
            print("❌ No player performances extracted")
            return False

    except Exception as e:
        print(f"❌ Error scraping scorecard: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Analyze performances
    print(f"\n{'='*70}")
    print("STEP 2: ANALYZING PLAYER PERFORMANCES")
    print('='*70)

    total_runs = sum(p.get('batting', {}).get('runs', 0) for p in player_performances)
    total_wickets = sum(p.get('bowling', {}).get('wickets', 0) for p in player_performances)
    total_catches = sum(p.get('fielding', {}).get('catches', 0) for p in player_performances)

    print(f"   Total runs: {total_runs}")
    print(f"   Total wickets: {total_wickets}")
    print(f"   Total catches: {total_catches}")

    # Show top 5 performers
    sorted_performers = sorted(player_performances,
                              key=lambda x: x.get('fantasy_points', 0),
                              reverse=True)

    print(f"\n   Top 5 Performers:")
    for i, player in enumerate(sorted_performers[:5], 1):
        name = player.get('player_name', 'Unknown')
        points = player.get('fantasy_points', 0)
        runs = player.get('batting', {}).get('runs', 0)
        wickets = player.get('bowling', {}).get('wickets', 0)
        catches = player.get('fielding', {}).get('catches', 0)

        print(f"   {i}. {name:25s} - {points:6.1f} pts (R:{runs}, W:{wickets}, C:{catches})")

    # Match to database
    print(f"\n{'='*70}")
    print("STEP 3: MATCHING TO DATABASE")
    print('='*70)

    try:
        db = SessionLocal()
        # Get all players from database (assuming ACC club)
        all_players = db.query(Player).all()
        db.close()

        print(f"   Database has {len(all_players)} players total")

        # Try to match scraped players to database
        matched_count = 0
        unmatched_players = []

        for performance in player_performances:
            player_name = performance.get('player_name', '')
            player_id = performance.get('player_id')

            # Simple name matching (exact or fuzzy)
            matched = False

            # First try player_id match
            if player_id:
                for db_player in all_players:
                    if hasattr(db_player, 'kncb_player_id') and db_player.kncb_player_id == player_id:
                        matched = True
                        matched_count += 1
                        break

            # Then try name match
            if not matched:
                normalized_name = player_name.lower().replace(' ', '').replace('.', '')
                for db_player in all_players:
                    db_normalized = db_player.name.lower().replace(' ', '').replace('.', '')
                    if normalized_name == db_normalized:
                        matched = True
                        matched_count += 1
                        break

            if not matched:
                unmatched_players.append(player_name)

        match_rate = (matched_count / len(player_performances)) * 100 if player_performances else 0

        print(f"\n   Matched: {matched_count}/{len(player_performances)} ({match_rate:.1f}%)")

        if unmatched_players:
            print(f"\n   ⚠️  Unmatched players ({len(unmatched_players)}):")
            for name in unmatched_players[:10]:  # Show first 10
                print(f"      - {name}")
            if len(unmatched_players) > 10:
                print(f"      ... and {len(unmatched_players) - 10} more")

    except Exception as e:
        print(f"❌ Error matching to database: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Manual verification prompts
    print(f"\n{'='*70}")
    print("STEP 4: MANUAL VERIFICATION")
    print('='*70)
    print(f"\n🔍 Please verify the following:")
    print(f"   1. Open the URL in your browser: {TEST_URL}")
    print(f"   2. Check that the top performer's stats match the scorecard")
    print(f"   3. Spot-check 2-3 other players' runs/wickets/catches")
    print(f"   4. Verify fantasy points calculation for top performer")

    if sorted_performers:
        top = sorted_performers[0]
        print(f"\n   Top performer to verify:")
        print(f"      Name: {top.get('player_name')}")
        print(f"      Runs: {top.get('batting', {}).get('runs', 0)}")
        print(f"      Balls: {top.get('batting', {}).get('balls_faced', 0)}")
        print(f"      Wickets: {top.get('bowling', {}).get('wickets', 0)}")
        print(f"      Overs: {top.get('bowling', {}).get('overs_bowled', 0)}")
        print(f"      Catches: {top.get('fielding', {}).get('catches', 0)}")
        print(f"      Fantasy Points: {top.get('fantasy_points', 0):.2f}")

    # Success criteria
    print(f"\n{'='*70}")
    print("SUCCESS CRITERIA")
    print('='*70)

    criteria = []
    criteria.append(("Scorecard parsed successfully", scorecard is not None))
    criteria.append(("20+ player performances extracted", len(player_performances) >= 20))
    criteria.append((">80% players matched to database", match_rate >= 80))
    criteria.append(("No scraper errors", True))  # If we got here, no exceptions

    all_passed = True
    for criterion, passed in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
        if not passed:
            all_passed = False

    print(f"\n{'='*70}")
    if all_passed:
        print("✅ PHASE 1: PASSED")
        print("   Ready to proceed to Phase 2 (Week 1 full test)")
    else:
        print("❌ PHASE 1: FAILED")
        print("   Fix issues before proceeding to Phase 2")
    print('='*70)

    return all_passed

if __name__ == "__main__":
    print("\n🏏 Starting Phase 1: Single URL Smoke Test\n")

    try:
        result = asyncio.run(test_single_url())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
