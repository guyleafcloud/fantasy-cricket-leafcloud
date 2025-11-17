#!/usr/bin/env python3
"""
Simulate Match Round for Live Fantasy Teams
============================================
Tests the full workflow with real teams from the database:
1. Query active teams and their players
2. Simulate matches with mock data
3. Calculate fantasy scores (with captain/VC multipliers)
4. Update leaderboard
5. Show results

Usage:
    python3 simulate_live_teams.py
"""

import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://fantasy_user:fantasy_password@localhost:5432/fantasy_cricket')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def get_active_teams():
    """Get all active fantasy teams from database (only finalized teams)"""
    session = Session()
    try:
        query = text("""
            SELECT
                ft.id as team_id,
                ft.team_name,
                COALESCE(u.full_name, u.email) as owner_name,
                ft.league_id,
                l.name as league_name,
                s.name as season_name,
                COUNT(ftp.player_id) as player_count
            FROM fantasy_teams ft
            JOIN users u ON ft.user_id = u.id
            JOIN leagues l ON ft.league_id = l.id
            JOIN seasons s ON l.season_id = s.id
            LEFT JOIN fantasy_team_players ftp ON ft.id = ftp.fantasy_team_id
            WHERE s.is_active = true
              AND ft.is_finalized = true
            GROUP BY ft.id, ft.team_name, u.full_name, u.email, ft.league_id, l.name, s.name
            ORDER BY ft.created_at DESC
        """)

        result = session.execute(query)
        teams = []

        for row in result:
            teams.append({
                'team_id': str(row.team_id),
                'team_name': row.team_name,
                'owner_name': row.owner_name,
                'league_id': str(row.league_id),
                'league_name': row.league_name,
                'season_name': row.season_name,
                'player_count': row.player_count
            })

        return teams
    finally:
        session.close()


def get_team_players(team_id):
    """Get all players for a specific team with their roles"""
    session = Session()
    try:
        query = text("""
            SELECT
                p.id as player_id,
                p.name as player_name,
                p.multiplier,
                t.name as club,
                ftp.is_captain,
                ftp.is_vice_captain,
                ftp.is_wicket_keeper as is_wicketkeeper,
                ftp.position
            FROM fantasy_team_players ftp
            JOIN players p ON ftp.player_id = p.id
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE ftp.fantasy_team_id = :team_id
            ORDER BY ftp.position
        """)

        result = session.execute(query, {'team_id': team_id})
        players = []

        for row in result:
            players.append({
                'player_id': str(row.player_id),
                'name': row.player_name,
                'multiplier': float(row.multiplier),
                'club': row.club,
                'is_captain': row.is_captain,
                'is_vice_captain': row.is_vice_captain,
                'is_wicketkeeper': row.is_wicketkeeper,
                'position': row.position
            })

        return players
    finally:
        session.close()


async def simulate_weekly_matches():
    """
    Simulate a week's worth of matches across all clubs
    Returns: dict mapping (player_name, club_name) -> performance
    """
    import random

    # Get actual club names from database
    session = Session()
    try:
        query = text("SELECT DISTINCT name FROM teams WHERE name IS NOT NULL ORDER BY name")
        result = session.execute(query)
        all_clubs = [row.name for row in result]
    finally:
        session.close()

    if not all_clubs:
        # Fallback to default clubs if database is empty
        all_clubs = ['ACC 1', 'ACC 2', 'VRA 1', 'HCC 1', 'VOC 1', 'Quick 1']

    print(f"\n📋 Using {len(all_clubs)} clubs from database:")
    print(f"   {', '.join(all_clubs[:5])}{'...' if len(all_clubs) > 5 else ''}")

    # Generate 20-30 matches this week across all clubs/grades
    num_matches = random.randint(20, 30)

    print(f"\n🎮 Simulating {num_matches} matches across all clubs...")
    print("="*80)

    all_performances = {}  # (player_name, club_name) -> performance

    for match_num in range(num_matches):
        # Random matchup
        home_club = random.choice(all_clubs)
        away_club = random.choice([c for c in all_clubs if c != home_club])
        grade = random.choice(['Hoofdklasse', 'Topklasse', '1e Klasse', '2e Klasse'])

        print(f"  Match {match_num+1}: {home_club} vs {away_club} ({grade})")

        # Generate 11-14 players per team (22-28 total)
        num_players_home = random.randint(11, 14)
        num_players_away = random.randint(11, 14)

        # Simulate home team players
        for _ in range(num_players_home):
            player_name = generate_random_player_name()
            perf = generate_random_performance()
            key = (player_name, home_club)

            # If player already performed this week, aggregate (shouldn't happen but just in case)
            if key in all_performances:
                all_performances[key] = aggregate_performances(all_performances[key], perf)
            else:
                all_performances[key] = perf

        # Simulate away team players
        for _ in range(num_players_away):
            player_name = generate_random_player_name()
            perf = generate_random_performance()
            key = (player_name, away_club)

            if key in all_performances:
                all_performances[key] = aggregate_performances(all_performances[key], perf)
            else:
                all_performances[key] = perf

    print(f"\n✅ Generated {len(all_performances)} player performances across {num_matches} matches")
    return all_performances


def generate_random_player_name():
    """Generate a random player name similar to those in the database"""
    import random

    # Actual names from database (without spaces - they're concatenated in DB)
    actual_names = [
        'VinodDawra', 'ArrushNadakatta', 'WaqasAhmad', 'NavinSaran', 'MukeshBhardwaj',
        'TimVersteegh', 'JordanWoolf', 'DaanVierling', 'AbhinandhanDevadiga',
        'AkshayaSripatnala', 'MaheshNavale', 'AkhilDixit', 'AxayaKansal', 'BaljotSingh',
        'ReinderLubbers', 'IrfanYounis', 'SiddarthMadhavan', 'MickBoendermaker',
        'TiboBalk', 'AbhinavVelidandla', 'JaganNarayanamoorthy', 'RachitGupta',
        'HarrySingh', 'LotteHeerkens', 'EzzatMuhseni', 'AyaanBarve', 'JuanFourie',
        'ShayanMoodley', 'AyaanAbhilash', 'FarhaanKhawaja', 'IzhaanSayed',
        'VivaanDhawan', 'ZishaanYousaf', 'ZamaanKhan', 'AkaashMahangoe',
        'AyaanshSehgal', 'AyaanFarooq', 'RandheerPonnamkunnath',
        'BalasubramaniamGurmurthy', 'KrishnakanthAjjarapu', 'WilkoFrieke',
        'SamEikelenboom', 'ParthaBhattacharjee', 'VetrivelanKarunanithi',
        'QudratullahAkbari', 'AbhisaarBhatnagar'
    ]

    # Common first/last names for random generation
    first_names = ['Tom', 'Jan', 'Pieter', 'Arjun', 'Rohan', 'Vivian', 'Colin',
                   'Max', 'Tim', 'Sam', 'Erik', 'Michael', 'Lars', 'Bas']
    last_names = ['Visee', 'Cooper', 'Singh', 'Patel', 'Kingma', 'deLeede',
                  'ODowd', 'Pringle', 'Edwards', 'Klein', 'Engelbrecht', 'Myburgh']

    # 40% chance use actual name, 60% chance generate random
    if random.random() < 0.4:
        return random.choice(actual_names)
    else:
        return random.choice(first_names) + random.choice(last_names)


def generate_random_performance():
    """Generate a random cricket performance"""
    import random

    # Simulate batting
    runs = random.choices(
        [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100],
        weights=[8, 12, 15, 12, 10, 8, 8, 6, 4, 3, 2, 1]
    )[0]

    if runs > 0:
        balls_faced = max(1, int(runs / random.uniform(0.8, 1.8)))
    else:
        balls_faced = random.randint(0, 5)

    is_out = random.random() < 0.7 if runs > 0 else (random.random() < 0.5)

    # Simulate bowling
    bowled = random.random() < 0.6
    if bowled:
        wickets = random.choices([0, 1, 2, 3, 4, 5], weights=[30, 30, 20, 10, 5, 2])[0]
        overs = random.uniform(2, 10)
        economy = random.uniform(3.0, 9.0)
        runs_conceded = int(overs * economy)
        maidens = random.choices(range(int(overs) + 1), weights=[50] + [20] * int(overs))[0]
    else:
        wickets = 0
        overs = 0
        runs_conceded = 0
        maidens = 0

    # Simulate fielding
    catches = random.choices([0, 1, 2, 3], weights=[70, 20, 8, 2])[0]
    stumpings = 0
    runouts = random.choices([0, 1], weights=[90, 10])[0]

    return {
        'runs': runs,
        'balls_faced': balls_faced,
        'is_out': is_out,
        'wickets': wickets,
        'overs': overs,
        'runs_conceded': runs_conceded,
        'maidens': maidens,
        'catches': catches,
        'stumpings': stumpings,
        'runouts': runouts
    }


def aggregate_performances(perf1, perf2):
    """Aggregate two performances (in case a player played multiple matches)"""
    return {
        'runs': perf1['runs'] + perf2['runs'],
        'balls_faced': perf1['balls_faced'] + perf2['balls_faced'],
        'is_out': perf1['is_out'] or perf2['is_out'],
        'wickets': perf1['wickets'] + perf2['wickets'],
        'overs': perf1['overs'] + perf2['overs'],
        'runs_conceded': perf1['runs_conceded'] + perf2['runs_conceded'],
        'maidens': perf1['maidens'] + perf2['maidens'],
        'catches': perf1['catches'] + perf2['catches'],
        'stumpings': perf1['stumpings'] + perf2['stumpings'],
        'runouts': perf1['runouts'] + perf2['runouts']
    }


def calculate_fantasy_points(performance, is_wicketkeeper=False):
    """Calculate fantasy points using the tiered system"""
    try:
        from rules_set_1 import calculate_total_fantasy_points
    except ImportError:
        import importlib
        rules_module = importlib.import_module('rules-set-1')
        calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

    result = calculate_total_fantasy_points(
        runs=performance['runs'],
        balls_faced=performance['balls_faced'],
        is_out=performance['is_out'],
        wickets=performance['wickets'],
        overs=performance['overs'],
        runs_conceded=performance['runs_conceded'],
        maidens=performance['maidens'],
        catches=performance['catches'],
        stumpings=performance['stumpings'],
        runouts=performance['runouts'],
        is_wicketkeeper=is_wicketkeeper
    )

    return result['grand_total']


def update_team_scores_in_db(all_team_scores):
    """Update fantasy_teams table with calculated points and ranks"""
    session = Session()
    try:
        print("\n💾 Updating database with calculated scores...")
        print("-"*80)

        # First, get current points for each team
        team_ids = [team_score['team']['team_id'] for team_score in all_team_scores]
        query = text("SELECT id, total_points FROM fantasy_teams WHERE id = ANY(:ids)")
        result = session.execute(query, {'ids': team_ids})
        current_points = {row.id: (row.total_points or 0.0) for row in result}

        # Add new points to existing points
        for team_score in all_team_scores:
            team_id = team_score['team']['team_id']
            round_points = team_score['total_points']
            previous_points = current_points.get(team_id, 0.0)
            new_total = previous_points + round_points
            team_score['cumulative_total'] = new_total
            team_score['round_points'] = round_points

        # Sort by cumulative totals to assign ranks
        sorted_teams = sorted(all_team_scores, key=lambda x: x['cumulative_total'], reverse=True)

        for rank, team_score in enumerate(sorted_teams, start=1):
            team_id = team_score['team']['team_id']
            cumulative_total = team_score['cumulative_total']
            round_points = team_score['round_points']

            # Update team in database with cumulative total
            update_query = text("""
                UPDATE fantasy_teams
                SET total_points = :points,
                    rank = :rank,
                    updated_at = NOW()
                WHERE id = :team_id
            """)

            session.execute(update_query, {
                'points': cumulative_total,
                'rank': rank,
                'team_id': team_id
            })

            print(f"   {rank}. {team_score['team']['team_name']:30s} - {cumulative_total:8.1f} pts (+{round_points:.1f})")

        session.commit()
        print("\n✅ Database updated successfully!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def store_player_performances(all_team_scores, round_number=1):
    """Store individual player performances in player_performances table and update fantasy_team_players"""
    import uuid
    session = Session()
    try:
        print("\n📊 Storing individual player performances...")
        print("-"*80)

        total_performances = 0
        updated_players = 0

        for team_score in all_team_scores:
            team_id = team_score['team']['team_id']
            league_id = team_score['team']['league_id']

            for player_score in team_score['player_scores']:
                perf = player_score['performance']
                player_id = player_score.get('player_id')

                if not player_id:
                    continue

                # Insert player performance for this round
                insert_query = text("""
                    INSERT INTO player_performances (
                        id, player_id, fantasy_team_id, league_id, round_number,
                        runs, balls_faced, is_out,
                        wickets, overs, runs_conceded, maidens,
                        catches, stumpings, runouts,
                        base_fantasy_points, multiplier_applied, captain_multiplier, final_fantasy_points,
                        is_captain, is_vice_captain, is_wicket_keeper,
                        match_date, created_at, updated_at
                    ) VALUES (
                        :id, :player_id, :fantasy_team_id, :league_id, :round_number,
                        :runs, :balls_faced, :is_out,
                        :wickets, :overs, :runs_conceded, :maidens,
                        :catches, :stumpings, :runouts,
                        :base_fantasy_points, :multiplier_applied, :captain_multiplier, :final_fantasy_points,
                        :is_captain, :is_vice_captain, :is_wicket_keeper,
                        NOW(), NOW(), NOW()
                    )
                    ON CONFLICT (player_id, league_id, round_number)
                    DO UPDATE SET
                        runs = EXCLUDED.runs,
                        balls_faced = EXCLUDED.balls_faced,
                        is_out = EXCLUDED.is_out,
                        wickets = EXCLUDED.wickets,
                        overs = EXCLUDED.overs,
                        runs_conceded = EXCLUDED.runs_conceded,
                        maidens = EXCLUDED.maidens,
                        catches = EXCLUDED.catches,
                        stumpings = EXCLUDED.stumpings,
                        runouts = EXCLUDED.runouts,
                        base_fantasy_points = EXCLUDED.base_fantasy_points,
                        multiplier_applied = EXCLUDED.multiplier_applied,
                        captain_multiplier = EXCLUDED.captain_multiplier,
                        final_fantasy_points = EXCLUDED.final_fantasy_points,
                        updated_at = NOW()
                """)

                session.execute(insert_query, {
                    'id': str(uuid.uuid4()),
                    'player_id': player_id,
                    'fantasy_team_id': team_id,
                    'league_id': league_id,
                    'round_number': round_number,
                    'runs': perf['runs'],
                    'balls_faced': perf['balls_faced'],
                    'is_out': perf['is_out'],
                    'wickets': perf['wickets'],
                    'overs': perf['overs'],
                    'runs_conceded': perf['runs_conceded'],
                    'maidens': perf['maidens'],
                    'catches': perf['catches'],
                    'stumpings': perf['stumpings'],
                    'runouts': perf['runouts'],
                    'base_fantasy_points': player_score['base_points'],
                    'multiplier_applied': player_score.get('multiplier', 1.0),
                    'captain_multiplier': player_score.get('captain_multiplier', 1.0),
                    'final_fantasy_points': player_score['final_points'],
                    'is_captain': player_score.get('is_captain', False),
                    'is_vice_captain': player_score.get('is_vice_captain', False),
                    'is_wicket_keeper': player_score.get('is_wicketkeeper', False)
                })

                total_performances += 1

                # Update fantasy_team_players.total_points with cumulative total
                update_player_query = text("""
                    UPDATE fantasy_team_players
                    SET total_points = COALESCE(total_points, 0) + :round_points
                    WHERE fantasy_team_id = :team_id
                      AND player_id = :player_id
                """)

                session.execute(update_player_query, {
                    'round_points': player_score['final_points'],
                    'team_id': team_id,
                    'player_id': player_id
                })

                updated_players += 1

        session.commit()
        print(f"   Stored {total_performances} player performances")
        print(f"   Updated {updated_players} player totals in fantasy_team_players")
        print("\n✅ Player performances saved successfully!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error storing player performances: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


async def simulate_round_for_teams():
    """Simulate a complete round for all active teams"""

    print("="*80)
    print("🏏 FANTASY CRICKET - LIVE TEAMS SIMULATION")
    print("="*80)

    # Get active teams
    print("\n📋 Fetching active teams from database...")
    teams = get_active_teams()

    if not teams:
        print("❌ No active teams found in database")
        return

    print(f"✅ Found {len(teams)} active team(s)")
    print()

    for team in teams:
        print(f"   Team: {team['team_name']}")
        print(f"   Owner: {team['owner_name']}")
        print(f"   League: {team['league_name']}")
        print(f"   Season: {team['season_name']}")
        print(f"   Players: {team['player_count']}")
        print()

    # STEP 1: Simulate ALL matches across all clubs this week
    weekly_performances = await simulate_weekly_matches()

    # STEP 2: Process each fantasy team
    all_team_scores = []

    for team in teams:
        print("="*80)
        print(f"🎯 SIMULATING ROUND FOR: {team['team_name']} (Owner: {team['owner_name']})")
        print("="*80)

        # Get team players
        players = get_team_players(team['team_id'])

        if not players:
            print(f"⚠️  No players found for team {team['team_name']}")
            continue

        print(f"\n📊 Team Squad ({len(players)} players):")
        print("-"*80)

        captain = None
        vice_captain = None

        for i, player in enumerate(players):
            role_markers = []
            if player['is_captain']:
                role_markers.append("(C)")
                captain = player
            if player['is_vice_captain']:
                role_markers.append("(VC)")
                vice_captain = player
            if player['is_wicketkeeper']:
                role_markers.append("(WK)")

            role_str = " ".join(role_markers) if role_markers else ""
            print(f"   {i+1:2d}. {player['name']:25s} {role_str:15s} Multiplier: {player['multiplier']:.2f}")

        print()

        # Match players to their performances from this week's matches
        print("🔍 Matching fantasy players to weekly performances...")
        print("-"*80)

        team_total_points = 0
        player_scores = []
        matched_count = 0
        unmatched_count = 0

        for player in players:
            # Look up performance by (name, club)
            # Club might be None for some players, so handle that
            player_club = player.get('club')
            lookup_key = (player['name'], player_club) if player_club else None

            if lookup_key and lookup_key in weekly_performances:
                performance = weekly_performances[lookup_key]
                matched_count += 1
            else:
                # Player didn't play this week (or name/club mismatch)
                # Give them zero performance
                performance = {
                    'runs': 0, 'balls_faced': 0, 'is_out': False,
                    'wickets': 0, 'overs': 0, 'runs_conceded': 0, 'maidens': 0,
                    'catches': 0, 'stumpings': 0, 'runouts': 0
                }
                unmatched_count += 1

            # Calculate fantasy points
            base_points = calculate_fantasy_points(
                performance,
                is_wicketkeeper=player['is_wicketkeeper']
            )

            # Apply player multiplier
            adjusted_points = base_points * player['multiplier']

            # Apply captain/vice-captain multipliers
            final_points = adjusted_points
            captain_multiplier = 1.0
            multiplier_text = f"{player['multiplier']:.2f}x"

            if player['is_captain']:
                captain_multiplier = 2.0
                final_points = adjusted_points * 2.0
                multiplier_text = f"{player['multiplier']:.2f}x × 2.0 (C)"
            elif player['is_vice_captain']:
                captain_multiplier = 1.5
                final_points = adjusted_points * 1.5
                multiplier_text = f"{player['multiplier']:.2f}x × 1.5 (VC)"

            team_total_points += final_points

            # Format performance summary
            stats = []
            if performance['runs'] > 0:
                stats.append(f"{performance['runs']}({performance['balls_faced']})")
            if performance['wickets'] > 0:
                stats.append(f"{performance['wickets']}/{performance['runs_conceded']}")
            if performance['catches'] > 0:
                stats.append(f"{performance['catches']}ct")

            stats_str = ", ".join(stats) if stats else "DNP"

            player_scores.append({
                'player_id': player['player_id'],
                'name': player['name'],
                'performance': performance,
                'base_points': base_points,
                'adjusted_points': adjusted_points,
                'final_points': final_points,
                'multiplier': player['multiplier'],
                'captain_multiplier': captain_multiplier,
                'is_captain': player['is_captain'],
                'is_vice_captain': player['is_vice_captain'],
                'is_wicketkeeper': player['is_wicketkeeper'],
                'stats': stats_str,
                'multiplier_text': multiplier_text
            })

            print(f"   {player['name']:25s} - {final_points:7.1f} pts ({stats_str:25s}) [{multiplier_text}]")

        # Sort by points
        player_scores.sort(key=lambda x: x['final_points'], reverse=True)

        print()
        print(f"   ✅ Matched: {matched_count}/{len(players)} players")
        print(f"   ⚠️  No match: {unmatched_count}/{len(players)} players (didn't play or club mismatch)")
        print()
        print("="*80)
        print(f"📊 TEAM SCORE: {team['team_name']}")
        print("="*80)
        print(f"Total Points: {team_total_points:.1f}")
        print()
        print("Top 5 Performers:")
        for i, scorer in enumerate(player_scores[:5]):
            print(f"   {i+1}. {scorer['name']:25s} - {scorer['final_points']:7.1f} pts ({scorer['stats']})")

        all_team_scores.append({
            'team': team,
            'total_points': team_total_points,
            'player_scores': player_scores
        })

        print()

    # Final Leaderboard
    if len(all_team_scores) > 1:
        print("\n" + "="*80)
        print("🏆 LEADERBOARD")
        print("="*80)

        all_team_scores.sort(key=lambda x: x['total_points'], reverse=True)

        for i, team_score in enumerate(all_team_scores):
            team = team_score['team']
            points = team_score['total_points']
            print(f"   {i+1}. {team['team_name']:30s} ({team['owner_name']:20s}) - {points:8.1f} pts")

        # Show winner
        winner = all_team_scores[0]
        print()
        print("="*80)
        print(f"🥇 WINNER: {winner['team']['team_name']} with {winner['total_points']:.1f} points!")
        print("="*80)

    # Update database with scores
    if all_team_scores:
        update_team_scores_in_db(all_team_scores)
        # Get round number from function parameter (default 1)
        round_num = getattr(simulate_round_for_teams, 'round_number', 1)
        store_player_performances(all_team_scores, round_number=round_num)

    return all_team_scores


async def main():
    """Main entry point"""
    import sys

    # Get round number from command line argument
    round_number = 1
    if len(sys.argv) > 1:
        try:
            round_number = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Invalid round number '{sys.argv[1]}', using round 1")
            round_number = 1

    # Store round number for use in simulate_round_for_teams
    simulate_round_for_teams.round_number = round_number
    print(f"\n🗓️  ROUND {round_number}\n")

    try:
        results = await simulate_round_for_teams()

        if results:
            print("\n✅ Simulation complete!")
            print("\nThis simulation demonstrated:")
            print("  ✓ Querying active teams from database")
            print("  ✓ Loading team players with roles (C/VC/WK)")
            print("  ✓ Simulating match performances")
            print("  ✓ Calculating fantasy points with tiered system")
            print("  ✓ Applying player multipliers")
            print("  ✓ Applying captain/vice-captain bonuses")
            print("  ✓ Generating team totals")
            print("  ✓ Creating leaderboard")
            print("  ✓ Updating database with points and ranks")

            print("\nNext steps:")
            print("  1. Run this weekly after real matches")
            print("  2. Replace simulated performances with actual scraped data")
            print("  3. Users can view updated leaderboard on frontend")
            print("  4. Add weekly/round history tracking (optional)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
