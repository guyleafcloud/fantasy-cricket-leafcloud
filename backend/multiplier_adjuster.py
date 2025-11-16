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

    def calculate_player_season_points(self, player: Player) -> float:
        """
        Calculate total fantasy points for a player's season using current stats

        Returns:
            Total fantasy points based on season performance
        """
        if not player.stats:
            return 0.0

        stats = player.stats

        # Calculate points for all performances
        total_points = 0.0

        # Use aggregate season stats if available
        runs = stats.get('total_runs', 0)
        balls_faced = stats.get('total_balls_faced', 0)
        fours = stats.get('total_fours', 0)
        sixes = stats.get('total_sixes', 0)
        wickets = stats.get('total_wickets', 0)
        overs = stats.get('total_overs', 0.0)
        runs_conceded = stats.get('total_runs_conceded', 0)
        maidens = stats.get('total_maidens', 0)
        catches = stats.get('total_catches', 0)
        run_outs = stats.get('total_run_outs', 0)
        stumpings = stats.get('total_stumpings', 0)

        # Calculate total points
        result = self.calculator.calculate_total_points(
            runs=runs,
            balls_faced=balls_faced,
            fours=fours,
            sixes=sixes,
            is_out=False,  # Not relevant for season totals
            wickets=wickets,
            overs_bowled=overs,
            runs_conceded=runs_conceded,
            maidens=maidens,
            catches=catches,
            run_outs=run_outs,
            stumpings=stumpings
        )

        return result['grand_total']

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
            score = self.calculate_player_season_points(player)
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
