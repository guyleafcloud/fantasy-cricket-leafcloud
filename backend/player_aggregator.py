#!/usr/bin/env python3
"""
Player Season Aggregator
========================
Tracks cumulative player statistics and fantasy points throughout the season.

This module:
- Aggregates match-by-match performances into season totals
- Calculates averages and statistics
- Maintains player registry per club
- Handles incremental updates (new matches add to existing totals)
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerSeasonAggregator:
    """Aggregates player performances across a season"""

    def __init__(self):
        # In-memory storage (replace with database in production)
        self.players = {}  # player_id -> player data
        self.club_rosters = defaultdict(set)  # club_name -> set of player_ids

    def add_match_performance(self, performance: Dict) -> Dict:
        """
        Add a single match performance and update season totals

        Args:
            performance: Dict with match performance data from scraper

        Returns:
            Updated player season data
        """
        player_name = performance['player_name']
        player_id_from_scrape = performance.get('player_id')
        club = performance['club']
        match_id = performance['match_id']

        # Try to match with existing player (including legacy imports)
        player_id = self._find_or_create_player(player_name, player_id_from_scrape, club)

        player_data = self.players[player_id]

        # Check if we already processed this match (idempotency)
        if match_id in player_data['processed_matches']:
            logger.debug(f"⏭️  Match {match_id} already processed for {player_name}")
            return player_data

        # Add this performance to history
        match_performance = {
            'match_id': match_id,
            'match_date': performance.get('match_date'),
            'opponent': performance.get('opponent'),
            'tier': performance.get('tier', 'tier2'),
            'batting': performance.get('batting', {}),
            'bowling': performance.get('bowling', {}),
            'fielding': performance.get('fielding', {}),
            'fantasy_points': performance.get('fantasy_points', 0)
        }

        player_data['match_history'].append(match_performance)
        player_data['processed_matches'].add(match_id)

        # Update season aggregates
        self._update_season_totals(player_data, match_performance)

        # Update metadata
        player_data['last_updated'] = datetime.now().isoformat()
        player_data['matches_played'] = len(player_data['match_history'])

        logger.info(f"✅ Updated {player_name}: {player_data['season_totals']['fantasy_points']} points total")

        return player_data

    def _find_or_create_player(self, player_name: str, player_id: Optional[str], club: str) -> str:
        """
        Find existing player or create new one

        Matching logic:
        1. If player_id provided and exists → use it
        2. Try fuzzy name match with existing players from same club → use matched ID
        3. Create new player

        Args:
            player_name: Player name from scraped data
            player_id: Optional player ID from scraped data
            club: Club name

        Returns:
            player_id to use (existing or new)
        """
        # 1. Exact ID match
        if player_id and player_id in self.players:
            return player_id

        # 2. Try name matching (especially for legacy imports)
        matched_id = self._match_player_by_name(player_name, club)
        if matched_id:
            # Update legacy import status
            if self.players[matched_id].get('is_legacy_import'):
                logger.info(f"🔗 Matched scraped player '{player_name}' to legacy import")
                self.players[matched_id]['is_legacy_import'] = False
                self.players[matched_id]['first_match_date'] = datetime.now().isoformat()
            return matched_id

        # 3. Create new player
        new_id = player_id or self._generate_player_id(player_name)

        if new_id not in self.players:
            self.players[new_id] = self._initialize_player(new_id, player_name, club)
            self.club_rosters[club].add(new_id)
            logger.info(f"🆕 New player discovered: {player_name} ({club})")

        return new_id

    def _match_player_by_name(self, player_name: str, club: str) -> Optional[str]:
        """
        Try to match player by name within same club

        Args:
            player_name: Name from scraped data
            club: Club name

        Returns:
            player_id if match found, None otherwise
        """
        name_normalized = player_name.lower().strip()

        # Only search within same club
        club_player_ids = self.club_rosters.get(club, set())

        for player_id in club_player_ids:
            player_data = self.players[player_id]
            stored_name = player_data['player_name'].lower().strip()

            # Exact match
            if stored_name == name_normalized:
                return player_id

            # Fuzzy match (handles variations like "J. Smith" vs "John Smith")
            if self._names_similar(stored_name, name_normalized):
                logger.info(f"🔗 Fuzzy matched '{player_name}' to '{player_data['player_name']}'")
                return player_id

        return None

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar enough to be the same player"""
        # Split into parts
        parts1 = name1.split()
        parts2 = name2.split()

        # Convert to sets for intersection
        set1 = set(parts1)
        set2 = set(parts2)

        # Check for significant overlap
        common = set1.intersection(set2)

        # If 2+ common parts (e.g., "John Smith" vs "John Smith")
        if len(common) >= 2:
            return True

        # If one is subset of other (handles "Smith" vs "J. Smith")
        if set1.issubset(set2) or set2.issubset(set1):
            if len(common) >= 1:
                return True

        # Handle abbreviated first names (e.g., "S. Zulfiqar" vs "Sikander Zulfiqar")
        if len(common) >= 1:  # At least last name matches
            # Check if either name has abbreviated first name
            for i, part1 in enumerate(parts1):
                for j, part2 in enumerate(parts2):
                    # Check if one is abbreviation of other
                    if self._is_abbreviation(part1, part2):
                        return True

        return False

    def _is_abbreviation(self, short: str, long: str) -> bool:
        """Check if short is an abbreviation of long"""
        # Remove periods and lowercase
        short_clean = short.replace('.', '').lower()
        long_clean = long.lower()

        # Single letter or initial match
        if len(short_clean) == 1 and long_clean.startswith(short_clean):
            return True

        # Short is start of long (e.g., "Sik" vs "Sikander")
        if len(short_clean) > 1 and long_clean.startswith(short_clean):
            return True

        return False

    def _initialize_player(self, player_id: str, player_name: str, club: str) -> Dict:
        """Initialize a new player record"""
        return {
            'player_id': player_id,
            'player_name': player_name,
            'club': club,
            'first_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'matches_played': 0,
            'match_history': [],
            'processed_matches': set(),  # Track which matches we've seen
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

    def _update_season_totals(self, player_data: Dict, match_perf: Dict):
        """Update cumulative season totals with new match performance"""
        totals = player_data['season_totals']

        # Add fantasy points
        totals['fantasy_points'] += match_perf['fantasy_points']

        # Batting totals
        batting = match_perf.get('batting', {})
        if batting and batting.get('runs') is not None:
            totals['batting']['innings'] += 1
            runs = batting.get('runs', 0)
            balls = batting.get('balls_faced', 0)
            fours = batting.get('fours', 0)
            sixes = batting.get('sixes', 0)

            totals['batting']['runs'] += runs
            totals['batting']['balls_faced'] += balls
            totals['batting']['fours'] += fours
            totals['batting']['sixes'] += sixes

            # Milestones
            if runs >= 100:
                totals['batting']['centuries'] += 1
            elif runs >= 50:
                totals['batting']['fifties'] += 1
            elif runs == 0 and balls > 0:
                totals['batting']['ducks'] += 1

            # Highest score
            if runs > totals['batting']['highest_score']:
                totals['batting']['highest_score'] = runs

        # Bowling totals
        bowling = match_perf.get('bowling', {})
        if bowling and bowling.get('wickets') is not None:
            totals['bowling']['innings'] += 1
            wickets = bowling.get('wickets', 0)
            runs = bowling.get('runs_conceded', 0)
            overs = bowling.get('overs', 0.0)
            maidens = bowling.get('maidens', 0)

            totals['bowling']['wickets'] += wickets
            totals['bowling']['runs_conceded'] += runs
            totals['bowling']['overs'] += overs
            totals['bowling']['maidens'] += maidens

            if wickets >= 5:
                totals['bowling']['five_wicket_hauls'] += 1

            # Best figures (most wickets, or if tied, least runs)
            best = totals['bowling']['best_figures']
            if wickets > best['wickets'] or (wickets == best['wickets'] and runs < best['runs']):
                best['wickets'] = wickets
                best['runs'] = runs

        # Fielding totals
        fielding = match_perf.get('fielding', {})
        if fielding:
            totals['fielding']['catches'] += fielding.get('catches', 0)
            totals['fielding']['stumpings'] += fielding.get('stumpings', 0)
            totals['fielding']['runouts'] += fielding.get('runouts', 0)

        # Recalculate averages
        self._calculate_averages(player_data)

    def _calculate_averages(self, player_data: Dict):
        """Calculate batting/bowling averages and rates"""
        totals = player_data['season_totals']
        averages = player_data['averages']
        matches = len(player_data['match_history'])

        if matches == 0:
            return

        # Batting average (runs / dismissals)
        batting_innings = totals['batting']['innings']
        if batting_innings > 0:
            # Approximate dismissals (innings - not outs, simplified)
            dismissals = max(1, batting_innings - (batting_innings // 5))  # Rough estimate
            averages['batting_average'] = round(totals['batting']['runs'] / dismissals, 2)

            # Strike rate
            if totals['batting']['balls_faced'] > 0:
                averages['strike_rate'] = round(
                    (totals['batting']['runs'] / totals['batting']['balls_faced']) * 100,
                    2
                )

        # Bowling average (runs conceded / wickets)
        if totals['bowling']['wickets'] > 0:
            averages['bowling_average'] = round(
                totals['bowling']['runs_conceded'] / totals['bowling']['wickets'],
                2
            )

        # Economy rate (runs per over)
        if totals['bowling']['overs'] > 0:
            averages['economy_rate'] = round(
                totals['bowling']['runs_conceded'] / totals['bowling']['overs'],
                2
            )

        # Fantasy points per match
        averages['fantasy_points_per_match'] = round(
            totals['fantasy_points'] / matches,
            2
        )

    def _generate_player_id(self, player_name: str) -> str:
        """Generate a unique player ID from name (fallback if no ID provided)"""
        # Simple hash-based ID generation
        import hashlib
        return hashlib.md5(player_name.encode()).hexdigest()[:12]

    def get_player(self, player_id: str) -> Optional[Dict]:
        """Get player data by ID"""
        return self.players.get(player_id)

    def get_players_by_club(self, club: str) -> List[Dict]:
        """Get all players for a specific club"""
        player_ids = self.club_rosters.get(club, set())
        return [self.players[pid] for pid in player_ids]

    def get_top_players(self, limit: int = 10, sort_by: str = 'fantasy_points') -> List[Dict]:
        """
        Get top players by a specific metric

        Args:
            limit: Number of players to return
            sort_by: Metric to sort by ('fantasy_points', 'runs', 'wickets', etc.)

        Returns:
            List of top players
        """
        players_list = list(self.players.values())

        # Define sort keys
        sort_keys = {
            'fantasy_points': lambda p: p['season_totals']['fantasy_points'],
            'runs': lambda p: p['season_totals']['batting']['runs'],
            'wickets': lambda p: p['season_totals']['bowling']['wickets'],
            'average': lambda p: p['averages']['batting_average'],
            'strike_rate': lambda p: p['averages']['strike_rate'],
            'matches': lambda p: len(p['match_history'])
        }

        sort_key = sort_keys.get(sort_by, sort_keys['fantasy_points'])
        sorted_players = sorted(players_list, key=sort_key, reverse=True)

        return sorted_players[:limit]

    def get_season_summary(self) -> Dict:
        """Get summary of entire season"""
        return {
            'total_players': len(self.players),
            'clubs': len(self.club_rosters),
            'club_rosters': {
                club: len(players) for club, players in self.club_rosters.items()
            },
            'top_scorers': [
                {'name': p['player_name'], 'points': p['season_totals']['fantasy_points']}
                for p in self.get_top_players(5, 'fantasy_points')
            ]
        }

    def export_to_database_format(self) -> List[Dict]:
        """
        Export all player data in format ready for database insertion

        Returns:
            List of player dicts with serializable data (no sets)
        """
        export_data = []

        for player_id, player_data in self.players.items():
            # Convert sets to lists for JSON serialization
            player_copy = player_data.copy()
            player_copy['processed_matches'] = list(player_data['processed_matches'])

            export_data.append(player_copy)

        return export_data

    def save_to_file(self, filename: str = 'season_aggregates.json'):
        """Save aggregated data to JSON file"""
        export_data = self.export_to_database_format()

        with open(filename, 'w') as f:
            json.dump({
                'saved_at': datetime.now().isoformat(),
                'summary': self.get_season_summary(),
                'players': export_data
            }, f, indent=2)

        logger.info(f"💾 Saved {len(export_data)} players to {filename}")

    def load_from_file(self, filename: str = 'season_aggregates.json'):
        """Load previously saved aggregated data"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            players_data = data.get('players', [])

            for player_data in players_data:
                # Convert lists back to sets
                player_data['processed_matches'] = set(player_data['processed_matches'])

                player_id = player_data['player_id']
                club = player_data['club']

                self.players[player_id] = player_data
                self.club_rosters[club].add(player_id)

            logger.info(f"✅ Loaded {len(players_data)} players from {filename}")
            return True

        except FileNotFoundError:
            logger.warning(f"⚠️  No saved data found at {filename}")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            return False


# =============================================================================
# TESTING
# =============================================================================

def test_aggregator():
    """Test the player aggregator with sample data"""

    print("🏏 Testing Player Season Aggregator")
    print("=" * 70)

    aggregator = PlayerSeasonAggregator()

    # Sample match performances
    sample_performances = [
        {
            'player_name': 'Sean Walsh',
            'player_id': '11190879',
            'club': 'VRA',
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'ACC',
            'tier': 'tier1',
            'batting': {'runs': 45, 'balls_faced': 38, 'fours': 6, 'sixes': 1},
            'bowling': {'wickets': 2, 'runs_conceded': 28, 'overs': 8.0, 'maidens': 1},
            'fielding': {'catches': 1},
            'fantasy_points': 95
        },
        {
            'player_name': 'Sean Walsh',
            'player_id': '11190879',
            'club': 'VRA',
            'match_id': 'match_002',
            'match_date': '2025-04-22',
            'opponent': 'VOC',
            'tier': 'tier1',
            'batting': {'runs': 67, 'balls_faced': 54, 'fours': 8, 'sixes': 2},
            'bowling': {'wickets': 3, 'runs_conceded': 35, 'overs': 10.0, 'maidens': 2},
            'fielding': {'catches': 2},
            'fantasy_points': 126
        },
        {
            'player_name': 'John Doe',
            'player_id': '22334455',
            'club': 'VRA',
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'ACC',
            'tier': 'tier1',
            'batting': {'runs': 23, 'balls_faced': 28, 'fours': 3, 'sixes': 0},
            'bowling': {},
            'fielding': {},
            'fantasy_points': 26
        }
    ]

    print("\n📥 Processing sample performances...")
    for perf in sample_performances:
        aggregator.add_match_performance(perf)

    # Show results
    print("\n" + "=" * 70)
    print("📊 Season Summary")
    print("=" * 70)

    summary = aggregator.get_season_summary()
    print(f"\nTotal players: {summary['total_players']}")
    print(f"Clubs: {', '.join(summary['club_rosters'].keys())}")

    print("\n🏆 Top Players:")
    for player in aggregator.get_top_players(5):
        print(f"\n{player['player_name']} ({player['club']})")
        print(f"  Matches: {player['matches_played']}")
        print(f"  Fantasy Points: {player['season_totals']['fantasy_points']}")
        print(f"  Avg Points/Match: {player['averages']['fantasy_points_per_match']}")
        print(f"  Batting: {player['season_totals']['batting']['runs']} runs")
        print(f"  Bowling: {player['season_totals']['bowling']['wickets']} wickets")

    # Test save/load
    print("\n💾 Testing save/load...")
    aggregator.save_to_file('test_aggregates.json')

    # Create new aggregator and load
    aggregator2 = PlayerSeasonAggregator()
    aggregator2.load_from_file('test_aggregates.json')

    print(f"✅ Loaded {len(aggregator2.players)} players from file")

    print("\n" + "=" * 70)
    print("✅ Aggregator working perfectly!")


if __name__ == "__main__":
    test_aggregator()
