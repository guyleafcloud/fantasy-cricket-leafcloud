#!/usr/bin/env python3
"""
Populate 2025 Season Stats from Match Centre Profiles
======================================================
Scrapes player profile pages to get their actual 2025 season statistics.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfileStatsScraper:
    """Scrape player stats from Match Centre profile pages"""

    def __init__(self, database_file: str):
        self.database_file = database_file
        self.stats_updated = 0
        self.stats_failed = 0
        self.no_id_count = 0

    async def scrape_player_stats(self, player_id: str, player_name: str) -> Optional[Dict]:
        """Scrape a single player's 2025 season stats from their profile summary"""

        url = f"https://matchcentre.kncb.nl/player/{player_id}/19/"

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(1)

                # Get page text
                page_text = await page.inner_text('body')
                lines = [line.strip() for line in page_text.split('\n')]

                # Initialize stats
                stats = {
                    'runs': 0,
                    'batting_avg': 0.0,
                    'strike_rate': 0.0,
                    'wickets': 0,
                    'bowling_avg': 0.0,
                    'economy': 0.0,
                    'catches': 0,
                    'run_outs': 0
                }

                # Find "SUMMARY" and "CURRENT SEASON" section
                summary_idx = None
                for i, line in enumerate(lines):
                    if line == 'SUMMARY' and i + 1 < len(lines) and 'CURRENT SEASON' in lines[i + 1]:
                        summary_idx = i + 2  # Start after "CURRENT SEASON (X MATCHES)"
                        break

                if summary_idx is None:
                    logger.warning(f"   ⚠️  No SUMMARY section for {player_name}")
                    await browser.close()
                    return None

                # Parse summary stats (alternating pattern: value, label, value, label...)
                # Expected pattern:
                # 201
                # TOTAL RUNS
                # 14.36
                # BATTING AVERAGE
                # 43
                # HIGHEST SCORE
                # 1
                # WICKETS
                # 45.00
                # BOWLING AVERAGE

                for i in range(summary_idx, min(summary_idx + 40, len(lines) - 1)):
                    line = lines[i]
                    next_line = lines[i + 1] if i + 1 < len(lines) else ""

                    # Check if next line is a label
                    next_lower = next_line.lower()

                    # Parse based on label in next line
                    if 'total runs' in next_lower or 'run' in next_lower:
                        try:
                            stats['runs'] = int(line)
                        except:
                            pass

                    elif 'batting average' in next_lower:
                        try:
                            stats['batting_avg'] = float(line)
                        except:
                            pass

                    elif 'strike rate' in next_lower:
                        try:
                            stats['strike_rate'] = float(line)
                        except:
                            pass

                    elif 'wickets' in next_lower and 'best' not in next_lower:
                        try:
                            stats['wickets'] = int(line)
                        except:
                            pass

                    elif 'bowling average' in next_lower:
                        try:
                            stats['bowling_avg'] = float(line)
                        except:
                            pass

                    elif 'economy' in next_lower:
                        try:
                            stats['economy'] = float(line)
                        except:
                            pass

                    elif 'catches' in next_lower:
                        try:
                            stats['catches'] = int(line)
                        except:
                            pass

                    # Stop when we hit "MATCH BY MATCH" section
                    if 'MATCH BY MATCH' in line:
                        break

                await browser.close()

                # Only return if we found some stats
                if stats['runs'] > 0 or stats['wickets'] > 0 or stats['catches'] > 0:
                    logger.info(f"   ✅ {player_name:30s} | R:{stats['runs']:3d} W:{stats['wickets']:2d} C:{stats['catches']:2d} | SR:{stats['strike_rate']:.1f} Econ:{stats['economy']:.2f}")
                    return stats
                else:
                    logger.warning(f"   ⚠️  No stats found for {player_name}")
                    return None

            except Exception as e:
                logger.error(f"   ❌ Error scraping {player_name}: {e}")
                return None

    async def update_all_players(self):
        """Update all players with their 2025 stats"""

        logger.info("=" * 80)
        logger.info("🔍 SCRAPING PLAYER PROFILES FOR 2025 SEASON STATS")
        logger.info("=" * 80)

        # Load database
        with open(self.database_file, 'r') as f:
            database = json.load(f)

        players = database.get('players', [])
        logger.info(f"\n📋 Loaded {len(players)} players from database")

        # Filter players with Match Centre IDs
        players_with_ids = [p for p in players if p.get('matchcentre_id')]
        players_without_ids = [p for p in players if not p.get('matchcentre_id')]

        logger.info(f"   Players WITH IDs: {len(players_with_ids)}")
        logger.info(f"   Players WITHOUT IDs: {len(players_without_ids)}")

        # Scrape stats for players with IDs
        logger.info(f"\n🌐 Scraping {len(players_with_ids)} player profiles...")

        for i, player in enumerate(players_with_ids, 1):
            player_id = player['matchcentre_id']
            player_name = player['name']

            logger.info(f"\n[{i}/{len(players_with_ids)}] {player_name} (ID: {player_id})")

            stats = await self.scrape_player_stats(player_id, player_name)

            if stats:
                # Update player stats
                player['stats'].update(stats)
                self.stats_updated += 1
            else:
                self.stats_failed += 1

            # Rate limiting - don't overwhelm the server
            if i % 10 == 0:
                logger.info(f"\n⏸️  Processed {i}/{len(players_with_ids)} players, pausing for 2 seconds...")
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(0.5)

        # Save updated database
        logger.info(f"\n💾 Saving updated database...")
        with open(self.database_file, 'w') as f:
            json.dump(database, f, indent=2)

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 SCRAPING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"   Total players: {len(players)}")
        logger.info(f"   Players with IDs: {len(players_with_ids)}")
        logger.info(f"   Stats updated: {self.stats_updated}")
        logger.info(f"   Stats failed: {self.stats_failed}")
        logger.info(f"   Players without IDs: {len(players_without_ids)}")
        logger.info("=" * 80)


async def main():
    scraper = ProfileStatsScraper('rosters/acc_legacy_database.json')
    await scraper.update_all_players()


if __name__ == "__main__":
    asyncio.run(main())
