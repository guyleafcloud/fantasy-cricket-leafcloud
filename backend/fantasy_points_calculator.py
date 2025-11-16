#!/usr/bin/env python3
"""
Fantasy Points Calculator
=========================
Calculates fantasy points for player performances based on cricket statistics.

Points System:
--------------
BATTING:
- Every run: +1 point
- Run points multiplied by (Strike Rate / 100)
  - Example: 50 runs at SR 150 = 50 × 1.5 = 75 points
  - Example: 50 runs at SR 80 = 50 × 0.8 = 40 points
- NO boundary bonuses (fours/sixes count as runs only)
- Milestone bonuses:
  - 50 runs: +8 points
  - 100 runs: +16 points
- Duck (0 runs while out): -2 points

BOWLING:
- Every wicket: +12 points
- Wicket points multiplied by (6 / Economy Rate)
  - Example: 3 wickets at ER 4.0 = 36 × 1.5 = 54 points
  - Example: 3 wickets at ER 8.0 = 36 × 0.75 = 27 points
- Maiden over: +25 points each
- 5 wicket haul: +8 points

FIELDING:
- Catch: +4 points
- Run out: +6 points
- Stumping: +6 points

NO TIER MULTIPLIERS - all performances scored equally
"""

from typing import Dict, Optional
import logging

# Import centralized rules
try:
    from rules_set_1 import FANTASY_RULES, calculate_total_fantasy_points as calc_total
except ImportError:
    # Fallback if module name has hyphens
    import importlib
    rules_module = importlib.import_module('rules-set-1')
    FANTASY_RULES = rules_module.FANTASY_RULES
    calc_total = rules_module.calculate_total_fantasy_points

logger = logging.getLogger(__name__)


class FantasyPointsCalculator:
    """Calculates fantasy cricket points from player performance stats

    Uses centralized rules from rules-set-1.py
    """

    def __init__(self):
        # Load rules from centralized configuration
        self.rules = FANTASY_RULES

        # Create convenient attribute access for backward compatibility
        self.POINTS_PER_RUN = self.rules['batting']['points_per_run']
        self.BONUS_FIFTY = self.rules['batting']['fifty_bonus']
        self.BONUS_HUNDRED = self.rules['batting']['century_bonus']
        self.PENALTY_DUCK = self.rules['batting']['duck_penalty']

        self.POINTS_PER_WICKET = self.rules['bowling']['points_per_wicket']
        self.POINTS_PER_MAIDEN = self.rules['bowling']['points_per_maiden']
        self.BONUS_5_WICKETS = self.rules['bowling']['five_wicket_haul_bonus']

        self.POINTS_PER_CATCH = self.rules['fielding']['points_per_catch']
        self.POINTS_PER_RUN_OUT = self.rules['fielding']['points_per_runout']
        self.POINTS_PER_STUMPING = self.rules['fielding']['points_per_stumping']

    def calculate_batting_points(
        self,
        runs: int,
        balls_faced: int,
        fours: int,
        sixes: int,
        is_out: bool
    ) -> Dict:
        """
        Calculate batting points and breakdown

        Args:
            runs: Runs scored
            balls_faced: Balls faced
            fours: Number of boundaries (not used for points, just tracking)
            sixes: Number of sixes (not used for points, just tracking)
            is_out: Whether the batsman was dismissed

        Returns:
            Dictionary with points breakdown
        """
        breakdown = {
            "runs": 0,
            "runs_base": 0,
            "runs_after_strike_rate": 0,
            "fifty_bonus": 0,
            "hundred_bonus": 0,
            "duck_penalty": 0,
            "total": 0
        }

        # Calculate base run points
        base_run_points = runs * self.POINTS_PER_RUN
        breakdown["runs_base"] = base_run_points

        # Apply strike rate multiplier (if balls faced)
        if balls_faced > 0 and runs > 0:
            strike_rate = (runs / balls_faced) * 100
            multiplier = strike_rate / 100
            breakdown["runs"] = base_run_points * multiplier
            breakdown["runs_after_strike_rate"] = breakdown["runs"] - base_run_points
        else:
            # No strike rate multiplier if no balls faced
            breakdown["runs"] = base_run_points
            breakdown["runs_after_strike_rate"] = 0

        # Milestone bonuses
        if runs >= 50:
            breakdown["fifty_bonus"] = self.BONUS_FIFTY
        if runs >= 100:
            breakdown["hundred_bonus"] = self.BONUS_HUNDRED

        # Duck penalty (out for 0)
        if is_out and runs == 0:
            breakdown["duck_penalty"] = self.PENALTY_DUCK

        # Calculate total
        breakdown["total"] = (
            breakdown["runs"] +
            breakdown["fifty_bonus"] +
            breakdown["hundred_bonus"] +
            breakdown["duck_penalty"]
        )

        return breakdown

    def calculate_bowling_points(
        self,
        wickets: int,
        overs_bowled: float,
        runs_conceded: int,
        maidens: int
    ) -> Dict:
        """
        Calculate bowling points and breakdown

        Args:
            wickets: Wickets taken
            overs_bowled: Overs bowled (e.g., 4.2 = 4 overs 2 balls)
            runs_conceded: Runs given away
            maidens: Maiden overs bowled

        Returns:
            Dictionary with points breakdown
        """
        breakdown = {
            "wickets": 0,
            "wickets_base": 0,
            "wickets_after_economy": 0,
            "maidens": 0,
            "five_wicket_bonus": 0,
            "total": 0
        }

        # Calculate base wicket points
        base_wicket_points = wickets * self.POINTS_PER_WICKET
        breakdown["wickets_base"] = base_wicket_points

        # Apply economy rate multiplier (if overs bowled)
        if overs_bowled > 0 and wickets > 0:
            economy = runs_conceded / overs_bowled
            if economy > 0:
                multiplier = 6.0 / economy
                breakdown["wickets"] = base_wicket_points * multiplier
                breakdown["wickets_after_economy"] = breakdown["wickets"] - base_wicket_points
            else:
                # Perfect economy (no runs conceded) - give maximum multiplier
                breakdown["wickets"] = base_wicket_points * 6.0
                breakdown["wickets_after_economy"] = breakdown["wickets"] - base_wicket_points
        else:
            # No economy rate multiplier if no overs bowled
            breakdown["wickets"] = base_wicket_points
            breakdown["wickets_after_economy"] = 0

        # Maiden over points
        breakdown["maidens"] = maidens * self.POINTS_PER_MAIDEN

        # Milestone bonus
        if wickets >= 5:
            breakdown["five_wicket_bonus"] = self.BONUS_5_WICKETS

        # Calculate total
        breakdown["total"] = (
            breakdown["wickets"] +
            breakdown["maidens"] +
            breakdown["five_wicket_bonus"]
        )

        return breakdown

    def calculate_fielding_points(
        self,
        catches: int,
        run_outs: int,
        stumpings: int
    ) -> Dict:
        """
        Calculate fielding points and breakdown

        Args:
            catches: Number of catches taken
            run_outs: Number of run outs effected
            stumpings: Number of stumpings (wicket-keeper)

        Returns:
            Dictionary with points breakdown
        """
        breakdown = {
            "catches": 0,
            "run_outs": 0,
            "stumpings": 0,
            "total": 0
        }

        breakdown["catches"] = catches * self.POINTS_PER_CATCH
        breakdown["run_outs"] = run_outs * self.POINTS_PER_RUN_OUT
        breakdown["stumpings"] = stumpings * self.POINTS_PER_STUMPING

        breakdown["total"] = sum(breakdown.values())

        return breakdown

    def calculate_total_points(
        self,
        runs: int = 0,
        balls_faced: int = 0,
        fours: int = 0,
        sixes: int = 0,
        is_out: bool = False,
        wickets: int = 0,
        overs_bowled: float = 0.0,
        runs_conceded: int = 0,
        maidens: int = 0,
        catches: int = 0,
        run_outs: int = 0,
        stumpings: int = 0
    ) -> Dict:
        """
        Calculate total fantasy points from all performance stats

        Returns:
            Dictionary with complete breakdown and grand total
        """
        batting = self.calculate_batting_points(runs, balls_faced, fours, sixes, is_out)
        bowling = self.calculate_bowling_points(wickets, overs_bowled, runs_conceded, maidens)
        fielding = self.calculate_fielding_points(catches, run_outs, stumpings)

        grand_total = batting["total"] + bowling["total"] + fielding["total"]

        return {
            "batting": batting,
            "bowling": bowling,
            "fielding": fielding,
            "grand_total": grand_total
        }

    def calculate_from_performance_dict(self, performance: Dict) -> Dict:
        """
        Calculate points from a performance dictionary (e.g., from scraper)

        Args:
            performance: Dictionary with performance stats

        Returns:
            Dictionary with complete breakdown and grand total
        """
        return self.calculate_total_points(
            runs=performance.get('runs', 0),
            balls_faced=performance.get('balls_faced', 0),
            fours=performance.get('fours', 0),
            sixes=performance.get('sixes', 0),
            is_out=performance.get('is_out', False),
            wickets=performance.get('wickets', 0),
            overs_bowled=performance.get('overs_bowled', 0.0),
            runs_conceded=performance.get('runs_conceded', 0),
            maidens=performance.get('maidens', 0),
            catches=performance.get('catches', 0),
            run_outs=performance.get('run_outs', 0),
            stumpings=performance.get('stumpings', 0)
        )


def format_points_summary(points_breakdown: Dict, player_name: str = None) -> str:
    """
    Format points breakdown as a readable summary string

    Args:
        points_breakdown: Points breakdown from calculator
        player_name: Optional player name

    Returns:
        Formatted string summary
    """
    lines = []

    if player_name:
        lines.append(f"Fantasy Points for {player_name}")
        lines.append("=" * 50)

    # Batting
    batting = points_breakdown.get('batting', {})
    if batting.get('total', 0) != 0:
        lines.append("BATTING:")
        if batting.get('runs_base', 0):
            lines.append(f"  Base Run Points: {batting['runs_base']:.1f} points")
        if batting.get('runs_after_strike_rate', 0):
            lines.append(f"  Strike Rate Multiplier: {batting['runs_after_strike_rate']:+.1f} points")
        if batting.get('runs', 0):
            lines.append(f"  Total Run Points: {batting['runs']:.1f} points")
        if batting.get('fifty_bonus', 0):
            lines.append(f"  Fifty Bonus: {batting['fifty_bonus']} points")
        if batting.get('hundred_bonus', 0):
            lines.append(f"  Hundred Bonus: {batting['hundred_bonus']} points")
        if batting.get('duck_penalty', 0):
            lines.append(f"  Duck Penalty: {batting['duck_penalty']} points")
        lines.append(f"  Batting Total: {batting['total']:.1f} points")
        lines.append("")

    # Bowling
    bowling = points_breakdown.get('bowling', {})
    if bowling.get('total', 0) != 0:
        lines.append("BOWLING:")
        if bowling.get('wickets_base', 0):
            lines.append(f"  Base Wicket Points: {bowling['wickets_base']:.1f} points")
        if bowling.get('wickets_after_economy', 0):
            lines.append(f"  Economy Rate Multiplier: {bowling['wickets_after_economy']:+.1f} points")
        if bowling.get('wickets', 0):
            lines.append(f"  Total Wicket Points: {bowling['wickets']:.1f} points")
        if bowling.get('maidens', 0):
            lines.append(f"  Maidens: {bowling['maidens']} points")
        if bowling.get('five_wicket_bonus', 0):
            lines.append(f"  5-Wicket Bonus: {bowling['five_wicket_bonus']} points")
        lines.append(f"  Bowling Total: {bowling['total']:.1f} points")
        lines.append("")

    # Fielding
    fielding = points_breakdown.get('fielding', {})
    if fielding.get('total', 0) != 0:
        lines.append("FIELDING:")
        if fielding.get('catches', 0):
            lines.append(f"  Catches: {fielding['catches']} points")
        if fielding.get('run_outs', 0):
            lines.append(f"  Run Outs: {fielding['run_outs']} points")
        if fielding.get('stumpings', 0):
            lines.append(f"  Stumpings: {fielding['stumpings']} points")
        lines.append(f"  Fielding Total: {fielding['total']} points")
        lines.append("")

    # Grand total
    lines.append("=" * 50)
    lines.append(f"GRAND TOTAL: {points_breakdown.get('grand_total', 0)} points")
    lines.append("=" * 50)

    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage and testing
    calculator = FantasyPointsCalculator()

    # Test case 1: Aggressive batting (50 runs at SR 150)
    print("Test 1: Aggressive batting (50 runs, 33 balls - SR 151.5)")
    print("-" * 70)
    result = calculator.calculate_total_points(
        runs=50,
        balls_faced=33,
        is_out=True
    )
    print(format_points_summary(result))
    print("Expected: 50 base × 1.515 SR multiplier = 75.75 runs + 8 fifty bonus = 83.75 points")
    print("\n")

    # Test case 2: Economical bowling (3 wickets at ER 4.0)
    print("Test 2: Economical bowling (3 wickets, 8 overs, 32 runs, 2 maidens)")
    print("-" * 70)
    result = calculator.calculate_total_points(
        wickets=3,
        overs_bowled=8.0,
        runs_conceded=32,
        maidens=2
    )
    print(format_points_summary(result))
    print("Expected: 36 base × 1.5 ER multiplier = 54 wickets + 50 maidens = 104 points")
    print("\n")

    # Test case 3: All-rounder performance
    print("Test 3: All-rounder (35 runs at SR 140, 2 wickets at ER 4.5, 1 catch)")
    print("-" * 70)
    result = calculator.calculate_total_points(
        runs=35,
        balls_faced=25,
        wickets=2,
        overs_bowled=4.0,
        runs_conceded=18,
        catches=1
    )
    print(format_points_summary(result))
    print("Expected: 35 × 1.4 = 49 runs + 24 × 1.33 = 32 wickets + 4 catch = 85 points")
    print("\n")
