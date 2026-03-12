#!/usr/bin/env python3
"""
Simple Transfer Validation Test
================================
Tests transfer validation logic without running the full API.
"""

import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from database_models import League, FantasyTeam, FantasyTeamPlayer, Player
from collections import Counter
from typing import List, Optional, Tuple

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def validate_league_rules(
    league: League,
    current_players: List[FantasyTeamPlayer],
    player_to_add: Player = None,
    player_to_remove_id: str = None,
    db: Session = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a squad composition follows league rules.
    (Copied from user_team_endpoints.py for standalone testing)
    """
    # Build the proposed squad
    proposed_squad = []

    # Get all current player IDs (excluding the one being removed)
    player_ids = [
        ftp.player_id for ftp in current_players
        if not (player_to_remove_id and ftp.player_id == player_to_remove_id)
    ]

    # Load all players at once
    if player_ids and db:
        players = db.query(Player).filter(Player.id.in_(player_ids)).all()
        proposed_squad = players
    else:
        # Fallback: try to use loaded relationships
        for ftp in current_players:
            # Skip the player being removed (for transfers)
            if player_to_remove_id and ftp.player_id == player_to_remove_id:
                continue
            if ftp.player:
                proposed_squad.append(ftp.player)

    # Add the player being added
    if player_to_add:
        proposed_squad.append(player_to_add)

    # If squad is empty, no validation needed yet
    if not proposed_squad:
        return True, None

    # Count player types
    batsmen_count = 0
    bowlers_count = 0

    for player in proposed_squad:
        if player.role == 'BATSMAN':
            batsmen_count += 1
        elif player.role == 'BOWLER':
            bowlers_count += 1
        elif player.role == 'ALL_ROUNDER':
            # All-rounders count as both batsman and bowler
            batsmen_count += 1
            bowlers_count += 1

    # Count players per RL team using rl_team string field
    team_counts = Counter()
    unique_teams = set()
    for player in proposed_squad:
        if player.rl_team:
            team_counts[player.rl_team] += 1
            unique_teams.add(player.rl_team)

    # Validate max_players_per_team
    if league.max_players_per_team:
        for rl_team, count in team_counts.items():
            if count > league.max_players_per_team:
                return False, f"Cannot have more than {league.max_players_per_team} players from {rl_team}"

    # For adding a player (not finalizing), we need to check if we're moving towards the rule, not enforce it strictly
    is_adding_player = player_to_add is not None and len(proposed_squad) < league.squad_size

    # Validate min_batsmen (only enforce when squad is complete or would prevent completion)
    if league.min_batsmen:
        if not is_adding_player and batsmen_count < league.min_batsmen:
            return False, f"Team must have at least {league.min_batsmen} batsmen (currently {batsmen_count})"

    # Validate min_bowlers (only enforce when squad is complete or would prevent completion)
    if league.min_bowlers:
        if not is_adding_player and bowlers_count < league.min_bowlers:
            return False, f"Team must have at least {league.min_bowlers} bowlers (currently {bowlers_count})"

    # Validate require_from_each_team using rl_team
    # IMPORTANT: Always check this for transfers (when player_to_remove_id is set)
    # Only skip for partial squads during initial team building
    is_transfer = player_to_remove_id is not None
    should_validate_team_distribution = is_transfer or not is_adding_player

    if league.require_from_each_team and should_validate_team_distribution:
        # Get total number of distinct RL teams in the club
        if db:
            # Get all distinct team names for this club
            all_team_names_query = db.query(Player.rl_team)\
                .filter(Player.club_id == league.club_id, Player.rl_team.isnot(None))\
                .distinct()\
                .all()

            all_team_names = {t[0] for t in all_team_names_query if t[0]}
            total_teams = len(all_team_names)

            if len(unique_teams) < total_teams:
                missing_teams = all_team_names - unique_teams
                missing_teams_str = ', '.join(sorted(missing_teams))
                return False, f"Team must have players from all {total_teams} RL teams. Missing: {missing_teams_str}"

            # Check minimum players per team (if specified)
            if league.min_players_per_team:
                for rl_team, count in team_counts.items():
                    if count < league.min_players_per_team:
                        return False, f"Must have at least {league.min_players_per_team} player(s) from each RL team (only {count} from {rl_team})"

    return True, None


def run_tests():
    """Run transfer validation tests"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        print("\n" + "="*80)
        print("🧪 TESTING TRANSFER VALIDATION")
        print("="*80)

        # Get a finalized fantasy team
        team = session.query(FantasyTeam).filter_by(is_finalized=True).first()

        if not team:
            print("⚠️  No finalized teams found. Creating test scenario...")
            return

        league = team.league
        print(f"\n📋 Test Subject:")
        print(f"   Team: {team.team_name}")
        print(f"   League: {league.name}")
        print(f"   Squad Size: {len(team.players)}/{league.squad_size}")

        print(f"\n⚙️  League Rules:")
        print(f"   - Require From Each Team: {league.require_from_each_team}")
        print(f"   - Min Players Per Team: {league.min_players_per_team}")
        print(f"   - Max Players Per Team: {league.max_players_per_team}")
        print(f"   - Min Batsmen: {league.min_batsmen}")
        print(f"   - Min Bowlers: {league.min_bowlers}")

        # Show current squad
        team_distribution = {}
        for ftp in team.players:
            player = ftp.player
            if player.rl_team:
                team_distribution[player.rl_team] = team_distribution.get(player.rl_team, 0) + 1

        print(f"\n👥 Current Squad Distribution:")
        for team_name, count in sorted(team_distribution.items()):
            players = [ftp.player.name for ftp in team.players if ftp.player.rl_team == team_name]
            print(f"   - {team_name}: {count} player(s) - {', '.join(players)}")

        # TEST 1: Try to transfer out only player from a team
        print(f"\n" + "="*80)
        print("TEST 1: Transfer out only player from a team (should FAIL)")
        print("="*80)

        single_player_teams = [team_name for team_name, count in team_distribution.items() if count == 1]

        if single_player_teams:
            test_team = single_player_teams[0]
            player_out = next(ftp.player for ftp in team.players if ftp.player.rl_team == test_team)

            # Find a player from a different team
            player_in = session.query(Player).filter(
                Player.club_id == league.club_id,
                Player.rl_team != test_team,
                ~Player.id.in_([ftp.player_id for ftp in team.players])
            ).first()

            if player_in:
                print(f"   Transferring OUT: {player_out.name} (from {test_team})")
                print(f"   Transferring IN:  {player_in.name} (from {player_in.rl_team})")

                is_valid, error = validate_league_rules(
                    league=league,
                    current_players=team.players,
                    player_to_add=player_in,
                    player_to_remove_id=player_out.id,
                    db=session
                )

                if is_valid:
                    print(f"   ❌ FAIL: Transfer should have been blocked!")
                else:
                    print(f"   ✅ PASS: Transfer correctly blocked")
                    print(f"   Error: {error}")
            else:
                print(f"   ⚠️  Could not find replacement player")
        else:
            print(f"   ⚠️  No single-player teams found")

        # TEST 2: Valid same-team swap
        print(f"\n" + "="*80)
        print("TEST 2: Valid same-team transfer (should PASS)")
        print("="*80)

        if single_player_teams:
            test_team = single_player_teams[0]
            player_out = next(ftp.player for ftp in team.players if ftp.player.rl_team == test_team)

            # Find replacement from SAME team
            player_in = session.query(Player).filter(
                Player.club_id == league.club_id,
                Player.rl_team == test_team,
                ~Player.id.in_([ftp.player_id for ftp in team.players])
            ).first()

            if player_in:
                print(f"   Transferring OUT: {player_out.name} (from {test_team})")
                print(f"   Transferring IN:  {player_in.name} (from {player_in.rl_team})")

                is_valid, error = validate_league_rules(
                    league=league,
                    current_players=team.players,
                    player_to_add=player_in,
                    player_to_remove_id=player_out.id,
                    db=session
                )

                if is_valid:
                    print(f"   ✅ PASS: Transfer correctly allowed")
                else:
                    print(f"   ❌ FAIL: Valid transfer was blocked!")
                    print(f"   Error: {error}")
            else:
                print(f"   ⚠️  No replacement players from {test_team}")

        print(f"\n" + "="*80)
        print("🏁 TESTING COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    run_tests()
