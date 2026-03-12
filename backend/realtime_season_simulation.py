#!/usr/bin/env python3
"""
Real-Time Season Simulation
============================
Simulates a full 2026 season in ~10-15 minutes by processing matches week by week.
Updates the app after each week so you can watch your team progress in real-time!

Usage:
    python3 realtime_season_simulation.py

Requirements:
    - Mock server must be running with preloaded data
    - Database must be reset to clean state
    - Frontend must be running to watch progress
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from kncb_html_scraper import KNCBMatchCentreScraper
from scraper_config import get_scraper_config, ScraperMode
from fantasy_team_points_service import update_all_fantasy_team_points
from database_models import get_db, PlayerPerformance, FantasyTeam
from sqlalchemy import func

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}📊 {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_progress(week: int, total_weeks: int, matches: int):
    """Print progress bar"""
    progress = (week / total_weeks) * 100
    bar_length = 50
    filled = int(bar_length * week / total_weeks)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"{Colors.OKCYAN}Week {week}/{total_weeks} [{bar}] {progress:.0f}% | {matches} matches{Colors.ENDC}")


async def reset_season():
    """Reset database to clean state for new season"""
    print_header("RESETTING SEASON")

    db = next(get_db())

    try:
        # Clear all player performances
        perf_count = db.query(PlayerPerformance).count()
        db.query(PlayerPerformance).delete()
        print_success(f"Cleared {perf_count} player performances")

        # Reset all fantasy team points
        teams = db.query(FantasyTeam).all()
        for team in teams:
            team.total_points = 0
            team.last_round_points = 0

        print_success(f"Reset {len(teams)} fantasy teams to 0 points")

        db.commit()
        print_success("Database reset complete!")

        return len(teams)

    except Exception as e:
        db.rollback()
        print(f"{Colors.FAIL}❌ Error resetting season: {e}{Colors.ENDC}")
        raise
    finally:
        db.close()


def load_week_matches(week_num: int) -> List[Dict]:
    """Load matches for a specific week from preloaded data"""
    week_file = Path(__file__).parent / f"mock_data/scorecards_2026/by_week/week_{week_num:02d}.json"

    if not week_file.exists():
        return []

    with open(week_file, 'r') as f:
        return json.load(f)


async def scrape_week_matches(week_num: int, scraper: KNCBMatchCentreScraper) -> int:
    """Scrape all matches for a specific week"""
    matches = load_week_matches(week_num)

    if not matches:
        print_warning(f"No matches found for week {week_num}")
        return 0

    print_info(f"Week {week_num}: Processing {len(matches)} matches...")

    performances_count = 0

    for i, match_data in enumerate(matches, 1):
        match_id = match_data['match_id']
        team = match_data.get('team', 'Unknown')

        # Show progress within week
        print(f"   [{i}/{len(matches)}] Match {match_id} ({team})...", end=' ')

        try:
            # Scrape scorecard
            scorecard = await scraper.scrape_match_scorecard(match_id)

            if scorecard:
                # Extract player stats
                players = scraper.extract_player_stats(scorecard, team, 'tier2')

                # Save to database
                db = next(get_db())
                try:
                    for player in players:
                        # Create performance record
                        perf = PlayerPerformance(
                            player_name=player['player_name'],
                            match_id=match_id,
                            runs=player['batting'].get('runs', 0),
                            balls_faced=player['batting'].get('balls_faced', 0),
                            fours=player['batting'].get('fours', 0),
                            sixes=player['batting'].get('sixes', 0),
                            wickets=player['bowling'].get('wickets', 0),
                            overs=player['bowling'].get('overs', 0.0),
                            runs_conceded=player['bowling'].get('runs_conceded', 0),
                            maidens=player['bowling'].get('maidens', 0),
                            catches=player['fielding'].get('catches', 0),
                            stumpings=player['fielding'].get('stumpings', 0),
                            runouts=player['fielding'].get('runouts', 0),
                            fantasy_points=player.get('fantasy_points', 0),
                            tier='tier2'
                        )
                        db.add(perf)

                    db.commit()
                    performances_count += len(players)
                    print(f"{Colors.OKGREEN}✓ {len(players)} players{Colors.ENDC}")

                except Exception as e:
                    db.rollback()
                    print(f"{Colors.FAIL}✗ DB error{Colors.ENDC}")
                finally:
                    db.close()
            else:
                print(f"{Colors.WARNING}✗ No data{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}✗ Error: {str(e)[:30]}{Colors.ENDC}")

        # Small delay to avoid overwhelming the mock server
        await asyncio.sleep(0.1)

    return performances_count


def update_fantasy_points(week_num: int) -> Dict:
    """Update all fantasy team points after week completion"""
    print_info(f"Calculating fantasy points for week {week_num}...")

    db = next(get_db())
    try:
        # Get all teams
        teams = db.query(FantasyTeam).all()

        # Update points for each team
        for team in teams:
            update_all_fantasy_team_points(db, team.id)

        db.commit()

        # Get statistics
        stats = {
            'total_teams': len(teams),
            'total_performances': db.query(PlayerPerformance).count(),
            'avg_points': db.query(func.avg(FantasyTeam.total_points)).scalar() or 0,
            'max_points': db.query(func.max(FantasyTeam.total_points)).scalar() or 0,
            'min_points': db.query(func.min(FantasyTeam.total_points)).scalar() or 0
        }

        return stats

    finally:
        db.close()


def show_top_teams(top_n: int = 5):
    """Show current top teams"""
    db = next(get_db())
    try:
        teams = db.query(FantasyTeam).order_by(FantasyTeam.total_points.desc()).limit(top_n).all()

        print(f"\n{Colors.OKBLUE}🏆 Current Top {top_n} Teams:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'Rank':<6}{'Team Name':<30}{'Manager':<20}{'Points':<12}{'Last Week':<10}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'-'*78}{Colors.ENDC}")

        for i, team in enumerate(teams, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji} {i:<4}{team.team_name:<30}{team.user.username:<20}"
                  f"{team.total_points:<12.1f}{team.last_round_points:<10.1f}")

    finally:
        db.close()


async def run_realtime_simulation():
    """Run full season simulation in real-time"""
    print_header("🏏 FANTASY CRICKET - REAL-TIME SEASON SIMULATION 🏏")

    print(f"{Colors.OKCYAN}This will simulate the entire 2026 season (12 weeks) in ~10-15 minutes")
    print(f"Watch your team progress in real-time on the frontend!")
    print(f"URL: http://localhost:3000{Colors.ENDC}\n")

    input(f"{Colors.WARNING}Press ENTER to start simulation...{Colors.ENDC}")

    # Step 1: Reset season
    team_count = await reset_season()
    print_info(f"Season reset complete - {team_count} teams ready to compete!\n")

    await asyncio.sleep(2)

    # Step 2: Initialize scraper in MOCK mode
    print_header("INITIALIZING SCRAPER")
    config = get_scraper_config(ScraperMode.MOCK)
    scraper = KNCBMatchCentreScraper(config=config)
    print_success("Scraper initialized in MOCK mode")
    print_info(f"Using mock server: {config.matchcentre_url}\n")

    await asyncio.sleep(1)

    # Step 3: Load available weeks
    weeks_dir = Path(__file__).parent / "mock_data/scorecards_2026/by_week"
    week_files = sorted([f for f in weeks_dir.glob("week_*.json")])
    total_weeks = len(week_files)

    print_header(f"STARTING SEASON - {total_weeks} WEEKS")

    start_time = time.time()
    total_performances = 0

    # Step 4: Process each week
    for week_num in range(1, total_weeks + 1):
        week_start = time.time()

        print(f"\n{Colors.BOLD}{Colors.HEADER}{'━'*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  WEEK {week_num} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'━'*80}{Colors.ENDC}\n")

        # Scrape matches for this week
        performances = await scrape_week_matches(week_num, scraper)
        total_performances += performances

        if performances > 0:
            # Update fantasy points
            stats = update_fantasy_points(week_num)

            print(f"\n{Colors.OKGREEN}✅ Week {week_num} Complete!{Colors.ENDC}")
            print_info(f"Performances: {performances} | Total: {total_performances}")
            print_info(f"Avg Team Points: {stats['avg_points']:.1f} | Max: {stats['max_points']:.1f}")

            # Show top teams
            show_top_teams(top_n=5)
        else:
            print_warning(f"Week {week_num} had no matches")

        # Show progress
        week_time = time.time() - week_start
        print(f"\n{Colors.OKCYAN}⏱️  Week processed in {week_time:.1f}s{Colors.ENDC}")
        print_progress(week_num, total_weeks, performances)

        # Pause between weeks (adjust this to control simulation speed)
        # Total simulation time ~= pause_time * total_weeks
        # For 10 minutes over 12 weeks: 50 seconds per week
        pause_time = 50  # seconds

        if week_num < total_weeks:
            print(f"\n{Colors.WARNING}⏸️  Next week starts in {pause_time}s... (Open http://localhost:3000 to watch!){Colors.ENDC}")
            await asyncio.sleep(pause_time)

    # Final summary
    elapsed = time.time() - start_time

    print_header("🎉 SEASON COMPLETE! 🎉")

    print(f"{Colors.OKGREEN}Season Duration: {elapsed/60:.1f} minutes{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Total Weeks: {total_weeks}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Total Performances: {total_performances}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Average per week: {total_performances/total_weeks:.0f}{Colors.ENDC}\n")

    # Show final standings
    print_header("🏆 FINAL STANDINGS 🏆")
    show_top_teams(top_n=10)

    print(f"\n{Colors.OKBLUE}View full leaderboard at: http://localhost:3000/leaderboard{Colors.ENDC}")
    print(f"{Colors.OKBLUE}View your team at: http://localhost:3000/dashboard{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_realtime_simulation())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Simulation interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
