#!/usr/bin/env python3
"""
Clean up database by removing all non-ACC players
Only keep players from the 10 ACC teams
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base, Player, Team, Club

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_secure_password_here@localhost:5432/fantasy_cricket')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# The 10 valid ACC team IDs
VALID_ACC_TEAM_IDS = [
    'dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e',  # ACC 1
    '413865ef-caa0-467d-a1fe-e022abc360a0',  # ACC 2
    'ecb3b816-3837-41e1-a63c-9038caf15027',  # ACC 3
    '36b9f713-1009-459b-859c-26fa4a23c4d1',  # ACC 4
    '16a5038c-00a0-44b1-bc51-d3af67510d13',  # ACC 5
    'eea4736e-3222-403b-ac06-f4484e3174c3',  # ACC 6
    '25f47fed-cad9-47ae-b8f3-4970af5d3b35',  # U13
    '3cf39d67-48bf-4f7c-a535-7d9cb780997b',  # U15
    'b3aaa883-477d-452b-8be8-49d91b0bd993',  # U17
    '4dd5536e-a838-4bcf-9ddd-c7178894129a',  # ZAMI 1
]

def main():
    print("=" * 80)
    print("CLEANING UP NON-ACC PLAYERS FROM DATABASE")
    print("=" * 80)

    # Get ACC club
    acc_club = db.query(Club).filter_by(name='ACC').first()
    if not acc_club:
        print("ERROR: ACC club not found in database!")
        return

    print(f"\nACC Club ID: {acc_club.id}")
    print(f"ACC Club Name: {acc_club.full_name}")

    # Get all ACC teams
    all_acc_teams = db.query(Team).filter_by(club_id=acc_club.id).all()
    print(f"\n{len(all_acc_teams)} teams found in ACC club:")
    for team in all_acc_teams:
        valid = "✓ VALID" if team.id in VALID_ACC_TEAM_IDS else "✗ INVALID"
        print(f"  {valid} - {team.name} (ID: {team.id})")

    # Get all players
    total_players = db.query(Player).filter_by(club_id=acc_club.id).count()
    print(f"\n{total_players} total players in ACC club before cleanup")

    # Get players with valid team IDs
    valid_players = db.query(Player).filter(
        Player.club_id == acc_club.id,
        Player.team_id.in_(VALID_ACC_TEAM_IDS)
    ).all()
    print(f"{len(valid_players)} players belong to valid ACC teams")

    # Get players with invalid team IDs (opposition players)
    invalid_players = db.query(Player).filter(
        Player.club_id == acc_club.id,
        ~Player.team_id.in_(VALID_ACC_TEAM_IDS)
    ).all()

    print(f"\n{len(invalid_players)} opposition players to be removed:")

    if len(invalid_players) > 0:
        # Group by team for display
        from collections import defaultdict
        players_by_team = defaultdict(list)

        for player in invalid_players:
            team = db.query(Team).filter_by(id=player.team_id).first()
            team_name = team.name if team else "Unknown Team"
            players_by_team[team_name].append(player.name)

        for team_name, player_names in sorted(players_by_team.items()):
            print(f"\n  {team_name} ({len(player_names)} players):")
            for name in sorted(player_names)[:10]:  # Show first 10
                print(f"    - {name}")
            if len(player_names) > 10:
                print(f"    ... and {len(player_names) - 10} more")

        print(f"\n{'=' * 80}")
        response = input(f"\nDo you want to DELETE these {len(invalid_players)} opposition players? (yes/no): ")

        if response.lower() == 'yes':
            print("\nDeleting opposition players...")
            for player in invalid_players:
                db.delete(player)

            db.commit()
            print(f"✓ Successfully deleted {len(invalid_players)} opposition players")

            # Verify
            remaining = db.query(Player).filter_by(club_id=acc_club.id).count()
            print(f"\n{remaining} players remaining in ACC club")

            # Show breakdown by team
            print("\nPlayers per team:")
            for team in all_acc_teams:
                if team.id in VALID_ACC_TEAM_IDS:
                    count = db.query(Player).filter_by(team_id=team.id).count()
                    print(f"  {team.name}: {count} players")
        else:
            print("\nCleanup cancelled - no players deleted")
    else:
        print("\n✓ No opposition players found - database is clean!")

    db.close()
    print(f"\n{'=' * 80}")
    print("CLEANUP COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
