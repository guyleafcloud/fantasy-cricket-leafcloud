#!/usr/bin/env python3
"""
Update player multipliers from CSV
"""
import csv
import os
import psycopg2
from datetime import datetime

# Database connection
DB_PASSWORD = os.getenv('DB_PASSWORD', '_8dbdlHVu5kVHclQhPkqhg8IuLa6Ni1QcR0GUT7M9d0')
DB_HOST = os.getenv('DB_HOST', 'fantasy_cricket_db')
DATABASE_URL = f"postgresql://cricket_admin:{DB_PASSWORD}@{DB_HOST}:5432/fantasy_cricket"

def update_multipliers(csv_file='acc_cleaned_players.csv'):
    """Update player multipliers from CSV"""
    print(f"🔄 Updating player multipliers from {csv_file}...")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Read CSV
        updates = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                updates.append({
                    'player_id': row['player_id'],
                    'multiplier': float(row['multiplier']),
                    'timestamp': datetime.utcnow()
                })

        print(f"✅ Parsed {len(updates)} multipliers from CSV")
        print()

        # Update players
        print("📥 Updating multipliers...")
        updated = 0
        not_found = 0

        for update in updates:
            cursor.execute("""
                UPDATE players
                SET multiplier = %s, multiplier_updated_at = %s
                WHERE id = %s
            """, (update['multiplier'], update['timestamp'], update['player_id']))

            if cursor.rowcount > 0:
                updated += 1
            else:
                not_found += 1

            if updated % 100 == 0:
                print(f"   Updated {updated}/{len(updates)}...")

        # Commit
        conn.commit()

        print()
        print(f"✅ Update complete!")
        print(f"   Updated: {updated} players")
        print(f"   Not found: {not_found}")

        # Show sample
        print()
        print("📊 Sample players with multipliers:")
        cursor.execute("""
            SELECT name, role, multiplier
            FROM players
            WHERE multiplier IS NOT NULL
            ORDER BY multiplier ASC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"   - {row[0]} ({row[1]}): {row[2]:.2f}")

        print()
        print("📊 Multiplier distribution:")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                MIN(multiplier) as min,
                MAX(multiplier) as max,
                AVG(multiplier) as avg
            FROM players
            WHERE multiplier IS NOT NULL
        """)
        stats = cursor.fetchone()
        print(f"   Total: {stats[0]} players")
        print(f"   Range: {stats[1]:.2f} - {stats[2]:.2f}")
        print(f"   Average: {stats[3]:.2f}")

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    update_multipliers()
