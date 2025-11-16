#!/usr/bin/env python3
"""
Analyze and clean up player data
"""
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base, Player, Team, Club
from collections import defaultdict

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_secure_password_here@db:5432/fantasy_cricket')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Patterns to identify invalid "players"
INVALID_PATTERNS = [
    r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Dates
    r'EXTRAS:',
    r'Fall of wickets',
    r'^c\s+\w+\s+b\s+\w+',  # Dismissal notations like "c Smith b Jones"
    r'^\d+\s+CEST',
    r'^\d+\s+CET',
    r'CSV Test Player',
    r'^Team\s+\d',
    r'^\(\)',  # Empty parentheses
]

# Known opposition team names (not ACC teams)
OPPOSITION_TEAMS = [
    'Rood en Wit', 'Salland', 'Ajax', 'Quick', 'VRA', 'VOC', 'Kampong',
    'HCC', 'HBS', 'Excelsior', 'VVV', 'Qui Vive', 'Voorburg', 'Hercules',
    'Dosti', 'SV Kampong'
]

def is_invalid_player(name):
    """Check if a player name matches invalid patterns"""
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True

    # Check if it's an opposition team name
    for team_name in OPPOSITION_TEAMS:
        if team_name.lower() in name.lower():
            return True

    return False

def main():
    print("=" * 80)
    print("ANALYZING ACC PLAYER DATA")
    print("=" * 80)

    # Get ACC club
    acc_club = db.query(Club).filter_by(name='ACC').first()
    if not acc_club:
        print("ERROR: ACC club not found!")
        return

    # Get all players
    all_players = db.query(Player).filter_by(club_id=acc_club.id).all()
    print(f"\nTotal players: {len(all_players)}")

    # Analyze invalid entries
    invalid_players = []
    valid_players = []

    for player in all_players:
        if is_invalid_player(player.name):
            invalid_players.append(player)
        else:
            valid_players.append(player)

    print(f"\n{len(invalid_players)} invalid entries found:")
    print("\nSample of invalid entries:")
    for player in invalid_players[:30]:
        team = db.query(Team).filter_by(id=player.team_id).first()
        team_name = team.name if team else "Unknown"
        print(f"  [{team_name}] {player.name}")

    if len(invalid_players) > 30:
        print(f"  ... and {len(invalid_players) - 30} more")

    # Check for duplicates among valid players
    print(f"\n{len(valid_players)} potentially valid players")

    name_counts = defaultdict(list)
    for player in valid_players:
        # Normalize name for comparison (lowercase, remove spaces)
        norm_name = player.name.lower().replace(' ', '')
        name_counts[norm_name].append(player)

    duplicates = {name: players for name, players in name_counts.items() if len(players) > 1}

    if duplicates:
        print(f"\n{len(duplicates)} duplicate player names found:")
        for norm_name, players in list(duplicates.items())[:20]:
            print(f"\n  {players[0].name} ({len(players)} occurrences):")
            for p in players:
                team = db.query(Team).filter_by(id=p.team_id).first()
                team_name = team.name if team else "Unknown"
                print(f"    - [{team_name}] multiplier={p.multiplier}, type={p.player_type}")

    # Count by team after cleanup
    print("\n" + "=" * 80)
    print("DISTRIBUTION OF VALID PLAYERS BY TEAM:")
    print("=" * 80)

    valid_by_team = defaultdict(list)
    for player in valid_players:
        team = db.query(Team).filter_by(id=player.team_id).first()
        team_name = team.name if team else "Unknown"
        valid_by_team[team_name].append(player)

    for team_name, players in sorted(valid_by_team.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {team_name}: {len(players)} players")

    total_after_cleanup = len(valid_players) - len([p for players in duplicates.values() for p in players[1:]])
    print(f"\nTotal valid unique players: ~{total_after_cleanup}")

    # Ask if user wants to proceed with cleanup
    print("\n" + "=" * 80)
    print("CLEANUP OPTIONS:")
    print("=" * 80)
    print("1. Delete invalid entries (dates, 'EXTRAS', etc.)")
    print("2. Delete duplicate players (keep one, remove duplicates)")
    print("3. Export valid player list for manual review")
    print("4. Cancel")

    choice = input("\nEnter your choice (1-4): ")

    if choice == '1':
        print(f"\nDeleting {len(invalid_players)} invalid entries...")
        for player in invalid_players:
            db.delete(player)
        db.commit()
        print("✓ Invalid entries deleted")

        remaining = db.query(Player).filter_by(club_id=acc_club.id).count()
        print(f"Remaining players: {remaining}")

    elif choice == '2':
        print("\nDeleting duplicate players (keeping first occurrence)...")
        deleted_count = 0
        for players in duplicates.values():
            # Keep first, delete rest
            for player in players[1:]:
                db.delete(player)
                deleted_count += 1
        db.commit()
        print(f"✓ Deleted {deleted_count} duplicate entries")

        remaining = db.query(Player).filter_by(club_id=acc_club.id).count()
        print(f"Remaining players: {remaining}")

    elif choice == '3':
        print("\nExporting valid players to 'acc_valid_players.csv'...")
        with open('acc_valid_players.csv', 'w') as f:
            f.write("team,player_name,player_type,multiplier,player_id\n")
            for team_name, players in sorted(valid_by_team.items()):
                for player in sorted(players, key=lambda p: p.name):
                    f.write(f'{team_name},"{player.name}",{player.player_type},{player.multiplier},{player.id}\n')
        print("✓ Exported to acc_valid_players.csv")

    else:
        print("\nCleanup cancelled")

    db.close()

if __name__ == '__main__':
    main()
