#!/usr/bin/env python3
"""
Match Performance Service
=========================
Service to process match scorecards and calculate fantasy points.

Workflow:
1. Scrape match scorecard
2. Match players to database
3. Calculate fantasy points for each player
4. Store Match and PlayerPerformance records
5. Update player aggregate statistics
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import Json

from database_models import Base, Match, PlayerPerformance, Player, Club, Season
from fantasy_points_calculator import FantasyPointsCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')


class MatchPerformanceService:
    """Service for processing match scorecards and calculating fantasy points"""

    def __init__(self, database_url: str = DATABASE_URL):
        """Initialize service with database connection"""
        self.database_url = database_url
        self.calculator = FantasyPointsCalculator()

        # Setup SQLAlchemy
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def normalize_player_name(self, name: str) -> str:
        """Normalize player name for matching"""
        return name.replace(' ', '').replace('-', '').lower()

    def match_player_to_database(
        self,
        player_name: str,
        club_id: str
    ) -> Optional[str]:
        """
        Match a player name from scorecard to database record

        Args:
            player_name: Player name from scorecard
            club_id: Club ID to search within

        Returns:
            Player ID if found, None otherwise
        """
        normalized_name = self.normalize_player_name(player_name)

        # Query database for matching player
        player = self.session.query(Player).filter(
            Player.club_id == club_id
        ).all()

        for p in player:
            if self.normalize_player_name(p.name) == normalized_name:
                return p.id

        return None

    def process_scorecard(
        self,
        scorecard_data: Dict,
        season_id: str,
        club_id: str
    ) -> Tuple[Optional[str], int, int]:
        """
        Process a match scorecard and store performance data

        Args:
            scorecard_data: Scorecard data from scraper
            season_id: Season ID
            club_id: Club ID

        Returns:
            Tuple of (match_id, matched_players, unmatched_players)
        """
        logger.info(f"Processing scorecard: {scorecard_data.get('match_title', 'Unknown')}")

        # Extract match info
        match_title = scorecard_data.get('match_title', '')
        match_date_str = scorecard_data.get('match_date', '')
        scorecard_url = scorecard_data.get('scorecard_url', '')

        # Parse match date
        try:
            match_date = datetime.strptime(match_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            logger.warning(f"Could not parse match date: {match_date_str}, using today")
            match_date = datetime.now()

        # Determine opponent from title
        opponent = "Unknown"
        if "vs" in match_title.lower():
            parts = match_title.split("vs")
            if len(parts) == 2:
                opponent = parts[1].strip()

        # Extract matchcentre_id and period_id from URL
        matchcentre_id = None
        period_id = None
        if scorecard_url:
            # Example URL: https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921
            if '/match/' in scorecard_url:
                match_part = scorecard_url.split('/match/')[1].split('/')[0]
                matchcentre_id = match_part
            if 'period=' in scorecard_url:
                period_id = scorecard_url.split('period=')[1].split('&')[0]

        # Check if match already exists
        existing_match = self.session.query(Match).filter(
            Match.scorecard_url == scorecard_url
        ).first()

        if existing_match:
            logger.info(f"Match already exists: {existing_match.id}")
            return existing_match.id, 0, 0

        # Create new Match record
        match = Match(
            season_id=season_id,
            club_id=club_id,
            match_date=match_date,
            opponent=opponent,
            match_title=match_title,
            matchcentre_id=matchcentre_id,
            scorecard_url=scorecard_url,
            period_id=period_id,
            raw_scorecard_data=scorecard_data,
            is_processed=False
        )

        self.session.add(match)
        self.session.flush()  # Get match.id

        # Process player performances
        performances = scorecard_data.get('player_performances', [])
        matched_count = 0
        unmatched_count = 0
        unmatched_players = []

        for perf_data in performances:
            player_name = perf_data.get('player_name', '')

            # Try to match player to database
            player_id = self.match_player_to_database(player_name, club_id)

            if not player_id:
                logger.warning(f"Could not match player: {player_name}")
                unmatched_count += 1
                unmatched_players.append(player_name)
                continue

            matched_count += 1

            # Calculate fantasy points
            points_breakdown = self.calculator.calculate_from_performance_dict(perf_data)
            fantasy_points = points_breakdown['grand_total']

            # Calculate strike rate and economy
            batting_sr = None
            if perf_data.get('balls_faced', 0) > 0:
                batting_sr = (perf_data.get('runs', 0) / perf_data.get('balls_faced')) * 100

            bowling_economy = None
            if perf_data.get('overs_bowled', 0) > 0:
                bowling_economy = perf_data.get('runs_conceded', 0) / perf_data.get('overs_bowled')

            # Create PlayerPerformance record
            performance = PlayerPerformance(
                match_id=match.id,
                player_id=player_id,
                runs=perf_data.get('runs', 0),
                balls_faced=perf_data.get('balls_faced', 0),
                fours=perf_data.get('fours', 0),
                sixes=perf_data.get('sixes', 0),
                batting_strike_rate=batting_sr,
                is_out=perf_data.get('is_out', False),
                dismissal_type=perf_data.get('dismissal_type'),
                overs_bowled=perf_data.get('overs_bowled', 0.0),
                maidens=perf_data.get('maidens', 0),
                runs_conceded=perf_data.get('runs_conceded', 0),
                wickets=perf_data.get('wickets', 0),
                bowling_economy=bowling_economy,
                catches=perf_data.get('catches', 0),
                run_outs=perf_data.get('run_outs', 0),
                stumpings=perf_data.get('stumpings', 0),
                fantasy_points=fantasy_points,
                points_breakdown=points_breakdown
            )

            self.session.add(performance)

        # Mark match as processed
        match.is_processed = True
        match.processed_at = datetime.utcnow()

        # Commit all changes
        self.session.commit()

        logger.info(f"Match processed successfully: {match.id}")
        logger.info(f"  Matched players: {matched_count}")
        logger.info(f"  Unmatched players: {unmatched_count}")

        if unmatched_players:
            logger.info(f"  Unmatched player names: {', '.join(unmatched_players[:5])}")

        return match.id, matched_count, unmatched_count

    def get_player_total_points(self, player_id: str, season_id: str = None) -> float:
        """
        Get total fantasy points for a player (optionally in a specific season)

        Args:
            player_id: Player ID
            season_id: Optional season ID to filter by

        Returns:
            Total fantasy points
        """
        query = self.session.query(PlayerPerformance).filter(
            PlayerPerformance.player_id == player_id
        )

        if season_id:
            query = query.join(Match).filter(Match.season_id == season_id)

        performances = query.all()
        total = sum(p.fantasy_points for p in performances)

        return total

    def get_top_performers(
        self,
        season_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top performing players by fantasy points in a season

        Args:
            season_id: Season ID
            limit: Number of top performers to return

        Returns:
            List of player dictionaries with total points
        """
        # Query all performances in season
        performances = self.session.query(
            PlayerPerformance.player_id,
            Player.name
        ).join(
            Match
        ).join(
            Player
        ).filter(
            Match.season_id == season_id
        ).all()

        # Aggregate points by player
        player_points = {}
        for player_id, name in performances:
            if player_id not in player_points:
                player_points[player_id] = {'player_id': player_id, 'name': name, 'total_points': 0}

            perf = self.session.query(PlayerPerformance).filter(
                PlayerPerformance.player_id == player_id
            ).first()
            if perf:
                player_points[player_id]['total_points'] += perf.fantasy_points

        # Sort by total points
        sorted_players = sorted(
            player_points.values(),
            key=lambda x: x['total_points'],
            reverse=True
        )

        return sorted_players[:limit]

    def update_player_season_stats(self, player_id: str, season_id: str):
        """
        Update a player's aggregate season statistics from all their performances

        Args:
            player_id: Player ID
            season_id: Season ID
        """
        # Get all performances for player in season
        performances = self.session.query(PlayerPerformance).join(Match).filter(
            PlayerPerformance.player_id == player_id,
            Match.season_id == season_id
        ).all()

        if not performances:
            logger.warning(f"No performances found for player {player_id} in season {season_id}")
            return

        # Aggregate statistics
        stats = {
            "matches": len(performances),
            "runs": sum(p.runs for p in performances),
            "balls_faced": sum(p.balls_faced for p in performances),
            "fours": sum(p.fours for p in performances),
            "sixes": sum(p.sixes for p in performances),
            "wickets": sum(p.wickets for p in performances),
            "overs_bowled": sum(p.overs_bowled for p in performances),
            "runs_conceded": sum(p.runs_conceded for p in performances),
            "maidens": sum(p.maidens for p in performances),
            "catches": sum(p.catches for p in performances),
            "run_outs": sum(p.run_outs for p in performances),
            "stumpings": sum(p.stumpings for p in performances),
            "total_fantasy_points": sum(p.fantasy_points for p in performances)
        }

        # Calculate averages
        if stats["balls_faced"] > 0:
            stats["batting_avg"] = stats["runs"] / stats["matches"]  # Simplified
            stats["strike_rate"] = (stats["runs"] / stats["balls_faced"]) * 100

        if stats["overs_bowled"] > 0:
            stats["bowling_avg"] = stats["runs_conceded"] / max(stats["wickets"], 1)
            stats["economy"] = stats["runs_conceded"] / stats["overs_bowled"]

        # Count milestones
        stats["fifties"] = sum(1 for p in performances if p.runs >= 50 and p.runs < 100)
        stats["hundreds"] = sum(1 for p in performances if p.runs >= 100)
        stats["five_wicket_hauls"] = sum(1 for p in performances if p.wickets >= 5)

        # Update player record
        player = self.session.query(Player).filter(Player.id == player_id).first()
        if player:
            player.stats = stats
            player.updated_at = datetime.utcnow()
            self.session.commit()
            logger.info(f"Updated season stats for player: {player.name}")

    def close(self):
        """Close database session"""
        self.session.close()


if __name__ == "__main__":
    # Example usage - this will be used in the test script
    print("Match Performance Service")
    print("=" * 70)
    print("This service processes match scorecards and calculates fantasy points.")
    print("Use test_match_performance.py to test with historical scorecards.")
    print("=" * 70)
