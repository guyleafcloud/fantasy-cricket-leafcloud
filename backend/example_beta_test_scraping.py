#!/usr/bin/env python3
"""
Example: Beta Test Scraping with Mock Data
===========================================
Demonstrates how to use the scraper in mock mode for beta testing.

This script simulates a weekly scraping workflow:
1. Fetch matches for configured clubs
2. Scrape match scorecards
3. Extract player stats
4. Calculate fantasy points
5. Prepare data for database update

Usage:
    python3 example_beta_test_scraping.py
"""

import asyncio
import logging
from datetime import datetime
from scraper_config import get_scraper_config, ScraperMode, print_config
from kncb_html_scraper import KNCBMatchCentreScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def scrape_weekly_matches(clubs: list, mode: ScraperMode = ScraperMode.MOCK):
    """
    Scrape weekly matches for all configured clubs

    Args:
        clubs: List of club names to scrape
        mode: Scraper mode (MOCK or PRODUCTION)
    """
    print("="*80)
    print(f"🏏 WEEKLY MATCH SCRAPING - {mode.value.upper()} MODE")
    print("="*80)

    # Initialize scraper
    config = get_scraper_config(mode)
    print_config(config)

    scraper = KNCBMatchCentreScraper(config=config)

    all_player_performances = []
    match_count = 0

    for club in clubs:
        print(f"\n📊 Processing club: {club}")
        print("-"*80)

        try:
            # Fetch recent matches
            matches = await scraper.get_recent_matches_for_club(
                club_name=club,
                days_back=7,  # Last week
                season_id=19
            )

            if not matches:
                logger.warning(f"No matches found for {club}")
                continue

            logger.info(f"Found {len(matches)} matches for {club}")

            # Process each match
            for i, match in enumerate(matches):
                match_id = match.get('match_id')
                home = match.get('home_club_name', 'Unknown')
                away = match.get('away_club_name', 'Unknown')
                grade = match.get('grade_name', 'Unknown')

                print(f"\n   Match {i+1}/{len(matches)}: {home} vs {away} ({grade})")

                # Scrape scorecard
                scorecard = await scraper.scrape_match_scorecard(match_id)

                if not scorecard:
                    logger.warning(f"   Failed to get scorecard for match {match_id}")
                    continue

                # Extract player stats
                tier = match.get('tier', 'tier2')
                players = scraper.extract_player_stats(scorecard, club, tier)

                if not players:
                    logger.warning(f"   No players extracted from match {match_id}")
                    continue

                logger.info(f"   ✅ Extracted {len(players)} players")

                # Add match metadata
                for player in players:
                    player['match_id'] = match_id
                    player['match_date'] = match.get('match_date_time', '')
                    player['grade'] = grade
                    player['home_team'] = home
                    player['away_team'] = away

                all_player_performances.extend(players)
                match_count += 1

                # Show top performer from this match
                if players:
                    top_player = max(players, key=lambda p: p.get('fantasy_points', 0))
                    name = top_player.get('name', 'Unknown')
                    points = top_player.get('fantasy_points', 0)
                    print(f"   🏆 Top performer: {name} ({points:.1f} pts)")

        except Exception as e:
            logger.error(f"Error processing {club}: {e}")
            continue

    # Summary
    print("\n" + "="*80)
    print("📊 SCRAPING SUMMARY")
    print("="*80)
    print(f"Clubs processed: {len(clubs)}")
    print(f"Matches scraped: {match_count}")
    print(f"Player performances: {len(all_player_performances)}")

    # Top performers across all matches
    if all_player_performances:
        print(f"\n🏆 TOP 10 PERFORMERS THIS WEEK:")
        print("-"*80)

        sorted_players = sorted(
            all_player_performances,
            key=lambda p: p.get('fantasy_points', 0),
            reverse=True
        )

        for i, player in enumerate(sorted_players[:10]):
            name = player.get('name', 'Unknown')
            club = player.get('club', 'Unknown')
            points = player.get('fantasy_points', 0)
            grade = player.get('grade', 'Unknown')

            # Get stats
            batting = player.get('batting', {})
            bowling = player.get('bowling', {})

            stats = []
            if batting.get('runs', 0) > 0:
                stats.append(f"{batting['runs']}({batting.get('balls_faced', 0)})")
            if bowling.get('wickets', 0) > 0:
                stats.append(f"{bowling['wickets']}/{bowling.get('runs_conceded', 0)}")

            stats_str = ", ".join(stats) if stats else "DNB/DNB"

            print(f"{i+1:2d}. {name:20s} ({club:15s}) - {points:6.1f} pts - {stats_str} - {grade}")

    return all_player_performances


async def simulate_beta_test_season(weeks: int = 4):
    """
    Simulate multiple weeks of beta testing

    Args:
        weeks: Number of weeks to simulate
    """
    print("\n" + "="*80)
    print(f"🧪 SIMULATING {weeks}-WEEK BETA TEST SEASON")
    print("="*80)

    # Clubs to monitor (example - adjust based on your beta testers)
    clubs = ["VRA", "ACC", "HCC"]

    all_weeks_data = []

    for week in range(1, weeks + 1):
        print(f"\n\n{'='*80}")
        print(f"📅 WEEK {week}")
        print(f"{'='*80}")

        # Scrape matches (mock mode generates new data each time)
        week_performances = await scrape_weekly_matches(clubs, mode=ScraperMode.MOCK)

        all_weeks_data.append({
            'week': week,
            'date': datetime.now().isoformat(),
            'performances': week_performances
        })

        print(f"\n✅ Week {week} complete: {len(week_performances)} performances")

        # In real scenario, you would:
        # 1. Update database with performances
        # 2. Calculate fantasy team scores
        # 3. Update leaderboards
        # 4. Adjust player multipliers

    # Final summary
    print("\n\n" + "="*80)
    print("📊 BETA TEST SEASON SUMMARY")
    print("="*80)

    total_performances = sum(len(week['performances']) for week in all_weeks_data)
    print(f"Total weeks: {weeks}")
    print(f"Total performances: {total_performances}")
    print(f"Avg performances per week: {total_performances / weeks:.1f}")

    print("\n✅ Beta test simulation complete!")
    print("\nNext steps:")
    print("  1. Review data quality and completeness")
    print("  2. Validate fantasy point calculations")
    print("  3. Check leaderboard updates")
    print("  4. Gather beta tester feedback")
    print("  5. Adjust rules if needed")

    return all_weeks_data


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--season":
        # Simulate full season
        weeks = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        await simulate_beta_test_season(weeks=weeks)
    else:
        # Single week scrape
        clubs = ["VRA", "ACC"]
        await scrape_weekly_matches(clubs, mode=ScraperMode.MOCK)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              FANTASY CRICKET - BETA TEST SCRAPING EXAMPLE                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

Usage:
  # Single week scrape
  python3 example_beta_test_scraping.py

  # Full season simulation (4 weeks)
  python3 example_beta_test_scraping.py --season 4

This example demonstrates:
  ✓ Mock mode scraping
  ✓ Multi-club processing
  ✓ Player stats extraction
  ✓ Fantasy points calculation
  ✓ Weekly aggregation
  ✓ Season simulation

""")

    asyncio.run(main())
