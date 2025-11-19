#!/usr/bin/env python3
"""
Restore 513 players from CSV into current database schema
"""
import csv
import os
import sys
import psycopg2
from datetime import datetime
import uuid

# Database connection
DB_PASSWORD = os.getenv('DB_PASSWORD', '_8dbdlHVu5kVHclQhPkqhg8IuLa6Ni1QcR0GUT7M9d0')
DB_HOST = os.getenv('DB_HOST', 'fantasy_cricket_db')  # Docker container name
DATABASE_URL = f"postgresql://cricket_admin:{DB_PASSWORD}@{DB_HOST}:5432/fantasy_cricket"

# Role mapping
ROLE_MAP = {
    'batsman': 'BATSMAN',
    'bowler': 'BOWLER',
    'all-rounder': 'ALL_ROUNDER',
    'wicket-keeper': 'WICKET_KEEPER'
}

def get_or_create_club(cursor, club_name):
    """Get club ID or create if doesn't exist"""
    # Check if club exists
    cursor.execute("SELECT id FROM clubs WHERE name = %s", (club_name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new club
    club_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO clubs (id, name, tier, location, founded_year, created_at)
        VALUES (%s, %s, 'HOOFDKLASSE', 'Amsterdam', 1900, NOW())
    """, (club_id, club_name))
    print(f"✅ Created club: {club_name}")
    return club_id

def import_players(csv_file='acc_cleaned_players.csv'):
    """Import players from CSV"""
    print(f"🏏 Restoring {csv_file}...")
    print(f"   Database: {DATABASE_URL.split('@')[1]}")
    print()

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Read CSV
        players = []
        club_cache = {}

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract club name from team (e.g., "ACC 1" -> "ACC")
                team = row['team']
                club_name = team.rsplit(' ', 1)[0] if ' ' in team else team

                # Get or create club
                if club_name not in club_cache:
                    club_cache[club_name] = get_or_create_club(cursor, club_name)

                club_id = club_cache[club_name]

                # Map role
                role = ROLE_MAP.get(row['player_type'], 'BATSMAN')

                # Determine tier from team number
                team_number = team.split()[-1] if ' ' in team else '1'
                if team_number in ('1', '2'):
                    tier = 'HOOFDKLASSE'
                elif team_number == '3':
                    tier = 'OVERGANGSKLASSE'
                elif team_number in ('4', '5'):
                    tier = 'EERSTE_KLASSE'
                else:
                    tier = 'TWEEDE_KLASSE'

                # Calculate price from multiplier (inverse relationship)
                multiplier = float(row['multiplier'])
                base_price = int(100 - (multiplier * 20))  # Lower multiplier = higher price

                players.append({
                    'id': row['player_id'],
                    'name': row['player_name'],
                    'club_id': club_id,
                    'role': role,
                    'tier': tier,
                    'base_price': base_price,
                    'current_price': base_price,
                    'multiplier': multiplier,  # Store in stats JSON later
                    'team': team
                })

        print(f"✅ Parsed {len(players)} players from CSV")
        print(f"   Clubs: {list(club_cache.keys())}")
        print()

        # Check existing players
        cursor.execute("SELECT COUNT(*) FROM players")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"⚠️  Database has {existing_count} existing players")
            print("   Deleting all players to start fresh...")
            cursor.execute("DELETE FROM players")
            print(f"   Deleted {cursor.rowcount} players")
            print()

        # Insert players
        print("📥 Inserting players...")
        inserted = 0
        errors = 0

        for player in players:
            try:
                cursor.execute("""
                    INSERT INTO players (
                        id, name, club_id, role, tier,
                        base_price, current_price, is_active, created_at
                    ) VALUES (%s, %s, %s, %s::playerrole, %s::crickettier, %s, %s, TRUE, NOW())
                """, (
                    player['id'],
                    player['name'],
                    player['club_id'],
                    player['role'],
                    player['tier'],
                    player['base_price'],
                    player['current_price']
                ))
                inserted += 1

                if inserted % 50 == 0:
                    print(f"   Inserted {inserted}/{len(players)}...")

            except Exception as e:
                errors += 1
                if errors < 10:  # Only print first 10 errors
                    print(f"   ⚠️  Error inserting {player['name']}: {e}")

        # Commit
        conn.commit()

        print()
        print(f"✅ Import complete!")
        print(f"   Inserted: {inserted} players")
        print(f"   Errors: {errors}")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM players")
        final_count = cursor.fetchone()[0]
        print(f"   Total in database: {final_count}")

        # Sample players
        print()
        print("📊 Sample players:")
        cursor.execute("""
            SELECT name, role, tier, base_price
            FROM players
            ORDER BY base_price DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]}, {row[2]}, €{row[3]})")

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    import_players()
