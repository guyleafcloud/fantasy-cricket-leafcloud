#!/usr/bin/env python3
"""
Import cleaned ACC players from CSV into PostgreSQL database
"""
import csv
import os
import sys
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.extras import Json

# Database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')

# ACC Club ID (must match the club record in database)
ACC_CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276'

def import_players_from_csv(csv_file='acc_cleaned_players.csv'):
    """Import players from CSV into database"""

    print(f"🏏 Importing ACC players from {csv_file}...")
    print(f"   Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")
    print(f"   Club ID: {ACC_CLUB_ID}")
    print()

    # Read CSV
    players = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            players.append({
                'id': row['player_id'],
                'club_id': ACC_CLUB_ID,
                'team_id': None,  # No teams exist yet
                'name': row['player_name'],
                'player_type': row['player_type'],
                'multiplier': float(row['multiplier']),
                'multiplier_updated_at': datetime.utcnow(),
                'fantasy_value': 25.0,  # Default legacy value
                'is_wicket_keeper': False,  # Default
                'stats': Json({}),  # Empty for now, wrapped in Json()
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'value_calculation_date': datetime.utcnow(),
                'value_manually_adjusted': False
            })

    print(f"✅ Read {len(players)} players from CSV")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Check if club exists
        cursor.execute("SELECT id, name FROM clubs WHERE id = %s", (ACC_CLUB_ID,))
        club = cursor.fetchone()
        if not club:
            print(f"❌ ERROR: Club {ACC_CLUB_ID} not found in database!")
            print("   Please create the ACC club first.")
            return

        print(f"✅ Found club: {club[1]}")

        # Check existing players
        cursor.execute("SELECT COUNT(*) FROM players WHERE club_id = %s", (ACC_CLUB_ID,))
        existing_count = cursor.fetchone()[0]
        print(f"ℹ️  Existing players in database: {existing_count}")

        if existing_count > 0:
            response = input("   Delete existing players and reimport? (yes/no): ")
            if response.lower() == 'yes':
                cursor.execute("DELETE FROM players WHERE club_id = %s", (ACC_CLUB_ID,))
                deleted = cursor.rowcount
                print(f"   Deleted {deleted} existing players")
            else:
                print("   Skipping import")
                return

        # Insert players
        print()
        print("📥 Inserting players into database...")

        insert_query = """
        INSERT INTO players (
            id, club_id, team_id, name, player_type, multiplier, multiplier_updated_at,
            fantasy_value, is_wicket_keeper, stats, created_at, updated_at,
            value_calculation_date, value_manually_adjusted
        ) VALUES (
            %(id)s, %(club_id)s, %(team_id)s, %(name)s, %(player_type)s, %(multiplier)s,
            %(multiplier_updated_at)s, %(fantasy_value)s, %(is_wicket_keeper)s, %(stats)s,
            %(created_at)s, %(updated_at)s, %(value_calculation_date)s, %(value_manually_adjusted)s
        )
        """

        inserted = 0
        skipped = 0

        for player in players:
            try:
                cursor.execute(insert_query, player)
                inserted += 1
                if inserted % 50 == 0:
                    print(f"   Inserted {inserted}/{len(players)} players...")
            except Exception as e:
                print(f"   ⚠️  Skipped {player['name']}: {e}")
                skipped += 1

        # Commit transaction
        conn.commit()

        print()
        print(f"✅ Import complete!")
        print(f"   Inserted: {inserted} players")
        print(f"   Skipped: {skipped} players")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM players WHERE club_id = %s", (ACC_CLUB_ID,))
        final_count = cursor.fetchone()[0]
        print(f"   Total in database: {final_count} players")

        # Show sample
        print()
        print("📊 Sample players:")
        cursor.execute("""
            SELECT name, player_type, multiplier
            FROM players
            WHERE club_id = %s
            ORDER BY multiplier ASC
            LIMIT 5
        """, (ACC_CLUB_ID,))

        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]}, multiplier: {row[2]})")

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'acc_cleaned_players.csv'
    import_players_from_csv(csv_file)
