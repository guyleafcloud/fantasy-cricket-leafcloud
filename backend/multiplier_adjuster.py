#!/usr/bin/env python3
"""
Multiplier Adjuster
===================
Adjusts player multipliers based on performance with a 15% weekly drift rate.
Integrates with the production fantasy points calculator.
"""

import logging
import statistics
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database_models import Player, Club
from fantasy_points_calculator import FantasyPointsCalculator

# Import centralized rules for multiplier bounds
try:
    from rules_set_1 import FANTASY_RULES
except ImportError:
    import importlib
    rules_module = importlib.import_module('rules-set-1')
    FANTASY_RULES = rules_module.FANTASY_RULES

logger = logging.getLogger(__name__)


class MultiplierAdjuster:
    """Adjusts player multipliers based on season performance"""

    def __init__(self, drift_rate: float = None):
        """
        Args:
            drift_rate: How much to move toward target each week (0.0 to 1.0)
                       If None, uses value from centralized rules (default 0.15 = 15% per week)
        """
        # Load drift rate from centralized rules if not specified
        if drift_rate is None:
            self.drift_rate = FANTASY_RULES['player_multipliers']['weekly_adjustment_max']
        else:
            self.drift_rate = drift_rate

        self.calculator = FantasyPointsCalculator()

        # Load multiplier bounds from centralized rules
        self.min_multiplier = FANTASY_RULES['player_multipliers']['min']  # 0.69
        self.max_multiplier = FANTASY_RULES['player_multipliers']['max']  # 5.0
        self.neutral_multiplier = FANTASY_RULES['player_multipliers']['neutral']  # 1.0

    def calculate_multiplier(
        self,
        player_score: float,
        min_score: float,
        median_score: float,
        max_score: float
    ) -> float:
        """
        Calculate target multiplier based on player score relative to league

        Multiplier Scale:
        - Below median (weaker players): 1.0 to 5.0 (linear scale)
        - At median: 1.0
        - Above median (stronger players): 1.0 to 0.69 (linear scale)

        This creates higher costs for star players and lower costs for weaker players.
        """
        if median_score == 0:
            return 1.0

        if player_score <= median_score:
            # Below median: interpolate from max_multiplier (min_score) to neutral (median)
            if median_score == min_score:
                return self.neutral_multiplier
            ratio = (player_score - min_score) / (median_score - min_score)
            return self.max_multiplier - (ratio * (self.max_multiplier - self.neutral_multiplier))
        else:
            # Above median: interpolate from neutral (median) to min_multiplier (max_score)
            if max_score == median_score:
                return self.neutral_multiplier
            ratio = (player_score - median_score) / (max_score - median_score)
            return self.neutral_multiplier - (ratio * (self.neutral_multiplier - self.min_multiplier))

    def calculate_player_season_points(self, player: Player, db: Session, league_id: Optional[str] = None) -> float:
        """
        Calculate total fantasy points for a player's season using actual performances

        IMPORTANT: Uses final fantasy_points (after multiplier) from PlayerPerformance records.
        This is correct because drift should be based on actual fantasy points earned,
        not base points.

        Args:
            player: Player object
            db: Database session
            league_id: Optional league ID to filter performances to specific league

        Returns:
            Total fantasy points based on season performance (after multipliers)
        """
        from database_models import PlayerPerformance

        # Sum all fantasy_points from PlayerPerformance records
        # This gives us the total points AFTER multipliers were applied
        query = db.query(
            db.func.coalesce(db.func.sum(PlayerPerformance.fantasy_points), 0.0)
        ).filter(
            PlayerPerformance.player_id == player.id
        )

        # Filter by league if specified (for league-specific multipliers)
        if league_id:
            query = query.filter(PlayerPerformance.league_id == league_id)

        total_points = query.scalar()

        return float(total_points) if total_points else 0.0

    def adjust_multipliers(
        self,
        db: Session,
        club_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Adjust multipliers for all players (or players in a specific club)

        Args:
            db: Database session
            club_id: Optional club ID to filter players
            dry_run: If True, calculate but don't save changes

        Returns:
            Dictionary with adjustment statistics
        """
        logger.info(f"🎯 Adjusting player multipliers (drift rate: {self.drift_rate:.1%})")

        # Get all players
        query = db.query(Player)
        if club_id:
            query = query.filter(Player.club_id == club_id)

        players = query.all()
        logger.info(f"   Found {len(players)} players")

        if not players:
            return {"error": "No players found"}

        # Calculate fantasy points for each player
        logger.info("   Calculating season fantasy points...")
        player_scores = []
        player_data = []

        for player in players:
            score = self.calculate_player_season_points(player, db)
            player_scores.append(score)
            player_data.append({
                'player': player,
                'score': score,
                'old_multiplier': player.multiplier
            })

        # Calculate statistics
        min_score = min(player_scores) if player_scores else 0
        max_score = max(player_scores) if player_scores else 0
        median_score = statistics.median(player_scores) if player_scores else 0
        mean_score = statistics.mean(player_scores) if player_scores else 0

        logger.info(f"   Score distribution:")
        logger.info(f"     Min: {min_score:.2f}, Median: {median_score:.2f}")
        logger.info(f"     Mean: {mean_score:.2f}, Max: {max_score:.2f}")

        # Adjust multipliers
        changes = []
        for data in player_data:
            player = data['player']
            score = data['score']
            old_multiplier = data['old_multiplier']

            # Players with 0 points get the median multiplier of 1.0
            if score == 0:
                target_multiplier = 1.0
            else:
                target_multiplier = self.calculate_multiplier(
                    score, min_score, median_score, max_score
                )

            # Apply drift: blend old multiplier with new target
            new_multiplier = old_multiplier * (1 - self.drift_rate) + target_multiplier * self.drift_rate
            new_multiplier = round(new_multiplier, 2)

            # Track change
            change = new_multiplier - old_multiplier
            if abs(change) > 0.01:  # Only track meaningful changes
                changes.append({
                    'player_name': player.name,
                    'old_multiplier': old_multiplier,
                    'target_multiplier': round(target_multiplier, 2),
                    'new_multiplier': new_multiplier,
                    'change': round(change, 2),
                    'score': score
                })

            # Update player (if not dry run)
            if not dry_run:
                player.multiplier = new_multiplier

        # Commit changes
        if not dry_run:
            db.commit()
            logger.info(f"   ✅ Updated {len(changes)} player multipliers")
        else:
            logger.info(f"   ℹ️  Dry run: would update {len(changes)} player multipliers")

        # Sort changes by magnitude
        changes.sort(key=lambda x: abs(x['change']), reverse=True)

        return {
            'total_players': len(players),
            'players_changed': len(changes),
            'score_stats': {
                'min': min_score,
                'median': median_score,
                'mean': mean_score,
                'max': max_score
            },
            'top_changes': changes[:10],  # Top 10 changes
            'drift_rate': self.drift_rate
        }

    def adjust_league_multipliers(
        self,
        db: Session,
        league_id: str,
        dry_run: bool = False
    ) -> Dict:
        """
        Adjust multipliers for a specific league based on league-specific performance.

        This calculates multipliers relative to the league's roster, ensuring
        different leagues have independent multiplier distributions.

        Args:
            db: Database session
            league_id: League ID to adjust multipliers for
            dry_run: If True, calculate but don't save changes

        Returns:
            Dictionary with adjustment statistics
        """
        from database_models import League, LeagueRoster
        from datetime import datetime

        logger.info(f"🎯 Adjusting league-specific multipliers for league {league_id}")
        logger.info(f"   Drift rate: {self.drift_rate:.1%}")

        # Get league
        league = db.query(League).filter_by(id=league_id).first()
        if not league:
            return {"error": "League not found"}

        # Get all players in this league's roster
        roster_entries = db.query(LeagueRoster).filter_by(league_id=league_id).all()
        player_ids = [entry.player_id for entry in roster_entries]

        if not player_ids:
            return {"error": "No players in league roster"}

        players = db.query(Player).filter(Player.id.in_(player_ids)).all()
        logger.info(f"   Found {len(players)} players in league roster")

        # Calculate league-specific fantasy points for each player
        logger.info("   Calculating league-specific season fantasy points...")
        player_scores = []
        player_data = []

        # Get current multipliers from league snapshot (or player table if not set)
        current_snapshot = league.multipliers_snapshot or {}

        for player in players:
            # Calculate points using ONLY this league's performances
            score = self.calculate_player_season_points(player, db, league_id=league_id)
            player_scores.append(score)

            # Get current league-specific multiplier (or fall back to player's global multiplier)
            old_multiplier = current_snapshot.get(player.id, player.multiplier)

            player_data.append({
                'player': player,
                'score': score,
                'old_multiplier': old_multiplier
            })

        # Calculate statistics for THIS LEAGUE's roster
        min_score = min(player_scores) if player_scores else 0
        max_score = max(player_scores) if player_scores else 0
        median_score = statistics.median(player_scores) if player_scores else 0
        mean_score = statistics.mean(player_scores) if player_scores else 0

        logger.info(f"   League-specific score distribution:")
        logger.info(f"     Min: {min_score:.2f}, Median: {median_score:.2f}")
        logger.info(f"     Mean: {mean_score:.2f}, Max: {max_score:.2f}")

        # Adjust multipliers
        changes = []
        new_snapshot = {}

        for data in player_data:
            player = data['player']
            score = data['score']
            old_multiplier = data['old_multiplier']

            # Players with 0 points get the median multiplier of 1.0
            if score == 0:
                target_multiplier = 1.0
            else:
                target_multiplier = self.calculate_multiplier(
                    score, min_score, median_score, max_score
                )

            # Apply drift: blend old multiplier with new target
            new_multiplier = old_multiplier * (1 - self.drift_rate) + target_multiplier * self.drift_rate
            new_multiplier = round(new_multiplier, 2)

            # Store in new snapshot
            new_snapshot[player.id] = new_multiplier

            # Track change
            change = new_multiplier - old_multiplier
            if abs(change) > 0.01:  # Only track meaningful changes
                changes.append({
                    'player_name': player.name,
                    'old_multiplier': old_multiplier,
                    'target_multiplier': round(target_multiplier, 2),
                    'new_multiplier': new_multiplier,
                    'change': round(change, 2),
                    'score': score
                })

        # Update league snapshot (if not dry run)
        if not dry_run:
            league.multipliers_snapshot = new_snapshot
            league.multipliers_frozen_at = datetime.utcnow()
            db.commit()
            logger.info(f"   ✅ Updated league multiplier snapshot with {len(new_snapshot)} players")
        else:
            logger.info(f"   ℹ️  Dry run: would update {len(changes)} multipliers in league snapshot")

        # Sort changes by magnitude
        changes.sort(key=lambda x: abs(x['change']), reverse=True)

        return {
            'league_id': league_id,
            'league_name': league.name,
            'total_players': len(players),
            'players_changed': len(changes),
            'score_stats': {
                'min': min_score,
                'median': median_score,
                'mean': mean_score,
                'max': max_score
            },
            'top_changes': changes[:10],  # Top 10 changes
            'drift_rate': self.drift_rate
        }
