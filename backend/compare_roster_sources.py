#!/usr/bin/env python3
"""
Compare roster data from different sources to assess scraper accuracy.

This script compares:
1. Current database roster (scraped data)
2. Ground truth CSV (user-provided accurate roster)

Calculates metrics:
- Coverage: % of CSV players found in database
- Precision: % of database players valid (in CSV)
- False Positives: Players in DB but not in CSV
- False Negatives: Players in CSV but not in DB
"""

import csv
import json
import re
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
from collections import defaultdict


class RosterComparison:
    """Compare roster data from different sources"""

    def __init__(self):
        self.db_players: List[Dict] = []
        self.csv_players: List[Dict] = []
        self.db_names: Set[str] = set()
        self.csv_names: Set[str] = set()

    def normalize_name(self, name: str) -> str:
        """
        Normalize player name for comparison.

        Examples:
            "MickBoendermaker" -> "mickboendermaker"
            "Mick Boendermaker" -> "mickboendermaker"
            "M BOENDERMAKER" -> "mboendermaker"
        """
        name = name.lower()
        name = re.sub(r'[^a-z]', '', name)  # Remove all non-letters
        return name

    def load_database_export(self, filepath: str):
        """Load current database roster export"""
        print(f"Loading database export from: {filepath}")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.db_players.append({
                    'id': row['id'],
                    'name': row['name'],
                    'team': row['rl_team'],
                    'role': row['role'],
                    'multiplier': float(row['multiplier']),
                    'normalized_name': self.normalize_name(row['name'])
                })
                self.db_names.add(self.normalize_name(row['name']))

        print(f"✓ Loaded {len(self.db_players)} players from database")

    def load_csv_roster(self, filepath: str):
        """Load ground truth CSV roster"""
        print(f"\nLoading ground truth CSV from: {filepath}")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Flexible column name handling
                name = row.get('name') or row.get('player_name') or row.get('Name')
                team = row.get('team_name') or row.get('team') or row.get('Team')
                role = row.get('player_type') or row.get('role') or row.get('Role')

                if not name:
                    continue

                self.csv_players.append({
                    'name': name,
                    'team': team or 'Unknown',
                    'role': role or 'Unknown',
                    'normalized_name': self.normalize_name(name)
                })
                self.csv_names.add(self.normalize_name(name))

        print(f"✓ Loaded {len(self.csv_players)} players from CSV")

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two names (0.0 to 1.0)"""
        return SequenceMatcher(None, name1, name2).ratio()

    def find_fuzzy_matches(self, name: str, candidates: List[str], threshold: float = 0.80) -> List[Tuple[str, float]]:
        """Find fuzzy matches for a name in candidate list"""
        matches = []
        for candidate in candidates:
            score = self.calculate_similarity(name, candidate)
            if score >= threshold:
                matches.append((candidate, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def compare(self) -> Dict:
        """Perform comparison and generate metrics"""
        print("\n" + "="*60)
        print("COMPARING ROSTERS")
        print("="*60)

        # Find exact matches
        exact_matches = self.db_names & self.csv_names

        # Find players only in database (potential false positives)
        only_in_db = self.db_names - self.csv_names

        # Find players only in CSV (scraper missed these)
        only_in_csv = self.csv_names - self.db_names

        # Calculate metrics
        total_db = len(self.db_players)
        total_csv = len(self.csv_players)
        matched = len(exact_matches)

        coverage = (matched / total_csv * 100) if total_csv > 0 else 0
        precision = (matched / total_db * 100) if total_db > 0 else 0

        print(f"\n📊 EXACT MATCH STATISTICS:")
        print(f"  Database Players: {total_db}")
        print(f"  CSV Players: {total_csv}")
        print(f"  Exact Matches: {matched}")
        print(f"  Coverage: {coverage:.1f}% (CSV players found in DB)")
        print(f"  Precision: {precision:.1f}% (DB players valid)")

        # Analyze unmatched players with fuzzy matching
        print(f"\n🔍 ANALYZING UNMATCHED PLAYERS:")

        # Players in CSV but not DB (scraper missed)
        fuzzy_matches_for_csv = {}
        if only_in_csv:
            print(f"\n  Players in CSV but NOT in DB: {len(only_in_csv)}")
            print(f"  (These are real ACC players the scraper missed)\n")

            # Get original names for display
            csv_name_map = {p['normalized_name']: p['name'] for p in self.csv_players}
            db_name_map = {p['normalized_name']: p['name'] for p in self.db_players}

            for i, norm_name in enumerate(list(only_in_csv)[:20], 1):  # Show first 20
                original_name = csv_name_map[norm_name]
                fuzzy = self.find_fuzzy_matches(norm_name, list(self.db_names), threshold=0.75)

                print(f"  {i}. {original_name}")
                if fuzzy:
                    fuzzy_matches_for_csv[original_name] = [
                        (db_name_map[match[0]], match[1]) for match in fuzzy[:3]
                    ]
                    for db_match, score in fuzzy[:3]:
                        print(f"     → Fuzzy match: {db_name_map[db_match]} ({score:.0%})")
                else:
                    fuzzy_matches_for_csv[original_name] = []
                    print(f"     → No fuzzy matches found")

            if len(only_in_csv) > 20:
                print(f"  ... and {len(only_in_csv) - 20} more")

        # Players in DB but not CSV (false positives)
        fuzzy_matches_for_db = {}
        if only_in_db:
            print(f"\n  Players in DB but NOT in CSV: {len(only_in_db)}")
            print(f"  (These might be opposition players or errors)\n")

            db_name_map = {p['normalized_name']: p['name'] for p in self.db_players}
            csv_name_map = {p['normalized_name']: p['name'] for p in self.csv_players}

            for i, norm_name in enumerate(list(only_in_db)[:20], 1):  # Show first 20
                original_name = db_name_map[norm_name]
                fuzzy = self.find_fuzzy_matches(norm_name, list(self.csv_names), threshold=0.75)

                print(f"  {i}. {original_name}")
                if fuzzy:
                    fuzzy_matches_for_db[original_name] = [
                        (csv_name_map[match[0]], match[1]) for match in fuzzy[:3]
                    ]
                    for csv_match, score in fuzzy[:3]:
                        print(f"     → Fuzzy match: {csv_name_map[csv_match]} ({score:.0%})")
                else:
                    fuzzy_matches_for_db[original_name] = []
                    print(f"     → No fuzzy matches found (likely opposition player)")

            if len(only_in_db) > 20:
                print(f"  ... and {len(only_in_db) - 20} more")

        # Team distribution analysis
        print(f"\n📋 TEAM DISTRIBUTION:")
        db_teams = defaultdict(int)
        csv_teams = defaultdict(int)

        for player in self.db_players:
            db_teams[player['team']] += 1

        for player in self.csv_players:
            csv_teams[player['team']] += 1

        print(f"\n  Database:")
        for team, count in sorted(db_teams.items(), key=lambda x: x[1], reverse=True):
            print(f"    {team}: {count}")

        print(f"\n  CSV:")
        for team, count in sorted(csv_teams.items(), key=lambda x: x[1], reverse=True):
            print(f"    {team}: {count}")

        # Generate results
        results = {
            'summary': {
                'total_db_players': total_db,
                'total_csv_players': total_csv,
                'exact_matches': matched,
                'coverage_percent': round(coverage, 2),
                'precision_percent': round(precision, 2),
                'false_negatives': len(only_in_csv),  # In CSV, not in DB
                'false_positives': len(only_in_db)     # In DB, not in CSV
            },
            'exact_matches': {
                'count': matched,
                'names': sorted([p['name'] for p in self.db_players if p['normalized_name'] in exact_matches])
            },
            'only_in_csv': {
                'count': len(only_in_csv),
                'names': sorted([p['name'] for p in self.csv_players if p['normalized_name'] in only_in_csv]),
                'fuzzy_matches': fuzzy_matches_for_csv
            },
            'only_in_db': {
                'count': len(only_in_db),
                'names': sorted([p['name'] for p in self.db_players if p['normalized_name'] in only_in_db]),
                'fuzzy_matches': fuzzy_matches_for_db
            },
            'team_distribution': {
                'database': dict(db_teams),
                'csv': dict(csv_teams)
            }
        }

        return results

    def save_results(self, results: Dict, output_path: str):
        """Save comparison results to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {output_path}")


def main():
    """Run roster comparison"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python compare_roster_sources.py <db_export.csv> <ground_truth.csv>")
        print("\nExample:")
        print("  python compare_roster_sources.py current_roster_export.csv acc_roster_2026.csv")
        sys.exit(1)

    db_file = sys.argv[1]
    csv_file = sys.argv[2]
    output_file = "roster_comparison_results.json"

    # Run comparison
    comparison = RosterComparison()
    comparison.load_database_export(db_file)
    comparison.load_csv_roster(csv_file)
    results = comparison.compare()
    comparison.save_results(results, output_file)

    # Print final assessment
    print("\n" + "="*60)
    print("FINAL ASSESSMENT")
    print("="*60)

    coverage = results['summary']['coverage_percent']
    precision = results['summary']['precision_percent']

    print(f"\n📈 SCRAPER ACCURACY:")
    print(f"  Coverage: {coverage:.1f}%")
    if coverage >= 95:
        print(f"    ✅ Excellent - Found almost all real ACC players")
    elif coverage >= 85:
        print(f"    🟡 Good - Missing ~{100-coverage:.0f}% of real players")
    else:
        print(f"    ❌ Poor - Missing {100-coverage:.0f}% of real players")

    print(f"\n  Precision: {precision:.1f}%")
    if precision >= 95:
        print(f"    ✅ Excellent - Very few false positives")
    elif precision >= 85:
        print(f"    🟡 Good - ~{100-precision:.0f}% might be opposition players")
    else:
        print(f"    ❌ Poor - {100-precision:.0f}% are likely invalid")

    print(f"\n💡 RECOMMENDATIONS:")
    if results['summary']['false_negatives'] > 0:
        print(f"  • Review {results['summary']['false_negatives']} missing players")
        print(f"    (Check fuzzy matches - might be name format issues)")

    if results['summary']['false_positives'] > 0:
        print(f"  • Review {results['summary']['false_positives']} extra players")
        print(f"    (Likely opposition players - consider filtering)")

    if results['only_in_csv']['fuzzy_matches']:
        print(f"  • Add manual name mappings for fuzzy matches")

    print(f"\n✓ Full report: {output_file}")


if __name__ == '__main__':
    main()
