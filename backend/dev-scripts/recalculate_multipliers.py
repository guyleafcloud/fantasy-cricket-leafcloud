#!/usr/bin/env python3
"""
Recalculate Player Multipliers
================================
Recalculates fantasy points and multipliers for all players using the new system.

Points System:
- Batting: Runs 0-50 = 1pt, 51-100 = 1.25pt, 100+ = 1.5pt, × (SR/100)
- Bowling: Wickets 1-4 = 22pts, 5+ = 32pts, × (5.0/Economy)
- Fielding: Catches/Stumpings = 20pts each

Multiplier System:
- Below median (weaker players): 1.0 to 5.0 (linear scale)
- At median: 1.0
- Above median (stronger players): 1.0 to 0.69 (linear scale)
"""

import json
import statistics
from typing import Dict, List


def calculate_batting_points(runs: int, strike_rate: float) -> float:
    """Calculate batting fantasy points"""
    if runs == 0:
        return 0.0

    # Tiered run scoring (increased significantly to properly value pure batsmen)
    # This ensures specialist batsmen start with lower multipliers
    points = 0.0
    if runs <= 50:
        points = runs * 1.3
    elif runs <= 100:
        points = 50 * 1.3 + (runs - 50) * 1.6
    else:
        points = 50 * 1.3 + 50 * 1.6 + (runs - 100) * 2.0

    # Apply strike rate multiplier
    if strike_rate > 0:
        points = points * (strike_rate / 100.0)

    return points


def calculate_bowling_points(wickets: int, economy: float) -> float:
    """Calculate bowling fantasy points"""
    if wickets == 0:
        return 0.0

    # Tiered wicket scoring
    if wickets <= 4:
        points = wickets * 22
    else:
        points = 4 * 22 + (wickets - 4) * 32

    # Apply economy multiplier (lower economy is better)
    if economy > 0:
        points = points * (5.0 / economy)

    return points


def calculate_fielding_points(catches: int, run_outs: int) -> float:
    """Calculate fielding fantasy points"""
    return (catches + run_outs) * 20


def calculate_player_total_points(player: Dict) -> float:
    """Calculate total fantasy points for a player's 2025 season"""
    stats = player.get('stats', {})

    # Batting points
    runs = stats.get('runs', 0)
    strike_rate = stats.get('strike_rate', 0.0)
    batting_points = calculate_batting_points(runs, strike_rate)

    # Bowling points
    wickets = stats.get('wickets', 0)
    bowling_avg = stats.get('bowling_avg', 0.0)

    # Estimate economy from bowling average (rough approximation)
    # In One Day cricket, economy is typically around 4-6
    # If we don't have economy, use 5.0 as default
    economy = stats.get('economy', 5.0)
    bowling_points = calculate_bowling_points(wickets, economy)

    # Fielding points
    catches = stats.get('catches', 0)
    run_outs = stats.get('run_outs', 0)
    fielding_points = calculate_fielding_points(catches, run_outs)

    total = batting_points + bowling_points + fielding_points
    return total


def calculate_multiplier(player_score: float, min_score: float, median_score: float, max_score: float) -> float:
    """
    Calculate multiplier based on player's score relative to median.

    - Below median: 1.0 to 5.0 (linear scale)
    - At median: 1.0
    - Above median: 1.0 to 0.69 (linear scale)
    """
    if median_score == 0:
        return 1.0

    if player_score <= median_score:
        # Below median: interpolate from 5.0 (min_score) to 1.0 (median)
        if median_score == min_score:
            return 1.0
        ratio = (player_score - min_score) / (median_score - min_score)
        return 5.0 - (ratio * 4.0)  # 5.0 → 1.0
    else:
        # Above median: interpolate from 1.0 (median) to 0.69 (max_score)
        if max_score == median_score:
            return 1.0
        ratio = (player_score - median_score) / (max_score - median_score)
        return 1.0 - (ratio * 0.31)  # 1.0 → 0.69


def recalculate_all_multipliers(database_file: str, output_file: str = None, mode: str = "initial", drift_rate: float = 0.15):
    """
    Recalculate fantasy points and multipliers for all players

    Args:
        database_file: Path to player database JSON
        output_file: Output path (defaults to overwriting input)
        mode: "initial" for 2025 baseline, "drift" for gradual weekly updates
        drift_rate: Alpha value for drift mode (0.0 to 1.0), how much to move toward target each week
    """

    print("📊 Recalculating Player Multipliers")
    print("=" * 60)
    print(f"   Mode: {mode}")
    if mode == "drift":
        print(f"   Drift rate: {drift_rate:.2%}")

    # Load database
    with open(database_file, 'r') as f:
        database = json.load(f)

    players = database.get('players', [])
    print(f"\n📋 Loaded {len(players)} players")

    # Calculate total points for each player
    print("\n🔢 Calculating fantasy points for all players...")
    player_scores = []

    for player in players:
        total_points = calculate_player_total_points(player)
        player['fantasy_points'] = round(total_points, 2)
        player_scores.append(total_points)

    # Calculate statistics
    if not player_scores:
        print("❌ No players found!")
        return

    min_score = min(player_scores)
    max_score = max(player_scores)
    median_score = statistics.median(player_scores)
    mean_score = statistics.mean(player_scores)

    print(f"\n📈 Score Distribution:")
    print(f"   Minimum: {min_score:.2f} points")
    print(f"   Median:  {median_score:.2f} points")
    print(f"   Mean:    {mean_score:.2f} points")
    print(f"   Maximum: {max_score:.2f} points")

    # Calculate multipliers
    print("\n🎯 Calculating multipliers...")
    for player in players:
        player_score = player['fantasy_points']

        # Players with 0 points (no stats) get the median multiplier of 1.0
        if player_score == 0:
            target_multiplier = 1.0
        else:
            target_multiplier = calculate_multiplier(player_score, min_score, median_score, max_score)

        if mode == "drift":
            # Gradual drift: blend old multiplier with new target
            old_multiplier = player.get('multiplier', 1.0)
            new_multiplier = old_multiplier * (1 - drift_rate) + target_multiplier * drift_rate
            player['multiplier'] = round(new_multiplier, 2)
        else:
            # Initial mode: directly assign calculated multiplier
            player['multiplier'] = round(target_multiplier, 2)

        # Remove old fantasy_value field if it exists
        if 'fantasy_value' in player:
            del player['fantasy_value']

    # Sort by fantasy points (descending)
    players.sort(key=lambda x: x['fantasy_points'], reverse=True)

    # Show top 10 and bottom 10
    print(f"\n🏆 Top 10 Players (Lowest Multipliers):")
    for i, player in enumerate(players[:10], 1):
        print(f"   {i:2d}. {player['name']:30s} | {player['fantasy_points']:6.1f} pts | "
              f"Multiplier: {player['multiplier']:.2f} | {player['team_name']}")

    print(f"\n📉 Bottom 10 Players (Highest Multipliers):")
    for i, player in enumerate(players[-10:], 1):
        print(f"   {i:2d}. {player['name']:30s} | {player['fantasy_points']:6.1f} pts | "
              f"Multiplier: {player['multiplier']:.2f} | {player['team_name']}")

    # Save updated database
    if output_file is None:
        output_file = database_file

    database['players'] = players

    with open(output_file, 'w') as f:
        json.dump(database, f, indent=2)

    print(f"\n💾 Saved updated database to {output_file}")
    print("=" * 60)
    print("✅ Recalculation complete!")


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    database_file = 'rosters/acc_legacy_database.json'
    mode = 'initial'
    drift_rate = 0.15

    if len(sys.argv) > 1:
        database_file = sys.argv[1]
    if len(sys.argv) > 2:
        mode = sys.argv[2]  # "initial" or "drift"
    if len(sys.argv) > 3:
        drift_rate = float(sys.argv[3])

    recalculate_all_multipliers(database_file, mode=mode, drift_rate=drift_rate)
