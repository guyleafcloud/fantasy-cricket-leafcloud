"""
Multiplier Calculator Service
==============================
Calculates player multipliers based on previous season fantasy points.

Median player(s) get 1.0 multiplier, with others scaled relative to their
distance from the median.
"""

import statistics
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Multiplier constants
MIN_MULTIPLIER = 0.69  # Best performers (above median)
MAX_MULTIPLIER = 5.0   # Weakest performers (below median)
NEUTRAL_MULTIPLIER = 1.0  # Median performers


def calculate_multiplier(
    player_score: float,
    min_score: float,
    median_score: float,
    max_score: float
) -> float:
    """
    Calculate multiplier based on player's score relative to median.

    Formula:
    - Below median (weaker): Linear scale from MAX_MULTIPLIER (at min) to NEUTRAL (at median)
    - At median: NEUTRAL_MULTIPLIER (1.0)
    - Above median (stronger): Linear scale from NEUTRAL (at median) to MIN_MULTIPLIER (at max)

    Args:
        player_score: Player's fantasy points from previous season
        min_score: Minimum score in the roster
        median_score: Median score in the roster (baseline for 1.0)
        max_score: Maximum score in the roster

    Returns:
        Calculated multiplier (0.69 - 5.0)
    """
    # Edge case: if median is 0 or invalid data
    if median_score == 0:
        return NEUTRAL_MULTIPLIER

    if player_score <= median_score:
        # Below median: scale from MAX_MULTIPLIER down to NEUTRAL
        if median_score == min_score:
            return NEUTRAL_MULTIPLIER

        ratio = (player_score - min_score) / (median_score - min_score)
        return MAX_MULTIPLIER - (ratio * (MAX_MULTIPLIER - NEUTRAL_MULTIPLIER))
    else:
        # Above median: scale from NEUTRAL down to MIN_MULTIPLIER
        if max_score == median_score:
            return NEUTRAL_MULTIPLIER

        ratio = (player_score - median_score) / (max_score - median_score)
        return NEUTRAL_MULTIPLIER - (ratio * (NEUTRAL_MULTIPLIER - MIN_MULTIPLIER))


def calculate_roster_multipliers(
    db: Session,
    active_player_ids: List[str],
    scrape_missing: bool = True
) -> Tuple[Dict[str, float], Dict[str, any]]:
    """
    Calculate multipliers for all active roster players based on previous season performance.

    Workflow:
    1. Get prev_season_fantasy_points for each player
    2. If missing, calculate from previous season matches
    3. If still missing and scrape_missing=True, scrape from KNCB
    4. Players with no data get neutral 1.0 multiplier
    5. Calculate median from players WITH data only
    6. Generate multipliers relative to median

    Args:
        db: Database session
        active_player_ids: List of player IDs in the active roster
        scrape_missing: Whether to scrape KNCB for missing data (default: True)

    Returns:
        Tuple of:
        - Dict[player_id, multiplier]: Calculated multipliers
        - Dict with calculation metadata (median, min, max, counts, etc.)
    """
    from database_models import Player

    logger.info(f"Calculating multipliers for {len(active_player_ids)} active roster players")

    # Get all active players
    players = db.query(Player).filter(Player.id.in_(active_player_ids)).all()

    if not players:
        logger.warning("No players found for multiplier calculation")
        return {}, {"error": "No players found"}

    # Step 1 & 2: Get or calculate previous season points
    player_scores = {}  # player_id -> prev_season_fantasy_points
    players_with_data = []
    players_without_data = []

    for player in players:
        if player.prev_season_fantasy_points is not None and player.prev_season_fantasy_points > 0:
            # Already have data
            player_scores[player.id] = player.prev_season_fantasy_points
            players_with_data.append(player)
            logger.debug(f"Player {player.name}: Using stored prev_season_fantasy_points = {player.prev_season_fantasy_points}")
        else:
            # Try to calculate from previous season matches
            prev_points = _calculate_from_previous_season_matches(db, player)

            if prev_points is not None and prev_points > 0:
                player_scores[player.id] = prev_points
                players_with_data.append(player)
                # Store for future use
                player.prev_season_fantasy_points = prev_points
                logger.info(f"Player {player.name}: Calculated from matches = {prev_points}")
            else:
                # No data available yet
                players_without_data.append(player)
                logger.debug(f"Player {player.name}: No previous season data found")

    # Step 3: Scrape KNCB for missing data if enabled
    if scrape_missing and players_without_data:
        logger.info(f"Scraping KNCB for {len(players_without_data)} players with missing data")
        scraped_count = 0

        for player in players_without_data:
            try:
                scraped_points = _scrape_player_prev_season_kncb(db, player)

                if scraped_points is not None and scraped_points > 0:
                    player_scores[player.id] = scraped_points
                    players_with_data.append(player)
                    # Store for future use
                    player.prev_season_fantasy_points = scraped_points
                    scraped_count += 1
                    logger.info(f"Player {player.name}: Scraped from KNCB = {scraped_points}")
            except Exception as e:
                logger.warning(f"Failed to scrape data for {player.name}: {e}")

        # Update players_without_data list
        players_without_data = [p for p in players_without_data if p.id not in player_scores]
        logger.info(f"Successfully scraped {scraped_count} players from KNCB")

    # Step 4: Calculate statistics (excluding players without data)
    if not players_with_data:
        logger.warning("No players have previous season data - all will get neutral multiplier")
        # Everyone gets neutral multiplier
        return {p.id: NEUTRAL_MULTIPLIER for p in players}, {
            "total_players": len(players),
            "players_with_data": 0,
            "players_without_data": len(players),
            "median_score": 0,
            "min_score": 0,
            "max_score": 0,
            "min_multiplier": NEUTRAL_MULTIPLIER,
            "max_multiplier": NEUTRAL_MULTIPLIER
        }

    # Calculate distribution stats
    scores_list = list(player_scores.values())
    min_score = min(scores_list)
    max_score = max(scores_list)
    median_score = statistics.median(scores_list)

    logger.info(f"Score distribution: min={min_score:.2f}, median={median_score:.2f}, max={max_score:.2f}")

    # Step 5: Calculate multipliers
    multipliers = {}

    for player in players:
        if player.id in player_scores:
            # Player has data - calculate multiplier
            score = player_scores[player.id]
            mult = calculate_multiplier(score, min_score, median_score, max_score)
            multipliers[player.id] = round(mult, 2)
            logger.debug(f"Player {player.name}: score={score:.2f} -> multiplier={mult:.2f}")
        else:
            # Player has no data - neutral multiplier
            multipliers[player.id] = NEUTRAL_MULTIPLIER
            logger.debug(f"Player {player.name}: No data -> neutral multiplier 1.0")

    # Commit any changes to prev_season_fantasy_points
    db.commit()

    # Calculate actual multiplier range
    calculated_multipliers = [m for pid, m in multipliers.items() if pid in player_scores]
    actual_min_mult = min(calculated_multipliers) if calculated_multipliers else NEUTRAL_MULTIPLIER
    actual_max_mult = max(calculated_multipliers) if calculated_multipliers else NEUTRAL_MULTIPLIER

    metadata = {
        "total_players": len(players),
        "players_with_data": len(players_with_data),
        "players_without_data": len(players_without_data),
        "median_score": round(median_score, 2),
        "min_score": round(min_score, 2),
        "max_score": round(max_score, 2),
        "min_multiplier": round(actual_min_mult, 2),
        "max_multiplier": round(actual_max_mult, 2),
        "players_at_median": len([s for s in scores_list if abs(s - median_score) < 0.01])
    }

    logger.info(f"Multiplier calculation complete: {metadata}")

    return multipliers, metadata


def _calculate_from_previous_season_matches(db: Session, player) -> Optional[float]:
    """
    Calculate total fantasy points from previous season's match performances.

    This looks for matches from the previous year in the database.

    Args:
        db: Database session
        player: Player object

    Returns:
        Total fantasy points from previous season, or None if no data
    """
    # TODO: Implement when we have match history in database
    # For now, return None to indicate no historical match data

    # Example implementation:
    # from database_models import Match, PlayerPerformance
    # from datetime import datetime
    #
    # current_year = datetime.now().year
    # prev_year = current_year - 1
    #
    # performances = db.query(PlayerPerformance).join(Match).filter(
    #     PlayerPerformance.player_id == player.id,
    #     Match.date >= f"{prev_year}-01-01",
    #     Match.date < f"{current_year}-01-01"
    # ).all()
    #
    # if performances:
    #     return sum(p.fantasy_points for p in performances)

    return None


def _scrape_player_prev_season_kncb(db: Session, player) -> Optional[float]:
    """
    Scrape player's previous season data from KNCB website and calculate fantasy points.

    This is slow and should only be called when data is not available in the database.

    Args:
        db: Database session
        player: Player object

    Returns:
        Total fantasy points from previous season scraped from KNCB, or None if unavailable
    """
    import asyncio
    from datetime import datetime
    from kncb_html_scraper import KNCBMatchCentreScraper
    from scorecard_player_matcher import ScorecardPlayerMatcher

    try:
        # Import fantasy points calculator
        try:
            from rules_set_1 import calculate_total_fantasy_points
        except ImportError:
            import importlib
            rules_module = importlib.import_module('rules-set-1')
            calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

        logger.info(f"Scraping KNCB for {player.name}'s previous season performance...")

        # Determine previous season year
        current_year = datetime.now().year
        prev_season_year = current_year - 1

        # Get club name
        club_name = player.club.name if player.club else "ACC"

        # Calculate date range for previous season (e.g., Jan 1 - Dec 31, 2024)
        # Cricket season is roughly April to September, but we'll scrape full year to be safe
        days_back = 365  # Full year

        # Run async scraping
        async def scrape_player_season():
            scraper = KNCBMatchCentreScraper()
            matcher = ScorecardPlayerMatcher(db)

            # Get all matches for the club from previous season
            logger.debug(f"Fetching {club_name} matches from {prev_season_year}")
            matches = await scraper.get_recent_matches_for_club(
                club_name=club_name,
                days_back=days_back,
                season_id=19  # May need to adjust based on KNCB season IDs
            )

            if not matches:
                logger.warning(f"No matches found for {club_name} in {prev_season_year}")
                return None

            # Filter matches to previous season year only
            prev_season_matches = [
                m for m in matches
                if m.get('date') and str(prev_season_year) in m.get('date', '')
            ]

            logger.debug(f"Found {len(prev_season_matches)} matches from {prev_season_year}")

            # Scrape each match and look for this player
            player_total_points = 0.0
            matches_found = 0

            for match in prev_season_matches:
                match_id = match.get('match_id')
                if not match_id:
                    continue

                try:
                    # Scrape scorecard
                    scorecard = await scraper.scrape_match_scorecard(match_id)

                    if not scorecard:
                        continue

                    # Extract player stats
                    player_stats_list = scraper.extract_player_stats(
                        scorecard,
                        club_name=club_name,
                        tier=player.tier
                    )

                    # Find this specific player in the scorecard
                    for player_stat in player_stats_list:
                        scorecard_name = player_stat.get('name', '').strip()

                        # Try to match player name
                        matched_player = matcher.match_scorecard_player(
                            scorecard_name,
                            club_name,
                            player.tier
                        )

                        if matched_player and matched_player.id == player.id:
                            # Found the player in this match!
                            fantasy_points = player_stat.get('fantasy_points', 0.0)
                            player_total_points += fantasy_points
                            matches_found += 1
                            logger.debug(f"Match {match_id}: {player.name} earned {fantasy_points:.2f} points")
                            break

                except Exception as match_error:
                    logger.debug(f"Error scraping match {match_id}: {match_error}")
                    continue

            if matches_found > 0:
                logger.info(f"✅ Found {player.name} in {matches_found} matches from {prev_season_year}, total: {player_total_points:.2f} points")
                return player_total_points
            else:
                logger.warning(f"❌ Could not find {player.name} in any {prev_season_year} matches")
                return None

        # Run the async scraping
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(scrape_player_season())
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Failed to scrape KNCB for {player.name}: {e}")
        return None
