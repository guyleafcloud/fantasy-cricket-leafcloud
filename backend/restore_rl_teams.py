#!/usr/bin/env python3
"""
Restore rl_team (real-life team) data from CSV to database
"""
import csv
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection (use service name in Docker network)
conn = psycopg2.connect(
    dbname="fantasy_cricket",
    user="cricket_admin",
    password=os.getenv("DB_PASSWORD"),
    host="fantasy_cricket_db",
    port="5432"
)
cursor = conn.cursor()

print("🔄 Restoring rl_team data from CSV...")

# Read CSV and update players
with open('acc_cleaned_players.csv', 'r') as f:
    reader = csv.DictReader(f)

    updated = 0
    not_found = 0

    for row in reader:
        player_id = row['player_id']
        rl_team = row['team']  # e.g., "ACC 1", "ACC ZAMI", "ACC Youth U17"

        # Update player's rl_team
        cursor.execute("""
            UPDATE players
            SET rl_team = %s
            WHERE id = %s
        """, (rl_team, player_id))

        if cursor.rowcount > 0:
            updated += 1
        else:
            not_found += 1
            print(f"⚠️  Player not found: {player_id}")

conn.commit()

print(f"\n✅ rl_team restoration complete!")
print(f"   Updated: {updated}")
print(f"   Not found: {not_found}")

# Verify results
cursor.execute("""
    SELECT rl_team, COUNT(*) as player_count
    FROM players
    WHERE rl_team IS NOT NULL
    GROUP BY rl_team
    ORDER BY rl_team
""")

print("\n📊 RL-Team Distribution:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]} players")

cursor.close()
conn.close()
