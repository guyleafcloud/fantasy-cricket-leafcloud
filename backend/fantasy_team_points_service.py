#!/usr/bin/env python3
"""
Fantasy Team Points Service
============================
Service to calculate and update fantasy team points based on player performances.

This service is called after match processing to update leaderboards.
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database_models import (
    FantasyTeam, FantasyTeamPlayer, Player,
    PlayerPerformance, League
)

logger = logging.getLogger(__name__)


class FantasyTeamPointsService:
    """Service for calculating and updating fantasy team points"""

    def __init__(self):
        pass

    def calculate_player_points_for_team(
        self,
        player_id: str,
        is_captain: bool,
        is_vice_captain: bool,
        league_id: str,
        db: Session
    ) -> float:
        """
        Calculate total fantasy points for a player in a team using league-specific multipliers

        Args:
            player_id: Player ID
            is_captain: Whether player is captain (2x multiplier)
            is_vice_captain: Whether player is vice-captain (1.5x multiplier)
            league_id: League ID (for league-specific multipliers)
            db: Database session

        Returns:
            Total points for this player (after league multiplier and captain/VC bonus)
        """
        # Get league to access multipliers snapshot
        league = db.query(League).filter(League.id == league_id).first()
        if not league:
            logger.warning(f"League {league_id} not found, using global multipliers")
            # Fall back to using stored fantasy_points (global multiplier)
            total = db.query(
                func.coalesce(func.sum(PlayerPerformance.fantasy_points), 0.0)
            ).filter(
                PlayerPerformance.player_id == player_id
            ).scalar()
            base_points = float(total) if total else 0.0
        else:
            # Get league-specific multiplier for this player
            multipliers_snapshot = league.multipliers_snapshot or {}
            league_multiplier = multipliers_snapshot.get(player_id)

            if league_multiplier is None:
                # Player not in league's roster, shouldn't happen but fallback to global
                logger.warning(f"Player {player_id} not in league {league_id} multiplier snapshot")
                player = db.query(Player).filter(Player.id == player_id).first()
                league_multiplier = player.multiplier if player else 1.0

            # Get all performances for this player
            performances = db.query(PlayerPerformance).filter(
                PlayerPerformance.player_id == player_id
            ).all()

            # Recalculate points using league-specific multiplier
            base_points = 0.0
            for perf in performances:
                # Use base_fantasy_points (before multiplier) and apply league's multiplier
                if perf.base_fantasy_points is not None:
                    base_points += perf.base_fantasy_points * league_multiplier
                else:
                    # Fallback: if base_fantasy_points is missing, use stored fantasy_points
                    base_points += (perf.fantasy_points or 0.0)

        # Apply captain/VC multiplier
        captain_mult = 1.0
        if is_captain:
            captain_mult = 2.0
        elif is_vice_captain:
            captain_mult = 1.5

        return base_points * captain_mult

    def calculate_team_total_points(
        self,
        fantasy_team_id: str,
        db: Session
    ) -> Dict:
        """
        Calculate total points for a fantasy team using league-specific multipliers

        Args:
            fantasy_team_id: Fantasy team ID
            db: Database session

        Returns:
            Dictionary with total_points and breakdown by player
        """
        # Get the team to access its league_id
        team = db.query(FantasyTeam).filter(FantasyTeam.id == fantasy_team_id).first()
        if not team:
            logger.error(f"Fantasy team {fantasy_team_id} not found")
            return {
                'total_points': 0.0,
                'player_breakdown': []
            }

        league_id = team.league_id

        # Get all players in the team
        team_players = db.query(FantasyTeamPlayer).filter(
            FantasyTeamPlayer.fantasy_team_id == fantasy_team_id
        ).all()

        if not team_players:
            return {
                'total_points': 0.0,
                'player_breakdown': []
            }

        total_points = 0.0
        breakdown = []

        for ftp in team_players:
            player = db.query(Player).filter(Player.id == ftp.player_id).first()
            if not player:
                continue

            player_points = self.calculate_player_points_for_team(
                ftp.player_id,
                ftp.is_captain,
                ftp.is_vice_captain,
                league_id,
                db
            )

            total_points += player_points

            breakdown.append({
                'player_id': player.id,
                'player_name': player.name,
                'points': player_points,
                'is_captain': ftp.is_captain,
                'is_vice_captain': ftp.is_vice_captain,
                'is_wicket_keeper': ftp.is_wicket_keeper
            })

        return {
            'total_points': total_points,
            'player_breakdown': breakdown
        }

    def update_team_points(
        self,
        fantasy_team_id: str,
        db: Session
    ) -> bool:
        """
        Update fantasy team points in database

        Args:
            fantasy_team_id: Fantasy team ID
            db: Database session

        Returns:
            True if updated successfully
        """
        try:
            result = self.calculate_team_total_points(fantasy_team_id, db)

            # Update team record
            team = db.query(FantasyTeam).filter(
                FantasyTeam.id == fantasy_team_id
            ).first()

            if not team:
                logger.error(f"Team not found: {fantasy_team_id}")
                return False

            old_points = team.total_points or 0
            new_points = result['total_points']

            team.total_points = new_points
            db.commit()

            logger.info(
                f"Updated team '{team.team_name}': "
                f"{old_points:.2f} → {new_points:.2f} pts"
            )

            return True

        except Exception as e:
            logger.error(f"Error updating team points: {e}")
            db.rollback()
            return False

    def update_league_leaderboard(
        self,
        league_id: str,
        db: Session
    ) -> Dict:
        """
        Update all team points in a league and recalculate ranks

        Args:
            league_id: League ID
            db: Database session

        Returns:
            Dictionary with update statistics
        """
        logger.info(f"Updating leaderboard for league: {league_id}")

        try:
            # Get all teams in the league
            teams = db.query(FantasyTeam).filter(
                FantasyTeam.league_id == league_id
            ).all()

            if not teams:
                logger.warning(f"No teams found in league {league_id}")
                return {
                    'teams_updated': 0,
                    'error': 'No teams in league'
                }

            # Update points for each team
            team_results = []

            for team in teams:
                result = self.calculate_team_total_points(team.id, db)
                team.total_points = result['total_points']

                team_results.append({
                    'team_id': team.id,
                    'team_name': team.team_name,
                    'points': result['total_points']
                })

            # Sort by points to assign ranks
            team_results.sort(key=lambda x: x['points'], reverse=True)

            for rank, team_result in enumerate(team_results, start=1):
                team = db.query(FantasyTeam).filter(
                    FantasyTeam.id == team_result['team_id']
                ).first()
                team.rank = rank

            db.commit()

            logger.info(f"Updated {len(teams)} teams in league {league_id}")

            return {
                'teams_updated': len(teams),
                'leaderboard': team_results
            }

        except Exception as e:
            logger.error(f"Error updating league leaderboard: {e}")
            db.rollback()
            return {
                'teams_updated': 0,
                'error': str(e)
            }

    def update_all_leagues(self, db: Session) -> Dict:
        """
        Update points and ranks for all active leagues

        Args:
            db: Database session

        Returns:
            Dictionary with update statistics
        """
        logger.info("Updating all league leaderboards")

        leagues = db.query(League).all()

        results = []

        for league in leagues:
            result = self.update_league_leaderboard(league.id, db)
            results.append({
                'league_id': league.id,
                'league_name': league.name,
                **result
            })

        total_teams = sum(r.get('teams_updated', 0) for r in results)

        logger.info(f"Updated {total_teams} teams across {len(leagues)} leagues")

        return {
            'leagues_processed': len(leagues),
            'total_teams_updated': total_teams,
            'results': results
        }


if __name__ == "__main__":
    # Example usage
    from database import SessionLocal

    db = SessionLocal()
    service = FantasyTeamPointsService()

    print("="*70)
    print("FANTASY TEAM POINTS SERVICE")
    print("="*70)

    result = service.update_all_leagues(db)

    print(f"\nProcessed {result['leagues_processed']} leagues")
    print(f"Updated {result['total_teams_updated']} teams")

    for league_result in result['results']:
        print(f"\nLeague: {league_result['league_name']}")
        print(f"  Teams updated: {league_result.get('teams_updated', 0)}")

        if 'leaderboard' in league_result:
            print("  Leaderboard:")
            for i, team in enumerate(league_result['leaderboard'][:5], 1):
                print(f"    {i}. {team['team_name']:30s} - {team['points']:.2f} pts")

    db.close()
