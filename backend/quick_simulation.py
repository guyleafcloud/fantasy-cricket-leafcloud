#!/usr/bin/env python3
"""
Quick Simulation - Process all mock data and update database
"""
import json
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:_8dbdlHVu5kVHclQhPkqhg8IuLa6Ni1QcR0GUT7M9d0@fantasy_cricket_db:5432/fantasy_cricket')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def import_week_performances(week_num):
    """Import performances from a week's mock data"""
    session = Session()

    week_file = Path(f'/app/mock_data/scorecards_2026/by_week/week_{week_num:02d}.json')

    if not week_file.exists():
        print(f"❌ Week {week_num} file not found")
        return 0

    with open(week_file) as f:
        matches = json.load(f)

    count = 0
    for match in matches:
        match_id = match['match_id']

        # Get players from batting and bowling
        players = []

        # Batting
        for innings in match.get('batting', []):
            for player in innings.get('players', []):
                players.append({
                    'name': player['name'],
                    'runs': player.get('runs', 0),
                    'balls_faced': player.get('balls_faced', 0),
                    'fours': player.get('fours', 0),
                    'sixes': player.get('sixes', 0),
                    'is_out': player.get('is_out', False),
                    'wickets': 0,
                    'overs_bowled': 0.0,
                    'runs_conceded': 0,
                    'maidens': 0,
                    'catches': 0,
                    'stumpings': 0,
                    'run_outs': 0
                })

        # Bowling
        for innings in match.get('bowling', []):
            for bowler in innings.get('bowlers', []):
                # Find existing player or create new
                existing = next((p for p in players if p['name'] == bowler['name']), None)
                if existing:
                    existing['wickets'] = bowler.get('wickets', 0)
                    existing['overs_bowled'] = bowler.get('overs', 0.0)
                    existing['runs_conceded'] = bowler.get('runs_conceded', 0)
                    existing['maidens'] = bowler.get('maidens', 0)
                else:
                    players.append({
                        'name': bowler['name'],
                        'runs': 0,
                        'balls_faced': 0,
                        'fours': 0,
                        'sixes': 0,
                        'is_out': False,
                        'wickets': bowler.get('wickets', 0),
                        'overs_bowled': bowler.get('overs', 0.0),
                        'runs_conceded': bowler.get('runs_conceded', 0),
                        'maidens': bowler.get('maidens', 0),
                        'catches': 0,
                        'stumpings': 0,
                        'run_outs': 0
                    })

        # Insert performances
        for player in players:
            # Calculate basic fantasy points (simplified)
            fantasy_points = player['runs'] + (player['wickets'] * 25) + (player['catches'] * 8)

            try:
                session.execute(text("""
                    INSERT INTO player_performances (
                        match_id, player_name, runs, balls_faced, fours, sixes, is_out,
                        wickets, overs_bowled, runs_conceded, maidens,
                        catches, stumpings, run_outs, fantasy_points, tier, created_at
                    ) VALUES (
                        :match_id, :player_name, :runs, :balls_faced, :fours, :sixes, :is_out,
                        :wickets, :overs_bowled, :runs_conceded, :maidens,
                        :catches, :stumpings, :run_outs, :fantasy_points, 'tier2', NOW()
                    )
                    ON CONFLICT (match_id, player_name) DO UPDATE SET
                        fantasy_points = EXCLUDED.fantasy_points
                """), {
                    'match_id': match_id,
                    'player_name': player['name'],
                    **player,
                    'fantasy_points': fantasy_points
                })
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting {player['name']}: {e}")

    session.commit()
    session.close()
    return count

def aggregate_to_teams():
    """Aggregate player performances to fantasy teams"""
    session = Session()

    # Update fantasy_team_players.total_points from matching player_performances
    session.execute(text("""
        UPDATE fantasy_team_players ftp
        SET total_points = COALESCE((
            SELECT SUM(pp.fantasy_points)
            FROM player_performances pp
            JOIN players p ON LOWER(TRIM(pp.player_name)) = LOWER(TRIM(p.name))
            WHERE p.id = ftp.player_id
        ), 0)
    """))

    # Update fantasy_teams.total_points from sum of player points
    session.execute(text("""
        UPDATE fantasy_teams ft
        SET total_points = COALESCE((
            SELECT SUM(ftp.total_points)
            FROM fantasy_team_players ftp
            WHERE ftp.fantasy_team_id = ft.id
        ), 0)
    """))

    session.commit()
    session.close()
    print("✅ Aggregated points to teams")

def main():
    print("🏏 Quick Simulation - Processing all mock data\n")

    total_performances = 0

    for week in range(1, 13):
        print(f"📅 Processing Week {week}...", end=" ")
        count = import_week_performances(week)
        total_performances += count
        print(f"✅ {count} performances")

    print(f"\n📊 Total: {total_performances} player performances imported")

    print("\n🔄 Aggregating to fantasy teams...")
    aggregate_to_teams()

    print("\n✨ Simulation complete!")
    print("👉 Visit https://fantcric.fun to see updated leaderboard")

if __name__ == "__main__":
    main()
