#!/usr/bin/env python3
"""
Test Tiered Fantasy Points System
===================================
Tests the current tiered points system from rules-set-1.py

Batting Tiers:
- Runs 1-30: 1.0 pts/run
- Runs 31-49: 1.25 pts/run
- Runs 50-99: 1.5 pts/run
- Runs 100+: 1.75 pts/run
- Multiplier: × (SR / 100)

Bowling Tiers:
- Wickets 1-2: 15 pts each
- Wickets 3-4: 20 pts each
- Wickets 5-10: 30 pts each
- Multiplier: × (6.0 / ER)
- Maidens: 15 pts each
"""

try:
    from rules_set_1 import calculate_total_fantasy_points, FANTASY_RULES
except ImportError:
    import importlib
    rules_module = importlib.import_module('rules-set-1')
    calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points
    FANTASY_RULES = rules_module.FANTASY_RULES


def test_scenario(name, **kwargs):
    """Test a scenario and print detailed breakdown"""
    print(f"\n{'='*80}")
    print(f"🧪 {name}")
    print(f"{'='*80}")

    # Calculate points
    result = calculate_total_fantasy_points(**kwargs)

    # Print batting breakdown if applicable
    if kwargs.get('runs', 0) > 0 or kwargs.get('balls_faced', 0) > 0:
        batting = result['batting']
        runs = kwargs['runs']
        balls_faced = kwargs.get('balls_faced', 0)
        sr = (runs / balls_faced * 100) if balls_faced > 0 else 0

        print(f"\n🏏 BATTING: {runs} runs off {balls_faced} balls (SR {sr:.1f})")
        print(f"   Base run points: {batting['base_run_points']:.2f}")
        print(f"   After SR multiplier: {batting['run_points_after_sr']:.2f} (× {sr/100:.2f})")
        if batting.get('fifty_bonus'):
            print(f"   Fifty bonus: +{batting['fifty_bonus']}")
        if batting.get('century_bonus'):
            print(f"   Century bonus: +{batting['century_bonus']}")
        if batting.get('duck_penalty'):
            print(f"   Duck penalty: {batting['duck_penalty']}")
        print(f"   Batting Total: {batting['total']:.2f} points")

    # Print bowling breakdown if applicable
    if kwargs.get('wickets', 0) > 0 or kwargs.get('overs', 0) > 0:
        bowling = result['bowling']
        wickets = kwargs['wickets']
        overs = kwargs.get('overs', 0)
        runs_conceded = kwargs.get('runs_conceded', 0)
        er = runs_conceded / overs if overs > 0 else 0
        maidens = kwargs.get('maidens', 0)

        print(f"\n⚾ BOWLING: {wickets}/{runs_conceded} in {overs} overs (ER {er:.2f})")
        print(f"   Base wicket points: {bowling['base_wicket_points']:.2f}")
        print(f"   After ER multiplier: {bowling['wicket_points_after_er']:.2f} (× {6.0/er if er > 0 else 6.0:.2f})")
        if maidens > 0:
            print(f"   Maidens: {bowling['maiden_points']} points ({maidens} × 15)")
        if bowling.get('five_wicket_bonus'):
            print(f"   5-wicket haul bonus: +{bowling['five_wicket_bonus']}")
        print(f"   Bowling Total: {bowling['total']:.2f} points")

    # Print fielding breakdown if applicable
    fielding = result['fielding']
    if fielding['total'] > 0:
        print(f"\n🥎 FIELDING:")
        if kwargs.get('catches', 0) > 0:
            wk_bonus = " (WK 2x)" if fielding.get('wicketkeeper_bonus', 0) > 0 else ""
            print(f"   Catches: {fielding['catch_points']} points{wk_bonus}")
        if kwargs.get('stumpings', 0) > 0:
            print(f"   Stumpings: {fielding['stumping_points']} points")
        if kwargs.get('runouts', 0) > 0:
            print(f"   Run-outs: {fielding['runout_points']} points")
        print(f"   Fielding Total: {fielding['total']} points")

    print(f"\n✅ GRAND TOTAL: {result['grand_total']:.2f} points")

    return result


def run_all_tests():
    """Run comprehensive test suite"""
    print("\n" + "="*80)
    print("🏏 TIERED FANTASY POINTS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)

    print("\nRULES BEING TESTED:")
    print("Batting: Tiered runs (1.0/1.25/1.5/1.75) × SR multiplier")
    print("Bowling: Tiered wickets (15/20/30) × ER multiplier")
    print("Fielding: Catches 15, Stumpings 15, Run-outs 6")

    # Test 1: Tier boundaries - 30 runs
    test_scenario(
        "Test 1: Tier 1 batting (30 runs at SR 100)",
        runs=30,
        balls_faced=30,
        is_out=False
    )
    expected = 30 * 1.0 * 1.0  # 30 pts
    print(f"   Expected: ~30.00 points (tier 1: 1.0 pts/run)")

    # Test 2: Tier boundaries - 50 runs with bonus
    test_scenario(
        "Test 2: Tier 2-3 batting (50 runs at SR 125)",
        runs=50,
        balls_faced=40,
        is_out=False
    )
    # 30 @ 1.0 + 20 @ 1.25 = 55 base, × 1.25 SR = 68.75 + 8 bonus = 76.75
    print(f"   Expected: ~76.75 points (30@1.0 + 20@1.25 = 55, ×1.25 SR = 68.75, +8 bonus)")

    # Test 3: Century
    test_scenario(
        "Test 3: Century (100 runs at SR 150)",
        runs=100,
        balls_faced=67,
        is_out=True
    )
    # 30@1.0 + 19@1.25 + 51@1.5 = 106.25 base, × 1.5 SR = 159.375 + 16 bonus = 175.375
    print(f"   Expected: ~175.38 points (tiered base 106.25, ×1.5 SR = 159.38, +16 bonus)")

    # Test 4: Duck penalty
    test_scenario(
        "Test 4: Duck (0 runs, dismissed)",
        runs=0,
        balls_faced=3,
        is_out=True
    )
    print(f"   Expected: -2 points (duck penalty)")

    # Test 5: Economy bowling - 2 wickets
    test_scenario(
        "Test 5: Economical bowling (2/18 in 6.0 overs, ER 3.0)",
        wickets=2,
        overs=6.0,
        runs_conceded=18,
        maidens=2
    )
    # 2 wickets @ 15 = 30, × (6.0/3.0) = 60, + 2 maidens @ 15 = 30, total = 90
    print(f"   Expected: ~90 points (30 base × 2.0 ER = 60, +30 maidens)")

    # Test 6: 5-wicket haul
    test_scenario(
        "Test 6: Five-wicket haul (5/35 in 8.0 overs, ER 4.375)",
        wickets=5,
        overs=8.0,
        runs_conceded=35,
        maidens=1
    )
    # 2@15 + 2@20 + 1@30 = 100, × (6.0/4.375) = 137.14, + 15 maidens + 8 bonus = 160.14
    print(f"   Expected: ~160.14 points (100 base × 1.37 ER = 137.14, +15 maiden, +8 bonus)")

    # Test 7: All-rounder performance
    test_scenario(
        "Test 7: All-rounder (45 runs SR 140, 2/20 in 4.0 overs, 1 catch)",
        runs=45,
        balls_faced=32,
        is_out=True,
        wickets=2,
        overs=4.0,
        runs_conceded=20,
        maidens=0,
        catches=1
    )
    # Batting: 30@1.0 + 15@1.25 = 48.75, × 1.40625 = 68.55
    # Bowling: 2@15 = 30, × (6.0/5.0) = 36
    # Fielding: 1 catch = 15
    # Total: 68.55 + 36 + 15 = 119.55
    print(f"   Expected: ~119.55 points (batting 68.55 + bowling 36 + fielding 15)")

    # Test 8: Slow batting penalty
    test_scenario(
        "Test 8: Slow innings (30 runs SR 50)",
        runs=30,
        balls_faced=60,
        is_out=False
    )
    # 30 @ 1.0 = 30, × 0.5 SR = 15
    print(f"   Expected: ~15 points (30 base × 0.5 SR)")

    # Test 9: Explosive batting
    test_scenario(
        "Test 9: Explosive innings (85 runs SR 185)",
        runs=85,
        balls_faced=46,
        is_out=True
    )
    # 30@1.0 + 19@1.25 + 36@1.5 = 107.75, × 1.85 = 199.34, + 8 bonus = 207.34
    print(f"   Expected: ~207.34 points (107.75 base × 1.85 SR = 199.34, +8 bonus)")

    # Test 10: Expensive bowling
    test_scenario(
        "Test 10: Expensive bowling (1/40 in 5.0 overs, ER 8.0)",
        wickets=1,
        overs=5.0,
        runs_conceded=40,
        maidens=0
    )
    # 1@15 = 15, × (6.0/8.0) = 11.25
    print(f"   Expected: ~11.25 points (15 base × 0.75 ER)")

    # Test 11: Wicketkeeper catches
    test_scenario(
        "Test 11: Wicketkeeper (2 catches, 1 stumping)",
        catches=2,
        stumpings=1,
        is_wicketkeeper=True
    )
    # 2 catches @ 15 × 2.0 = 60, + 1 stumping @ 15 = 15, total = 75
    print(f"   Expected: ~75 points (2 catches × 30 WK bonus + 1 stumping × 15)")

    # Test 12: 100+ runs tier 4
    test_scenario(
        "Test 12: 150 runs at SR 120 (tier 4)",
        runs=150,
        balls_faced=125,
        is_out=True
    )
    # 30@1.0 + 19@1.25 + 50@1.5 + 51@1.75 = 188.0, × 1.2 SR = 225.6, + 16 bonus = 241.6
    print(f"   Expected: ~241.60 points (188 tiered base × 1.2 SR = 225.6, +16 bonus)")

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80)
    print("\nNOTE: If all calculations match expectations, the tiered system is working correctly!")
    print("Frontend calculator should produce identical results with rules-set-1.json")


if __name__ == "__main__":
    run_all_tests()
