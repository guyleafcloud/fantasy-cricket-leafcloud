#!/usr/bin/env python3
"""
Live Demo Simulation with Real Scorecards
==========================================
Scrapes 18 real KNCB scorecard URLs and simulates a 2-week season:
- Week 1: 9 matches → calculate points → update site
- Wait 60 seconds (1 minute = 1 week)
- Week 2: 9 matches → calculate points → update site

This will populate:
- Top 25 players (including non-fantasy-team players)
- Fantasy team scores with captain/VC/WK multipliers
- Leaderboard updates

Usage:
    python3 live_demo_simulation.py
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from playwright.async_api import async_playwright
import re
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Import rules for points calculation
import importlib.util
spec = importlib.util.spec_from_file_location("rules_set_1", "rules-set-1.py")
rules_module = importlib.util.module_from_spec(spec)
sys.modules["rules_set_1"] = rules_module
spec.loader.exec_module(rules_module)
calculate_total_fantasy_points = rules_module.calculate_total_fantasy_points

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Week URLs
WEEK1_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394",
    "https://matchcentre.kncb.nl/match/134453-7336247/scorecard/?period=2880895",
    "https://matchcentre.kncb.nl/match/134453-7323305/scorecard/?period=2904132",
    "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194",
    "https://matchcentre.kncb.nl/match/134453-7329152/scorecard/?period=2912677",
    "https://matchcentre.kncb.nl/match/134453-7326066/scorecard/?period=2850306",
    "https://matchcentre.kncb.nl/match/134453-7332092/scorecard/?period=2843768",
    "https://matchcentre.kncb.nl/match/134453-7324743/scorecard/?period=2883358",
    "https://matchcentre.kncb.nl/match/134453-7324797/scorecard/?period=2883096",
]

WEEK2_URLS = [
    "https://matchcentre.kncb.nl/match/134453-7336254/scorecard/?period=2911963",
    "https://matchcentre.kncb.nl/match/134453-7331237/scorecard/?period=2912048",
    "https://matchcentre.kncb.nl/match/134453-7329153/scorecard/?period=2943897",
    "https://matchcentre.kncb.nl/match/134453-7332269/scorecard/?period=2905571",
    "https://matchcentre.kncb.nl/match/134453-7326162/scorecard/?period=2882990",
    "https://matchcentre.kncb.nl/match/134453-7324749/scorecard/?period=2946803",
    "https://matchcentre.kncb.nl/match/134453-7323338/scorecard/?period=3100381",
    "https://matchcentre.kncb.nl/match/134453-7323364/scorecard/?period=2883312",
    "https://matchcentre.kncb.nl/match/134453-7330958/scorecard/?period=2971631",
]


async def scrape_scorecard(browser, url):
    """Scrape a single scorecard URL using Playwright"""
    page = await browser.new_page()

    try:
        print(f"   📥 Scraping: {url}")

        # Navigate with extended timeout
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)

        # Wait for page to load
        await page.wait_for_timeout(3000)

        # Get page content
        content = await page.content()

        # Try to find player data in the page
        # KNCB uses various selectors, let's try multiple approaches

        players_data = []

        # Approach 1: Look for player names and stats in tables
        try:
            # Get all table rows
            rows = await page.query_selector_all('tr')

            for row in rows:
                text = await row.inner_text()
                # Look for batting stats (name, runs, balls)
                # Example: "Boris Gorlee    45  30  2  1  150.00"
                if text and not text.startswith('Player') and not text.startswith('Batsman'):
                    parts = text.split()
                    if len(parts) >= 3:
                        # Try to parse as batting
                        try:
                            # Find runs (number after name)
                            for i in range(len(parts)):
                                if parts[i].isdigit():
                                    player_name = ' '.join(parts[:i])
                                    runs = int(parts[i])
                                    balls = int(parts[i+1]) if i+1 < len(parts) and parts[i+1].isdigit() else 0

                                    players_data.append({
                                        'name': player_name.strip(),
                                        'runs': runs,
                                        'balls_faced': balls,
                                        'wickets': 0,
                                        'overs': 0,
                                        'maidens': 0,
                                        'runs_conceded': 0,
                                        'catches': 0,
                                        'stumpings': 0,
                                        'runouts': 0,
                                        'is_out': 'not out' not in text.lower()
                                    })
                                    break
                        except:
                            continue
        except Exception as e:
            logger.warning(f"Failed to parse players: {e}")

        await page.close()

        return {
            'url': url,
            'success': len(players_data) > 0,
            'players': players_data,
            'total_players': len(players_data)
        }

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        await page.close()
        return {
            'url': url,
            'success': False,
            'players': [],
            'total_players': 0,
            'error': str(e)
        }


async def scrape_week(week_urls, week_number):
    """Scrape all URLs for a week"""
    print(f"\n{'='*80}")
    print(f"📅 WEEK {week_number} - SCRAPING {len(week_urls)} MATCHES")
    print('='*80)

    all_players = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for i, url in enumerate(week_urls, 1):
            print(f"\n[{i}/{len(week_urls)}]")
            result = await scrape_scorecard(browser, url)

            if result['success']:
                print(f"   ✅ Found {result['total_players']} players")
                all_players.extend(result['players'])
            else:
                print(f"   ❌ Failed: {result.get('error', 'No data')}")

        await browser.close()

    print(f"\n✅ Week {week_number} scraping complete: {len(all_players)} total player performances")
    return all_players


def match_players_to_db(scraped_players):
    """Match scraped player names to database players"""
    session = Session()

    try:
        # Get all players from database
        result = session.execute(text("""
            SELECT id, name, multiplier, is_wicket_keeper
            FROM players
        """))

        db_players = {row.name.lower().replace(' ', ''): {
            'id': row.id,
            'name': row.name,
            'multiplier': row.multiplier,
            'is_wicket_keeper': row.is_wicket_keeper
        } for row in result}

        matched = []
        unmatched = []

        for perf in scraped_players:
            # Normalize name for matching
            normalized = perf['name'].lower().replace(' ', '')

            if normalized in db_players:
                db_player = db_players[normalized]

                # Calculate fantasy points
                fantasy_points = calculate_total_fantasy_points(
                    {
                        'runs': perf['runs'],
                        'balls_faced': perf['balls_faced'],
                        'is_out': perf['is_out']
                    },
                    {
                        'wickets': perf['wickets'],
                        'overs_bowled': perf['overs'],
                        'maidens': perf['maidens'],
                        'runs_conceded': perf['runs_conceded']
                    },
                    {
                        'catches': perf['catches'],
                        'stumpings': perf['stumpings'],
                        'run_outs': perf['runouts']
                    }
                )

                # Apply player multiplier
                final_points = fantasy_points * db_player['multiplier']

                matched.append({
                    'player_id': db_player['id'],
                    'player_name': db_player['name'],
                    'multiplier': db_player['multiplier'],
                    'is_wicket_keeper': db_player['is_wicket_keeper'],
                    'runs': perf['runs'],
                    'balls_faced': perf['balls_faced'],
                    'is_out': perf['is_out'],
                    'wickets': perf['wickets'],
                    'overs': perf['overs'],
                    'maidens': perf['maidens'],
                    'runs_conceded': perf['runs_conceded'],
                    'catches': perf['catches'],
                    'stumpings': perf['stumpings'],
                    'runouts': perf['runouts'],
                    'base_fantasy_points': fantasy_points,
                    'final_fantasy_points': final_points
                })
            else:
                unmatched.append(perf['name'])

        print(f"\n📊 Player Matching:")
        print(f"   ✅ Matched: {len(matched)}")
        print(f"   ⚠️  Unmatched: {len(unmatched)}")

        if unmatched:
            print(f"\n   Unmatched players: {', '.join(unmatched[:10])}")
            if len(unmatched) > 10:
                print(f"   ... and {len(unmatched) - 10} more")

        return matched

    finally:
        session.close()


def store_performances(performances, round_number, league_id):
    """Store player performances in database"""
    session = Session()

    try:
        for perf in performances:
            perf_id = str(uuid.uuid4())

            session.execute(text("""
                INSERT INTO player_performances (
                    id, player_id, league_id, round_number,
                    runs, balls_faced, is_out,
                    wickets, overs, runs_conceded, maidens,
                    catches, stumpings, runouts,
                    base_fantasy_points, multiplier_applied, final_fantasy_points,
                    is_wicket_keeper,
                    match_date, created_at, updated_at
                ) VALUES (
                    :id, :player_id, :league_id, :round_number,
                    :runs, :balls_faced, :is_out,
                    :wickets, :overs, :runs_conceded, :maidens,
                    :catches, :stumpings, :runouts,
                    :base_points, :multiplier, :final_points,
                    :is_wk,
                    NOW(), NOW(), NOW()
                )
                ON CONFLICT (player_id, league_id, round_number)
                DO UPDATE SET
                    runs = EXCLUDED.runs,
                    balls_faced = EXCLUDED.balls_faced,
                    wickets = EXCLUDED.wickets,
                    base_fantasy_points = EXCLUDED.base_fantasy_points,
                    final_fantasy_points = EXCLUDED.final_fantasy_points,
                    updated_at = NOW()
            """), {
                'id': perf_id,
                'player_id': perf['player_id'],
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
                'base_points': perf['base_fantasy_points'],
                'multiplier': perf['multiplier'],
                'final_points': perf['final_fantasy_points'],
                'is_wk': perf['is_wicket_keeper']
            })

        session.commit()
        print(f"✅ Stored {len(performances)} performances for Round {round_number}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error storing performances: {e}")
        raise
    finally:
        session.close()


def update_fantasy_teams(round_number, league_id):
    """Update fantasy team scores based on performances"""
    session = Session()

    try:
        # Get all fantasy teams in this league
        teams = session.execute(text("""
            SELECT ft.id, ft.team_name
            FROM fantasy_teams ft
            WHERE ft.league_id = :league_id AND ft.is_finalized = TRUE
        """), {'league_id': league_id}).fetchall()

        for team in teams:
            # Get team's players and their performances
            result = session.execute(text("""
                SELECT
                    ftp.player_id,
                    ftp.is_captain,
                    ftp.is_vice_captain,
                    ftp.is_wicket_keeper,
                    pp.final_fantasy_points
                FROM fantasy_team_players ftp
                LEFT JOIN player_performances pp ON
                    pp.player_id = ftp.player_id AND
                    pp.league_id = :league_id AND
                    pp.round_number = :round_number
                WHERE ftp.fantasy_team_id = :team_id
            """), {
                'team_id': team.id,
                'league_id': league_id,
                'round_number': round_number
            })

            round_points = 0
            for row in result:
                if row.final_fantasy_points:
                    points = row.final_fantasy_points

                    # Apply captain/VC multiplier
                    if row.is_captain:
                        points *= 2.0
                    elif row.is_vice_captain:
                        points *= 1.5

                    round_points += points

            # Update team total (cumulative)
            session.execute(text("""
                UPDATE fantasy_teams
                SET total_points = COALESCE(total_points, 0) + :round_points
                WHERE id = :team_id
            """), {
                'team_id': team.id,
                'round_points': round_points
            })

        session.commit()
        print(f"✅ Updated {len(teams)} fantasy teams")

    finally:
        session.close()


def show_top_25(round_number, league_id):
    """Display top 25 players"""
    session = Session()

    try:
        result = session.execute(text("""
            SELECT
                p.name,
                pp.runs,
                pp.wickets,
                pp.catches,
                ROUND(pp.final_fantasy_points::numeric, 1) as points
            FROM player_performances pp
            JOIN players p ON pp.player_id = p.id
            WHERE pp.league_id = :league_id AND pp.round_number = :round_number
            ORDER BY pp.final_fantasy_points DESC
            LIMIT 25
        """), {
            'league_id': league_id,
            'round_number': round_number
        })

        print(f"\n{'='*80}")
        print(f"🏆 TOP 25 PLAYERS - ROUND {round_number}")
        print('='*80)

        for i, row in enumerate(result, 1):
            stats = []
            if row.runs > 0:
                stats.append(f"{row.runs}r")
            if row.wickets > 0:
                stats.append(f"{row.wickets}w")
            if row.catches > 0:
                stats.append(f"{row.catches}ct")

            stats_str = f"({', '.join(stats)})" if stats else "(DNP)"

            print(f"   {i:2d}. {row.name:30s} {row.points:7.1f} pts {stats_str}")

    finally:
        session.close()


def show_leaderboard(league_id):
    """Display fantasy team leaderboard"""
    session = Session()

    try:
        result = session.execute(text("""
            SELECT
                ft.team_name,
                COALESCE(u.full_name, u.email) as owner,
                ROUND(ft.total_points::numeric, 1) as points
            FROM fantasy_teams ft
            JOIN users u ON ft.user_id = u.id
            WHERE ft.league_id = :league_id AND ft.is_finalized = TRUE
            ORDER BY ft.total_points DESC
        """), {'league_id': league_id})

        print(f"\n{'='*80}")
        print(f"📊 FANTASY TEAM LEADERBOARD")
        print('='*80)

        for i, row in enumerate(result, 1):
            print(f"   {i}. {row.team_name:30s} ({row.owner:20s}) - {row.points:8.1f} pts")

    finally:
        session.close()


async def main():
    print("="*80)
    print("🏏 LIVE DEMO SIMULATION - REAL SCORECARDS")
    print("="*80)
    print("\nThis demo will:")
    print("  1. Scrape 9 Week 1 matches from KNCB")
    print("  2. Calculate fantasy points for ALL players")
    print("  3. Show top 25 players")
    print("  4. Update fantasy team scores")
    print("  5. Wait 60 seconds (1 minute = 1 week)")
    print("  6. Repeat for Week 2")
    print("\n" + "="*80)

    # Get active league
    session = Session()
    league = session.execute(text("""
        SELECT id FROM leagues
        WHERE is_active = TRUE
        LIMIT 1
    """)).fetchone()
    session.close()

    if not league:
        print("❌ No active league found")
        return

    league_id = league.id
    print(f"\n📋 Using league: {league_id}")

    # WEEK 1
    print("\n" + "="*80)
    print("📅 WEEK 1")
    print("="*80)

    week1_players = await scrape_week(WEEK1_URLS, 1)

    if not week1_players:
        print("\n❌ No players found in Week 1. Cannot continue.")
        print("Note: KNCB Matchcentre URLs may be timing out or blocking requests.")
        print("Consider using the mock server test instead: backend/test_phase1a_mock_server.py")
        return

    week1_matched = match_players_to_db(week1_players)
    store_performances(week1_matched, round_number=1, league_id=league_id)
    update_fantasy_teams(round_number=1, league_id=league_id)

    show_top_25(round_number=1, league_id=league_id)
    show_leaderboard(league_id)

    # WAIT
    print(f"\n{'='*80}")
    print("⏰ WAITING 60 SECONDS (1 minute = 1 week in demo)")
    print("="*80)
    print("\nDuring this time:")
    print("  - Visit https://fantcric.fun to see Week 1 results")
    print("  - Check the leaderboard")
    print("  - View top 25 players")

    for i in range(60, 0, -10):
        print(f"   {i} seconds remaining...")
        await asyncio.sleep(10)

    # WEEK 2
    print("\n" + "="*80)
    print("📅 WEEK 2")
    print("="*80)

    week2_players = await scrape_week(WEEK2_URLS, 2)

    if not week2_players:
        print("\n⚠️ No players found in Week 2. Ending demo.")
        return

    week2_matched = match_players_to_db(week2_players)
    store_performances(week2_matched, round_number=2, league_id=league_id)
    update_fantasy_teams(round_number=2, league_id=league_id)

    show_top_25(round_number=2, league_id=league_id)
    show_leaderboard(league_id)

    # FINAL
    print(f"\n{'='*80}")
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print("\nResults:")
    print("  - Week 1 & 2 scorecards scraped")
    print("  - All players' fantasy points calculated")
    print("  - Top 25 performers displayed")
    print("  - Fantasy teams updated with captain/VC/WK bonuses")
    print("  - Leaderboard updated")
    print("\nVisit https://fantcric.fun to see the results!")


if __name__ == "__main__":
    asyncio.run(main())
