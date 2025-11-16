#!/usr/bin/env python3
"""
Player Value Calculator
=======================
Calculates fantasy team values for players based on their season performance.

Algorithm:
1. Performance Scoring (0-100 points)
   - Batting: runs, average, strike rate
   - Bowling: wickets, economy, bowling average
   - Fielding: catches, run outs
   - Consistency: standard deviation of performances

2. Value Assignment (€20-€50 range)
   - Top 10% performers: €45-50
   - Top 25%: €40-45
   - Top 50%: €35-40
   - Below average: €25-35
   - Poor performers: €20-25

Usage:
    calculator = PlayerValueCalculator()
    value, justification = calculator.calculate_value(player_stats, tier="1st")
"""

import math
import logging
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from statistics import mean, stdev

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlayerStats:
    """Player season statistics"""
    player_name: str
    club: str

    # Batting stats
    matches_played: int = 0
    total_runs: int = 0
    total_balls_faced: int = 0
    batting_average: float = 0.0
    strike_rate: float = 0.0
    fours: int = 0
    sixes: int = 0
    fifties: int = 0
    hundreds: int = 0

    # Bowling stats
    total_wickets: int = 0
    total_runs_conceded: int = 0
    total_overs_bowled: float = 0.0
    bowling_average: float = 0.0
    economy_rate: float = 0.0
    maidens: int = 0
    five_wicket_hauls: int = 0

    # Fielding stats
    catches: int = 0
    run_outs: int = 0
    stumpings: int = 0

    # Team context
    team_level: str = "1st"  # 1st, 2nd, 3rd, social

    # Match-by-match data (for consistency calculation)
    match_performances: List[int] = None  # fantasy points per match


class PlayerValueCalculator:
    """
    Calculate fantasy team values for players based on performance
    """

    # Value ranges
    MIN_VALUE = 20.0
    MAX_VALUE = 50.0

    # Performance thresholds
    EXCELLENT_PERCENTILE = 90  # Top 10%
    GOOD_PERCENTILE = 75       # Top 25%
    AVERAGE_PERCENTILE = 50    # Top 50%

    def __init__(self):
        self.league_stats = []  # Store all players for relative comparison

    def calculate_value(
        self,
        stats: PlayerStats,
        relative_to: Optional[List[PlayerStats]] = None
    ) -> Tuple[float, str]:
        """
        Calculate player value based on their stats

        Args:
            stats: Player statistics
            relative_to: Other players to compare against (for percentile ranking)

        Returns:
            (value, justification) tuple
        """

        # Calculate performance score (0-100)
        performance_score = self._calculate_performance_score(stats)

        # Calculate consistency bonus/penalty
        consistency_score = self._calculate_consistency_score(stats)

        # Final score
        final_score = performance_score + consistency_score

        # Convert score to value (€20-€50)
        if relative_to:
            # Use percentile-based pricing
            value = self._score_to_value_percentile(final_score, relative_to, stats)
        else:
            # Use absolute pricing
            value = self._score_to_value_absolute(final_score)

        # Generate justification
        justification = self._generate_justification(
            stats, performance_score,
            consistency_score, final_score, value
        )

        return round(value, 1), justification

    def _calculate_performance_score(self, stats: PlayerStats) -> float:
        """
        Calculate overall performance score (0-100)

        Breakdown:
        - Batting: 0-40 points
        - Bowling: 0-40 points
        - Fielding: 0-10 points
        - All-rounder bonus: 0-10 points
        """
        if stats.matches_played == 0:
            return 20.0  # Minimum score for players with no data

        batting_score = self._calculate_batting_score(stats)
        bowling_score = self._calculate_bowling_score(stats)
        fielding_score = self._calculate_fielding_score(stats)
        allrounder_bonus = self._calculate_allrounder_bonus(
            batting_score, bowling_score
        )

        total = batting_score + bowling_score + fielding_score + allrounder_bonus

        # Cap at 100
        return min(100.0, total)

    def _calculate_batting_score(self, stats: PlayerStats) -> float:
        """Calculate batting performance score (0-40 points)"""
        if stats.total_runs == 0:
            return 0.0

        score = 0.0

        # Runs scored (0-15 points)
        # Scale: 0 runs = 0, 500+ runs = 15
        runs_score = min(15.0, (stats.total_runs / 500) * 15)
        score += runs_score

        # Batting average (0-10 points)
        # Scale: 0 avg = 0, 40+ avg = 10
        avg_score = min(10.0, (stats.batting_average / 40) * 10)
        score += avg_score

        # Strike rate (0-10 points)
        # Scale: 0 SR = 0, 150+ SR = 10
        sr_score = min(10.0, (stats.strike_rate / 150) * 10)
        score += sr_score

        # Milestones (0-5 points)
        milestone_score = (stats.hundreds * 2) + (stats.fifties * 1)
        score += min(5.0, milestone_score)

        return score

    def _calculate_bowling_score(self, stats: PlayerStats) -> float:
        """Calculate bowling performance score (0-40 points)"""
        if stats.total_wickets == 0:
            return 0.0

        score = 0.0

        # Wickets taken (0-15 points)
        # Scale: 0 wickets = 0, 40+ wickets = 15
        wickets_score = min(15.0, (stats.total_wickets / 40) * 15)
        score += wickets_score

        # Economy rate (0-10 points) - lower is better
        # Scale: 10+ economy = 0, 3 economy = 10
        if stats.economy_rate > 0:
            economy_score = max(0, 10 - (stats.economy_rate - 3) * 2)
            score += min(10.0, economy_score)

        # Bowling average (0-10 points) - lower is better
        # Scale: 40+ avg = 0, 15 avg = 10
        if stats.bowling_average > 0:
            avg_score = max(0, 10 - ((stats.bowling_average - 15) / 5))
            score += min(10.0, avg_score)

        # Milestones (0-5 points)
        milestone_score = (stats.five_wicket_hauls * 2) + (stats.maidens * 0.5)
        score += min(5.0, milestone_score)

        return score

    def _calculate_fielding_score(self, stats: PlayerStats) -> float:
        """Calculate fielding performance score (0-10 points)"""
        score = 0.0

        # Catches (0-5 points)
        # Scale: 0 catches = 0, 20+ catches = 5
        catches_score = min(5.0, (stats.catches / 20) * 5)
        score += catches_score

        # Run outs and stumpings (0-5 points)
        # Scale: 0 = 0, 10+ = 5
        dismissals = stats.run_outs + stats.stumpings
        dismissals_score = min(5.0, (dismissals / 10) * 5)
        score += dismissals_score

        return score

    def _calculate_allrounder_bonus(
        self,
        batting_score: float,
        bowling_score: float
    ) -> float:
        """
        Calculate all-rounder bonus (0-10 points)

        Players who contribute significantly in both batting and bowling
        get a bonus to reflect their versatility.
        """
        # Only give bonus if both batting and bowling are significant
        min_threshold = 8.0  # At least 8 points in each

        if batting_score >= min_threshold and bowling_score >= min_threshold:
            # Bonus scales with how balanced they are
            balance = 1.0 - abs(batting_score - bowling_score) / max(batting_score, bowling_score)
            return 10.0 * balance

        return 0.0

    def _calculate_consistency_score(self, stats: PlayerStats) -> float:
        """
        Calculate consistency bonus/penalty (-5 to +5 points)

        Consistent performers are more valuable than inconsistent ones.
        """
        if not stats.match_performances or len(stats.match_performances) < 3:
            return 0.0  # Not enough data

        # Calculate coefficient of variation (CV)
        # CV = stdev / mean (lower is more consistent)
        avg_performance = mean(stats.match_performances)

        if avg_performance == 0:
            return -5.0  # Consistently poor

        try:
            std_dev = stdev(stats.match_performances)
            cv = std_dev / avg_performance

            # Convert to score (-5 to +5)
            # CV < 0.5 = very consistent (+5)
            # CV = 1.0 = average (0)
            # CV > 1.5 = very inconsistent (-5)

            if cv < 0.5:
                return 5.0
            elif cv < 0.75:
                return 2.5
            elif cv < 1.25:
                return 0.0
            elif cv < 1.5:
                return -2.5
            else:
                return -5.0

        except:
            return 0.0

    def _score_to_value_percentile(
        self,
        score: float,
        all_players: List[PlayerStats],
        current_player: PlayerStats
    ) -> float:
        """
        Convert score to value based on percentile ranking within league
        """
        # Calculate scores for all players
        all_scores = []
        for player in all_players:
            player_score = self._calculate_performance_score(player)
            all_scores.append(player_score)

        # Add current player's score
        all_scores.append(score)
        all_scores.sort(reverse=True)

        # Find percentile
        rank = all_scores.index(score) + 1
        percentile = ((len(all_scores) - rank) / len(all_scores)) * 100

        # Map percentile to value
        if percentile >= self.EXCELLENT_PERCENTILE:
            # Top 10%: €45-50
            value = 45 + ((percentile - self.EXCELLENT_PERCENTILE) / 10) * 5
        elif percentile >= self.GOOD_PERCENTILE:
            # Top 25%: €40-45
            value = 40 + ((percentile - self.GOOD_PERCENTILE) / 15) * 5
        elif percentile >= self.AVERAGE_PERCENTILE:
            # Top 50%: €35-40
            value = 35 + ((percentile - self.AVERAGE_PERCENTILE) / 25) * 5
        elif percentile >= 25:
            # Below average: €30-35
            value = 30 + ((percentile - 25) / 25) * 5
        else:
            # Bottom 25%: €20-30
            value = 20 + (percentile / 25) * 10

        return value

    def _score_to_value_absolute(self, score: float) -> float:
        """
        Convert score to value using absolute scale (when no comparison available)
        """
        # Simple linear mapping
        # Score 0-30 → €20-30
        # Score 30-60 → €30-40
        # Score 60-100 → €40-50

        if score <= 30:
            return self.MIN_VALUE + (score / 30) * 10
        elif score <= 60:
            return 30 + ((score - 30) / 30) * 10
        else:
            return 40 + ((score - 60) / 40) * 10

    def _generate_justification(
        self,
        stats: PlayerStats,
        performance_score: float,
        consistency_score: float,
        final_score: float,
        value: float
    ) -> str:
        """Generate human-readable justification for the value"""

        lines = []
        lines.append(f"Player: {stats.player_name} ({stats.club})")
        lines.append(f"Team Level: {stats.team_level}")
        lines.append(f"")

        # Performance breakdown
        lines.append(f"Performance Score: {performance_score:.1f}/100")

        if stats.total_runs > 0:
            lines.append(f"  - Batting: {stats.total_runs} runs @ {stats.batting_average:.1f} avg, SR {stats.strike_rate:.1f}")

        if stats.total_wickets > 0:
            lines.append(f"  - Bowling: {stats.total_wickets} wickets @ {stats.bowling_average:.1f} avg, ER {stats.economy_rate:.2f}")

        if stats.catches > 0 or stats.run_outs > 0:
            lines.append(f"  - Fielding: {stats.catches} catches, {stats.run_outs} run outs")

        lines.append(f"")

        # Adjustments
        if consistency_score != 0:
            consistency_label = "consistent" if consistency_score > 0 else "inconsistent"
            lines.append(f"Consistency: {consistency_score:+.1f} points ({consistency_label})")

        lines.append(f"")
        lines.append(f"Final Score: {final_score:.1f}/105")
        lines.append(f"Fantasy Value: €{value:.1f}")

        return "\n".join(lines)

    def calculate_team_values(
        self,
        players: List[PlayerStats]
    ) -> List[Tuple[PlayerStats, float, str]]:
        """
        Calculate values for all players in a team, using relative comparison

        Returns:
            List of (player, value, justification) tuples
        """
        results = []

        for player in players:
            value, justification = self.calculate_value(player, relative_to=players)
            results.append((player, value, justification))

        # Sort by value (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def calculate_team_values_per_team(
        self,
        players: List[PlayerStats],
        team_name_getter=None
    ) -> List[Tuple[PlayerStats, float, str]]:
        """
        Calculate values PER TEAM - best player in each team gets €45-50,
        worst gets €20-25. This ensures all teams have expensive and cheap players.

        This forces strategic team selection: you must choose between expensive
        stars across different teams, not just load up on one team.

        Args:
            players: List of all players
            team_name_getter: Optional function to get team name from player
                             If None, uses player.team_level

        Returns:
            List of (player, value, justification) tuples
        """
        from collections import defaultdict

        # Group players by team
        teams = defaultdict(list)
        for player in players:
            if team_name_getter:
                team_key = team_name_getter(player)
            else:
                team_key = player.team_level
            teams[team_key].append(player)

        all_results = []

        # Calculate values within each team
        for team_key, team_players in teams.items():
            # Calculate performance scores for this team only
            team_scores = []
            for player in team_players:
                perf_score = self._calculate_performance_score(player)
                # DON'T apply tier multiplier - we're ranking within team
                team_scores.append((player, perf_score))

            # Sort by performance within this team
            team_scores.sort(key=lambda x: x[1], reverse=True)

            # Assign values based on rank within team
            team_size = len(team_scores)

            for rank, (player, perf_score) in enumerate(team_scores):
                # Use simple linear scale: #1 = €50, last = €20
                # This ensures EVERY team has expensive and cheap players regardless of size
                if team_size == 1:
                    value = 35.0  # Solo player gets middle value
                else:
                    # Linear interpolation from €50 (rank 0) to €20 (last rank)
                    value = 50.0 - (rank / (team_size - 1)) * 30.0

                # Calculate percentile for display
                percentile = ((team_size - rank - 1) / max(1, team_size - 1)) * 100

                # Create justification
                justification = f"""
Player Value: €{value:.1f}

Rank in {team_key}: #{rank + 1} of {team_size} players
Percentile in team: {percentile:.1f}%

Performance Score: {perf_score:.1f}/100
- This player ranks #{rank + 1} among {team_size} players in {team_key}
- Best {team_key} player: €50.0
- Worst {team_key} player: €20.0
- Linear scale: Each rank costs €{30.0 / (team_size - 1):.2f} less

Note: Values are relative to teammates, not global ranking.
This ensures EVERY team has both €50 stars and €20 budget options.
"""

                all_results.append((player, value, justification))

        # Sort all results by value
        all_results.sort(key=lambda x: x[1], reverse=True)

        return all_results


def load_player_stats_from_legacy(legacy_data: Dict) -> PlayerStats:
    """
    Convert legacy roster data to PlayerStats format

    Args:
        legacy_data: Player data from legacy roster JSON

    Returns:
        PlayerStats object
    """
    # Extract stats from legacy format
    stats = legacy_data.get('stats', {})

    return PlayerStats(
        player_name=legacy_data.get('name', 'Unknown'),
        club=legacy_data.get('club', 'Unknown'),
        matches_played=stats.get('matches', 0),
        total_runs=stats.get('runs', 0),
        batting_average=stats.get('batting_avg', 0.0),
        strike_rate=stats.get('strike_rate', 0.0),
        total_wickets=stats.get('wickets', 0),
        bowling_average=stats.get('bowling_avg', 0.0),
        economy_rate=stats.get('economy', 0.0),
        catches=stats.get('catches', 0),
        team_level=legacy_data.get('team_level', '1st'),
        match_performances=stats.get('match_performances', None)
    )


# CLI for testing
if __name__ == "__main__":
    import json
    import sys

    print("🏏 Player Value Calculator - Test Mode\n")

    # Example usage with sample data
    sample_players = [
        PlayerStats(
            player_name="Boris Gorlee",
            club="ACC",
            matches_played=12,
            total_runs=450,
            batting_average=37.5,
            strike_rate=125.0,
            total_wickets=18,
            bowling_average=22.5,
            economy_rate=4.5,
            catches=6,
            team_level="1st"
        ),
        PlayerStats(
            player_name="Sikander Zulfiqar",
            club="ACC",
            matches_played=10,
            total_runs=520,
            batting_average=52.0,
            strike_rate=140.0,
            total_wickets=2,
            bowling_average=45.0,
            economy_rate=6.0,
            catches=4,
            team_level="1st"
        ),
        PlayerStats(
            player_name="Shariz Ahmad",
            club="ACC",
            matches_played=8,
            total_runs=180,
            batting_average=22.5,
            strike_rate=90.0,
            total_wickets=15,
            bowling_average=18.0,
            economy_rate=3.8,
            catches=3,
            team_level="2nd"
        )
    ]

    calculator = PlayerValueCalculator()
    results = calculator.calculate_team_values(sample_players)

    print("=" * 80)
    for player, value, justification in results:
        print(f"\n{justification}")
        print("=" * 80)

    print(f"\n✅ Calculated values for {len(results)} players")
