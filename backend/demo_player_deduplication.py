#!/usr/bin/env python3
"""
Demo: Player Deduplication Across Multiple Grades
==================================================
Demonstrates how the system handles a player who plays in multiple
teams/grades in the same week.

Scenario:
- Jan de Vries plays in ACC 1, U17, and ZAMI in the same week
- System correctly identifies this is the same player
- Aggregates points across all matches
- Links to database player record
"""

from player_matcher import PlayerMatcher
from kncb_html_scraper import KNCBMatchCentreScraper


def demo():
    print("\n" + "=" * 80)
    print("🏏 PLAYER DEDUPLICATION DEMO")
    print("=" * 80)
    print()

    # Initialize
    scraper = KNCBMatchCentreScraper()
    matcher = PlayerMatcher()

    # Simulate scraped performances from a weekly scrape
    print("SCENARIO: Jan de Vries plays in 3 different grades this week")
    print("=" * 80)
    print()

    performances = [
        # Match 1: ACC 1 (Eerste Klasse) - tier2
        {
            'player_id': '12345',
            'player_name': 'Jan de Vries',
            'match_id': 7001,
            'match_date': '2025-11-10',
            'tier': 'tier2',
            'opponent': 'VRA',
            'batting': {'runs': 45, 'balls_faced': 38, 'fours': 5, 'sixes': 1},
            'bowling': {'wickets': 2, 'runs_conceded': 32, 'overs': 8.0, 'maidens': 1},
            'fielding': {'catches': 1, 'stumpings': 0, 'runouts': 0},
            'fantasy_points': 0  # Will calculate
        },
        # Match 2: U17 Competition - youth tier
        {
            'player_id': '12345',
            'player_name': 'Jan de Vries',
            'match_id': 7002,
            'match_date': '2025-11-11',
            'tier': 'youth',
            'opponent': 'Quick Haarlem U17',
            'batting': {'runs': 78, 'balls_faced': 52, 'fours': 8, 'sixes': 3},
            'bowling': {},
            'fielding': {},
            'fantasy_points': 0  # Will calculate
        },
        # Match 3: ZAMI Social - social tier
        # Note: Name appears slightly different (J. de Vries)
        {
            'player_id': '12345',
            'player_name': 'J. de Vries',
            'match_id': 7003,
            'match_date': '2025-11-12',
            'tier': 'social',
            'opponent': 'Excelsior ZAMI',
            'batting': {},
            'bowling': {'wickets': 3, 'runs_conceded': 25, 'overs': 6.0, 'maidens': 0},
            'fielding': {'catches': 2, 'stumpings': 0, 'runouts': 0},
            'fantasy_points': 0  # Will calculate
        },

        # Other players for context
        {
            'player_id': '67890',
            'player_name': 'Peter Smith',
            'match_id': 7001,
            'match_date': '2025-11-10',
            'tier': 'tier2',
            'opponent': 'ACC',
            'batting': {'runs': 35, 'balls_faced': 42, 'fours': 3, 'sixes': 0},
            'bowling': {},
            'fielding': {},
            'fantasy_points': 0
        }
    ]

    # Calculate fantasy points for each performance
    for perf in performances:
        perf['fantasy_points'] = scraper._calculate_fantasy_points(perf)

    print("📊 RAW SCRAPED PERFORMANCES:")
    print("=" * 80)
    for i, perf in enumerate(performances, 1):
        print(f"\n{i}. Match {perf['match_id']} - {perf['tier']}")
        print(f"   Player: {perf['player_name']} (ID: {perf['player_id']})")
        print(f"   Date: {perf['match_date']}")
        print(f"   vs {perf['opponent']}")

        if perf['batting']:
            b = perf['batting']
            if b.get('runs', 0) > 0:
                print(f"   Batting: {b['runs']}({b['balls_faced']}) [{b['fours']}x4, {b['sixes']}x6]")

        if perf['bowling']:
            bw = perf['bowling']
            if bw.get('wickets', 0) > 0:
                print(f"   Bowling: {bw['wickets']}/{bw['runs_conceded']} ({bw['overs']} ov, {bw['maidens']}M)")

        if perf['fielding']:
            f = perf['fielding']
            if f.get('catches', 0) > 0:
                print(f"   Fielding: {f['catches']} catches")

        print(f"   Fantasy Points: {perf['fantasy_points']}")

    print("\n" + "=" * 80)
    print()

    # Simulate database players
    db_players = [
        {'id': 'acc-player-001', 'name': 'Jan de Vries', 'player_id': '12345', 'club_id': 'acc-club-id'},
        {'id': 'acc-player-002', 'name': 'Peter Smith', 'player_id': '67890', 'club_id': 'acc-club-id'},
    ]

    # Process the weekly scrape
    print("🔄 PROCESSING WEEKLY SCRAPE (Deduplication + Matching)")
    print("=" * 80)
    print()

    result = matcher.process_weekly_scrape(performances, db_players)

    print(f"✅ Processing Complete!")
    print(f"   Total performances scraped: {result['total_performances']}")
    print(f"   Unique players identified: {result['total_unique_players']}")
    print(f"   Matched to database: {len(result['matched_players'])}")
    print(f"   New players (not in DB): {len(result['unmatched_players'])}")
    print()

    # Show aggregated player data
    print("=" * 80)
    print("👤 AGGREGATED PLAYER STATS (Ready for Database Update)")
    print("=" * 80)
    print()

    for i, player in enumerate(result['matched_players'], 1):
        print(f"{i}. {player['player_name']} (Player ID: {player['player_id']})")
        print(f"   Database ID: {player['db_player_id']}")
        print(f"   Total Matches: {player['total_matches']}")
        print(f"   Total Fantasy Points: {player['total_fantasy_points']}")
        print()

        stats = player['stats_summary']
        if stats['total_runs'] > 0:
            print(f"   Batting: {stats['total_runs']} runs total")
        if stats['total_wickets'] > 0:
            print(f"   Bowling: {stats['total_wickets']} wickets total")
        if stats['total_catches'] > 0:
            print(f"   Fielding: {stats['total_catches']} catches total")

        print(f"\n   Matches by tier:")
        for tier, count in stats['matches_by_tier'].items():
            print(f"      {tier}: {count} match(es)")

        print(f"\n   Match-by-match breakdown:")
        for j, perf in enumerate(player['performances'], 1):
            print(f"      Match {j} (ID {perf['match_id']}):")
            print(f"         Tier: {perf['tier']}")
            print(f"         Points: {perf['fantasy_points']}")

        print()

    # Show SQL that would be executed
    print("=" * 80)
    print("💾 DATABASE UPDATES (SQL Preview)")
    print("=" * 80)
    print()

    for player in result['matched_players']:
        print(f"-- Update player: {player['player_name']}")
        print(f"-- Database ID: {player['db_player_id']}")
        print()

        for perf in player['performances']:
            print(f"INSERT INTO player_performances (")
            print(f"  player_id, match_id, tier, fantasy_points,")
            print(f"  runs, wickets, catches, match_date")
            print(f") VALUES (")
            print(f"  '{player['db_player_id']}',")
            print(f"  {perf['match_id']},")
            print(f"  '{perf['tier']}',")
            print(f"  {perf['fantasy_points']},")
            print(f"  {perf['batting'].get('runs', 0)},")
            print(f"  {perf['bowling'].get('wickets', 0)},")
            print(f"  {perf['fielding'].get('catches', 0)},")
            print(f"  '{perf['match_date']}'")
            print(f");")
            print()

        print(f"-- Update season total")
        print(f"UPDATE players")
        print(f"SET ")
        print(f"  total_fantasy_points = total_fantasy_points + {player['total_fantasy_points']},")
        print(f"  total_matches = total_matches + {player['total_matches']},")
        print(f"  updated_at = NOW()")
        print(f"WHERE id = '{player['db_player_id']}';")
        print()
        print()

    print("=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print()
    print("KEY TAKEAWAYS:")
    print("  ✓ System correctly identified Jan de Vries playing in 3 different grades")
    print("  ✓ Name variation (Jan vs J.) was handled by player ID matching")
    print("  ✓ Fantasy points calculated with appropriate tier multipliers")
    print("  ✓ All performances aggregated into single player record")
    print("  ✓ Ready to update database with consolidated stats")
    print()
    print("NEXT STEPS:")
    print("  1. Test with real scraped data from matchcentre")
    print("  2. Integrate with database")
    print("  3. Run weekly automated scrape")
    print("  4. Update user team points based on player performances")
    print()


if __name__ == "__main__":
    demo()
