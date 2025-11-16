#!/usr/bin/env python3
"""
Fantasy Cricket Rules - Set 1
==============================
Centralized rules configuration for fantasy cricket points calculation.

All files that need rules should import from this file to ensure consistency.

Usage:
    from rules_set_1 import FANTASY_RULES, calculate_batting_points, calculate_bowling_points
"""

# ============================================================================
# FANTASY POINTS RULES CONFIGURATION
# ============================================================================

FANTASY_RULES = {
    # BATTING POINTS
    # --------------
    # Tiered run points:
    #   - Runs 1-30: 1.0 points per run
    #   - Runs 31-49: 1.25 points per run
    #   - Runs 50-99: 1.5 points per run
    #   - Runs 100+: 1.75 points per run
    # Multiplier: Run points × (Strike Rate / 100)
    #   - SR 100 = 1.0x (neutral)
    #   - SR 150 = 1.5x (50% bonus)
    #   - SR 50 = 0.5x (50% penalty)
    # NO boundary bonuses (fours/sixes count as runs only)
    'batting': {
        'run_tiers': [
            {'min': 1, 'max': 30, 'points_per_run': 1.0},
            {'min': 31, 'max': 49, 'points_per_run': 1.25},
            {'min': 50, 'max': 99, 'points_per_run': 1.5},
            {'min': 100, 'max': 999, 'points_per_run': 1.75},
        ],
        'strike_rate_applies_as_multiplier': True,  # Run points × (SR / 100)
        'fifty_bonus': 8,
        'century_bonus': 16,
        'duck_penalty': -2,  # 0 runs while dismissed
    },

    # BOWLING POINTS
    # --------------
    # Tiered wicket points:
    #   - Wickets 1-2: 15 points each
    #   - Wickets 3-4: 20 points each
    #   - Wickets 5-10: 30 points each
    # Multiplier: Wicket points × (6.0 / Economy Rate)
    #   - ER 6.0 = 1.0x (neutral)
    #   - ER 4.0 = 1.5x (50% bonus)
    #   - ER 8.0 = 0.75x (25% penalty)
    'bowling': {
        'wicket_tiers': [
            {'min': 1, 'max': 2, 'points_per_wicket': 15},
            {'min': 3, 'max': 4, 'points_per_wicket': 20},
            {'min': 5, 'max': 10, 'points_per_wicket': 30},
        ],
        'economy_rate_applies_as_multiplier': True,  # Wicket points × (6.0 / ER)
        'points_per_maiden': 15,  # Same value as wickets 1-2
        'five_wicket_haul_bonus': 8,
    },

    # FIELDING POINTS
    # ---------------
    'fielding': {
        'points_per_catch': 4,
        'points_per_stumping': 6,
        'points_per_runout': 6,
        'wicketkeeper_catch_multiplier': 2.0,  # Wicketkeeper catches worth 2x
    },

    # PLAYER MULTIPLIERS
    # ------------------
    # Each player has a personal performance multiplier based on historical stats
    # relative to their club's median performance.
    # IMPORTANT: Lower multiplier = HANDICAP for strong players
    #   - 0.69 = Best real-life players (their fantasy points are REDUCED)
    #   - 1.0 = Median performers (no adjustment)
    #   - 5.0 = Weakest players (their fantasy points are BOOSTED)
    # This creates balance: strong players cost more, weak players are valuable picks
    'player_multipliers': {
        'min': 0.69,  # Best IRL players - fantasy points HANDICAPPED (0.69x)
        'neutral': 1.0,  # Median club performance - no change
        'max': 5.0,  # Weak IRL players - fantasy points BOOSTED (5.0x)
        'weekly_adjustment_max': 0.15,  # Max 15% change per week
    },

    # LEADERSHIP & SPECIAL ROLES
    # --------------------------
    # Applied in fantasy team scoring (not in base calculations)
    'leadership': {
        'captain_multiplier': 2.0,
        'vice_captain_multiplier': 1.5,
        'wicketkeeper_multiplier': 2.0,  # Applied to catches only
    },

    # TIER/LEAGUE SETTINGS
    # --------------------
    # Tier is used ONLY for team identification and roster constraints
    # NO scoring multipliers based on tier/league
    'tiers': {
        'applies_to_scoring': False,
        'used_for': 'team_identification_only',
    }
}


# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate_batting_points(runs: int, balls_faced: int, is_out: bool) -> dict:
    """
    Calculate batting points with tiered run values and strike rate multiplier

    Args:
        runs: Runs scored
        balls_faced: Balls faced
        is_out: Whether batsman was dismissed

    Returns:
        Dictionary with breakdown:
        {
            'base_run_points': float,
            'run_points_after_sr': float,
            'sr_multiplier': float,
            'fifty_bonus': int,
            'century_bonus': int,
            'duck_penalty': int,
            'total': float
        }
    """
    rules = FANTASY_RULES['batting']
    breakdown = {
        'base_run_points': 0.0,
        'run_points_after_sr': 0.0,
        'sr_multiplier': 1.0,
        'fifty_bonus': 0,
        'century_bonus': 0,
        'duck_penalty': 0,
        'total': 0.0
    }

    # Calculate tiered run points
    base_run_points = 0.0
    if runs > 0:
        runs_counted = 0
        for tier in rules['run_tiers']:
            tier_min = tier['min']
            tier_max = tier['max']
            points_per_run = tier['points_per_run']

            if runs >= tier_min:
                # How many runs fall in this tier?
                tier_start = max(runs_counted + 1, tier_min)
                tier_end = min(runs, tier_max)
                runs_in_tier = tier_end - tier_start + 1

                if runs_in_tier > 0:
                    base_run_points += runs_in_tier * points_per_run
                    runs_counted = tier_end

                if runs_counted >= runs:
                    break

    breakdown['base_run_points'] = base_run_points

    # Apply strike rate multiplier
    if balls_faced > 0 and runs > 0:
        strike_rate = (runs / balls_faced) * 100
        sr_multiplier = strike_rate / 100
        breakdown['sr_multiplier'] = sr_multiplier
        breakdown['run_points_after_sr'] = base_run_points * sr_multiplier
    else:
        breakdown['run_points_after_sr'] = base_run_points

    # Milestone bonuses
    if runs >= 100:
        breakdown['century_bonus'] = rules['century_bonus']
    elif runs >= 50:
        breakdown['fifty_bonus'] = rules['fifty_bonus']

    # Duck penalty
    if is_out and runs == 0:
        breakdown['duck_penalty'] = rules['duck_penalty']

    # Total
    breakdown['total'] = (
        breakdown['run_points_after_sr'] +
        breakdown['fifty_bonus'] +
        breakdown['century_bonus'] +
        breakdown['duck_penalty']
    )

    return breakdown


def calculate_bowling_points(wickets: int, overs: float, runs_conceded: int, maidens: int) -> dict:
    """
    Calculate bowling points with tiered wicket values and economy rate multiplier

    Args:
        wickets: Wickets taken
        overs: Overs bowled (e.g., 4.2 = 4 overs 2 balls)
        runs_conceded: Runs given away
        maidens: Maiden overs bowled

    Returns:
        Dictionary with breakdown:
        {
            'base_wicket_points': float,
            'wicket_points_after_er': float,
            'er_multiplier': float,
            'maiden_points': int,
            'five_wicket_bonus': int,
            'total': float
        }
    """
    rules = FANTASY_RULES['bowling']
    breakdown = {
        'base_wicket_points': 0.0,
        'wicket_points_after_er': 0.0,
        'er_multiplier': 1.0,
        'maiden_points': 0,
        'five_wicket_bonus': 0,
        'total': 0.0
    }

    # Calculate tiered wicket points
    base_wicket_points = 0.0
    if wickets > 0:
        remaining_wickets = wickets
        wicket_number = 1

        for tier in rules['wicket_tiers']:
            tier_min = tier['min']
            tier_max = tier['max']
            points_per_wicket = tier['points_per_wicket']

            while wicket_number <= wickets and wicket_number <= tier_max:
                if wicket_number >= tier_min:
                    base_wicket_points += points_per_wicket
                wicket_number += 1

            if wicket_number > wickets:
                break

    breakdown['base_wicket_points'] = base_wicket_points

    # Apply economy rate multiplier
    if overs > 0 and wickets > 0:
        economy_rate = runs_conceded / overs
        if economy_rate > 0:
            er_multiplier = 6.0 / economy_rate
            breakdown['er_multiplier'] = er_multiplier
            breakdown['wicket_points_after_er'] = base_wicket_points * er_multiplier
        else:
            # Perfect economy (no runs conceded)
            breakdown['er_multiplier'] = 6.0
            breakdown['wicket_points_after_er'] = base_wicket_points * 6.0
    else:
        breakdown['wicket_points_after_er'] = base_wicket_points

    # Maiden points
    breakdown['maiden_points'] = maidens * rules['points_per_maiden']

    # Five wicket haul bonus
    if wickets >= 5:
        breakdown['five_wicket_bonus'] = rules['five_wicket_haul_bonus']

    # Total
    breakdown['total'] = (
        breakdown['wicket_points_after_er'] +
        breakdown['maiden_points'] +
        breakdown['five_wicket_bonus']
    )

    return breakdown


def calculate_fielding_points(catches: int = 0, stumpings: int = 0, runouts: int = 0, is_wicketkeeper: bool = False) -> dict:
    """
    Calculate fielding points

    Args:
        catches: Number of catches
        stumpings: Number of stumpings
        runouts: Number of runouts
        is_wicketkeeper: Whether player is designated wicketkeeper (2x catch points)

    Returns:
        Dictionary with breakdown:
        {
            'catch_points': int,
            'stumping_points': int,
            'runout_points': int,
            'wicketkeeper_bonus': int,
            'total': int
        }
    """
    rules = FANTASY_RULES['fielding']
    catch_points = catches * rules['points_per_catch']

    breakdown = {
        'catch_points': catch_points,
        'stumping_points': stumpings * rules['points_per_stumping'],
        'runout_points': runouts * rules['points_per_runout'],
        'wicketkeeper_bonus': 0,
    }

    # Apply wicketkeeper multiplier to catches
    if is_wicketkeeper and catches > 0:
        wk_multiplier = rules['wicketkeeper_catch_multiplier']
        breakdown['wicketkeeper_bonus'] = catch_points * (wk_multiplier - 1)  # Additional points from multiplier
        breakdown['catch_points'] = catch_points * wk_multiplier

    breakdown['total'] = (
        breakdown['catch_points'] +
        breakdown['stumping_points'] +
        breakdown['runout_points']
    )
    return breakdown


def calculate_total_fantasy_points(
    runs: int = 0,
    balls_faced: int = 0,
    is_out: bool = False,
    wickets: int = 0,
    overs: float = 0.0,
    runs_conceded: int = 0,
    maidens: int = 0,
    catches: int = 0,
    stumpings: int = 0,
    runouts: int = 0,
    is_wicketkeeper: bool = False
) -> dict:
    """
    Calculate total fantasy points from all performance stats

    Args:
        is_wicketkeeper: Whether player is designated wicketkeeper (2x catch points)

    Returns:
        Dictionary with complete breakdown and grand total
    """
    batting = calculate_batting_points(runs, balls_faced, is_out)
    bowling = calculate_bowling_points(wickets, overs, runs_conceded, maidens)
    fielding = calculate_fielding_points(catches, stumpings, runouts, is_wicketkeeper)

    grand_total = batting['total'] + bowling['total'] + fielding['total']

    return {
        'batting': batting,
        'bowling': bowling,
        'fielding': fielding,
        'grand_total': grand_total
    }


def apply_player_multiplier(base_points: float, player_multiplier: float) -> float:
    """
    Apply player performance multiplier to base points

    Args:
        base_points: Base fantasy points before player multiplier
        player_multiplier: Player's personal multiplier (0.69 to 5.0)

    Returns:
        Points after applying player multiplier
    """
    return base_points * player_multiplier


def apply_leadership_multiplier(points: float, is_captain: bool = False, is_vice_captain: bool = False) -> float:
    """
    Apply leadership multiplier (Captain/Vice-Captain)

    Args:
        points: Points before leadership multiplier
        is_captain: Whether player is captain
        is_vice_captain: Whether player is vice-captain

    Returns:
        Points after applying leadership multiplier
    """
    rules = FANTASY_RULES['leadership']

    if is_captain:
        return points * rules['captain_multiplier']
    elif is_vice_captain:
        return points * rules['vice_captain_multiplier']
    else:
        return points


# ============================================================================
# VALIDATION
# ============================================================================

def validate_player_multiplier(multiplier: float) -> bool:
    """Validate that player multiplier is within allowed range"""
    rules = FANTASY_RULES['player_multipliers']
    return rules['min'] <= multiplier <= rules['max']


def get_rules_summary() -> str:
    """Get a human-readable summary of the rules"""
    rules = FANTASY_RULES

    summary = """
Fantasy Cricket Points Rules - Set 1
====================================

BATTING:
- Tiered Run Points:
  - Runs 1-30: 1.0 pts per run
  - Runs 31-49: 1.25 pts per run
  - Runs 50-99: 1.5 pts per run
  - Runs 100+: 1.75 pts per run
- Strike Rate Multiplier: Run points × (SR / 100)
  - SR 100 = 1.0x, SR 150 = 1.5x, SR 200 = 2.0x
- Fifty bonus: +{batting[fifty_bonus]} points
- Century bonus: +{batting[century_bonus]} points
- Duck penalty: {batting[duck_penalty]} points
- NO boundary bonuses

BOWLING:
- Tiered Wicket Points:
  - Wickets 1-2: 15 pts each
  - Wickets 3-4: 20 pts each
  - Wickets 5-10: 30 pts each
- Economy Rate Multiplier: Wicket points × (6.0 / ER)
  - ER 6.0 = 1.0x, ER 4.0 = 1.5x, ER 3.0 = 2.0x
- Maiden over: +{bowling[points_per_maiden]} points each
- Five wicket haul: +{bowling[five_wicket_haul_bonus]} points

FIELDING:
- Catch: +{fielding[points_per_catch]} points
- Stumping: +{fielding[points_per_stumping]} points
- Runout: +{fielding[points_per_runout]} points
- Wicketkeeper: {fielding[wicketkeeper_catch_multiplier]}x catch points

PLAYER MULTIPLIERS (Performance Handicap System):
- Range: {player_multipliers[min]} to {player_multipliers[max]}
- {player_multipliers[min]} = Best IRL players (fantasy points REDUCED/handicapped)
- {player_multipliers[neutral]} = Median performers (no change)
- {player_multipliers[max]} = Weak IRL players (fantasy points BOOSTED)
- Weekly adjustment: max {player_multipliers[weekly_adjustment_max]} (15%)

FANTASY TEAM ROLES:
- Captain: {leadership[captain_multiplier]}x points
- Vice-Captain: {leadership[vice_captain_multiplier]}x points
- Wicketkeeper: {leadership[wicketkeeper_multiplier]}x catch points

FINAL FORMULA:
Base Points × Player Multiplier (0.69-5.0) × Leadership Multiplier
""".format(**rules)

    return summary


if __name__ == "__main__":
    # Print rules summary
    print(get_rules_summary())

    # Example calculation
    print("\n" + "="*70)
    print("EXAMPLE: Aggressive batsman (50 runs, 33 balls)")
    print("="*70)
    result = calculate_total_fantasy_points(runs=50, balls_faced=33, is_out=True)
    print(f"Base run points: {result['batting']['base_run_points']:.1f}")
    print(f"SR multiplier: {result['batting']['sr_multiplier']:.2f}x")
    print(f"Run points after SR: {result['batting']['run_points_after_sr']:.1f}")
    print(f"Fifty bonus: {result['batting']['fifty_bonus']}")
    print(f"TOTAL: {result['grand_total']:.1f} points")
