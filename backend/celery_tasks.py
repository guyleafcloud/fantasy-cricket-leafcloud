#!/usr/bin/env python3
"""
Celery Tasks for KNCB Fantasy Cricket
======================================
Autonomous scheduled tasks for scraping and updating player data.
Includes season-long aggregation of player statistics.
"""

from celery import Celery
from celery.schedules import crontab
import os
import logging
import asyncio
from kncb_html_scraper import KNCBMatchCentreScraper
from player_aggregator import PlayerSeasonAggregator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://fantasy_cricket_redis:6379")

app = Celery(
    "fantasy_cricket_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure beat schedule
app.conf.beat_schedule = {
    # Scrape match data every Monday at 1 AM (after weekend matches)
    'scrape-weekly-matches': {
        'task': 'celery_tasks.scrape_kncb_weekly',
        'schedule': crontab(day_of_week='monday', hour=1, minute=0),
    },
    # Adjust player multipliers every Monday at 2 AM (after scraping)
    'adjust-multipliers-weekly': {
        'task': 'celery_tasks.adjust_multipliers_weekly',
        'schedule': crontab(day_of_week='monday', hour=2, minute=0),
    },
    # Backup aggregated data every day at 3 AM
    'backup-season-data': {
        'task': 'celery_tasks.backup_season_aggregates',
        'schedule': crontab(hour=3, minute=0),
    },
}

app.conf.timezone = 'Europe/Amsterdam'

# Clubs to scrape (configure these based on your league)
CONFIGURED_CLUBS = [
    "VRA",
    "ACC",
    "VOC",
    "HCC",
    "Excelsior '20",
    # Add more clubs as needed
]

# Global aggregator instance (persists between tasks)
aggregator = PlayerSeasonAggregator()

# Load previous season data if exists
aggregator.load_from_file('season_aggregates.json')

# Load legacy rosters (from previous season)
def load_legacy_rosters():
    """Load legacy player rosters from previous season"""
    from legacy_roster_loader import LegacyRosterLoader
    import glob
    import os

    loader = LegacyRosterLoader()
    total_imported = 0

    # Find all legacy roster files
    roster_files = glob.glob('rosters/*_roster.json')

    if not roster_files:
        logger.info("ℹ️  No legacy rosters found")
        return 0

    logger.info(f"📥 Loading legacy rosters from {len(roster_files)} file(s)...")

    for roster_file in roster_files:
        club_name = os.path.basename(roster_file).split('_')[0].upper()
        logger.info(f"   Loading {club_name} roster from {roster_file}")

        legacy_players = loader.load_from_json(roster_file)
        count = loader.import_to_aggregator(aggregator, legacy_players)
        total_imported += count

    logger.info(f"✅ Legacy roster loading complete: {total_imported} players imported")
    return total_imported

# Load legacy rosters on startup
legacy_count = load_legacy_rosters()


@app.task(name='celery_tasks.scrape_kncb_weekly')
def scrape_kncb_weekly():
    """
    Scrape KNCB match data weekly and aggregate player stats
    Runs every Monday at 1 AM (after weekend matches)

    This task:
    1. Scrapes recent matches for configured clubs
    2. Extracts player performances
    3. Updates season aggregates (cumulative totals)
    4. Saves aggregated data
    5. Syncs to database
    """
    logger.info("🏏 Starting weekly KNCB scrape with aggregation...")

    try:
        # Run async scraper
        loop = asyncio.get_event_loop()
        scraper = KNCBMatchCentreScraper()

        results = loop.run_until_complete(
            scraper.scrape_weekly_update(CONFIGURED_CLUBS, days_back=7)
        )

        logger.info(f"✅ Scrape complete! {results['total_performances']} performances")

        # Aggregate all performances into season totals
        logger.info("📊 Aggregating player statistics...")

        new_players = 0
        updated_players = 0

        for performance in results['performances']:
            player_id = performance.get('player_id')

            # Check if new player
            was_new = player_id not in aggregator.players

            # Add/update performance
            aggregator.add_match_performance(performance)

            if was_new:
                new_players += 1
            else:
                updated_players += 1

        logger.info(f"🆕 New players discovered: {new_players}")
        logger.info(f"🔄 Existing players updated: {updated_players}")

        # Save aggregated data to file
        aggregator.save_to_file('season_aggregates.json')

        # Get summary
        summary = aggregator.get_season_summary()

        logger.info(f"\n📈 Season Summary:")
        logger.info(f"   Total players: {summary['total_players']}")
        logger.info(f"   Clubs: {summary['clubs']}")

        # TODO: Sync to database
        # db_data = aggregator.export_to_database_format()
        # sync_to_database(db_data)

        return {
            "status": "success",
            "performances_scraped": results['total_performances'],
            "new_players": new_players,
            "updated_players": updated_players,
            "total_players": summary['total_players'],
            "clubs": results['clubs']
        }

    except Exception as e:
        logger.error(f"❌ Weekly scrape failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.backup_season_aggregates')
def backup_season_aggregates():
    """
    Backup aggregated season data
    Runs daily at 3 AM
    """
    logger.info("💾 Backing up season aggregates...")

    try:
        # Save to file
        aggregator.save_to_file('season_aggregates.json')

        # Also create dated backup
        from datetime import datetime
        backup_filename = f"season_aggregates_backup_{datetime.now().strftime('%Y%m%d')}.json"
        aggregator.save_to_file(backup_filename)

        summary = aggregator.get_season_summary()

        logger.info(f"✅ Backup complete!")
        logger.info(f"   Players: {summary['total_players']}")

        return {
            "status": "success",
            "players_backed_up": summary['total_players']
        }

    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.scrape_single_match')
def scrape_single_match(match_id: int):
    """
    Scrape a single match by ID
    Can be triggered manually via API
    """
    logger.info(f"📥 Scraping match {match_id}...")

    try:
        loop = asyncio.get_event_loop()
        scraper = KNCBMatchCentreScraper()

        scorecard = loop.run_until_complete(
            scraper.scrape_match_scorecard(match_id)
        )

        if scorecard:
            logger.info(f"✅ Match {match_id} scraped successfully")
            return {"status": "success", "scorecard": scorecard}
        else:
            logger.warning(f"⚠️  Could not scrape match {match_id}")
            return {"status": "error", "error": "Scorecard not found"}

    except Exception as e:
        logger.error(f"❌ Match scrape failed: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.adjust_multipliers_weekly')
def adjust_multipliers_weekly():
    """
    Adjust player multipliers based on performance with 15% weekly drift
    Runs every Monday at 2 AM (after weekly scrape)
    """
    logger.info("🎯 Adjusting player multipliers (weekly drift)...")

    try:
        from multiplier_adjuster import MultiplierAdjuster
        from database_setup import SessionLocal

        # Create database session
        db = SessionLocal()

        try:
            # Create adjuster with 15% drift rate
            adjuster = MultiplierAdjuster(drift_rate=0.15)

            # Adjust multipliers for all players
            result = adjuster.adjust_multipliers(db, dry_run=False)

            logger.info(f"✅ Multiplier adjustment complete!")
            logger.info(f"   Total players: {result['total_players']}")
            logger.info(f"   Players changed: {result['players_changed']}")

            # Log top changes
            if result['top_changes']:
                logger.info(f"\n📊 Top multiplier changes:")
                for change in result['top_changes'][:5]:
                    direction = "↑" if change['change'] > 0 else "↓"
                    logger.info(
                        f"      {change['player_name']}: "
                        f"{change['old_multiplier']:.2f} → {change['new_multiplier']:.2f} "
                        f"({direction}{abs(change['change']):.2f})"
                    )

            return {
                "status": "success",
                "players_adjusted": result['players_changed'],
                "total_players": result['total_players'],
                "drift_rate": result['drift_rate']
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Multiplier adjustment failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


# =============================================================================
# DATA ACCESS HELPERS
# =============================================================================

def get_player_stats(player_id: str) -> dict:
    """Get season stats for a specific player"""
    return aggregator.get_player(player_id)


def get_club_roster(club_name: str) -> list:
    """Get all players for a specific club"""
    return aggregator.get_players_by_club(club_name)


def get_top_fantasy_scorers(limit: int = 10) -> list:
    """Get top fantasy point scorers"""
    return aggregator.get_top_players(limit, sort_by='fantasy_points')


def get_top_run_scorers(limit: int = 10) -> list:
    """Get top run scorers"""
    return aggregator.get_top_players(limit, sort_by='runs')


def get_top_wicket_takers(limit: int = 10) -> list:
    """Get top wicket takers"""
    return aggregator.get_top_players(limit, sort_by='wickets')


def get_season_summary() -> dict:
    """Get overall season summary"""
    return aggregator.get_season_summary()


# =============================================================================
# MANUAL TRIGGERS (for testing)
# =============================================================================

def trigger_scrape_now():
    """Manually trigger a scrape (for testing)"""
    result = scrape_kncb_weekly.delay()
    return result.id


def trigger_backup_now():
    """Manually trigger backup (for testing)"""
    result = backup_season_aggregates.delay()
    return result.id


if __name__ == "__main__":
    print("🔧 Celery Tasks Configuration with Aggregation")
    print("=" * 70)
    print("\n📅 Scheduled Tasks:")
    print("   - Weekly scrape + aggregation: Every Monday at 1:00 AM")
    print("   - Daily backup: Every day at 3:00 AM")
    print(f"\n🏏 Configured clubs: {', '.join(CONFIGURED_CLUBS)}")

    # Show current season stats if available
    summary = aggregator.get_season_summary()
    if summary['total_players'] > 0:
        print(f"\n📊 Current Season Stats:")
        print(f"   Total players: {summary['total_players']}")
        print(f"   Clubs: {summary['clubs']}")
        print(f"\n🏆 Top 5 Fantasy Scorers:")
        for player in aggregator.get_top_players(5):
            print(f"      {player['player_name']}: {player['season_totals']['fantasy_points']} pts")

    print("\n✅ Celery tasks ready!")
    print("\nTo start Celery:")
    print("   celery -A celery_tasks worker --loglevel=info")
    print("   celery -A celery_tasks beat --loglevel=info")
