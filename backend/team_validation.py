"""
Team Validation Module
=======================
Validates fantasy team composition according to league rules.
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from database_models import League, FantasyTeam, FantasyTeamPlayer, Player


def validate_team_composition(
    db: Session,
    league: League,
    fantasy_team: FantasyTeam
) -> Tuple[bool, List[str]]:
    """
    Validate that a fantasy team meets league composition requirements.

    Args:
        db: Database session
        league: League with composition rules
        fantasy_team: Fantasy team to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Get all players in the team
    team_players = (
        db.query(FantasyTeamPlayer, Player)
        .join(Player, FantasyTeamPlayer.player_id == Player.id)
        .filter(FantasyTeamPlayer.fantasy_team_id == fantasy_team.id)
        .all()
    )

    if not team_players:
        errors.append("Team has no players")
        return False, errors

    # Count by player type
    batsmen_count = 0
    bowlers_count = 0
    all_rounders_count = 0
    wicket_keepers_count = 0
    unclassified_count = 0

    for ftp, player in team_players:
        player_type = player.player_type

        if player_type == "batsman":
            batsmen_count += 1
        elif player_type == "bowler":
            bowlers_count += 1
        elif player_type == "all-rounder":
            all_rounders_count += 1
        else:
            unclassified_count += 1

        # Count wicket-keepers separately (can be any player type)
        if player.is_wicket_keeper:
            wicket_keepers_count += 1

    # Validate minimum batsmen
    if league.min_batsmen and batsmen_count < league.min_batsmen:
        errors.append(
            f"Team must have at least {league.min_batsmen} batsmen (currently has {batsmen_count})"
        )

    # Validate minimum bowlers
    if league.min_bowlers and bowlers_count < league.min_bowlers:
        errors.append(
            f"Team must have at least {league.min_bowlers} bowlers (currently has {bowlers_count})"
        )

    # Validate wicket-keeper requirement
    if league.require_wicket_keeper and wicket_keepers_count == 0:
        errors.append("Team must have at least 1 wicket-keeper")

    # Validate squad size
    total_players = len(team_players)
    if total_players != league.squad_size:
        errors.append(
            f"Team must have exactly {league.squad_size} players (currently has {total_players})"
        )

    # Validate players per team constraints (if applicable)
    if league.require_from_each_team or league.max_players_per_team:
        # Use rl_team (string field) for team distribution, consistent with user_team_endpoints
        team_distribution = {}
        for ftp, player in team_players:
            rl_team = player.rl_team
            if rl_team:
                team_distribution[rl_team] = team_distribution.get(rl_team, 0) + 1

        # Check max players per team
        if league.max_players_per_team:
            for rl_team, count in team_distribution.items():
                if count > league.max_players_per_team:
                    errors.append(
                        f"Cannot have more than {league.max_players_per_team} players from {rl_team}"
                    )
                    break

        # Check if all teams are represented (if required)
        if league.require_from_each_team:
            # Get all distinct RL team names for this club
            from sqlalchemy import func

            all_team_names_query = db.query(Player.rl_team)\
                .filter(Player.club_id == league.club_id, Player.rl_team.isnot(None))\
                .distinct()\
                .all()

            all_team_names = {t[0] for t in all_team_names_query if t[0]}
            represented_teams = set(team_distribution.keys())

            missing_teams = all_team_names - represented_teams
            if missing_teams:
                missing_teams_str = ', '.join(sorted(missing_teams))
                errors.append(
                    f"Team must have at least 1 player from each club team. Missing: {missing_teams_str}"
                )

            # Check minimum players per team (if specified)
            if league.min_players_per_team:
                for rl_team, count in team_distribution.items():
                    if count < league.min_players_per_team:
                        errors.append(
                            f"Must have at least {league.min_players_per_team} player(s) from each RL team (only {count} from {rl_team})"
                        )

    is_valid = len(errors) == 0
    return is_valid, errors


def get_team_composition_summary(
    db: Session,
    fantasy_team: FantasyTeam
) -> Dict:
    """
    Get a summary of the team's composition.

    Args:
        db: Database session
        fantasy_team: Fantasy team to summarize

    Returns:
        Dictionary with composition counts
    """
    team_players = (
        db.query(FantasyTeamPlayer, Player)
        .join(Player, FantasyTeamPlayer.player_id == Player.id)
        .filter(FantasyTeamPlayer.fantasy_team_id == fantasy_team.id)
        .all()
    )

    batsmen_count = 0
    bowlers_count = 0
    all_rounders_count = 0
    wicket_keepers_count = 0
    unclassified_count = 0

    for ftp, player in team_players:
        player_type = player.player_type

        if player_type == "batsman":
            batsmen_count += 1
        elif player_type == "bowler":
            bowlers_count += 1
        elif player_type == "all-rounder":
            all_rounders_count += 1
        else:
            unclassified_count += 1

        if player.is_wicket_keeper:
            wicket_keepers_count += 1

    return {
        "total_players": len(team_players),
        "batsmen": batsmen_count,
        "bowlers": bowlers_count,
        "all_rounders": all_rounders_count,
        "wicket_keepers": wicket_keepers_count,
        "unclassified": unclassified_count
    }
