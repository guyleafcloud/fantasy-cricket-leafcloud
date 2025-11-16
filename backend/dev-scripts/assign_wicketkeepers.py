#!/usr/bin/env python3
"""
Assign Wicket-Keepers to Teams
================================
Assigns one batsman from each team to be a wicket-keeper.
This ensures every team has at least one wicket-keeper for league validation.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Player, Team

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fantasy_cricket')

def assign_wicketkeepers():
    """
    For each team, find one batsman and mark them as a wicket-keeper.
    Prefers batsmen who have better stats or are more established players.
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get all teams
        teams = session.query(Team).all()
        print(f"Found {len(teams)} teams\n")

        total_assigned = 0

        for team in teams:
            print(f"Processing {team.name} (level: {team.level})...")

            # Check if team already has a wicket-keeper
            existing_wk = session.query(Player).filter(
                Player.team_id == team.id,
                Player.is_wicket_keeper == True
            ).first()

            if existing_wk:
                print(f"  ✓ Already has wicket-keeper: {existing_wk.name}")
                continue

            # Find batsmen in this team (ordered by multiplier - lower is better)
            batsmen = session.query(Player).filter(
                Player.team_id == team.id,
                Player.player_type == 'batsman'
            ).order_by(Player.multiplier.asc()).all()

            if not batsmen:
                print(f"  ⚠ No batsmen found in this team, checking all players...")
                # If no batsmen, try to find any player
                all_players = session.query(Player).filter(
                    Player.team_id == team.id
                ).order_by(Player.multiplier.asc()).all()

                if not all_players:
                    print(f"  ✗ No players found in this team at all!")
                    continue

                # Pick the first player (best multiplier)
                player_to_assign = all_players[0]
                print(f"  → Assigning {player_to_assign.name} ({player_to_assign.player_type or 'unknown type'}) as wicket-keeper")
            else:
                # Pick the first batsman (best multiplier)
                player_to_assign = batsmen[0]
                print(f"  → Assigning {player_to_assign.name} (batsman) as wicket-keeper")

            # Assign as wicket-keeper
            player_to_assign.is_wicket_keeper = True
            total_assigned += 1

        # Commit all changes
        session.commit()
        print(f"\n{'='*60}")
        print(f"✓ Successfully assigned {total_assigned} wicket-keepers")
        print(f"{'='*60}")

    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    print("="*60)
    print("ASSIGN WICKET-KEEPERS TO TEAMS")
    print("="*60)
    print()
    assign_wicketkeepers()
