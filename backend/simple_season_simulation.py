#!/usr/bin/env python3
"""
Simple Season Simulation
Process matches week by week from mock data and update database
"""
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

from kncb_html_scraper import KNCBMatchCentreScraper
from scraper_config import get_scraper_config, ScraperMode
from database import get_db_session
from database_models import PlayerPerformance

# ANSI colors
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
ENDC = '\033[0m'


async def process_week(week_num: int, scraper: KNCBMatchCentreScraper):
    """Process all matches for a week"""
    week_file = Path('/app/mock_data/scorecards_2026/by_week') / f'week_{week_num:02d}.json'

    if not week_file.exists():
        print(f"{YELLOW}No data for week {week_num}{ENDC}")
        return 0

    with open(week_file) as f:
        matches = json.load(f)

    print(f"\n{CYAN}{BOLD}━━━ WEEK {week_num} - {len(matches)} matches ━━━{ENDC}")

    total_players = 0

    for i, match_data in enumerate(matches, 1):
        match_id = match_data['match_id']
        team = match_data.get('team', 'Unknown')

        print(f"  [{i}/{len(matches)}] Match {match_id} ({team})...", end=' ', flush=True)

        try:
            # Scrape scorecard
            scorecard = await scraper.scrape_match_scorecard(match_id)

            if scorecard:
                # Extract players
                players = scraper.extract_player_stats(scorecard, team, 'tier2')

                # Save to database
                with get_db_session() as db:
                    for player in players:
                        perf = PlayerPerformance(
                            player_name=player['player_name'],
                            match_id=match_id,
                            runs=player['batting'].get('runs', 0),
                            balls_faced=player['batting'].get('balls_faced', 0),
                            fours=player['batting'].get('fours', 0),
                            sixes=player['batting'].get('sixes', 0),
                            wickets=player['bowling'].get('wickets', 0),
                            overs_bowled=player['bowling'].get('overs', 0.0),
                            runs_conceded=player['bowling'].get('runs_conceded', 0),
                            maidens=player['bowling'].get('maidens', 0),
                            catches=player['fielding'].get('catches', 0),
                            stumpings=player['fielding'].get('stumpings', 0),
                            run_outs=player['fielding'].get('runouts', 0),
                            fantasy_points=player.get('fantasy_points', 0),
                            tier='tier2'
                        )
                        db.add(perf)

                total_players += len(players)
                print(f"{GREEN}✓ {len(players)} players{ENDC}")
            else:
                print(f"{YELLOW}✗ No data{ENDC}")

        except Exception as e:
            print(f"{YELLOW}✗ Error: {str(e)[:30]}{ENDC}")

        await asyncio.sleep(0.1)

    print(f"{GREEN}✅ Week {week_num} complete: {total_players} player performances{ENDC}")
    return total_players


async def main():
    """Run the simulation"""
    print(f"\n{CYAN}{BOLD}{'='*60}{ENDC}")
    print(f"{CYAN}{BOLD}🏏 FANTASY CRICKET SEASON SIMULATION 🏏{ENDC}")
    print(f"{CYAN}{BOLD}{'='*60}{ENDC}\n")

    # Initialize scraper in MOCK mode
    config = get_scraper_config(ScraperMode.MOCK)
    scraper = KNCBMatchCentreScraper(config=config)
    print(f"{GREEN}✅ Scraper initialized in MOCK mode{ENDC}")
    print(f"{CYAN}📡 Mock server: {config.matchcentre_url}{ENDC}\n")

    # Process weeks 1-12
    start_time = time.time()
    total_performances = 0

    for week in range(1, 13):
        week_start = time.time()

        performances = await process_week(week, scraper)
        total_performances += performances

        week_time = time.time() - week_start
        print(f"{CYAN}⏱️  Week {week} processed in {week_time:.1f}s{ENDC}")

        # Pause between weeks (50 seconds to make it ~10 minutes total)
        if week < 12:
            print(f"{YELLOW}⏸️  Next week in 50s...{ENDC}")
            await asyncio.sleep(50)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{GREEN}{BOLD}{'='*60}{ENDC}")
    print(f"{GREEN}{BOLD}🎉 SEASON COMPLETE! 🎉{ENDC}")
    print(f"{GREEN}{BOLD}{'='*60}{ENDC}\n")
    print(f"{GREEN}Duration: {elapsed/60:.1f} minutes{ENDC}")
    print(f"{GREEN}Total performances: {total_performances}{ENDC}")
    print(f"{GREEN}Average per week: {total_performances/12:.0f}{ENDC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Simulation interrupted{ENDC}")
    except Exception as e:
        print(f"\n{YELLOW}Error: {e}{ENDC}")
        import traceback
        traceback.print_exc()
