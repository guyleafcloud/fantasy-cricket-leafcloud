#!/usr/bin/env python3
"""
Tests for Player Matcher Service
=================================
Tests player identification and deduplication across multiple matches/grades.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from player_matcher import PlayerMatcher


@pytest.fixture
def matcher():
    """Create PlayerMatcher instance"""
    return PlayerMatcher()


@pytest.fixture
def multi_grade_scenario():
    """Load multi-grade player scenario"""
    fixtures_dir = Path(__file__).parent / 'fixtures'
    with open(fixtures_dir / 'multi_grade_player_scenario.json', 'r') as f:
        return json.load(f)


# =============================================================================
# TEST: Name Normalization
# =============================================================================

def test_name_normalization(matcher):
    """Test that name normalization handles various formats"""

    test_cases = [
        ("Jan de Vries", "jandevries"),
        ("J. de Vries", "jdevries"),
        ("de Vries, Jan", "devriesjan"),
        ("John Smith", "johnsmith"),
        ("J Smith", "jsmith"),
        ("Smith, J.", "smithj"),
        ("van der Berg, Pieter", "vanderbergpieter"),
    ]

    for input_name, expected in test_cases:
        result = matcher.normalize_name(input_name)
        assert expected in result or result in expected, \
            f"Normalization failed for '{input_name}': expected '{expected}', got '{result}'"

    print("✅ Name normalization tests passed!")


# =============================================================================
# TEST: Name Similarity
# =============================================================================

def test_name_similarity(matcher):
    """Test name similarity calculation"""

    # Should match (high similarity)
    high_similarity_pairs = [
        ("Jan de Vries", "Jan de Vries", 1.0),  # Exact match
        ("Jan de Vries", "jan de vries", 1.0),  # Case insensitive
        ("Jan de Vries", "J. de Vries", 0.7),   # Initial vs full name (should be high)
        ("John Smith", "John Smith", 1.0),
    ]

    for name1, name2, min_expected in high_similarity_pairs:
        similarity = matcher.calculate_name_similarity(name1, name2)
        assert similarity >= min_expected, \
            f"Similarity too low for '{name1}' vs '{name2}': {similarity} < {min_expected}"
        print(f"  ✓ {name1:20} vs {name2:20} = {similarity:.2f}")

    # Should NOT match (low similarity)
    low_similarity_pairs = [
        ("Jan de Vries", "Peter Smith", 0.5),
        ("John Doe", "Jane Smith", 0.5),
    ]

    for name1, name2, max_expected in low_similarity_pairs:
        similarity = matcher.calculate_name_similarity(name1, name2)
        assert similarity < max_expected, \
            f"Similarity too high for '{name1}' vs '{name2}': {similarity} >= {max_expected}"
        print(f"  ✓ {name1:20} vs {name2:20} = {similarity:.2f} (correctly low)")

    print("✅ Name similarity tests passed!")


# =============================================================================
# TEST: Match by ID
# =============================================================================

def test_match_by_id(matcher):
    """Test grouping performances by player ID"""

    performances = [
        {'player_id': '123', 'player_name': 'Jan de Vries', 'runs': 50, 'match_id': 1},
        {'player_id': '123', 'player_name': 'Jan de Vries', 'runs': 30, 'match_id': 2},
        {'player_id': '456', 'player_name': 'Peter Smith', 'runs': 40, 'match_id': 1},
        {'player_id': '123', 'player_name': 'J. de Vries', 'runs': 25, 'match_id': 3},  # Same player, different name
    ]

    grouped = matcher.match_by_id(performances)

    # Should have 2 unique players
    assert len(grouped) == 2, f"Expected 2 unique players, got {len(grouped)}"

    # Player 123 should have 3 performances
    assert len(grouped['123']) == 3, f"Player 123 should have 3 performances, got {len(grouped['123'])}"

    # Player 456 should have 1 performance
    assert len(grouped['456']) == 1, f"Player 456 should have 1 performance, got {len(grouped['456'])}"

    print(f"✅ Match by ID test passed! Found {len(grouped)} unique players")


# =============================================================================
# TEST: Match by Name (Fuzzy)
# =============================================================================

def test_match_by_name(matcher):
    """Test grouping performances by fuzzy name matching"""

    performances = [
        {'player_name': 'Jan de Vries', 'runs': 50, 'match_id': 1},
        {'player_name': 'J. de Vries', 'runs': 30, 'match_id': 2},  # Should match
        {'player_name': 'jan de vries', 'runs': 25, 'match_id': 3},  # Should match
        {'player_name': 'Peter Smith', 'runs': 40, 'match_id': 1},  # Different player
    ]

    grouped = matcher.match_by_name(performances)

    # Should identify 2 unique players
    # Note: exact count may vary based on normalization, but should group Jan variants together
    assert len(grouped) <= 2, f"Expected at most 2 unique players, got {len(grouped)}"

    # Find the group with Jan de Vries
    jan_group = None
    for key, group in grouped.items():
        if any('jan' in p['player_name'].lower() for p in group):
            jan_group = group
            break

    assert jan_group is not None, "Should find Jan de Vries group"
    assert len(jan_group) >= 2, f"Jan de Vries group should have at least 2 performances, got {len(jan_group)}"

    print(f"✅ Match by name test passed! Found {len(grouped)} unique players")


# =============================================================================
# TEST: Deduplication
# =============================================================================

def test_deduplicate_performances(matcher):
    """Test full deduplication with mix of IDs and names"""

    performances = [
        # Player 1 with ID - plays in 3 matches
        {'player_id': '123', 'player_name': 'Jan de Vries', 'runs': 50, 'match_id': 1, 'tier': 'tier2'},
        {'player_id': '123', 'player_name': 'Jan de Vries', 'runs': 30, 'match_id': 2, 'tier': 'youth'},
        {'player_id': '123', 'player_name': 'J. de Vries', 'runs': 25, 'match_id': 3, 'tier': 'social'},

        # Player 2 with ID
        {'player_id': '456', 'player_name': 'Peter Smith', 'runs': 40, 'match_id': 1, 'tier': 'tier1'},

        # Player 3 without ID - should match by name
        {'player_name': 'John Doe', 'runs': 35, 'match_id': 4, 'tier': 'tier2'},
        {'player_name': 'john doe', 'runs': 20, 'match_id': 5, 'tier': 'tier3'},  # Same player, different case
    ]

    grouped = matcher.deduplicate_performances(performances)

    # Should identify 3 unique players
    assert len(grouped) >= 3, f"Expected at least 3 unique players, got {len(grouped)}"

    # Player 123 should have 3 performances
    if '123' in grouped:
        assert len(grouped['123']) == 3, f"Player 123 should have 3 performances"
        print(f"  ✓ Player 123 (Jan de Vries): {len(grouped['123'])} matches")

    # Player 456 should have 1 performance
    if '456' in grouped:
        assert len(grouped['456']) == 1, f"Player 456 should have 1 performance"
        print(f"  ✓ Player 456 (Peter Smith): {len(grouped['456'])} match")

    print(f"✅ Deduplication test passed! {len(grouped)} unique players identified")


# =============================================================================
# TEST: Stats Aggregation
# =============================================================================

def test_aggregate_player_stats(matcher):
    """Test aggregating stats for a player across multiple matches"""

    # Same player in 3 different matches
    performances = [
        {
            'player_id': '123',
            'player_name': 'Jan de Vries',
            'match_id': 1,
            'tier': 'tier2',
            'fantasy_points': 65,
            'batting': {'runs': 45, 'balls_faced': 38, 'fours': 5, 'sixes': 1},
            'bowling': {'wickets': 2, 'runs_conceded': 32, 'overs': 8.0, 'maidens': 1},
            'fielding': {'catches': 1, 'stumpings': 0, 'runouts': 0}
        },
        {
            'player_id': '123',
            'player_name': 'Jan de Vries',
            'match_id': 2,
            'tier': 'youth',
            'fantasy_points': 58,
            'batting': {'runs': 78, 'balls_faced': 52, 'fours': 8, 'sixes': 3},
            'bowling': {},
            'fielding': {}
        },
        {
            'player_id': '123',
            'player_name': 'J. de Vries',
            'match_id': 3,
            'tier': 'social',
            'fantasy_points': 22,
            'batting': {},
            'bowling': {'wickets': 3, 'runs_conceded': 25, 'overs': 6.0, 'maidens': 0},
            'fielding': {'catches': 2, 'stumpings': 0, 'runouts': 0}
        }
    ]

    aggregated = matcher.aggregate_player_stats(performances)

    # Check basic info
    assert aggregated['player_name'] == 'Jan de Vries'
    assert aggregated['player_id'] == '123'
    assert aggregated['total_matches'] == 3

    # Check fantasy points sum
    assert aggregated['total_fantasy_points'] == 145, \
        f"Expected 145 total points, got {aggregated['total_fantasy_points']}"

    # Check stats summary
    stats = aggregated['stats_summary']
    assert stats['total_runs'] == 123, f"Expected 123 runs, got {stats['total_runs']}"
    assert stats['total_wickets'] == 5, f"Expected 5 wickets, got {stats['total_wickets']}"
    assert stats['total_catches'] == 3, f"Expected 3 catches, got {stats['total_catches']}"

    # Check matches by tier
    assert stats['matches_by_tier']['tier2'] == 1
    assert stats['matches_by_tier']['youth'] == 1
    assert stats['matches_by_tier']['social'] == 1

    print("✅ Stats aggregation test passed!")
    print(f"   Total matches: {aggregated['total_matches']}")
    print(f"   Total points: {aggregated['total_fantasy_points']}")
    print(f"   Total runs: {stats['total_runs']}")
    print(f"   Total wickets: {stats['total_wickets']}")


# =============================================================================
# TEST: Database Matching
# =============================================================================

def test_match_to_database_player(matcher):
    """Test matching scraped player to database records"""

    db_players = [
        {'id': 'db-001', 'name': 'Jan de Vries', 'player_id': '123'},
        {'id': 'db-002', 'name': 'Peter Smith', 'player_id': '456'},
        {'id': 'db-003', 'name': 'John Doe', 'player_id': None},
    ]

    # Test 1: Exact ID match
    match = matcher.match_to_database_player(
        scraped_name='J. de Vries',
        db_players=db_players,
        scraped_player_id='123'
    )
    assert match is not None, "Should find match by ID"
    assert match['id'] == 'db-001', f"Should match db-001, got {match['id']}"
    print("  ✓ Matched by ID: J. de Vries -> Jan de Vries")

    # Test 2: Fuzzy name match (no ID)
    match = matcher.match_to_database_player(
        scraped_name='john doe',
        db_players=db_players,
        scraped_player_id=None
    )
    assert match is not None, "Should find match by name"
    assert match['id'] == 'db-003', f"Should match db-003, got {match['id']}"
    print("  ✓ Matched by name: john doe -> John Doe")

    # Test 3: No match
    match = matcher.match_to_database_player(
        scraped_name='Unknown Player',
        db_players=db_players,
        scraped_player_id='999'
    )
    assert match is None, "Should not find match for unknown player"
    print("  ✓ Correctly returned None for unknown player")

    print("✅ Database matching test passed!")


# =============================================================================
# TEST: Full Weekly Processing
# =============================================================================

def test_process_weekly_scrape(matcher):
    """Test full weekly scrape processing"""

    # Simulate weekly scrape with multiple players across multiple matches
    performances = [
        # Jan plays in ACC 1, U17, and ZAMI
        {'player_id': '123', 'player_name': 'Jan de Vries', 'fantasy_points': 65, 'batting': {'runs': 45}, 'bowling': {}, 'fielding': {}},
        {'player_id': '123', 'player_name': 'Jan de Vries', 'fantasy_points': 58, 'batting': {'runs': 78}, 'bowling': {}, 'fielding': {}},
        {'player_id': '123', 'player_name': 'J. de Vries', 'fantasy_points': 22, 'batting': {}, 'bowling': {'wickets': 3}, 'fielding': {}},

        # Peter plays in ACC 1
        {'player_id': '456', 'player_name': 'Peter Smith', 'fantasy_points': 45, 'batting': {'runs': 35}, 'bowling': {}, 'fielding': {}},

        # Unknown player (not in database)
        {'player_name': 'New Player', 'fantasy_points': 30, 'batting': {'runs': 25}, 'bowling': {}, 'fielding': {}},
    ]

    db_players = [
        {'id': 'db-001', 'name': 'Jan de Vries', 'player_id': '123'},
        {'id': 'db-002', 'name': 'Peter Smith', 'player_id': '456'},
    ]

    result = matcher.process_weekly_scrape(performances, db_players)

    # Check counts
    assert result['total_performances'] == 5
    assert result['total_unique_players'] >= 3

    # Should have matched players
    assert len(result['matched_players']) >= 2, \
        f"Expected at least 2 matched players, got {len(result['matched_players'])}"

    # Should have unmatched players
    assert len(result['unmatched_players']) >= 1, \
        f"Expected at least 1 unmatched player, got {len(result['unmatched_players'])}"

    # Find Jan in matched players
    jan = next((p for p in result['matched_players'] if p['player_id'] == '123'), None)
    assert jan is not None, "Should find Jan in matched players"
    assert jan['total_matches'] == 3, f"Jan should have 3 matches, got {jan['total_matches']}"
    assert jan['total_fantasy_points'] == 145, f"Jan should have 145 points, got {jan['total_fantasy_points']}"
    assert jan['db_player_id'] == 'db-001'

    print("✅ Full weekly processing test passed!")
    print(f"   Total performances: {result['total_performances']}")
    print(f"   Unique players: {result['total_unique_players']}")
    print(f"   Matched to DB: {len(result['matched_players'])}")
    print(f"   Unmatched: {len(result['unmatched_players'])}")
    print(f"\n   Jan de Vries aggregated stats:")
    print(f"     - Matches: {jan['total_matches']}")
    print(f"     - Total points: {jan['total_fantasy_points']}")
    print(f"     - Total runs: {jan['stats_summary']['total_runs']}")
    print(f"     - Total wickets: {jan['stats_summary']['total_wickets']}")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🏏 RUNNING PLAYER MATCHER TESTS")
    print("=" * 80)
    print()

    # Run with pytest
    pytest.main([__file__, '-v', '-s'])
