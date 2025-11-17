#!/usr/bin/env python3
"""
Quick test of the stats endpoint
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database_models import FantasyTeam, FantasyTeamPlayer, Player, Team, PlayerPerformance
import json

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://fantasy_user:fantasy_password@localhost:5432/fantasy_cricket')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_stats_endpoint():
    session = Session()
    try:
        # Get a league
        query = text("SELECT id FROM leagues LIMIT 1")
        result = session.execute(query)
        league_id = result.scalar()

        print(f"Testing stats for league: {league_id}")

        # Get all fantasy teams in this league
        fantasy_teams = session.query(FantasyTeam).filter(
            FantasyTeam.league_id == league_id
        ).all()

        print(f"Found {len(fantasy_teams)} fantasy teams")

        team_ids = [team.id for team in fantasy_teams]

        # Query fantasy_team_players with player info and points
        from sqlalchemy import and_
        player_fantasy_data = session.query(
            FantasyTeamPlayer.player_id,
            FantasyTeamPlayer.total_points,
            FantasyTeamPlayer.fantasy_team_id,
            Player.name,
            Player.team_id
        ).join(
            Player, Player.id == FantasyTeamPlayer.player_id
        ).filter(
            FantasyTeamPlayer.fantasy_team_id.in_(team_ids)
        ).all()

        print(f"Found {len(player_fantasy_data)} players")

        # Get player points
        player_points = []
        for pfd in player_fantasy_data:
            player_id, total_points, fantasy_team_id, player_name, cricket_team_id = pfd

            team_name = session.query(Team.name).filter(Team.id == cricket_team_id).scalar() if cricket_team_id else 'Unknown'

            player_points.append({
                'player_name': player_name,
                'team_name': team_name,
                'total_points': total_points or 0
            })

        # Top 25 players
        top_players = sorted(player_points, key=lambda x: x['total_points'], reverse=True)[:25]

        print(f"\nTop 25 Players:")
        print("-" * 80)
        for i, p in enumerate(top_players[:10], 1):
            print(f"{i}. {p['player_name']:30s} ({p['team_name']:10s}) - {p['total_points']:.1f} pts")

        print(f"\nTotal players with points: {sum(1 for p in player_points if p['total_points'] > 0)}")

    finally:
        session.close()

if __name__ == "__main__":
    test_stats_endpoint()
