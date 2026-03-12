#!/usr/bin/env python3
"""
Scorecard Player Matcher
========================
Matches scraped player names from KNCB scorecards to database players.

Specifically designed for:
- Scorecard format: "M BOENDERMAKER", "DV DOORNINCK", "I ALIM"
- Database format: "MickBoendermaker", "DaanDoorninck", "IshaqAlim"

Matching Strategy:
1. Exact match (normalized)
2. Surname match (most reliable for scorecards)
3. Initials + surname match
4. Fuzzy match (>80% confidence)
5. Manual mapping table
"""

import logging
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Manual mappings for problem cases
# Add mappings here as discovered: "scraped_name" -> player_id
MANUAL_MAPPINGS = {
    # Will be populated during testing
    # Example: "m boendermaker": "some-uuid-here"
}


class ScorecardPlayerMatcher:
    """Match scorecard player names to database players"""

    def __init__(self, session: Session):
        self.session = session
        self._players_cache = None
        self._load_all_players()

    def _load_all_players(self):
        """Load all players from database into memory"""
        query = text("""
            SELECT p.id, p.name, p.player_type, p.multiplier, p.is_wicket_keeper,
                   t.name as team_name, c.name as club_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            LEFT JOIN clubs c ON p.club_id = c.id
        """)

        result = self.session.execute(query)
        self._players_cache = [
            {
                'id': row[0],
                'name': row[1],
                'player_type': row[2],
                'multiplier': row[3],
                'is_wicket_keeper': row[4],
                'team_name': row[5],
                'club_name': row[6]
            }
            for row in result
        ]

        logger.info(f"Loaded {len(self._players_cache)} players into cache")

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison: lowercase, no spaces/punctuation"""
        # Remove captain (*) and wicketkeeper (†) symbols, plus other punctuation
        name = name.replace('†', '').replace('*', '').replace('‡', '')
        return name.replace(' ', '').replace('.', '').replace('-', '').lower()

    def _extract_surname(self, name: str) -> str:
        """Extract surname (last word) from name"""
        parts = name.strip().split()
        return parts[-1] if parts else ""

    def _extract_initials(self, name: str) -> str:
        """Extract initials from name (all parts except last)"""
        parts = name.strip().split()
        if len(parts) <= 1:
            return ""
        return ''.join(p[0] for p in parts[:-1] if p)

    def _split_camel_case(self, name: str) -> List[str]:
        """Split camelCase name: MickBoendermaker → ['Mick', 'Boendermaker']"""
        import re
        return [word for word in re.findall(r'[A-Z][a-z]*', name) if word]

    def match_player(
        self,
        scraped_name: str,
        club_filter: Optional[str] = None,
        team_filter: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Match a scraped player name to database player

        Args:
            scraped_name: Name from scorecard (e.g., "M BOENDERMAKER")
            club_filter: Optional club name to narrow search (e.g., "ACC")
            team_filter: Optional team name to narrow search (e.g., "ACC 1")

        Returns:
            Player dict if found, None otherwise
        """

        # Filter candidates by club/team
        candidates = self._get_candidates(club_filter, team_filter)

        if not candidates:
            logger.warning(f"No candidates for club={club_filter}, team={team_filter}")
            return None

        # Try matching strategies
        player = (
            self._try_exact_match(scraped_name, candidates) or
            self._try_manual_mapping(scraped_name) or
            self._try_surname_match(scraped_name, candidates) or
            self._try_initials_match(scraped_name, candidates) or
            self._try_fuzzy_match(scraped_name, candidates)
        )

        if player:
            logger.debug(f"✅ Matched '{scraped_name}' → {player['name']}")
        else:
            logger.warning(f"⚠️  No match for '{scraped_name}'")

        return player

    def _get_candidates(
        self,
        club_filter: Optional[str],
        team_filter: Optional[str]
    ) -> List[Dict]:
        """Get candidate players filtered by club/team"""
        candidates = self._players_cache

        if club_filter:
            candidates = [p for p in candidates if p['club_name'] == club_filter]

        if team_filter:
            candidates = [p for p in candidates if p['team_name'] == team_filter]

        return candidates

    def _try_exact_match(self, scraped_name: str, candidates: List[Dict]) -> Optional[Dict]:
        """Try exact normalized match"""
        normalized = self._normalize_name(scraped_name)

        for player in candidates:
            if self._normalize_name(player['name']) == normalized:
                logger.debug(f"   Exact: {scraped_name} → {player['name']}")
                return player

        return None

    def _try_manual_mapping(self, scraped_name: str) -> Optional[Dict]:
        """Try manual mapping table"""
        normalized = self._normalize_name(scraped_name)

        if normalized in MANUAL_MAPPINGS:
            player_id = MANUAL_MAPPINGS[normalized]

            for player in self._players_cache:
                if player['id'] == player_id:
                    logger.debug(f"   Manual: {scraped_name} → {player['name']}")
                    return player

        return None

    def _try_surname_match(self, scraped_name: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Match by surname (most reliable for scorecards)

        Examples:
        - "M BOENDERMAKER" → "MickBoendermaker"
        - "DOORNINCK" → "DaanDoorninck"
        """
        surname = self._normalize_name(self._extract_surname(scraped_name))

        if not surname:
            return None

        matches = [p for p in candidates if surname in self._normalize_name(p['name'])]

        if len(matches) == 1:
            logger.debug(f"   Surname: {scraped_name} → {matches[0]['name']}")
            return matches[0]
        elif len(matches) > 1:
            # Multiple people with same surname - try initials
            return self._disambiguate_by_initials(scraped_name, matches)

        return None

    def _try_initials_match(self, scraped_name: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Match by initials + surname

        Examples:
        - "DV DOORNINCK" → "DaanDoorninck" (D matches Daan, V could be middle name)
        """
        initials = self._normalize_name(self._extract_initials(scraped_name))
        surname = self._normalize_name(self._extract_surname(scraped_name))

        if not surname:
            return None

        for player in candidates:
            # Check if surname matches
            if surname not in self._normalize_name(player['name']):
                continue

            # Extract player's name parts
            parts = self._split_camel_case(player['name'])
            if not parts:
                continue

            # Check if initials match
            player_initials = self._normalize_name(''.join(p[0] for p in parts[:-1]))

            if initials == player_initials:
                logger.debug(f"   Initials: {scraped_name} → {player['name']}")
                return player

        return None

    def _disambiguate_by_initials(self, scraped_name: str, candidates: List[Dict]) -> Optional[Dict]:
        """Disambiguate multiple surname matches using initials"""
        initials = self._extract_initials(scraped_name)

        if not initials:
            return None

        first_initial = self._normalize_name(initials[0]) if initials else None

        # Try exact initials first
        normalized_initials = self._normalize_name(initials)

        for player in candidates:
            parts = self._split_camel_case(player['name'])
            player_initials = self._normalize_name(''.join(p[0] for p in parts[:-1]))

            if normalized_initials == player_initials:
                logger.debug(f"   Disambiguate: {scraped_name} → {player['name']}")
                return player

        # Try just first initial
        if first_initial:
            first_initial_matches = [
                p for p in candidates
                if self._normalize_name(p['name'][0]) == first_initial
            ]

            if len(first_initial_matches) == 1:
                logger.debug(f"   First initial: {scraped_name} → {first_initial_matches[0]['name']}")
                return first_initial_matches[0]

        return None

    def _try_fuzzy_match(self, scraped_name: str, candidates: List[Dict]) -> Optional[Dict]:
        """Fuzzy string matching for typos/variations"""
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            logger.debug("fuzzywuzzy not available")
            return None

        normalized_scraped = self._normalize_name(scraped_name)

        best_match = None
        best_score = 0

        for player in candidates:
            normalized_player = self._normalize_name(player['name'])
            score = fuzz.ratio(normalized_scraped, normalized_player)

            if score > best_score:
                best_score = score
                best_match = player

        if best_score >= 80:
            logger.debug(f"   Fuzzy ({best_score}%): {scraped_name} → {best_match['name']}")
            return best_match

        return None

    def batch_match(
        self,
        scraped_names: List[str],
        club_filter: Optional[str] = None,
        team_filter: Optional[str] = None
    ) -> List[Tuple[str, Optional[Dict]]]:
        """
        Match multiple player names in batch

        Returns:
            List of (scraped_name, matched_player) tuples
        """
        results = []

        for name in scraped_names:
            player = self.match_player(name, club_filter, team_filter)
            results.append((name, player))

        return results

    def get_statistics(self, matches: List[Tuple[str, Optional[Dict]]]) -> Dict:
        """Calculate matching statistics"""
        total = len(matches)
        matched = sum(1 for _, player in matches if player is not None)
        unmatched = total - matched

        unmatched_names = [name for name, player in matches if player is None]

        return {
            'total': total,
            'matched': matched,
            'unmatched': unmatched,
            'match_rate': (matched / total * 100) if total > 0 else 0,
            'unmatched_names': unmatched_names
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def add_manual_mapping(scraped_name: str, player_id: str):
    """
    Add a manual mapping for a problem case

    Usage:
        add_manual_mapping("M BOENDERMAKER", "player-uuid-here")
    """
    normalized = scraped_name.replace(' ', '').replace('.', '').lower()
    MANUAL_MAPPINGS[normalized] = player_id
    logger.info(f"Added manual mapping: '{scraped_name}' → {player_id}")


# =============================================================================
# TESTING
# =============================================================================

def test_matcher():
    """Test with sample data"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\n" + "="*80)
        print("🧪 TESTING SCORECARD PLAYER MATCHER")
        print("="*80)

        matcher = ScorecardPlayerMatcher(session)

        # Test cases from real 2025 scorecards
        test_cases = [
            ("M BOENDERMAKER", "ACC"),
            ("DV DOORNINCK", "ACC"),
            ("I ALIM", "ACC"),
            ("H ALI", "ACC"),
            ("G GABA", "ACC"),
            ("S DIWAN", "ACC"),
            ("CD LANGE", "ACC"),
            ("MI KHAN", "ACC"),
            ("A SEHGAL", "ACC"),
            ("R SRIPATNALA", "ACC"),
        ]

        print(f"\n📋 Testing {len(test_cases)} player names:")
        print("-"*80)

        results = matcher.batch_match(
            [name for name, _ in test_cases],
            club_filter="ACC"
        )

        for (scraped_name, club), (_, player) in zip(test_cases, results):
            if player:
                print(f"✅ '{scraped_name:<20}' → {player['name']:<25} ({player['player_type'] or 'unknown'})")
            else:
                print(f"❌ '{scraped_name:<20}' → NOT FOUND")

        # Statistics
        stats = matcher.get_statistics(results)

        print("\n" + "="*80)
        print("📊 MATCHING STATISTICS")
        print("="*80)
        print(f"Total:          {stats['total']}")
        print(f"Matched:        {stats['matched']}")
        print(f"Unmatched:      {stats['unmatched']}")
        print(f"Match Rate:     {stats['match_rate']:.1f}%")

        if stats['unmatched_names']:
            print(f"\n⚠️  Unmatched players:")
            for name in stats['unmatched_names']:
                print(f"   - {name}")
                # Show closest matches for debugging
                candidates = matcher._get_candidates("ACC", None)
                surnames = [c['name'] for c in candidates if
                           matcher._normalize_name(matcher._extract_surname(name))
                           in matcher._normalize_name(c['name'])]
                if surnames:
                    print(f"      Similar surnames: {', '.join(surnames[:3])}")

        print("\n" + "="*80)

    finally:
        session.close()


if __name__ == "__main__":
    test_matcher()
