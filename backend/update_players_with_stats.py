#!/usr/bin/env python3
"""
Update players in database with complete stats from acc_legacy_database.json
Matches players by name and updates their stats, multiplier, and other fields
"""
import json
import os
import psycopg2
from psycopg2.extras import Json
from datetime import datetime

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')
ACC_CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276'

def normalize_name(name):
    """Normalize player name for matching - remove spaces, lowercase"""
    return name.replace(' ', '').lower()

def update_players_from_legacy_db(json_file='rosters/acc_legacy_database.json'):
    """Update players with complete stats from legacy database"""

    print(f"🏏 Updating ACC players with stats from {json_file}...")
    print(f"   Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")
    print(f"   Club ID: {ACC_CLUB_ID}")
    print()

    # Load legacy database JSON
    with open(json_file, 'r') as f:
        legacy_data = json.load(f)

    legacy_players = legacy_data.get('players', [])
    print(f"✅ Loaded {len(legacy_players)} players from legacy database")

    # Create lookup by normalized name
    legacy_by_name = {}
    for player in legacy_players:
        norm_name = normalize_name(player['name'])
        # Keep the player with highest multiplier if duplicates
        if norm_name not in legacy_by_name or player.get('multiplier', 0) > legacy_by_name[norm_name].get('multiplier', 0):
            legacy_by_name[norm_name] = player

    print(f"   Unique players after deduplication: {len(legacy_by_name)}")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Get existing players from database
        cursor.execute("""
            SELECT id, name, player_type, multiplier, stats
            FROM players
            WHERE club_id = %s
        """, (ACC_CLUB_ID,))

        db_players = cursor.fetchall()
        print(f"✅ Found {len(db_players)} players in database")
        print()

        # Update each player with stats from legacy database
        print("📝 Updating players with complete stats...")
        updated = 0
        not_found = 0
        skipped = 0

        for db_player in db_players:
            player_id, name, player_type, multiplier, current_stats = db_player
            norm_name = normalize_name(name)

            # Find matching player in legacy database
            legacy_player = legacy_by_name.get(norm_name)

            if not legacy_player:
                print(f"   ⚠️  No match found for: {name}")
                not_found += 1
                continue

            # Prepare updated stats
            new_stats = legacy_player.get('stats', {})
            new_multiplier = legacy_player.get('multiplier', multiplier)

            # Determine player type from stats
            new_player_type = player_type  # Keep existing by default
            if new_stats:
                runs = new_stats.get('runs', 0)
                wickets = new_stats.get('wickets', 0)

                # Simple role determination
                if wickets > 10 and runs > 100:
                    new_player_type = 'all-rounder'
                elif wickets > 10:
                    new_player_type = 'bowler'
                elif runs > 100:
                    new_player_type = 'batsman'

            # Update the player
            try:
                cursor.execute("""
                    UPDATE players
                    SET
                        stats = %s,
                        multiplier = %s,
                        player_type = %s,
                        multiplier_updated_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    Json(new_stats),
                    new_multiplier,
                    new_player_type,
                    datetime.utcnow(),
                    datetime.utcnow(),
                    player_id
                ))
                updated += 1

                if updated % 50 == 0:
                    print(f"   Updated {updated}/{len(db_players)} players...")

            except Exception as e:
                print(f"   ❌ Failed to update {name}: {e}")
                skipped += 1

        # Commit changes
        conn.commit()

        print()
        print(f"✅ Update complete!")
        print(f"   Updated: {updated} players")
        print(f"   Not found in legacy DB: {not_found} players")
        print(f"   Skipped (errors): {skipped} players")

        # Show sample of updated players
        print()
        print("📊 Sample updated players:")
        cursor.execute("""
            SELECT name, player_type, multiplier,
                   stats->>'matches' as matches,
                   stats->>'runs' as runs,
                   stats->>'wickets' as wickets
            FROM players
            WHERE club_id = %s AND stats IS NOT NULL
            ORDER BY multiplier DESC
            LIMIT 5
        """, (ACC_CLUB_ID,))

        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]}, mult: {row[2]:.2f}) - {row[3]} matches, {row[4]} runs, {row[5]} wickets")

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    update_players_from_legacy_db()
