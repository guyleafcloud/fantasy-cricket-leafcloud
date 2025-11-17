#!/usr/bin/env python3
"""
Generate Initial Player Multipliers from Season Scorecards
===========================================================
Use this script at the start of each season to calculate initial multipliers
based on previous season's performance data.

Usage:
    python3 generate_initial_multipliers.py players.json

Input Format (JSON):
{
  "players": [
    {
      "name": "PlayerName",
      "team": "ACC 1",
      "role": "BATSMAN",
      "stats": {
        "runs": 450,
        "balls_faced": 380,
        "wickets": 0,
        "overs": 0.0,
        "runs_conceded": 0,
        "catches": 5,
        "run_outs": 1,
        "stumpings": 0
      }
    },
    ...
  ]
}

Output:
- Updates each player with calculated multiplier (0.69-5.00)
- Saves to output file with multipliers
"""

import json
import statistics
import sys
from typing import Dict, List


# Import centralized fantasy points calculator
try:
    from rules_set_1 import FANTASY_RULES, calculate_total_fantasy_points
except ImportError:
    # Try with hyphens
    import importlib
    try:
        rules_module = importlib.import_module('rules-set-1')
        FANTASY_RULES = rules_module.FANTASY_RULES
        calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points
    except ImportError:
        print("ERROR: Could not import rules-set-1.py")
        print("Make sure rules-set-1.py is in the same directory")
        sys.exit(1)


def calculate_player_season_points(player_stats: Dict) -> float:
    """
    Calculate total fantasy points from season statistics
    Uses centralized rules from rules-set-1.py
    """
    result = calculate_total_fantasy_points(
        runs=player_stats.get('runs', 0),
        balls_faced=player_stats.get('balls_faced', 0),
        is_out=False,  # Not relevant for season totals
        wickets=player_stats.get('wickets', 0),
        overs=player_stats.get('overs', 0.0),
        runs_conceded=player_stats.get('runs_conceded', 0),
        maidens=player_stats.get('maidens', 0),
        catches=player_stats.get('catches', 0),
        stumpings=player_stats.get('stumpings', 0),
        runouts=player_stats.get('run_outs', 0),
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


def generate_multipliers(input_file: str, output_file: str = None):
    """
    Generate initial multipliers for all players based on season stats

    Args:
        input_file: Path to JSON file with player stats
        output_file: Output path (defaults to input_file with _multipliers suffix)
    """
    print("=" * 70)
    print("🎯 GENERATING INITIAL PLAYER MULTIPLIERS FROM SEASON STATS")
    print("=" * 70)

    # Load player data
    print(f"\n📂 Loading player data from: {input_file}")
    with open(input_file, 'r') as f:
        data = json.load(f)

    players = data.get('players', [])
    print(f"   Found {len(players)} players")

    if not players:
        print("❌ No players found in input file!")
        return

    # Calculate fantasy points for each player
    print("\n🔢 Calculating season fantasy points for all players...")
    player_scores = []

    for player in players:
        stats = player.get('stats', {})
        if not stats:
            print(f"   ⚠️  Warning: {player['name']} has no stats, will get neutral multiplier")
            player['fantasy_points'] = 0.0
            player_scores.append(0.0)
        else:
            points = calculate_player_season_points(stats)
            player['fantasy_points'] = round(points, 2)
            player_scores.append(points)

    # Calculate league statistics
    print("\n📊 Calculating league statistics...")
    min_score = min(player_scores) if player_scores else 0
    max_score = max(player_scores) if player_scores else 0
    median_score = statistics.median(player_scores) if player_scores else 0
    mean_score = statistics.mean(player_scores) if player_scores else 0

    print(f"   Minimum:  {min_score:7.2f} points")
    print(f"   Median:   {median_score:7.2f} points")
    print(f"   Mean:     {mean_score:7.2f} points")
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

    # Display results
    print(f"\n🏆 TOP 10 PLAYERS (Lowest Multipliers - Best Performers):")
    print(f"{'Rank':<6}{'Name':<30}{'Team':<12}{'Points':<10}{'Multiplier':<12}")
    print("-" * 70)
    for i, player in enumerate(players[:10], 1):
        print(f"{i:<6}{player['name']:<30}{player.get('team', 'N/A'):<12}"
              f"{player['fantasy_points']:<10.1f}{player['multiplier']:<12.2f}")

    print(f"\n📉 BOTTOM 10 PLAYERS (Highest Multipliers - Weakest Performers):")
    print(f"{'Rank':<6}{'Name':<30}{'Team':<12}{'Points':<10}{'Multiplier':<12}")
    print("-" * 70)
    for i, player in enumerate(players[-10:], 1):
        print(f"{i:<6}{player['name']:<30}{player.get('team', 'N/A'):<12}"
              f"{player['fantasy_points']:<10.1f}{player['multiplier']:<12.2f}")

    # Save results
    if output_file is None:
        base_name = input_file.rsplit('.', 1)[0]
        output_file = f"{base_name}_with_multipliers.json"

    print(f"\n💾 Saving results to: {output_file}")
    data['players'] = players

    # Add metadata
    data['metadata'] = {
        'total_players': len(players),
        'score_distribution': {
            'min': min_score,
            'median': median_score,
            'mean': mean_score,
            'max': max_score
        },
        'multiplier_range': {
            'min': FANTASY_RULES['player_multipliers']['min'],
            'max': FANTASY_RULES['player_multipliers']['max'],
            'neutral': FANTASY_RULES['player_multipliers']['neutral']
        }
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 70)
    print("✅ MULTIPLIER GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\n📋 Summary:")
    print(f"   Players processed: {len(players)}")
    print(f"   Multiplier range: {min([p['multiplier'] for p in players]):.2f} - "
          f"{max([p['multiplier'] for p in players]):.2f}")
    print(f"   Output file: {output_file}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_initial_multipliers.py <input_file.json> [output_file.json]")
        print()
        print("Example:")
        print("  python3 generate_initial_multipliers.py season_2026_stats.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    generate_multipliers(input_file, output_file)
