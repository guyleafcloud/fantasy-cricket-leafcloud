#!/usr/bin/env python3
"""
Test Legacy Roster Integration
===============================
Demonstrates how legacy rosters seed the aggregator and match with scraped data.
"""

from player_aggregator import PlayerSeasonAggregator
from legacy_roster_loader import LegacyRosterLoader
import json


def test_full_integration():
    """Test complete flow: legacy import → scraping → matching"""

    print("🏏 Testing Legacy Roster Integration")
    print("=" * 70)

    # Step 1: Create aggregator
    print("\n1️⃣ Creating aggregator...")
    aggregator = PlayerSeasonAggregator()

    # Step 2: Load legacy roster
    print("\n2️⃣ Loading ACC legacy roster...")
    loader = LegacyRosterLoader()

    legacy_roster = {
        "club": "ACC",
        "season": "2024",
        "players": [
            {"name": "Boris Gorlee", "club": "ACC", "role": "all-rounder"},
            {"name": "Sikander Zulfiqar", "club": "ACC", "role": "batsman"},
            {"name": "Shariz Ahmad", "club": "ACC", "role": "bowler"},
        ]
    }

    # Save and load
    with open('test_acc_roster.json', 'w') as f:
        json.dump(legacy_roster, f, indent=2)

    legacy_players = loader.load_from_json('test_acc_roster.json')
    imported = loader.import_to_aggregator(aggregator, legacy_players)

    print(f"   ✅ Imported {imported} legacy players")

    # Show initial state
    print("\n📊 Initial State (Legacy Only):")
    acc_players = aggregator.get_players_by_club('ACC')
    for player in acc_players:
        legacy_marker = " 🏷️  LEGACY" if player.get('is_legacy_import') else ""
        print(f"   - {player['player_name']}{legacy_marker}")
        print(f"     Matches: {player['matches_played']}, Points: {player['season_totals']['fantasy_points']}")

    # Step 3: Simulate scraped match performances
    print("\n3️⃣ Simulating scraped match data...")
    print("   (New season starts, first match played)")

    scraped_performances = [
        # RETURNING PLAYER: Boris Gorlee (should match legacy)
        {
            'player_name': 'Boris Gorlee',  # Exact match
            'player_id': None,  # No ID from scraper
            'club': 'ACC',
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'VRA',
            'tier': 'tier1',
            'batting': {'runs': 56, 'balls_faced': 45, 'fours': 7, 'sixes': 2},
            'bowling': {'wickets': 2, 'runs_conceded': 32, 'overs': 9.0, 'maidens': 1},
            'fielding': {'catches': 1},
            'fantasy_points': 108
        },
        # RETURNING PLAYER: Sikander (name variation - fuzzy match)
        {
            'player_name': 'S. Zulfiqar',  # Abbreviated version
            'player_id': None,
            'club': 'ACC',
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'VRA',
            'tier': 'tier1',
            'batting': {'runs': 34, 'balls_faced': 29, 'fours': 4, 'sixes': 1},
            'bowling': {},
            'fielding': {},
            'fantasy_points': 40
        },
        # NEW PLAYER: Not in legacy roster
        {
            'player_name': 'Tom de Grooth',  # New debut
            'player_id': None,
            'club': 'ACC',
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'VRA',
            'tier': 'tier1',
            'batting': {'runs': 23, 'balls_faced': 31, 'fours': 2, 'sixes': 0},
            'bowling': {},
            'fielding': {'catches': 2},
            'fantasy_points': 31
        }
    ]

    # Process scraped data
    for perf in scraped_performances:
        print(f"\n   Processing: {perf['player_name']}")
        aggregator.add_match_performance(perf)

    # Step 4: Show results
    print("\n" + "=" * 70)
    print("📊 RESULTS After First Match")
    print("=" * 70)

    acc_players = aggregator.get_players_by_club('ACC')
    print(f"\nACC Roster: {len(acc_players)} players")

    for player in acc_players:
        is_legacy = player.get('is_legacy_import', False)
        played = player['matches_played'] > 0

        if is_legacy and not played:
            status = "🏷️  LEGACY (not played yet)"
        elif is_legacy and played:
            status = "⚠️  ERROR - should not be legacy after playing"
        elif not is_legacy and played:
            status = "✅ ACTIVE"
        else:
            status = "❓ UNKNOWN"

        print(f"\n{player['player_name']} - {status}")
        print(f"   Matches: {player['matches_played']}")
        print(f"   Fantasy Points: {player['season_totals']['fantasy_points']}")
        if player['season_totals']['batting']['runs'] > 0:
            print(f"   Runs: {player['season_totals']['batting']['runs']}")
        if player['season_totals']['bowling']['wickets'] > 0:
            print(f"   Wickets: {player['season_totals']['bowling']['wickets']}")

    # Verify matching worked correctly
    print("\n" + "=" * 70)
    print("🧪 VERIFICATION")
    print("=" * 70)

    # Check Boris Gorlee (exact match)
    boris = next((p for p in acc_players if 'Boris' in p['player_name']), None)
    if boris:
        if boris['matches_played'] == 1 and boris['season_totals']['fantasy_points'] == 108:
            print("✅ Boris Gorlee: Legacy player matched and updated correctly")
        else:
            print(f"❌ Boris Gorlee: Expected 1 match/108 pts, got {boris['matches_played']}/{boris['season_totals']['fantasy_points']}")
    else:
        print("❌ Boris Gorlee: Not found!")

    # Check Sikander (fuzzy match)
    sikander = next((p for p in acc_players if 'Zulfiqar' in p['player_name'] and 'Sikander' in p['player_name']), None)
    if sikander:
        if sikander['matches_played'] == 1 and sikander['season_totals']['fantasy_points'] == 40:
            print("✅ Sikander Zulfiqar: Fuzzy matched 'S. Zulfiqar' and updated correctly")
        else:
            print(f"❌ Sikander: Expected 1 match/40 pts, got {sikander['matches_played']}/{sikander['season_totals']['fantasy_points']}")
    else:
        print("❌ Sikander: Not found!")

    # Check Tom (new player)
    tom = next((p for p in acc_players if 'Tom' in p['player_name']), None)
    if tom:
        if tom['matches_played'] == 1 and not tom.get('is_legacy_import'):
            print("✅ Tom de Grooth: New player added correctly")
        else:
            print(f"❌ Tom: Should be new player, is_legacy={tom.get('is_legacy_import')}")
    else:
        print("❌ Tom: Not found!")

    # Check Shariz (legacy but didn't play)
    shariz = next((p for p in acc_players if 'Shariz' in p['player_name']), None)
    if shariz:
        if shariz['matches_played'] == 0 and shariz.get('is_legacy_import'):
            print("✅ Shariz Ahmad: Legacy player preserved (didn't play yet)")
        else:
            print(f"❌ Shariz: Should be legacy with 0 matches, got matches={shariz['matches_played']}, legacy={shariz.get('is_legacy_import')}")
    else:
        print("❌ Shariz: Not found!")

    print("\n" + "=" * 70)
    print("✅ INTEGRATION TEST COMPLETE!")
    print("\n💡 Summary:")
    print("   - Legacy players seed the roster")
    print("   - When they play, they match by name and accumulate stats")
    print("   - New players are added as they debut")
    print("   - Legacy players who don't play yet remain in roster")


if __name__ == "__main__":
    test_full_integration()
