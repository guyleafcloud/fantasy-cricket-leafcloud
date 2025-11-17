#!/usr/bin/env python3
"""
Recalculate ACC Player Multipliers from 2025 Season Data
=========================================================
Uses the complete 2025 season statistics and rules-set-1.py to calculate
accurate multipliers for all ACC players and update the database.

Usage:
    python3 recalculate_2025_multipliers.py
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List
import statistics

# Import centralized fantasy points calculator
import importlib
rules_module = importlib.import_module('rules-set-1')
FANTASY_RULES = rules_module.FANTASY_RULES
calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

# Database connection
try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)

DB_PASSWORD = os.getenv('DB_PASSWORD', '_8dbdlHVu5kVHclQhPkqhg8IuLa6Ni1QcR0GUT7M9d0')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_URL = f"postgresql://cricket_admin:{DB_PASSWORD}@{DB_HOST}:5432/fantasy_cricket"

# ACC Club ID from database
ACC_CLUB_ID = '625f1c55-6d5b-40a9-be1d-8f7abe6fa00e'


def calculate_player_season_points(player_stats: Dict) -> float:
    """
    Calculate total fantasy points from season statistics
    Uses centralized rules from rules-set-1.py

    Args:
        player_stats: Dict with keys: runs, batting_avg, strike_rate, wickets,
                      bowling_avg, economy, catches, run_outs, matches
    """
    # Extract stats
    runs = player_stats.get('runs', 0)
    wickets = player_stats.get('wickets', 0)
    catches = player_stats.get('catches', 0)
    run_outs = player_stats.get('run_outs', 0)
    strike_rate = player_stats.get('strike_rate', 100.0)
    economy = player_stats.get('economy', 6.0)
    matches = player_stats.get('matches', 1)

    # Calculate balls_faced from runs and strike_rate
    if strike_rate > 0 and runs > 0:
        balls_faced = int(runs / (strike_rate / 100))
    else:
        balls_faced = 0

    # Calculate overs bowled from wickets and economy
    # Assumption: average 3 overs per match for bowlers
    if wickets > 0 and economy > 0:
        overs = matches * 3.0  # Rough estimate
    else:
        overs = 0.0

    # Calculate runs conceded
    runs_conceded = int(overs * economy) if overs > 0 else 0

    # Calculate fantasy points
    result = calculate_total_fantasy_points(
        runs=runs,
        balls_faced=balls_faced,
        is_out=False,  # Not relevant for season totals
        wickets=wickets,
        overs=overs,
        runs_conceded=runs_conceded,
        maidens=0,  # Not available in our data
        catches=catches,
        stumpings=0,  # Not available in our data
        runouts=run_outs,
        is_wicketkeeper=False  # Not relevant for multiplier calculation
    )

    return result['grand_total']


def calculate_multiplier(
    player_score: float,
    min_score: float,
    median_score: float,
    max_score: float
) -> float:
    """
    Calculate multiplier based on player's score relative to median

    Multiplier Scale:
    - Below median (weaker players): 1.0 to 5.0 (linear scale)
    - At median: 1.0
    - Above median (stronger players): 1.0 to 0.69 (linear scale)

    This creates a reverse handicap: strong players get lower multipliers (handicap),
    weak players get higher multipliers (boost).
    """
    # Get bounds from centralized rules
    min_multiplier = FANTASY_RULES['player_multipliers']['min']  # 0.69
    max_multiplier = FANTASY_RULES['player_multipliers']['max']  # 5.0
    neutral_multiplier = FANTASY_RULES['player_multipliers']['neutral']  # 1.0

    if median_score == 0:
        return neutral_multiplier

    if player_score <= median_score:
        # Below median: interpolate from max_multiplier (min_score) to neutral (median)
        if median_score == min_score:
            return neutral_multiplier
        ratio = (player_score - min_score) / (median_score - min_score)
        return max_multiplier - (ratio * (max_multiplier - neutral_multiplier))
    else:
        # Above median: interpolate from neutral (median) to min_multiplier (max_score)
        if max_score == median_score:
            return neutral_multiplier
        ratio = (player_score - median_score) / (max_score - median_score)
        return neutral_multiplier - (ratio * (neutral_multiplier - min_multiplier))


def load_2025_roster():
    """Load the 2025 ACC roster data"""
    roster_file = 'rosters/acc_2025_complete.json'

    print(f"📂 Loading 2025 ACC roster from: {roster_file}")
    with open(roster_file, 'r') as f:
        data = json.load(f)

    players = data.get('players', [])
    print(f"   Found {len(players)} players from 2025 season")
    return players


def calculate_all_multipliers(players: List[Dict]) -> List[Dict]:
    """Calculate fantasy points and multipliers for all players"""

    print("\n🔢 Calculating season fantasy points for all players...")
    player_scores = []

    for player in players:
        stats = player.get('stats', {})
        if not stats or stats.get('matches', 0) == 0:
            print(f"   ⚠️  Warning: {player['name']} has no stats, will get neutral multiplier")
            player['fantasy_points'] = 0.0
            player_scores.append(0.0)
        else:
            points = calculate_player_season_points(stats)
            player['fantasy_points'] = round(points, 2)
            player_scores.append(points)

    # Calculate league statistics
    print("\n📊 Calculating league statistics...")
    scores_with_data = [s for s in player_scores if s > 0]

    if not scores_with_data:
        print("❌ No players with stats found!")
        return players

    min_score = min(scores_with_data)
    max_score = max(scores_with_data)
    median_score = statistics.median(scores_with_data)
    mean_score = statistics.mean(player_scores)

    print(f"   Minimum:  {min_score:7.2f} points (excluding 0s)")
    print(f"   Median:   {median_score:7.2f} points")
    print(f"   Mean:     {mean_score:7.2f} points (including 0s)")
    print(f"   Maximum:  {max_score:7.2f} points")

    # Calculate multipliers
    print("\n⚖️  Calculating multipliers for all players...")
    for player in players:
        player_score = player['fantasy_points']

        # Players with 0 points (no stats) get neutral multiplier
        if player_score == 0:
            player['multiplier'] = 1.0
        else:
            multiplier = calculate_multiplier(
                player_score, min_score, median_score, max_score
            )
            player['multiplier'] = round(multiplier, 2)

    # Sort players by fantasy points (descending)
    players.sort(key=lambda x: x['fantasy_points'], reverse=True)

    return players


def display_results(players: List[Dict]):
    """Display the calculated results"""

    print(f"\n🏆 TOP 10 PLAYERS (Lowest Multipliers - Best Performers):")
    print(f"{'Rank':<6}{'Name':<30}{'Team':<12}{'Points':<10}{'Multiplier':<12}")
    print("-" * 70)
    for i, player in enumerate(players[:10], 1):
        print(f"{i:<6}{player['name']:<30}{player.get('team_level', 'N/A'):<12}"
              f"{player['fantasy_points']:<10.1f}{player['multiplier']:<12.2f}")

    print(f"\n📉 BOTTOM 10 PLAYERS (Highest Multipliers - Weakest Performers):")
    print(f"{'Rank':<6}{'Name':<30}{'Team':<12}{'Points':<10}{'Multiplier':<12}")
    print("-" * 70)
    for i, player in enumerate(players[-10:], 1):
        print(f"{i:<6}{player['name']:<30}{player.get('team_level', 'N/A'):<12}"
              f"{player['fantasy_points']:<10.1f}{player['multiplier']:<12.2f}")

    print(f"\n📊 Multiplier Distribution:")
    multipliers = [p['multiplier'] for p in players]
    print(f"   Range: {min(multipliers):.2f} - {max(multipliers):.2f}")
    print(f"   Players with 0.69 (best): {sum(1 for m in multipliers if m == 0.69)}")
    print(f"   Players < 1.0 (above median): {sum(1 for m in multipliers if m < 1.0)}")
    print(f"   Players = 1.0 (at median or no data): {sum(1 for m in multipliers if m == 1.0)}")
    print(f"   Players > 1.0 (below median): {sum(1 for m in multipliers if m > 1.0)}")
    print(f"   Players with 5.0 (worst): {sum(1 for m in multipliers if m == 5.0)}")


def update_database(players: List[Dict]):
    """Update player multipliers in the database"""

    print(f"\n💾 Updating database with new multipliers...")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Get all current players from database
        cursor.execute("""
            SELECT id, name, club_id FROM players
            WHERE club_id = %s
        """, (ACC_CLUB_ID,))

        db_players = {row[1]: row[0] for row in cursor.fetchall()}  # name -> id mapping
        print(f"   Found {len(db_players)} players in database")

        # Update multipliers
        updated = 0
        not_found = []
        timestamp = datetime.utcnow()

        for player in players:
            player_name = player['name']
            multiplier = player['multiplier']

            if player_name in db_players:
                player_id = db_players[player_name]

                cursor.execute("""
                    UPDATE players
                    SET multiplier = %s, multiplier_updated_at = %s
                    WHERE id = %s
                """, (multiplier, timestamp, player_id))

                updated += 1
            else:
                not_found.append(player_name)

        # Commit changes
        conn.commit()

        print(f"\n✅ Database update complete!")
        print(f"   Updated: {updated} players")
        print(f"   Not found in DB: {len(not_found)}")

        if not_found and len(not_found) <= 10:
            print(f"\n⚠️  Players not found in database:")
            for name in not_found:
                print(f"   - {name}")

        # Verify update
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                MIN(multiplier) as min,
                MAX(multiplier) as max,
                AVG(multiplier) as avg
            FROM players
            WHERE club_id = %s AND multiplier IS NOT NULL
        """, (ACC_CLUB_ID,))

        stats = cursor.fetchone()
        print(f"\n📊 Database multiplier statistics:")
        print(f"   Total ACC players with multipliers: {stats[0]}")
        print(f"   Range: {stats[1]:.2f} - {stats[2]:.2f}")
        print(f"   Average: {stats[3]:.2f}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Database error: {e}")
        raise


def main():
    """Main execution"""

    print("=" * 70)
    print("🎯 RECALCULATING ACC PLAYER MULTIPLIERS FROM 2025 SEASON")
    print("=" * 70)
    print(f"Using rules from: rules-set-1.py")
    print(f"Season data: rosters/acc_2025_complete.json")
    print(f"Database: {DB_HOST}")
    print()

    try:
        # Step 1: Load 2025 roster
        players = load_2025_roster()

        # Step 2: Calculate multipliers
        players = calculate_all_multipliers(players)

        # Step 3: Display results
        display_results(players)

        # Step 4: Confirm before updating database
        print("\n" + "=" * 70)
        response = input("Update database with these multipliers? (yes/no): ")

        if response.lower() in ['yes', 'y']:
            update_database(players)
            print("\n" + "=" * 70)
            print("✅ MULTIPLIER RECALCULATION COMPLETE!")
            print("=" * 70)
            print("\nAll ACC player multipliers have been updated based on 2025 season")
            print("using the current rules-set-1.py point system.")
            print()
        else:
            print("\n❌ Database update cancelled")
            print("   Multipliers were calculated but not saved to database")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
