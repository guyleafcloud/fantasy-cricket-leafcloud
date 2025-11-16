#!/usr/bin/env python3
"""
Update Player Team Assignments
===============================
Reads the acc_cleaned_players.csv file and updates all players
with their correct team_id based on the team name in the CSV.
"""

import csv
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')
ACC_CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276'


def update_player_teams(csv_file='acc_cleaned_players.csv'):
    """Update players with their team assignments"""

    print("\n" + "=" * 70)
    print("🏏 UPDATING PLAYER TEAM ASSIGNMENTS")
    print("=" * 70)
    print(f"CSV File: {csv_file}")
    print(f"Club ID: {ACC_CLUB_ID}")
    print()

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Get all teams for ACC club
        cursor.execute("""
            SELECT id, name
            FROM teams
            WHERE club_id = %s
        """, (ACC_CLUB_ID,))

        teams = {row[1]: row[0] for row in cursor.fetchall()}

        if not teams:
            print("❌ No teams found for ACC club!")
            print("   Please create teams first using season_setup_service.py")
            return

        print(f"✅ Found {len(teams)} teams:")
        for team_name in sorted(teams.keys()):
            print(f"   - {team_name}")
        print()

        # Read CSV and build update list
        print("📖 Reading player data from CSV...")
        updates = []

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team_name = row['team']
                player_id = row['player_id']
                player_name = row['player_name']

                if team_name in teams:
                    team_id = teams[team_name]
                    updates.append((team_id, player_id, player_name, team_name))
                else:
                    print(f"⚠️  Warning: Team '{team_name}' not found for player {player_name}")

        print(f"✅ Prepared {len(updates)} player updates")
        print()

        # Update players
        print("💾 Updating players in database...")
        updated_count = 0
        not_found_count = 0

        for team_id, player_id, player_name, team_name in updates:
            cursor.execute("""
                UPDATE players
                SET team_id = %s, updated_at = NOW()
                WHERE id = %s AND club_id = %s
            """, (team_id, player_id, ACC_CLUB_ID))

            if cursor.rowcount > 0:
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"   Updated {updated_count}/{len(updates)} players...")
            else:
                not_found_count += 1
                print(f"   ⚠️  Player not found: {player_name} (ID: {player_id})")

        # Commit changes
        conn.commit()

        print()
        print("=" * 70)
        print("✅ UPDATE COMPLETE")
        print("=" * 70)
        print(f"   Updated: {updated_count} players")
        print(f"   Not found: {not_found_count} players")
        print()

        # Verify by showing sample of each team
        print("📊 Sample players per team:")
        for team_name, team_id in sorted(teams.items()):
            cursor.execute("""
                SELECT name, player_type
                FROM players
                WHERE team_id = %s
                ORDER BY name
                LIMIT 3
            """, (team_id,))

            players = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) FROM players WHERE team_id = %s", (team_id,))
            total = cursor.fetchone()[0]

            print(f"\n   {team_name} ({total} players):")
            for player_name, player_type in players:
                print(f"      - {player_name} ({player_type})")

        print()
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"❌ ERROR: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'acc_cleaned_players.csv'
    update_player_teams(csv_file)
