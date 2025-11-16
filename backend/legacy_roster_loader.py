#!/usr/bin/env python3
"""
Legacy Roster Loader
====================
Load players from previous seasons to seed the aggregator.

This allows you to:
- Start with known players from last season
- Match returning players by name/ID when they appear in new matches
- Add new players as they debut
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegacyRosterLoader:
    """Load and manage legacy roster data from previous seasons"""

    def __init__(self):
        pass

    def load_from_json(self, filename: str) -> List[Dict]:
        """
        Load legacy roster from JSON file

        Args:
            filename: Path to legacy roster JSON file

        Returns:
            List of legacy player dicts
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            players = data.get('players', [])
            logger.info(f"✅ Loaded {len(players)} legacy players from {filename}")

            return players

        except FileNotFoundError:
            logger.warning(f"⚠️  Legacy roster file not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading legacy roster: {e}")
            return []

    def import_to_aggregator(self, aggregator, legacy_players: List[Dict]):
        """
        Import legacy players into the aggregator

        Args:
            aggregator: PlayerSeasonAggregator instance
            legacy_players: List of legacy player dicts

        This creates "shell" player profiles with:
        - Basic info (name, club)
        - Zero season stats (will accumulate as they play)
        - Marked as legacy import
        """
        imported_count = 0
        skipped_count = 0

        for legacy in legacy_players:
            player_name = legacy.get('name')
            player_id = legacy.get('id') or self._generate_id_from_name(player_name)
            club = legacy.get('club')

            if not player_name or not club:
                logger.warning(f"⚠️  Skipping invalid legacy player: {legacy}")
                skipped_count += 1
                continue

            # Check if player already exists (from scraping or previous import)
            if player_id in aggregator.players:
                logger.debug(f"⏭️  Player already exists: {player_name}")
                skipped_count += 1
                continue

            # Create shell player profile
            player_profile = self._create_legacy_profile(
                player_id=player_id,
                player_name=player_name,
                club=club,
                role=legacy.get('role'),
                last_season_stats=legacy.get('last_season_stats', {})
            )

            # Add to aggregator
            aggregator.players[player_id] = player_profile
            aggregator.club_rosters[club].add(player_id)

            imported_count += 1
            logger.info(f"📥 Imported legacy player: {player_name} ({club})")

        logger.info(f"\n✅ Legacy import complete!")
        logger.info(f"   Imported: {imported_count}")
        logger.info(f"   Skipped: {skipped_count}")

        return imported_count

    def _create_legacy_profile(
        self,
        player_id: str,
        player_name: str,
        club: str,
        role: Optional[str] = None,
        last_season_stats: Dict = None
    ) -> Dict:
        """Create a player profile for legacy import"""

        profile = {
            'player_id': player_id,
            'player_name': player_name,
            'club': club,
            'role': role,  # e.g., "batsman", "bowler", "all-rounder"
            'is_legacy_import': True,
            'legacy_imported_at': datetime.now().isoformat(),
            'first_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'matches_played': 0,
            'match_history': [],
            'processed_matches': set(),
            'season_totals': {
                'fantasy_points': 0,
                'batting': {
                    'innings': 0,
                    'runs': 0,
                    'balls_faced': 0,
                    'fours': 0,
                    'sixes': 0,
                    'fifties': 0,
                    'centuries': 0,
                    'ducks': 0,
                    'highest_score': 0
                },
                'bowling': {
                    'innings': 0,
                    'wickets': 0,
                    'runs_conceded': 0,
                    'overs': 0.0,
                    'maidens': 0,
                    'five_wicket_hauls': 0,
                    'best_figures': {'wickets': 0, 'runs': 999}
                },
                'fielding': {
                    'catches': 0,
                    'stumpings': 0,
                    'runouts': 0
                }
            },
            'averages': {
                'batting_average': 0.0,
                'strike_rate': 0.0,
                'bowling_average': 0.0,
                'economy_rate': 0.0,
                'fantasy_points_per_match': 0.0
            }
        }

        # Optional: Store last season stats for reference
        if last_season_stats:
            profile['last_season_stats'] = last_season_stats

        return profile

    def _generate_id_from_name(self, player_name: str) -> str:
        """Generate player ID from name if ID not provided"""
        import hashlib
        return f"legacy_{hashlib.md5(player_name.encode()).hexdigest()[:12]}"

    def match_player_by_name(self, aggregator, player_name: str) -> Optional[str]:
        """
        Find player ID by name (fuzzy matching)

        Useful for matching scraped players to legacy roster when ID is unknown

        Args:
            aggregator: PlayerSeasonAggregator instance
            player_name: Player name from scraped data

        Returns:
            player_id if match found, None otherwise
        """
        # Normalize name for comparison
        name_normalized = player_name.lower().strip()

        for player_id, player_data in aggregator.players.items():
            stored_name = player_data['player_name'].lower().strip()

            # Exact match
            if stored_name == name_normalized:
                return player_id

            # Fuzzy match: check if names are very similar
            # (handles minor variations like "J. Smith" vs "John Smith")
            if self._names_similar(stored_name, name_normalized):
                logger.info(f"🔗 Matched '{player_name}' to legacy player '{player_data['player_name']}'")
                return player_id

        return None

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar enough to be the same player"""
        # Split into parts
        parts1 = set(name1.split())
        parts2 = set(name2.split())

        # Check for significant overlap
        common = parts1.intersection(parts2)

        # If last name matches and at least one initial/first name
        if len(common) >= 2:
            return True

        return False

    def create_legacy_roster_template(self, club_name: str, filename: str):
        """
        Create a template JSON file for legacy roster

        Args:
            club_name: Name of the club
            filename: Output filename
        """
        template = {
            "club": club_name,
            "season": "2024",
            "notes": "Legacy roster from previous season",
            "players": [
                {
                    "name": "Player Name",
                    "id": "optional_player_id",
                    "club": club_name,
                    "role": "all-rounder",
                    "last_season_stats": {
                        "matches": 12,
                        "fantasy_points": 856,
                        "runs": 423,
                        "wickets": 15
                    }
                }
            ]
        }

        with open(filename, 'w') as f:
            json.dump(template, f, indent=2)

        logger.info(f"📝 Created legacy roster template: {filename}")


# =============================================================================
# TESTING
# =============================================================================

def test_legacy_loader():
    """Test legacy roster loading"""
    from player_aggregator import PlayerSeasonAggregator

    print("🏏 Testing Legacy Roster Loader")
    print("=" * 70)

    # Create aggregator
    aggregator = PlayerSeasonAggregator()

    # Create loader
    loader = LegacyRosterLoader()

    # Create sample legacy roster
    sample_roster = {
        "club": "ACC",
        "season": "2024",
        "players": [
            {
                "name": "Boris Gorlee",
                "club": "ACC",
                "role": "all-rounder"
            },
            {
                "name": "Sikander Zulfiqar",
                "club": "ACC",
                "role": "batsman"
            },
            {
                "name": "Shariz Ahmad",
                "club": "ACC",
                "role": "bowler"
            }
        ]
    }

    # Save to file
    with open('acc_legacy_roster.json', 'w') as f:
        json.dump(sample_roster, f, indent=2)

    print("\n📥 Loading legacy roster...")
    legacy_players = loader.load_from_json('acc_legacy_roster.json')

    print(f"\n✅ Found {len(legacy_players)} legacy players")

    print("\n📥 Importing to aggregator...")
    count = loader.import_to_aggregator(aggregator, legacy_players)

    print(f"\n✅ Imported {count} players")

    print("\n📊 Aggregator state:")
    summary = aggregator.get_season_summary()
    print(f"   Total players: {summary['total_players']}")
    print(f"   Clubs: {list(summary['club_rosters'].keys())}")

    print("\n👥 ACC Roster:")
    acc_players = aggregator.get_players_by_club('ACC')
    for player in acc_players:
        legacy_marker = " (Legacy)" if player.get('is_legacy_import') else ""
        print(f"   - {player['player_name']}{legacy_marker}")

    print("\n" + "=" * 70)
    print("✅ Legacy loader working!")


if __name__ == "__main__":
    test_legacy_loader()
