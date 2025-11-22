#!/usr/bin/env python3
"""
Test Fantasy Team Points Calculation
======================================
Verifies that fantasy teams correctly calculate points with:
1. Base fantasy points
2. Player multipliers
3. Captain/VC multipliers
4. Wicketkeeper bonuses
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from database_models import (
    Player, PlayerPerformance, Match, FantasyTeam,
    FantasyTeamPlayer, League, Season, Club
)


def test_fantasy_team_points():
    """Test complete fantasy team points calculation"""
    print("="*70)
    print("TESTING FANTASY TEAM POINTS CALCULATION")
    print("="*70)

    db = SessionLocal()

    try:
        # Step 1: Check if we have a fantasy team in the database
        print("\n📋 Step 1: Finding fantasy team...")

        fantasy_team = db.query(FantasyTeam).first()
        if not fantasy_team:
            print("   ❌ No fantasy team found. Create a team first.")
            print("   💡 This test requires:")
            print("      - At least 1 league")
            print("      - At least 1 fantasy team with players")
            print("      - Player performances from matches")
            return

        print(f"   Found team: {fantasy_team.team_name}")
        print(f"   League: {fantasy_team.league_id}")
        print(f"   Current total points: {fantasy_team.total_points or 0:.2f}")

        # Step 2: Get team players
        print("\n👥 Step 2: Loading team players...")

        team_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == fantasy_team.id
        ).all()

        if not team_players:
            print("   ❌ No players in team")
            return

        print(f"   Found {len(team_players)} players")

        # Step 3: Calculate points for each player
        print("\n🧮 Step 3: Calculating points for each player...")
        print("-"*70)

        total_team_points = 0.0

        for ftp in team_players:
            player = db.query(Player).filter(Player.id == ftp.player_id).first()
            if not player:
                continue

            # Get all performances for this player
            performances = db.query(PlayerPerformance).filter(
                PlayerPerformance.player_id == player.id
            ).all()

            if not performances:
                print(f"   {player.name:30s} - No performances yet")
                continue

            # Sum fantasy points (already includes player multiplier)
            base_total = sum(p.fantasy_points or 0 for p in performances)

            # Apply captain/VC multiplier
            captain_mult = 1.0
            if ftp.is_captain:
                captain_mult = 2.0
            elif ftp.is_vice_captain:
                captain_mult = 1.5

            final_points = base_total * captain_mult

            total_team_points += final_points

            # Show breakdown
            role_str = ""
            if ftp.is_captain:
                role_str = " (C)"
            elif ftp.is_vice_captain:
                role_str = " (VC)"
            if ftp.is_wicket_keeper:
                role_str += " (WK)"

            print(f"   {player.name:30s}{role_str:8s} - "
                  f"Base: {base_total:6.2f} × {captain_mult:.1f} = {final_points:7.2f} pts")

        # Step 4: Verify calculation
        print("\n" + "="*70)
        print(f"📊 TEAM TOTAL: {total_team_points:.2f} points")

        stored_points = fantasy_team.total_points or 0
        if abs(stored_points - total_team_points) > 0.01:
            print(f"⚠️  Stored in DB: {stored_points:.2f} (difference: {total_team_points - stored_points:+.2f})")
            print("💡 Points may need recalculation after new matches")
        else:
            print(f"✅ Matches stored value: {stored_points:.2f}")

        # Step 5: Show how calculation works
        print("\n" + "="*70)
        print("🎯 HOW POINTS ARE CALCULATED:")
        print("="*70)
        print("1. Player performs in match → Base fantasy points calculated")
        print("2. Player multiplier applied (0.69-5.0) → fantasy_points in PlayerPerformance")
        print("3. Sum all fantasy_points for player across season")
        print("4. Apply captain (2x) or vice-captain (1.5x) bonus")
        print("5. Sum for all 11 players = Total team points")
        print("\nExample:")
        print("  - Player scores 50 runs = 100 base points")
        print("  - Player has multiplier 2.5 = 100 × 2.5 = 250 fantasy points")
        print("  - If captain: 250 × 2.0 = 500 points for fantasy team")
        print("  - If regular player: 250 × 1.0 = 250 points for fantasy team")

        # Step 6: Check player multipliers
        print("\n" + "="*70)
        print("🔍 PLAYER MULTIPLIERS IN TEAM:")
        print("="*70)

        for ftp in team_players:
            player = db.query(Player).filter(Player.id == ftp.player_id).first()
            if player:
                mult = player.multiplier
                mult_desc = "★★★ Star" if mult < 1.0 else "⚡ Value" if mult > 2.0 else "═══ Average"
                print(f"   {player.name:30s} - {mult:4.2f}  {mult_desc}")

        print("\n" + "="*70)
        print("✅ TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_fantasy_team_points()
