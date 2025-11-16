#!/usr/bin/env python3
"""
API Endpoints for Player Statistics
====================================
FastAPI endpoints to access aggregated player data.

Add these to your main.py to expose player stats via API.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from celery_tasks import (
    get_player_stats,
    get_club_roster,
    get_top_fantasy_scorers,
    get_top_run_scorers,
    get_top_wicket_takers,
    get_season_summary,
    trigger_scrape_now
)

router = APIRouter(prefix="/api/v1", tags=["player_stats"])


# Pydantic models for responses
class PlayerStats(BaseModel):
    player_id: str
    player_name: str
    club: str
    matches_played: int
    season_totals: dict
    averages: dict


class SeasonSummary(BaseModel):
    total_players: int
    clubs: int
    club_rosters: dict
    top_scorers: list


# =============================================================================
# PLAYER ENDPOINTS
# =============================================================================

@router.get("/players/{player_id}", response_model=dict)
async def get_player(player_id: str):
    """
    Get season statistics for a specific player

    Args:
        player_id: Unique player identifier

    Returns:
        Player stats including match history, season totals, and averages
    """
    player = get_player_stats(player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Convert sets to lists for JSON serialization
    player_copy = player.copy()
    player_copy['processed_matches'] = list(player['processed_matches'])

    return player_copy


@router.get("/players", response_model=List[dict])
async def search_players(
    club: Optional[str] = Query(None, description="Filter by club name"),
    limit: int = Query(50, le=100, description="Maximum number of results")
):
    """
    Search for players

    Args:
        club: Optional club name to filter by
        limit: Maximum results to return

    Returns:
        List of players matching criteria
    """
    if club:
        players = get_club_roster(club)
    else:
        # Get top players by fantasy points
        players = get_top_fantasy_scorers(limit)

    # Serialize for JSON
    serialized = []
    for player in players:
        player_copy = player.copy()
        player_copy['processed_matches'] = list(player.get('processed_matches', set()))
        serialized.append(player_copy)

    return serialized[:limit]


# =============================================================================
# LEADERBOARDS
# =============================================================================

@router.get("/leaderboards/fantasy-points", response_model=List[dict])
async def fantasy_points_leaderboard(
    limit: int = Query(10, le=50, description="Number of players to return")
):
    """
    Get top fantasy point scorers

    Returns:
        List of top players sorted by fantasy points
    """
    players = get_top_fantasy_scorers(limit)

    return [{
        'player_id': p['player_id'],
        'player_name': p['player_name'],
        'club': p['club'],
        'fantasy_points': p['season_totals']['fantasy_points'],
        'matches_played': p['matches_played'],
        'avg_per_match': p['averages']['fantasy_points_per_match']
    } for p in players]


@router.get("/leaderboards/runs", response_model=List[dict])
async def runs_leaderboard(
    limit: int = Query(10, le=50, description="Number of players to return")
):
    """
    Get top run scorers

    Returns:
        List of top batters sorted by runs scored
    """
    players = get_top_run_scorers(limit)

    return [{
        'player_id': p['player_id'],
        'player_name': p['player_name'],
        'club': p['club'],
        'runs': p['season_totals']['batting']['runs'],
        'average': p['averages']['batting_average'],
        'strike_rate': p['averages']['strike_rate'],
        'fifties': p['season_totals']['batting']['fifties'],
        'centuries': p['season_totals']['batting']['centuries']
    } for p in players]


@router.get("/leaderboards/wickets", response_model=List[dict])
async def wickets_leaderboard(
    limit: int = Query(10, le=50, description="Number of players to return")
):
    """
    Get top wicket takers

    Returns:
        List of top bowlers sorted by wickets taken
    """
    players = get_top_wicket_takers(limit)

    return [{
        'player_id': p['player_id'],
        'player_name': p['player_name'],
        'club': p['club'],
        'wickets': p['season_totals']['bowling']['wickets'],
        'average': p['averages']['bowling_average'],
        'economy': p['averages']['economy_rate'],
        'five_wicket_hauls': p['season_totals']['bowling']['five_wicket_hauls']
    } for p in players]


# =============================================================================
# CLUB ENDPOINTS
# =============================================================================

@router.get("/clubs/{club_name}/roster", response_model=List[dict])
async def get_club_players(club_name: str):
    """
    Get all players for a specific club

    Args:
        club_name: Name of the club

    Returns:
        List of all discovered players for this club
    """
    players = get_club_roster(club_name)

    if not players:
        raise HTTPException(
            status_code=404,
            detail=f"No players found for club '{club_name}'"
        )

    return [{
        'player_id': p['player_id'],
        'player_name': p['player_name'],
        'matches_played': p['matches_played'],
        'fantasy_points': p['season_totals']['fantasy_points'],
        'runs': p['season_totals']['batting']['runs'],
        'wickets': p['season_totals']['bowling']['wickets']
    } for p in players]


# =============================================================================
# SEASON SUMMARY
# =============================================================================

@router.get("/season/summary", response_model=dict)
async def season_summary():
    """
    Get overall season summary

    Returns:
        Summary of entire season including player counts and top performers
    """
    return get_season_summary()


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("/admin/scrape-now")
async def trigger_manual_scrape():
    """
    Manually trigger a scraping task (admin only)

    Returns:
        Task ID for tracking
    """
    task_id = trigger_scrape_now()
    return {
        "status": "triggered",
        "task_id": task_id,
        "message": "Scraping task started"
    }


# =============================================================================
# HOW TO USE IN main.py
# =============================================================================

"""
Add to your main.py:

from api_endpoints import router as stats_router

app = FastAPI()

# Include stats endpoints
app.include_router(stats_router)

Then access via:
- GET /api/v1/players/{player_id}
- GET /api/v1/players?club=VRA
- GET /api/v1/leaderboards/fantasy-points
- GET /api/v1/leaderboards/runs
- GET /api/v1/leaderboards/wickets
- GET /api/v1/clubs/{club_name}/roster
- GET /api/v1/season/summary
- POST /api/v1/admin/scrape-now
"""
