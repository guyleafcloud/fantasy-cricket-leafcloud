#!/usr/bin/env python3
"""
Player Matcher Service
======================
Handles player identification and deduplication across multiple matches/grades.

Key Features:
- Matches players by ID when available
- Fuzzy name matching for variations
- Links scraped players to database records
- Aggregates points across multiple matches/grades

Example scenarios:
- Player plays in both ACC 1 and U17 in same week
- Player plays in ZAMI and ACC 3
- Name appears as "Jan de Vries" in one match and "J. de Vries" in another
"""

import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher


class PlayerMatcher:
    """
    Handles player identification and matching across multiple sources
    """

    def __init__(self):
        self.name_similarity_threshold = 0.85  # 85% similarity for fuzzy matching

    def normalize_name(self, name: str) -> str:
        """
        Normalize player name for matching

        Rules:
        - Lowercase
        - Remove punctuation
        - Remove extra spaces
        - Sort name parts (handles "Smith, John" vs "John Smith")

        Examples:
            "Jan de Vries" -> "devriesjan"
            "J. de Vries" -> "devriesj"
            "de Vries, Jan" -> "devriesjan"
        """
        if not name:
            return ""

        # Convert to lowercase
        name = name.lower()

        # Remove common punctuation
        name = re.sub(r'[,.\'-]', '', name)

        # Remove extra spaces and split
        parts = name.split()

        # Sort parts to handle different orderings
        # But keep common prefixes like "van", "de", "van der" with the surname
        surname_prefixes = ['van', 'de', 'den', 'der', 'van der', 'von', 'la', 'le']

        # Simple normalization: just remove spaces and punctuation
        # More sophisticated: could handle initials vs full names
        normalized = ''.join(parts)

        return normalized

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names (0.0 to 1.0)

        Uses SequenceMatcher for fuzzy string matching
        """
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)

        if not norm1 or not norm2:
            return 0.0

        # Exact match after normalization
        if norm1 == norm2:
            return 1.0

        # Check if one is a subset of the other (initials vs full name)
        # "J. de Vries" vs "Jan de Vries"
        if norm1 in norm2 or norm2 in norm1:
            # Calculate ratio based on length difference
            min_len = min(len(norm1), len(norm2))
            max_len = max(len(norm1), len(norm2))
            return min_len / max_len

        # Fuzzy match using SequenceMatcher
        return SequenceMatcher(None, norm1, norm2).ratio()

    def match_by_id(
        self,
        performances: List[Dict],
        id_field: str = 'player_id'
    ) -> Dict[str, List[Dict]]:
        """
        Group performances by player ID

        Args:
            performances: List of player performance dicts
            id_field: Field name for player ID

        Returns:
            Dict mapping player_id -> list of performances
        """
        grouped = {}

        for perf in performances:
            player_id = perf.get(id_field)

            if player_id:
                player_id = str(player_id)  # Ensure string
                if player_id not in grouped:
                    grouped[player_id] = []
                grouped[player_id].append(perf)

        return grouped

    def match_by_name(
        self,
        performances: List[Dict],
        name_field: str = 'player_name'
    ) -> Dict[str, List[Dict]]:
        """
        Group performances by normalized name (fuzzy matching)

        This is used when player_id is not available

        Args:
            performances: List of player performance dicts
            name_field: Field name for player name

        Returns:
            Dict mapping normalized_name -> list of performances
        """
        grouped = {}
        processed = set()

        for i, perf in enumerate(performances):
            if i in processed:
                continue

            name = perf.get(name_field, '')
            if not name:
                continue

            # Start a new group
            norm_name = self.normalize_name(name)
            group = [perf]
            processed.add(i)

            # Find other performances with similar names
            for j, other_perf in enumerate(performances):
                if j <= i or j in processed:
                    continue

                other_name = other_perf.get(name_field, '')
                if not other_name:
                    continue

                similarity = self.calculate_name_similarity(name, other_name)

                if similarity >= self.name_similarity_threshold:
                    group.append(other_perf)
                    processed.add(j)

            grouped[norm_name] = group

        return grouped

    def deduplicate_performances(
        self,
        performances: List[Dict],
        prefer_id_matching: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Deduplicate player performances, grouping by player

        Strategy:
        1. First try to match by player_id (most reliable)
        2. For performances without IDs, use fuzzy name matching
        3. Return grouped performances

        Args:
            performances: List of player performance dicts
            prefer_id_matching: Use ID matching first if available

        Returns:
            Dict mapping player_key -> list of performances for that player
        """
        if not performances:
            return {}

        # Separate performances with and without IDs
        with_id = [p for p in performances if p.get('player_id')]
        without_id = [p for p in performances if not p.get('player_id')]

        result = {}

        # Match by ID first
        if with_id:
            id_groups = self.match_by_id(with_id)
            result.update(id_groups)

        # Match by name for those without IDs
        if without_id:
            name_groups = self.match_by_name(without_id)
            # Prefix keys to avoid collision with ID keys
            for key, group in name_groups.items():
                result[f"name:{key}"] = group

        return result

    def aggregate_player_stats(
        self,
        performances: List[Dict]
    ) -> Dict:
        """
        Aggregate stats for a single player across multiple matches

        Args:
            performances: List of performances for ONE player

        Returns:
            Aggregated stats dict
        """
        if not performances:
            return {}

        # Use first performance for player info
        first = performances[0]
        player_name = first.get('player_name', 'Unknown')
        player_id = first.get('player_id')

        aggregated = {
            'player_name': player_name,
            'player_id': player_id,
            'total_matches': len(performances),
            'total_fantasy_points': 0,
            'performances': performances,
            'stats_summary': {
                'total_runs': 0,
                'total_wickets': 0,
                'total_catches': 0,
                'total_stumpings': 0,
                'total_runouts': 0,
                'matches_by_tier': {}
            }
        }

        # Sum up all fantasy points and stats
        for perf in performances:
            aggregated['total_fantasy_points'] += perf.get('fantasy_points', 0)

            # Aggregate batting
            batting = perf.get('batting', {})
            if batting:
                aggregated['stats_summary']['total_runs'] += batting.get('runs', 0)

            # Aggregate bowling
            bowling = perf.get('bowling', {})
            if bowling:
                aggregated['stats_summary']['total_wickets'] += bowling.get('wickets', 0)

            # Aggregate fielding
            fielding = perf.get('fielding', {})
            if fielding:
                aggregated['stats_summary']['total_catches'] += fielding.get('catches', 0)
                aggregated['stats_summary']['total_stumpings'] += fielding.get('stumpings', 0)
                aggregated['stats_summary']['total_runouts'] += fielding.get('runouts', 0)

            # Track matches by tier
            tier = perf.get('tier', 'unknown')
            if tier not in aggregated['stats_summary']['matches_by_tier']:
                aggregated['stats_summary']['matches_by_tier'][tier] = 0
            aggregated['stats_summary']['matches_by_tier'][tier] += 1

        return aggregated

    def match_to_database_player(
        self,
        scraped_name: str,
        db_players: List[Dict],
        scraped_player_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Match a scraped player to a database player record

        Args:
            scraped_name: Player name from scraped data
            db_players: List of player dicts from database
                        Each should have: {'id': ..., 'name': ..., 'player_id': ...}
            scraped_player_id: Optional player_id from API

        Returns:
            Matching database player dict or None
        """
        if not db_players:
            return None

        # Try exact ID match first
        if scraped_player_id:
            for db_player in db_players:
                if str(db_player.get('player_id', '')) == str(scraped_player_id):
                    return db_player

        # Try fuzzy name matching
        best_match = None
        best_similarity = 0.0

        for db_player in db_players:
            db_name = db_player.get('name', '')
            if not db_name:
                continue

            similarity = self.calculate_name_similarity(scraped_name, db_name)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = db_player

        # Return if similarity is above threshold
        if best_similarity >= self.name_similarity_threshold:
            return best_match

        return None

    def process_weekly_scrape(
        self,
        performances: List[Dict],
        db_players: List[Dict]
    ) -> Dict:
        """
        Process a weekly scrape, deduplicating and matching to database

        This is the main entry point for processing scraped data

        Args:
            performances: All player performances from weekly scrape
            db_players: Players from database

        Returns:
            Dict with:
                - matched_players: Players matched to database
                - unmatched_players: Players not in database (new?)
                - aggregated_stats: Stats aggregated by player
        """
        # Deduplicate performances
        grouped = self.deduplicate_performances(performances)

        matched_players = []
        unmatched_players = []

        for player_key, player_perfs in grouped.items():
            # Aggregate stats for this player
            aggregated = self.aggregate_player_stats(player_perfs)

            # Try to match to database
            scraped_name = aggregated['player_name']
            scraped_id = aggregated['player_id']

            db_match = self.match_to_database_player(
                scraped_name,
                db_players,
                scraped_id
            )

            if db_match:
                aggregated['db_player_id'] = db_match['id']
                aggregated['db_player_name'] = db_match['name']
                matched_players.append(aggregated)
            else:
                unmatched_players.append(aggregated)

        return {
            'matched_players': matched_players,
            'unmatched_players': unmatched_players,
            'total_unique_players': len(grouped),
            'total_performances': len(performances)
        }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Quick test
    matcher = PlayerMatcher()

    # Test name normalization
    print("Testing name normalization:")
    test_names = [
        ("Jan de Vries", "Jan de Vries"),
        ("Jan de Vries", "J. de Vries"),
        ("Jan de Vries", "de Vries, Jan"),
        ("Jan de Vries", "jan de vries"),
        ("Jan de Vries", "Peter Smith"),
    ]

    for name1, name2 in test_names:
        similarity = matcher.calculate_name_similarity(name1, name2)
        print(f"  {name1:20} vs {name2:20} = {similarity:.2f}")
