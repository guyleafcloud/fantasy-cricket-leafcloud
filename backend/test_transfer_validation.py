#!/usr/bin/env python3
"""
Test Transfer Validation System
================================
Tests that transfers properly enforce league rules.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import League, FantasyTeam, FantasyTeamPlayer, Player
from user_team_endpoints import validate_league_rules

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def test_transfer_validation():
    """Test transfer validation with real database data"""
    session = Session()

    try:
        print("\n" + "="*80)
        print("🧪 TESTING TRANSFER VALIDATION")
        print("="*80)

        # Get a finalized fantasy team to test with
        team = session.query(FantasyTeam).filter_by(is_finalized=True).first()

        if not team:
            print("⚠️  No finalized teams found. Cannot test transfers.")
            print("   Create and finalize a team first, then run this test.")
            return

        league = team.league
        print(f"\n📋 Testing Team: {team.team_name}")
        print(f"   League: {league.name}")
        print(f"   Squad Size: {len(team.players)}/{league.squad_size}")
        print(f"   Transfers Used: {team.transfers_used}")

        # Display league rules
        print(f"\n⚙️  League Rules:")
        print(f"   - Min Batsmen: {league.min_batsmen}")
        print(f"   - Min Bowlers: {league.min_bowlers}")
        print(f"   - Max Players Per Team: {league.max_players_per_team}")
        print(f"   - Require From Each Team: {league.require_from_each_team}")
        print(f"   - Min Players Per Team: {league.min_players_per_team}")

        # Display current team composition
        print(f"\n👥 Current Squad:")
        team_distribution = {}
        role_distribution = {}

        for ftp in team.players:
            player = ftp.player
            if player.rl_team:
                team_distribution[player.rl_team] = team_distribution.get(player.rl_team, 0) + 1
            if player.role:
                role_distribution[player.role] = role_distribution.get(player.role, 0) + 1

            print(f"   - {player.name:30} | {player.rl_team or 'No Team':15} | {player.role or 'Unknown'}")

        print(f"\n📊 Team Distribution:")
        for team_name, count in sorted(team_distribution.items()):
            print(f"   - {team_name}: {count} player(s)")

        print(f"\n📊 Role Distribution:")
        for role, count in sorted(role_distribution.items()):
            print(f"   - {role}: {count} player(s)")

        # Find a player who is the ONLY one from their team
        single_player_teams = [
            team_name for team_name, count in team_distribution.items()
            if count == 1
        ]

        if not single_player_teams:
            print(f"\n⚠️  No single-player teams found. Cannot test 'only player from team' scenario.")
            print("   All teams have 2+ players, so transfers should be flexible.")
        else:
            print(f"\n🎯 Testing Scenario: Transfer out only player from a team")
            print(f"   Teams with only 1 player: {', '.join(single_player_teams)}")

            # Find the player from first single-player team
            test_team_name = single_player_teams[0]
            player_to_remove = None

            for ftp in team.players:
                if ftp.player.rl_team == test_team_name:
                    player_to_remove = ftp.player
                    break

            if player_to_remove:
                print(f"\n   Player to remove: {player_to_remove.name} (from {test_team_name})")

                # Find a replacement player from a DIFFERENT team
                available_players = session.query(Player).filter(
                    Player.club_id == league.club_id,
                    Player.rl_team != test_team_name,
                    ~Player.id.in_([ftp.player_id for ftp in team.players])
                ).limit(5).all()

                if available_players:
                    player_to_add = available_players[0]
                    print(f"   Player to add: {player_to_add.name} (from {player_to_add.rl_team})")

                    # Test validation
                    print(f"\n   🔍 Running validation...")
                    is_valid, error_message = validate_league_rules(
                        league=league,
                        current_players=team.players,
                        player_to_add=player_to_add,
                        player_to_remove_id=player_to_remove.id,
                        db=session
                    )

                    if is_valid:
                        print(f"   ❌ FAIL: Validation should have blocked this transfer!")
                        print(f"      Removing {player_to_remove.name} leaves {test_team_name} with 0 players")
                    else:
                        print(f"   ✅ PASS: Transfer correctly blocked")
                        print(f"      Error: {error_message}")
                else:
                    print(f"   ⚠️  No available players found for testing")

        # Test valid transfer (same team swap)
        if single_player_teams:
            print(f"\n🎯 Testing Scenario: Valid same-team transfer")
            test_team_name = single_player_teams[0]
            player_to_remove = None

            for ftp in team.players:
                if ftp.player.rl_team == test_team_name:
                    player_to_remove = ftp.player
                    break

            if player_to_remove:
                # Find replacement from SAME team
                available_same_team = session.query(Player).filter(
                    Player.club_id == league.club_id,
                    Player.rl_team == test_team_name,
                    ~Player.id.in_([ftp.player_id for ftp in team.players])
                ).limit(5).all()

                if available_same_team:
                    player_to_add = available_same_team[0]
                    print(f"   Player to remove: {player_to_remove.name} (from {test_team_name})")
                    print(f"   Player to add: {player_to_add.name} (from {player_to_add.rl_team})")

                    print(f"\n   🔍 Running validation...")
                    is_valid, error_message = validate_league_rules(
                        league=league,
                        current_players=team.players,
                        player_to_add=player_to_add,
                        player_to_remove_id=player_to_remove.id,
                        db=session
                    )

                    if is_valid:
                        print(f"   ✅ PASS: Valid transfer allowed")
                    else:
                        print(f"   ❌ FAIL: Valid transfer was blocked!")
                        print(f"      Error: {error_message}")
                else:
                    print(f"   ⚠️  No available players from {test_team_name} for testing")

        # Test exceeding max_players_per_team
        print(f"\n🎯 Testing Scenario: Exceed max players per team")

        # Find a team with fewer than max_players_per_team
        teams_with_room = [
            team_name for team_name, count in team_distribution.items()
            if count < league.max_players_per_team
        ]

        if teams_with_room:
            test_team_name = teams_with_room[0]
            current_count = team_distribution[test_team_name]
            print(f"   Team with room: {test_team_name} ({current_count}/{league.max_players_per_team})")

            # We need to add enough players to exceed the limit
            # For testing, we'll simulate adding players until we exceed
            simulated_squad = list(team.players)

            # Find available players from this team
            available_from_team = session.query(Player).filter(
                Player.club_id == league.club_id,
                Player.rl_team == test_team_name,
                ~Player.id.in_([ftp.player_id for ftp in team.players])
            ).limit(10).all()

            if len(available_from_team) > 0:
                # Try to add one more player than allowed from this team
                needed = league.max_players_per_team - current_count + 1
                print(f"   Need to add {needed} more players from {test_team_name} to exceed limit")

                if len(available_from_team) >= needed:
                    # Simulate adding players
                    for i in range(needed):
                        print(f"   Simulating add: {available_from_team[i].name}")

                    print(f"   This would give {test_team_name}: {current_count + needed} players (exceeds {league.max_players_per_team})")
                    print(f"   ⚠️  Cannot test with current validation function (needs simulated squad)")
                else:
                    print(f"   ⚠️  Not enough available players from {test_team_name}")
        else:
            print(f"   ⚠️  All teams are at max capacity")

        print("\n" + "="*80)
        print("🏁 TESTING COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    test_transfer_validation()
