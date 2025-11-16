#!/usr/bin/env python3
"""
Test New Fantasy Points Rules
==============================
Updated rules:
- NO boundary bonuses (removed 4s/6s points)
- Maidens: 25 points (was 4)
- Strike rate bonuses/penalties (no minimum)
- Economy rate bonuses/penalties (no minimum)
"""

from kncb_html_scraper import KNCBMatchCentreScraper


def print_section(title):
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)
    print()


def test_new_rules():
    """Test new fantasy points rules"""

    scraper = KNCBMatchCentreScraper()

    print("\n" + "=" * 80)
    print("🏏 NEW FANTASY POINTS RULES TEST")
    print("=" * 80)
    print()
    print("Rules:")
    print("  ✓ NO boundary bonuses (fours/sixes don't give extra points)")
    print("  ✓ Maidens: 25 points each (was 4)")
    print("  ✓ Strike rate bonuses:")
    print("      - SR >= 150: +10 points")
    print("      - SR >= 100: +5 points")
    print("      - SR < 50:   -5 points")
    print("  ✓ Economy rate bonuses:")
    print("      - ER < 4.0:  +10 points")
    print("      - ER < 5.0:  +5 points")
    print("      - ER > 7.0:  -5 points")
    print()

    # Test scenarios
    scenarios = [
        {
            'name': '1. Explosive innings (SR 184)',
            'perf': {
                'tier': 'tier2',
                'batting': {
                    'runs': 85,
                    'balls_faced': 46,  # SR = 184.78
                    'fours': 10,  # Should NOT add extra points
                    'sixes': 4    # Should NOT add extra points
                },
                'bowling': {},
                'fielding': {}
            },
            'expected_breakdown': {
                'runs': 85,
                'fifty_bonus': 8,
                'sr_bonus': 10,  # SR >= 150
                'boundary_bonus': 0,  # NONE!
                'total_before_tier': 103,
                'tier_multiplier': 1.0,
                'final': 103
            }
        },
        {
            'name': '2. Anchor innings (SR 45 - slow)',
            'perf': {
                'tier': 'tier2',
                'batting': {
                    'runs': 45,
                    'balls_faced': 100,  # SR = 45
                    'fours': 5,
                    'sixes': 0
                },
                'bowling': {},
                'fielding': {}
            },
            'expected_breakdown': {
                'runs': 45,
                'sr_penalty': -5,  # SR < 50
                'total_before_tier': 40,
                'tier_multiplier': 1.0,
                'final': 40
            }
        },
        {
            'name': '3. Economical bowling with maidens',
            'perf': {
                'tier': 'tier2',
                'batting': {},
                'bowling': {
                    'wickets': 2,
                    'runs_conceded': 18,
                    'overs': 6.0,  # ER = 3.0
                    'maidens': 2
                },
                'fielding': {}
            },
            'expected_breakdown': {
                'wickets': 24,  # 2 x 12
                'maidens': 50,  # 2 x 25 (NEW!)
                'economy_bonus': 10,  # ER < 4.0
                'total_before_tier': 84,
                'tier_multiplier': 1.0,
                'final': 84
            }
        },
        {
            'name': '4. Expensive bowling (ER 8.0)',
            'perf': {
                'tier': 'tier2',
                'batting': {},
                'bowling': {
                    'wickets': 1,
                    'runs_conceded': 40,
                    'overs': 5.0,  # ER = 8.0
                    'maidens': 0
                },
                'fielding': {}
            },
            'expected_breakdown': {
                'wickets': 12,
                'economy_penalty': -5,  # ER > 7.0
                'total_before_tier': 7,
                'tier_multiplier': 1.0,
                'final': 7
            }
        },
        {
            'name': '5. Boundaries without bonus',
            'perf': {
                'tier': 'tier2',
                'batting': {
                    'runs': 42,
                    'balls_faced': 28,  # SR = 150
                    'fours': 6,  # Should NOT add points
                    'sixes': 1   # Should NOT add points
                },
                'bowling': {},
                'fielding': {}
            },
            'expected_breakdown': {
                'runs': 42,  # ONLY runs, no boundary bonus
                'sr_bonus': 10,  # SR >= 150
                'total_before_tier': 52,
                'tier_multiplier': 1.0,
                'final': 52
            }
        },
        {
            'name': '6. Maiden masterclass',
            'perf': {
                'tier': 'tier1',
                'batting': {},
                'bowling': {
                    'wickets': 3,
                    'runs_conceded': 22,
                    'overs': 10.0,  # ER = 2.2
                    'maidens': 5  # 5 maidens!
                },
                'fielding': {}
            },
            'expected_breakdown': {
                'wickets': 36,  # 3 x 12
                'maidens': 125,  # 5 x 25 (HUGE!)
                'economy_bonus': 10,  # ER < 4.0
                'total_before_tier': 171,
                'tier_multiplier': 1.2,  # tier1
                'final': 205  # 171 x 1.2
            }
        },
        {
            'name': '7. Match-winning century (SR 125)',
            'perf': {
                'tier': 'tier1',
                'batting': {
                    'runs': 105,
                    'balls_faced': 84,  # SR = 125
                    'fours': 12,
                    'sixes': 3
                },
                'bowling': {},
                'fielding': {}
            },
            'expected_breakdown': {
                'runs': 105,
                'century_bonus': 16,
                'sr_bonus': 5,  # SR >= 100
                'total_before_tier': 126,
                'tier_multiplier': 1.2,
                'final': 151
            }
        }
    ]

    # Run tests
    for scenario in scenarios:
        points = scraper._calculate_fantasy_points(scenario['perf'])
        expected = scenario['expected_breakdown']['final']

        status = "✅" if points == expected else "⚠️"

        print(f"{status} {scenario['name']}")

        # Show batting details
        batting = scenario['perf']['batting']
        if batting:
            runs = batting.get('runs', 0)
            balls = batting.get('balls_faced', 0)
            fours = batting.get('fours', 0)
            sixes = batting.get('sixes', 0)

            if balls > 0:
                sr = (runs / balls) * 100
                print(f"   Batting: {runs}({balls}) [{fours}x4, {sixes}x6] SR: {sr:.1f}")

        # Show bowling details
        bowling = scenario['perf']['bowling']
        if bowling:
            wickets = bowling.get('wickets', 0)
            runs_conceded = bowling.get('runs_conceded', 0)
            overs = bowling.get('overs', 0)
            maidens = bowling.get('maidens', 0)

            if overs > 0:
                er = runs_conceded / overs
                print(f"   Bowling: {wickets}/{runs_conceded} ({overs} ov, {maidens}M) ER: {er:.2f}")

        # Show breakdown
        print(f"\n   Points Breakdown:")
        breakdown = scenario['expected_breakdown']

        if 'runs' in breakdown:
            print(f"      Runs: {breakdown['runs']}")

        if 'fifty_bonus' in breakdown:
            print(f"      Fifty bonus: +{breakdown['fifty_bonus']}")

        if 'century_bonus' in breakdown:
            print(f"      Century bonus: +{breakdown['century_bonus']}")

        if 'sr_bonus' in breakdown:
            print(f"      Strike rate bonus: +{breakdown['sr_bonus']}")

        if 'sr_penalty' in breakdown:
            print(f"      Strike rate penalty: {breakdown['sr_penalty']}")

        if 'wickets' in breakdown:
            print(f"      Wickets: {breakdown['wickets']}")

        if 'maidens' in breakdown:
            print(f"      Maidens: {breakdown['maidens']} (25 pts each!)")

        if 'economy_bonus' in breakdown:
            print(f"      Economy bonus: +{breakdown['economy_bonus']}")

        if 'economy_penalty' in breakdown:
            print(f"      Economy penalty: {breakdown['economy_penalty']}")

        if 'boundary_bonus' in breakdown:
            print(f"      Boundary bonus: {breakdown['boundary_bonus']} (REMOVED!)")

        if 'total_before_tier' in breakdown:
            print(f"      Subtotal: {breakdown['total_before_tier']}")

        if breakdown.get('tier_multiplier', 1.0) != 1.0:
            print(f"      Tier multiplier: x{breakdown['tier_multiplier']}")

        print(f"\n   Final Points: {points} (expected: {expected})")

        if points != expected:
            print(f"   ⚠️  MISMATCH! Got {points}, expected {expected}")

        print()

    print("=" * 80)
    print()

    # Comparison with old rules
    print_section("COMPARISON: Old vs New Rules")

    comparison_perf = {
        'tier': 'tier2',
        'batting': {
            'runs': 50,
            'balls_faced': 40,  # SR = 125
            'fours': 6,
            'sixes': 2
        },
        'bowling': {},
        'fielding': {}
    }

    new_points = scraper._calculate_fantasy_points(comparison_perf)

    # Calculate old rules manually
    old_points = (
        50 +      # runs
        (6 * 1) + # fours (old rule)
        (2 * 2) + # sixes (old rule)
        8         # fifty bonus
    )  # = 68 points

    print("Example: 50 runs off 40 balls (6 fours, 2 sixes)")
    print()
    print("OLD RULES:")
    print("  50 runs = 50")
    print("  6 fours = 6")
    print("  2 sixes = 4")
    print("  Fifty bonus = 8")
    print(f"  TOTAL: {old_points} points")
    print()
    print("NEW RULES:")
    print("  50 runs = 50")
    print("  6 fours = 0 (no bonus)")
    print("  2 sixes = 0 (no bonus)")
    print("  Fifty bonus = 8")
    print("  SR bonus (125) = 5")
    print(f"  TOTAL: {new_points} points")
    print()

    if new_points < old_points:
        diff = old_points - new_points
        print(f"⬇️  NEW RULES: {diff} points LESS (boundary bonuses removed)")
    elif new_points > old_points:
        diff = new_points - old_points
        print(f"⬆️  NEW RULES: {diff} points MORE (strike rate bonus added)")
    else:
        print("➡️  SAME points")

    print()
    print("=" * 80)
    print("✅ NEW RULES TEST COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    test_new_rules()
