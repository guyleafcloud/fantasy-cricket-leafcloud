#!/usr/bin/env python3
"""
Recalculate Player Multipliers in Database
===========================================
Recalculates fantasy points and multipliers for all players in the PostgreSQL database.
"""

import statistics
from typing import List, Tuple
from database import get_db_session
from database_models import Player, Club
from datetime import datetime


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


def calculate_player_total_points(player: Player) -> float:
    """Calculate total fantasy points for a player"""
    stats = player.stats or {}

    # Batting points
    runs = stats.get('runs', 0)
    strike_rate = stats.get('strike_rate', 0.0)
    batting_points = calculate_batting_points(runs, strike_rate)

    # Bowling points
    wickets = stats.get('wickets', 0)
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


def recalculate_club_multipliers(club_id: str):
    """Recalculate multipliers for all players in a club"""

    print("📊 Recalculating Player Multipliers in Database")
    print("=" * 60)

    with get_db_session() as db:
        # Get club
        club = db.query(Club).filter_by(id=club_id).first()
        if not club:
            print(f"❌ Club {club_id} not found!")
            return

        print(f"Club: {club.name}")

        # Get all players for this club
        players = db.query(Player).filter_by(club_id=club_id).all()
        print(f"\n📋 Found {len(players)} players")

        if not players:
            print("❌ No players found!")
            return

        # Calculate fantasy points for each player
        print("\n🔢 Calculating fantasy points...")
        player_scores: List[Tuple[Player, float]] = []

        for player in players:
            total_points = calculate_player_total_points(player)
            player_scores.append((player, total_points))

        # Calculate statistics (only from players with points > 0)
        scores_with_points = [score for _, score in player_scores if score > 0]
        all_scores = [score for _, score in player_scores]

        if not scores_with_points:
            print("❌ No players with points!")
            return

        min_score = min(scores_with_points)
        max_score = max(scores_with_points)
        median_score = statistics.median(scores_with_points)
        mean_score = statistics.mean(all_scores)

        print(f"\n📈 Score Distribution (excluding 0-point players):")
        print(f"   Minimum: {min_score:.2f} points")
        print(f"   Median:  {median_score:.2f} points")
        print(f"   Mean:    {mean_score:.2f} points")
        print(f"   Maximum: {max_score:.2f} points")

        # Calculate and update multipliers
        print("\n🎯 Updating multipliers in database...")
        updates = 0
        zero_point_players = 0

        for player, player_score in player_scores:
            # Players with 0 points get median multiplier of 1.0
            if player_score == 0:
                new_multiplier = 1.0
                zero_point_players += 1
            else:
                new_multiplier = calculate_multiplier(player_score, min_score, median_score, max_score)

            # Update player
            player.multiplier = round(new_multiplier, 2)
            player.multiplier_updated_at = datetime.utcnow()
            updates += 1

        # Commit all changes
        db.commit()

        print(f"\n✅ Updated {updates} players")
        print(f"   Players with 0 points (set to 1.0): {zero_point_players}")

        # Show distribution
        print("\n📊 Multiplier Distribution:")
        multipliers = [p.multiplier for p in players]
        print(f"   Min multiplier: {min(multipliers):.2f}")
        print(f"   Max multiplier: {max(multipliers):.2f}")
        print(f"   Players with 1.0: {sum(1 for m in multipliers if m == 1.0)}")
        print(f"   Players < 1.0 (best): {sum(1 for m in multipliers if m < 1.0)}")
        print(f"   Players > 1.0 (worst): {sum(1 for m in multipliers if m > 1.0)}")

        # Show top and bottom players
        players_sorted = sorted(player_scores, key=lambda x: x[1], reverse=True)

        print(f"\n🏆 Top 10 Players (Best - Lowest Multipliers):")
        for i, (player, score) in enumerate(players_sorted[:10], 1):
            team_name = player.team.name if player.team else "Unknown"
            print(f"   {i:2d}. {player.name:30s} | {score:6.1f} pts | "
                  f"Multiplier: {player.multiplier:.2f} | {team_name}")

        print(f"\n📉 Bottom 10 Players (Worst - Highest Multipliers):")
        for i, (player, score) in enumerate(players_sorted[-10:], 1):
            team_name = player.team.name if player.team else "Unknown"
            print(f"   {i:2d}. {player.name:30s} | {score:6.1f} pts | "
                  f"Multiplier: {player.multiplier:.2f} | {team_name}")

        print("\n" + "=" * 60)
        print("✅ Multiplier recalculation complete!")


if __name__ == "__main__":
    import sys

    # Get club ID from command line or use default ACC club ID
    club_id = "a7a580a7-7d3f-476c-82ea-afa6ae7ee276"  # ACC

    if len(sys.argv) > 1:
        club_id = sys.argv[1]

    recalculate_club_multipliers(club_id)
