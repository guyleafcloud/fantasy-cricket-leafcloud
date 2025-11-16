#!/usr/bin/env python3
"""
Test Match Performance System
==============================
End-to-end test of the fantasy points calculation system:
1. Scrape historical scorecard
2. Match players to database
3. Calculate fantasy points
4. Store in database
5. Display results
"""

import asyncio
import os
import psycopg2
from kncb_html_scraper import KNCBMatchCentreScraper
from match_performance_service import MatchPerformanceService
from database_models import init_database
from sqlalchemy import create_engine

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')
ACC_CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276'

# Test with known historical scorecards
TEST_SCORECARDS = [
    "https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921",
    "https://matchcentre.kncb.nl/match/134453-7254571/scorecard/?period=2821925",
    "https://matchcentre.kncb.nl/match/134453-7254576/scorecard/?period=2821930",
    "https://matchcentre.kncb.nl/match/134453-7254580/scorecard/?period=2821934"
]


async def test_fantasy_points_system():
    """Test the complete fantasy points calculation system"""

    print("\n" + "=" * 80)
    print("🏏 FANTASY CRICKET POINTS SYSTEM TEST")
    print("=" * 80)
    print()

    # Initialize database tables
    print("📦 Initializing database tables...")
    try:
        engine = create_engine(DATABASE_URL)
        init_database(engine)
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print("   Make sure the database is running and accessible")
        return
    print()

    # Get season ID
    print("🔍 Finding active season...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM seasons WHERE name = '2025' LIMIT 1")
        season_row = cursor.fetchone()
        if not season_row:
            print("❌ No 2025 season found in database")
            print("   Please create a season first")
            cursor.close()
            conn.close()
            return
        season_id = season_row[0]
        print(f"✅ Found season: {season_id}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    print()

    # Initialize services
    print("🔧 Initializing services...")
    scraper = KNCBMatchCentreScraper()
    service = MatchPerformanceService(DATABASE_URL)
    print("✅ Services initialized")
    print()

    # Test with first 4 scorecards (or as many as requested by user)
    num_tests = 4
    print(f"📋 Testing with {num_tests} historical scorecards:")
    print()

    total_matched = 0
    total_unmatched = 0
    processed_matches = []

    for i, scorecard_url in enumerate(TEST_SCORECARDS[:num_tests], 1):
        print(f"--- TEST {i}/{num_tests} ---")
        print(f"URL: {scorecard_url}")
        print()

        # Extract match ID from URL
        # Example URL: https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921
        # Match ID: 134453-7254567 (but we need just the numeric part after the dash)
        try:
            match_id_str = scorecard_url.split('/match/')[1].split('/')[0]
            # Extract the second number (e.g., 7254567 from 134453-7254567)
            match_id = int(match_id_str.split('-')[1])
        except (IndexError, ValueError) as e:
            print(f"  ❌ Could not parse match ID from URL: {e}")
            continue

        # Scrape scorecard
        print(f"  📡 Scraping scorecard (Match ID: {match_id})...")
        try:
            match_data = await scraper.scrape_match_scorecard(match_id)
        except Exception as e:
            print(f"  ❌ Scraping error: {e}")
            continue

        if not match_data:
            print("  ❌ Failed to scrape scorecard")
            print()
            continue

        print(f"  ✅ Scorecard scraped: {match_data.get('match_title', 'Unknown')}")
        print(f"     Date: {match_data.get('match_date', 'Unknown')}")
        print(f"     Players found: {len(match_data.get('player_performances', []))}")
        print()

        # Process scorecard
        print("  💾 Processing scorecard and calculating points...")
        try:
            match_id, matched, unmatched = service.process_scorecard(
                scorecard_data=match_data,
                season_id=season_id,
                club_id=ACC_CLUB_ID
            )

            total_matched += matched
            total_unmatched += unmatched

            print(f"  ✅ Match processed: {match_id}")
            print(f"     Matched players: {matched}")
            print(f"     Unmatched players: {unmatched}")

            processed_matches.append({
                'match_id': match_id,
                'title': match_data.get('match_title', 'Unknown'),
                'matched': matched,
                'unmatched': unmatched
            })

        except Exception as e:
            print(f"  ❌ Processing error: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Scorecards tested: {len(processed_matches)}")
    print(f"Total players matched: {total_matched}")
    print(f"Total players unmatched: {total_unmatched}")
    if total_matched + total_unmatched > 0:
        match_rate = (total_matched / (total_matched + total_unmatched)) * 100
        print(f"Match rate: {match_rate:.1f}%")
    print()

    # Show top performers
    if processed_matches:
        print("🏆 TOP PERFORMERS:")
        print()
        try:
            top_performers = service.get_top_performers(season_id, limit=10)
            for i, player in enumerate(top_performers, 1):
                print(f"   {i}. {player['name']}: {player['total_points']:.0f} points")
            print()
        except Exception as e:
            print(f"   ⚠️  Could not fetch top performers: {e}")
            print()

    # Show processed matches
    if processed_matches:
        print("📋 PROCESSED MATCHES:")
        print()
        for i, match in enumerate(processed_matches, 1):
            print(f"   {i}. {match['title']}")
            print(f"      Match ID: {match['match_id']}")
            print(f"      Players: {match['matched']} matched, {match['unmatched']} unmatched")
            print()

    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()

    # Cleanup
    service.close()


if __name__ == "__main__":
    asyncio.run(test_fantasy_points_system())
