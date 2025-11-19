#!/usr/bin/env python3
"""
Live Demo Simulation - Using Mock Data for Reliability
======================================================
Since KNCB URLs timeout, this demo uses the validated mock server
to simulate a 2-week season with realistic data:

- Week 1: Generate performances → Show top 25 → Update teams
- Wait 60 seconds (1 minute = 1 week)
- Week 2: Generate performances → Show top 25 → Update teams

This guarantees the demo works and shows all features.

Usage:
    python3 live_demo_with_mock_data.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# Run the simulation script
DATABASE_URL = os.getenv('DATABASE_URL')


async def run_demo():
    print("="*80)
    print("🏏 LIVE DEMO SIMULATION - 2 WEEK SEASON")
    print("="*80)
    print("\nThis demo will:")
    print("  1. Simulate Week 1 matches (ACC teams)")
    print("  2. Calculate fantasy points for ALL players")
    print("  3. Show top 25 players")
    print("  4. Update fantasy team scores with captain/VC/WK bonuses")
    print("  5. Wait 60 seconds (1 minute = 1 week)")
    print("  6. Simulate Week 2 matches")
    print("  7. Show cumulative results")
    print("\n" + "="*80)
    print("\n⏱️  Total demo time: ~2 minutes\n")

    input("Press ENTER to start the demo...")

    # WEEK 1
    print("\n" + "="*80)
    print("📅 WEEK 1 - SIMULATING MATCHES...")
    print("="*80)

    os.system("python3 /app/simulate_live_teams.py 1")

    print("\n✅ Week 1 complete!")
    print("\n👉 Visit https://fantcric.fun to see:")
    print("   - League leaderboard (updated team totals)")
    print("   - League stats page (top 25 players)")
    print("   - Your fantasy team (player scores with captain/VC bonuses)")

    # WAIT
    print(f"\n{'='*80}")
    print("⏰ WAITING 60 SECONDS (1 minute = 1 week in demo)")
    print("="*80)
    print("\nWhat to check during this time:")
    print("  1. Go to https://fantcric.fun")
    print("  2. Click on your league")
    print("  3. Check the leaderboard - teams should have Week 1 points")
    print("  4. Click 'Stats' - should show top 25 performers")
    print("  5. Click your team - should show individual player scores")
    print()

    for i in range(60, 0, -10):
        print(f"   ⏳ {i} seconds until Week 2...")
        await asyncio.sleep(10)

    # WEEK 2
    print("\n" + "="*80)
    print("📅 WEEK 2 - SIMULATING MATCHES...")
    print("="*80)

    os.system("python3 /app/simulate_live_teams.py 2")

    print("\n✅ Week 2 complete!")
    print("\n👉 Refresh https://fantcric.fun to see:")
    print("   - Updated leaderboard (Week 1 + Week 2 cumulative)")
    print("   - New top 25 performers from Week 2")
    print("   - Updated fantasy team totals")

    # FINAL RESULTS
    print(f"\n{'='*80}")
    print("🏆 DEMO COMPLETE - FINAL RESULTS")
    print("="*80)

    # Show final stats
    print("\n📊 Getting final statistics...\n")

    import subprocess
    result = subprocess.run([
        "python3", "-c",
        """
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    # Leaderboard
    print("\\n📊 FINAL LEADERBOARD:")
    print("-" * 80)
    result = conn.execute(text('''
        SELECT
            ROW_NUMBER() OVER (ORDER BY ft.total_points DESC) as rank,
            ft.team_name,
            COALESCE(u.full_name, u.email) as owner,
            ROUND(ft.total_points::numeric, 1) as points
        FROM fantasy_teams ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.is_finalized = TRUE
        ORDER BY ft.total_points DESC
    '''))
    for row in result:
        print(f"   {row[0]:2d}. {row[1]:30s} ({row[2]:20s}) - {row[3]:8.1f} pts")

    # Top performers across both weeks
    print("\\n\\n🌟 TOP 10 PERFORMERS (BOTH WEEKS COMBINED):")
    print("-" * 80)
    result = conn.execute(text('''
        SELECT
            p.name,
            SUM(pp.runs) as total_runs,
            SUM(pp.wickets) as total_wickets,
            SUM(pp.catches) as total_catches,
            ROUND(SUM(pp.final_fantasy_points)::numeric, 1) as total_points
        FROM player_performances pp
        JOIN players p ON pp.player_id = p.id
        GROUP BY p.id, p.name
        ORDER BY SUM(pp.final_fantasy_points) DESC
        LIMIT 10
    '''))
    for i, row in enumerate(result, 1):
        stats = []
        if row[1] > 0:
            stats.append(f"{row[1]}r")
        if row[2] > 0:
            stats.append(f"{row[2]}w")
        if row[3] > 0:
            stats.append(f"{row[3]}ct")
        stats_str = f"({', '.join(stats)})" if stats else ""
        print(f"   {i:2d}. {row[0]:30s} {row[4]:7.1f} pts {stats_str}")

    # Stats
    print("\\n\\n📈 DEMO STATISTICS:")
    print("-" * 80)
    result = conn.execute(text('''
        SELECT
            COUNT(DISTINCT player_id) as total_players,
            COUNT(*) as total_performances,
            ROUND(AVG(final_fantasy_points)::numeric, 1) as avg_points,
            ROUND(MAX(final_fantasy_points)::numeric, 1) as max_points
        FROM player_performances
    '''))
    row = result.fetchone()
    print(f"   Total unique players: {row[0]}")
    print(f"   Total performances: {row[1]}")
    print(f"   Average fantasy points: {row[2]}")
    print(f"   Highest single performance: {row[3]} pts")
"""
    ], capture_output=False)

    print("\n" + "="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print("\n🎯 What was demonstrated:")
    print("   ✓ Match simulation for 2 weeks")
    print("   ✓ Fantasy points calculation (tiered system)")
    print("   ✓ Player multipliers (handicap system)")
    print("   ✓ Captain bonuses (2x)")
    print("   ✓ Vice-captain bonuses (1.5x)")
    print("   ✓ Wicketkeeper catch bonuses (2x)")
    print("   ✓ Cumulative scoring across rounds")
    print("   ✓ Leaderboard updates")
    print("   ✓ Top 25 players (including non-fantasy-team players)")
    print("\n🌐 View results at: https://fantcric.fun")
    print("\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
