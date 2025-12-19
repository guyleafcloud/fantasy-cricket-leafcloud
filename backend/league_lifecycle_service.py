#!/usr/bin/env python3
"""
League Lifecycle Service
========================
Manages league state transitions: draft → active → locked → completed
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database_models import League, FantasyTeam, LeagueRoster, Player
from typing import Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)


class LeagueLifecycleService:
    """
    Manages league lifecycle and status transitions.

    Status flow:
    - draft: League being set up, rules can be edited
    - active: League confirmed, roster locked, users can create teams
    - locked: Registration closed, all teams must be finalized
    - completed: Season ended
    """

    def __init__(self, db: Session):
        self.db = db

    def confirm_league(self, league_id: str) -> Tuple[bool, str, Dict]:
        """
        Transition league from 'draft' to 'active' status.

        This:
        - Validates league configuration
        - Freezes all league rules
        - Captures INITIAL multipliers for roster players (will drift weekly)
        - Sets status to 'active'
        - Opens league for user team creation

        NOTE: multipliers_snapshot is DYNAMIC and updated weekly based on
        league-specific performance distribution.

        Returns:
            Tuple of (success, message, metadata)
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found", {}

        if league.status != "draft":
            return False, f"League is already {league.status}, cannot confirm", {}

        # Validate league configuration
        if not league.squad_size or league.squad_size < 11:
            return False, "Invalid squad size (must be >= 11)", {}

        # Check roster size
        roster_count = self.db.query(LeagueRoster).filter_by(league_id=league_id).count()

        if roster_count < league.squad_size:
            return False, f"Not enough players in roster: {roster_count} < {league.squad_size}", {}

        logger.info(f"Confirming league {league.name} ({league_id}) with {roster_count} roster players")

        # Calculate and capture multipliers for all roster players
        multipliers_snapshot = {}
        roster_entries = self.db.query(LeagueRoster).filter_by(league_id=league_id).all()

        min_mult = 5.0
        max_mult = 0.69

        for entry in roster_entries:
            player = self.db.query(Player).filter_by(id=entry.player_id).first()
            if player:
                mult = player.multiplier if player.multiplier else 1.0
                multipliers_snapshot[player.id] = round(mult, 2)
                min_mult = min(min_mult, mult)
                max_mult = max(max_mult, mult)

        # Freeze league rules (copy current → frozen_*)
        league.status = "active"
        league.confirmed_at = datetime.utcnow()
        league.frozen_squad_size = league.squad_size
        league.frozen_transfers_per_season = league.transfers_per_season
        league.frozen_min_batsmen = league.min_batsmen
        league.frozen_min_bowlers = league.min_bowlers
        league.frozen_require_wicket_keeper = league.require_wicket_keeper
        league.frozen_max_players_per_team = league.max_players_per_team
        league.frozen_require_from_each_team = league.require_from_each_team

        # Store multipliers snapshot
        league.multipliers_snapshot = multipliers_snapshot
        league.multipliers_frozen_at = datetime.utcnow()

        self.db.commit()

        metadata = {
            "roster_count": roster_count,
            "min_multiplier": round(min_mult, 2),
            "max_multiplier": round(max_mult, 2),
            "multipliers_captured": len(multipliers_snapshot),
            "frozen_rules": {
                "squad_size": league.frozen_squad_size,
                "transfers_per_season": league.frozen_transfers_per_season,
                "min_batsmen": league.frozen_min_batsmen,
                "min_bowlers": league.frozen_min_bowlers
            }
        }

        logger.info(f"✅ League {league.name} confirmed: {metadata}")

        return True, "League confirmed and rules frozen", metadata

    def lock_league(self, league_id: str) -> Tuple[bool, str]:
        """
        Transition league from 'active' to 'locked' status.

        This:
        - Prevents new team registration
        - Validates all existing teams are finalized
        - Prepares league for season start

        Returns:
            Tuple of (success, message)
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found"

        if league.status != "active":
            return False, f"League is {league.status}, not active"

        # Check all teams are finalized
        teams = self.db.query(FantasyTeam).filter_by(league_id=league_id).all()
        unfinalized_teams = [t for t in teams if not t.is_finalized]

        if unfinalized_teams:
            team_names = ", ".join([t.team_name for t in unfinalized_teams[:3]])
            return False, f"{len(unfinalized_teams)} teams not finalized: {team_names}..."

        league.status = "locked"
        league.locked_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"✅ League {league.name} locked with {len(teams)} teams")

        return True, f"League locked for play ({len(teams)} teams ready)"

    def complete_league(self, league_id: str) -> Tuple[bool, str]:
        """
        Mark league as completed (end of season).

        Returns:
            Tuple of (success, message)
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return False, "League not found"

        if league.status == "completed":
            return False, "League already completed"

        league.status = "completed"
        league.completed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"✅ League {league.name} marked as completed")

        return True, "League marked as completed"

    def get_league_status(self, league_id: str) -> Dict:
        """
        Get detailed league status and readiness information.

        Returns:
            Dict with status, counts, and readiness flags
        """
        league = self.db.query(League).filter_by(id=league_id).first()
        if not league:
            return None

        teams = self.db.query(FantasyTeam).filter_by(league_id=league_id).all()
        finalized_count = sum(1 for t in teams if t.is_finalized)
        roster_count = self.db.query(LeagueRoster).filter_by(league_id=league_id).count()

        return {
            "league_id": league.id,
            "league_name": league.name,
            "status": league.status,
            "confirmed_at": league.confirmed_at.isoformat() if league.confirmed_at else None,
            "locked_at": league.locked_at.isoformat() if league.locked_at else None,
            "completed_at": league.completed_at.isoformat() if league.completed_at else None,
            "teams_total": len(teams),
            "teams_finalized": finalized_count,
            "teams_not_finalized": len(teams) - finalized_count,
            "roster_size": roster_count,
            "squad_size": league.squad_size,
            "multipliers_captured": len(league.multipliers_snapshot) if league.multipliers_snapshot else 0,
            "can_confirm": league.status == "draft" and roster_count >= league.squad_size,
            "can_lock": league.status == "active" and finalized_count == len(teams) and len(teams) > 0,
            "can_complete": league.status == "locked",
            "validation_errors": self._get_validation_errors(league, roster_count, teams, finalized_count)
        }

    def _get_validation_errors(self, league: League, roster_count: int, teams: List, finalized_count: int) -> List[str]:
        """Get list of validation errors preventing confirmation/lock."""
        errors = []

        if league.status == "draft":
            if roster_count < league.squad_size:
                errors.append(f"Not enough roster players: {roster_count} < {league.squad_size}")

        if league.status == "active":
            if len(teams) == 0:
                errors.append("No teams have joined this league yet")
            if finalized_count < len(teams):
                errors.append(f"{len(teams) - finalized_count} teams not finalized yet")

        return errors
