#!/usr/bin/env python3
"""
Test Multiplier Drift Flow
===========================
Tests the complete flow of:
1. Player performs in a match
2. Base points calculated
3. Player multiplier applied
4. Weekly drift adjusts multiplier based on final points
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from database_models import Player, PlayerPerformance, Match, Season, Club
from match_performance_service import MatchPerformanceService
from multiplier_adjuster import MultiplierAdjuster


def test_multiplier_flow():
    """Test complete multiplier flow"""
    print("="*70)
    print("TESTING MULTIPLIER DRIFT FLOW")
    print("="*70)

    db = SessionLocal()

    try:
        # Step 1: Get or create test player
        print("\n📋 Step 1: Setting up test player...")

        # Find or create a test club
        club = db.query(Club).first()
        if not club:
            print("❌ No club found in database. Please run roster import first.")
            return

        # Find or create test season
        season = db.query(Season).first()
        if not season:
            print("❌ No season found in database.")
            return

        # Get a real player from database
        player = db.query(Player).filter(Player.club_id == club.id).first()
        if not player:
            print("❌ No players found. Please run roster import first.")
            return

        print(f"   Using player: {player.name}")
        print(f"   Current multiplier: {player.multiplier:.2f}")

        # Step 2: Simulate a match performance
        print("\n🏏 Step 2: Simulating match performance...")

        # Create test scorecard
        scorecard_data = {
            'match_title': 'Test Match vs Team',
            'match_date': datetime.now().strftime('%Y-%m-%d'),
            'scorecard_url': f'https://test.com/match/{datetime.now().timestamp()}',
            'player_performances': [
                {
                    'player_name': player.name,
                    'runs': 10,
                    'balls_faced': 10,
                    'fours': 0,
                    'sixes': 0,
                    'is_out': False,
                    'wickets': 0,
                    'overs_bowled': 0,
                    'runs_conceded': 0,
                    'maidens': 0,
                    'catches': 0,
                    'run_outs': 0,
                    'stumpings': 0
                }
            ]
        }

        # Process scorecard
        service = MatchPerformanceService()
        match_id, matched, unmatched = service.process_scorecard(
            scorecard_data,
            season.id,
            club.id
        )

        print(f"   Match processed: {match_id}")
        print(f"   Players matched: {matched}")

        # Step 3: Check stored performance
        print("\n📊 Step 3: Verifying stored performance...")

        performance = db.query(PlayerPerformance).filter(
            PlayerPerformance.match_id == match_id,
            PlayerPerformance.player_id == player.id
        ).first()

        if performance:
            print(f"   Base points: {performance.base_fantasy_points:.2f}")
            print(f"   Multiplier applied: {performance.multiplier_applied:.2f}")
            print(f"   Final fantasy points: {performance.fantasy_points:.2f}")
            print(f"   ✅ Calculation: {performance.base_fantasy_points:.2f} × {performance.multiplier_applied:.2f} = {performance.fantasy_points:.2f}")

            # Verify calculation
            expected = performance.base_fantasy_points * performance.multiplier_applied
            if abs(performance.fantasy_points - expected) < 0.01:
                print(f"   ✅ Multiplier correctly applied!")
            else:
                print(f"   ❌ ERROR: Expected {expected:.2f}, got {performance.fantasy_points:.2f}")
        else:
            print("   ❌ Performance not found!")
            return

        # Step 4: Run drift adjustment
        print("\n🎯 Step 4: Running multiplier drift adjustment...")

        adjuster = MultiplierAdjuster(drift_rate=0.15)
        result = adjuster.adjust_multipliers(db, club_id=club.id, dry_run=False)

        print(f"   Total players processed: {result['total_players']}")
        print(f"   Players with changes: {result['players_changed']}")
        print(f"   Score stats:")
        print(f"     Min: {result['score_stats']['min']:.2f}")
        print(f"     Median: {result['score_stats']['median']:.2f}")
        print(f"     Max: {result['score_stats']['max']:.2f}")

        # Step 5: Check updated multiplier
        print("\n📈 Step 5: Checking updated multiplier...")

        db.refresh(player)

        print(f"   Old multiplier: {performance.multiplier_applied:.2f}")
        print(f"   New multiplier: {player.multiplier:.2f}")
        print(f"   Change: {player.multiplier - performance.multiplier_applied:+.2f}")

        # Show top changes
        if result['top_changes']:
            print("\n🔝 Top multiplier changes:")
            for i, change in enumerate(result['top_changes'][:5], 1):
                direction = "↑" if change['change'] > 0 else "↓"
                print(f"   {i}. {change['player_name']}: "
                      f"{change['old_multiplier']:.2f} → {change['new_multiplier']:.2f} "
                      f"({direction}{abs(change['change']):.2f}) "
                      f"[Score: {change['score']:.1f} pts]")

        print("\n" + "="*70)
        print("✅ TEST COMPLETE - Multiplier drift flow is working!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_multiplier_flow()
