#!/usr/bin/env python3
"""
Test player matching accuracy for scorecard name variations.

This tests if the scraper can correctly identify players from scorecard formats
like "M BOENDERMAKER" and match them to database entries like "MickBoendermaker".
"""

import sys
sys.path.insert(0, '/Users/guypa/github/fantasy-cricket-leafcloud/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Player
from scorecard_player_matcher import ScorecardPlayerMatcher
import os

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')

def test_player_matching():
    """Test player matching with various name formats"""

    print("="*60)
    print("PLAYER MATCHING TEST")
    print("="*60)

    # Connect to database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get all ACC players
    acc_club_id = '625f1c55-6d5b-40a9-be1d-8f7abe6fa00e'  # ACC
    players = session.query(Player).filter_by(club_id=acc_club_id).limit(20).all()

    print(f"\nLoaded {len(players)} sample players from database")
    print("\nSample players:")
    for i, p in enumerate(players[:10], 1):
        print(f"  {i}. {p.name} ({p.rl_team})")

    # Initialize matcher
    matcher = ScorecardPlayerMatcher(session)

    print("\n" + "="*60)
    print("TESTING NAME FORMAT VARIATIONS")
    print("="*60)

    # Test various scorecard formats for each player
    test_cases = []

    for player in players[:10]:  # Test first 10 players
        # Generate scorecard-style variations
        name_parts = []
        for char in player.name:
            if char.isupper() and name_parts:  # New word starting
                break
            name_parts.append(char)

        first_name = ''.join(name_parts) if name_parts else player.name[0]

        # Try to extract surname (everything after first capital)
        surname_start = 0
        for i, char in enumerate(player.name[1:], 1):
            if char.isupper():
                surname_start = i
                break

        surname = player.name[surname_start:] if surname_start > 0 else player.name

        variations = [
            player.name,  # Full name
            f"{player.name[0]} {surname}",  # Initial + surname
            surname.upper(),  # Surname only (uppercase)
            f"{first_name[0].upper()} {surname.upper()}",  # Scorecard format
        ]

        for variation in variations:
            test_cases.append({
                'original': player.name,
                'original_team': player.rl_team,
                'variation': variation,
                'player_id': player.id
            })

    # Test each variation
    results = {
        'correct_matches': 0,
        'wrong_matches': 0,
        'no_matches': 0,
        'total': len(test_cases)
    }

    print(f"\nTesting {len(test_cases)} name variations...\n")

    for i, test in enumerate(test_cases[:30], 1):  # Show first 30 results
        matched = matcher.match_player(
            test['variation'],
            club_filter='ACC'
        )

        if matched:
            if matched['id'] == test['player_id']:
                results['correct_matches'] += 1
                status = "✅ CORRECT"
            else:
                results['wrong_matches'] += 1
                status = f"❌ WRONG (matched to {matched['name']})"
        else:
            results['no_matches'] += 1
            status = "❓ NOT FOUND"

        print(f"{i}. '{test['variation']}' → {status}")
        print(f"   Expected: {test['original']} ({test['original_team']})")
        if matched and matched['id'] != test['player_id']:
            print(f"   Got: {matched['name']} ({matched.get('team', 'Unknown')})")
        print()

    # Calculate accuracy
    accuracy = (results['correct_matches'] / results['total'] * 100) if results['total'] > 0 else 0

    print("="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"\nTotal Tests: {results['total']}")
    print(f"✅ Correct Matches: {results['correct_matches']} ({accuracy:.1f}%)")
    print(f"❌ Wrong Matches: {results['wrong_matches']}")
    print(f"❓ No Matches: {results['no_matches']}")

    print(f"\n📊 MATCHING ACCURACY: {accuracy:.1f}%")

    if accuracy >= 90:
        print("✅ Excellent - Scraper should reliably match players")
    elif accuracy >= 75:
        print("🟡 Good - Most players matched, some manual mappings needed")
    elif accuracy >= 60:
        print("⚠️  Fair - Significant manual mapping required")
    else:
        print("❌ Poor - Scraper matching needs improvement")

    session.close()

    return results


if __name__ == '__main__':
    # Check if running on production
    if 'fantcric.fun' in os.getenv('DATABASE_URL', ''):
        print("⚠️  WARNING: This will test against PRODUCTION database")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    try:
        results = test_player_matching()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
