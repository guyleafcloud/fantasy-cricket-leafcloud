#!/usr/bin/env python3
"""
Load 2025 Scorecards to Mock Server
====================================
Fetches all 136 ACC 2025 scorecards and prepares them for mock server to serve as 2026 data.

Strategy:
1. Fetch all 136 scorecards from real KNCB API (one-time operation)
2. Save to JSON files with 2026 dates (map 2025 → 2026)
3. Mock server will load these files and serve via its endpoints
4. Scraper will fetch from mock server thinking it's 2026 data
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from acc_2025_matches import ALL_2025_MATCHES

# Configuration
MOCK_DATA_DIR = "./mock_data/scorecards_2026"
BATCH_SIZE = 10  # Process 10 matches at a time
DELAY_BETWEEN_REQUESTS = 1  # seconds

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print('='*80 + '\n')

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def create_directories():
    """Create necessary directories for mock data"""
    os.makedirs(MOCK_DATA_DIR, exist_ok=True)
    os.makedirs(f"{MOCK_DATA_DIR}/by_match_id", exist_ok=True)
    os.makedirs(f"{MOCK_DATA_DIR}/by_team", exist_ok=True)
    os.makedirs(f"{MOCK_DATA_DIR}/by_week", exist_ok=True)
    print_success(f"Created directories in {MOCK_DATA_DIR}")


def fetch_scorecard(url: str) -> Dict:
    """
    Fetch a scorecard from the real KNCB API

    Args:
        url: Full scorecard URL from matchcentre.kncb.nl

    Returns:
        Dict containing scorecard HTML and metadata
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        return {
            'url': url,
            'html': response.text,
            'status_code': response.status_code,
            'content_length': len(response.text),
            'fetched_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print_error(f"Failed to fetch {url}: {str(e)}")
        return None


def map_2025_to_2026_date(period_id: int) -> str:
    """
    Map a 2025 period ID to a 2026 date

    Period IDs are sequential, we'll estimate dates based on season progression
    """
    # 2025 season: April 1 - September 30
    # First period ID: ~2821921 (early April)
    # Last period ID: ~3349431 (late September)

    BASE_PERIOD = 2821921
    SEASON_START = datetime(2026, 4, 1)  # 2026 season start
    SEASON_LENGTH_DAYS = 183  # April 1 - September 30

    # Estimate days into season based on period progression
    period_range = 3349431 - 2821921  # ~527510
    period_offset = period_id - BASE_PERIOD

    if period_offset < 0:
        period_offset = 0

    # Map period to days
    days_into_season = int((period_offset / period_range) * SEASON_LENGTH_DAYS)

    match_date = SEASON_START + timedelta(days=days_into_season)
    return match_date.strftime("%Y-%m-%d")


def extract_period_id(url: str) -> int:
    """Extract period ID from URL"""
    try:
        period_str = url.split('period=')[1]
        return int(period_str)
    except:
        return 0


def assign_week_number(date_str: str) -> int:
    """Assign week number based on date (1-12 weeks for April-September)"""
    match_date = datetime.strptime(date_str, "%Y-%m-%d")
    season_start = datetime(2026, 4, 1)

    days_since_start = (match_date - season_start).days
    week_number = (days_since_start // 7) + 1

    return max(1, min(12, week_number))  # Clamp to 1-12


def process_match(match: Dict, index: int, total: int) -> Dict:
    """
    Process a single match: fetch scorecard and prepare for 2026

    Args:
        match: Match dict with match_id, team, url
        index: Current match number
        total: Total matches

    Returns:
        Processed match data ready for mock server
    """
    print(f"\n[{index}/{total}] Processing {match['team']} - Match {match['match_id']}")

    # Fetch scorecard
    print(f"   Fetching from: {match['url']}")
    scorecard = fetch_scorecard(match['url'])

    if not scorecard:
        return None

    # Extract period ID and map to 2026 date
    period_id = extract_period_id(match['url'])
    date_2026 = map_2025_to_2026_date(period_id)
    week_number = assign_week_number(date_2026)

    print(f"   📅 2025 Period: {period_id} → 2026 Date: {date_2026} (Week {week_number})")
    print(f"   📄 Downloaded: {scorecard['content_length']} bytes")

    # Prepare processed match data
    processed = {
        'match_id': match['match_id'],
        'team': match['team'],
        'original_url_2025': match['url'],
        'period_id_2025': period_id,
        'mapped_date_2026': date_2026,
        'week_number': week_number,
        'scorecard_html': scorecard['html'],
        'metadata': {
            'fetched_at': scorecard['fetched_at'],
            'content_length': scorecard['content_length'],
            'status_code': scorecard['status_code']
        }
    }

    return processed


def save_match_data(match_data: Dict):
    """Save match data to multiple locations for easy lookup"""
    match_id = match_data['match_id']
    team = match_data['team']
    week = match_data['week_number']

    # Save by match ID
    match_file = f"{MOCK_DATA_DIR}/by_match_id/{match_id}.json"
    with open(match_file, 'w') as f:
        json.dump(match_data, f, indent=2)

    # Append to team file
    team_file = f"{MOCK_DATA_DIR}/by_team/{team.replace(' ', '_')}.json"
    if os.path.exists(team_file):
        with open(team_file, 'r') as f:
            team_matches = json.load(f)
    else:
        team_matches = []

    team_matches.append(match_data)
    with open(team_file, 'w') as f:
        json.dump(team_matches, f, indent=2)

    # Append to week file
    week_file = f"{MOCK_DATA_DIR}/by_week/week_{week:02d}.json"
    if os.path.exists(week_file):
        with open(week_file, 'r') as f:
            week_matches = json.load(f)
    else:
        week_matches = []

    week_matches.append(match_data)
    with open(week_file, 'w') as f:
        json.dump(week_matches, f, indent=2)


def create_index_file(all_matches: List[Dict]):
    """Create master index file with all matches"""
    index = {
        'total_matches': len(all_matches),
        'generated_at': datetime.utcnow().isoformat(),
        'season_year': 2026,
        'source_data': '2025 ACC matches mapped to 2026',
        'matches_by_team': {},
        'matches_by_week': {},
        'matches': []
    }

    # Group by team
    for match in all_matches:
        team = match['team']
        if team not in index['matches_by_team']:
            index['matches_by_team'][team] = []
        index['matches_by_team'][team].append({
            'match_id': match['match_id'],
            'date': match['mapped_date_2026'],
            'week': match['week_number']
        })

    # Group by week
    for match in all_matches:
        week = match['week_number']
        if week not in index['matches_by_week']:
            index['matches_by_week'][week] = []
        index['matches_by_week'][week].append({
            'match_id': match['match_id'],
            'team': match['team'],
            'date': match['mapped_date_2026']
        })

    # Summary list
    for match in all_matches:
        index['matches'].append({
            'match_id': match['match_id'],
            'team': match['team'],
            'date': match['mapped_date_2026'],
            'week': match['week_number'],
            'file': f"by_match_id/{match['match_id']}.json"
        })

    # Save index
    with open(f"{MOCK_DATA_DIR}/index.json", 'w') as f:
        json.dump(index, f, indent=2)

    print_success(f"Created index file with {len(all_matches)} matches")


def generate_statistics(all_matches: List[Dict]):
    """Generate and print statistics"""
    print_header("📊 Statistics")

    print(f"Total matches processed: {len(all_matches)}")

    # By team
    by_team = {}
    for match in all_matches:
        team = match['team']
        by_team[team] = by_team.get(team, 0) + 1

    print("\nMatches by team:")
    for team in sorted(by_team.keys()):
        print(f"   {team}: {by_team[team]} matches")

    # By week
    by_week = {}
    for match in all_matches:
        week = match['week_number']
        by_week[week] = by_week.get(week, 0) + 1

    print("\nMatches by week:")
    for week in sorted(by_week.keys()):
        print(f"   Week {week:2d}: {by_week[week]} matches")

    # Date range
    dates = [match['mapped_date_2026'] for match in all_matches]
    print(f"\nDate range: {min(dates)} to {max(dates)}")

    # Total data size
    total_size = sum(os.path.getsize(os.path.join(root, file))
                     for root, dirs, files in os.walk(MOCK_DATA_DIR)
                     for file in files)
    print(f"Total data size: {total_size / 1024 / 1024:.2f} MB")


def main():
    """Main execution function"""
    import time

    print_header("🏏 Load 2025 Scorecards to Mock Server (as 2026 data)")

    print(f"📋 Configuration:")
    print(f"   Source: {len(ALL_2025_MATCHES)} ACC matches from 2025 season")
    print(f"   Target: {MOCK_DATA_DIR}")
    print(f"   Strategy: Map 2025 dates → 2026 dates")
    print(f"   Batch size: {BATCH_SIZE} matches")

    # Create directories
    print()
    create_directories()

    # Ask for confirmation
    print(f"\n⚠️  This will fetch {len(ALL_2025_MATCHES)} scorecards from matchcentre.kncb.nl")
    print(f"   Estimated time: {len(ALL_2025_MATCHES) * 2 // 60} minutes")
    print(f"   Rate limit: {DELAY_BETWEEN_REQUESTS}s between requests")

    confirm = input("\nProceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return

    # Process all matches
    print_header("📥 Fetching Scorecards")

    processed_matches = []
    failed_matches = []

    for i, match in enumerate(ALL_2025_MATCHES, 1):
        try:
            processed = process_match(match, i, len(ALL_2025_MATCHES))

            if processed:
                save_match_data(processed)
                processed_matches.append(processed)
                print_success(f"Saved match {match['match_id']}")
            else:
                failed_matches.append(match)
                print_error(f"Failed to process match {match['match_id']}")

            # Rate limiting
            if i < len(ALL_2025_MATCHES):
                time.sleep(DELAY_BETWEEN_REQUESTS)

            # Progress update every 10 matches
            if i % 10 == 0:
                print(f"\n📊 Progress: {i}/{len(ALL_2025_MATCHES)} ({i*100//len(ALL_2025_MATCHES)}%)")
                print(f"   ✅ Success: {len(processed_matches)}")
                print(f"   ❌ Failed: {len(failed_matches)}\n")

        except KeyboardInterrupt:
            print_warning("\n\nInterrupted by user")
            break
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            failed_matches.append(match)

    # Create index
    if processed_matches:
        print()
        create_index_file(processed_matches)

    # Generate statistics
    if processed_matches:
        generate_statistics(processed_matches)

    # Summary
    print_header("✅ Complete")
    print(f"Successfully processed: {len(processed_matches)}/{len(ALL_2025_MATCHES)} matches")
    if failed_matches:
        print(f"\n❌ Failed matches ({len(failed_matches)}):")
        for match in failed_matches[:10]:  # Show first 10
            print(f"   - {match['team']}: {match['match_id']}")
        if len(failed_matches) > 10:
            print(f"   ... and {len(failed_matches) - 10} more")

    print(f"\n📁 Data saved to: {MOCK_DATA_DIR}")
    print(f"   - By match ID: {MOCK_DATA_DIR}/by_match_id/")
    print(f"   - By team: {MOCK_DATA_DIR}/by_team/")
    print(f"   - By week: {MOCK_DATA_DIR}/by_week/")
    print(f"   - Index: {MOCK_DATA_DIR}/index.json")

    print("\n📝 Next steps:")
    print("   1. Review generated data: cat mock_data/scorecards_2026/index.json")
    print("   2. Update mock_kncb_server.py to load this data")
    print("   3. Start mock server: ./start_mock_server.sh")
    print("   4. Test scraper with mock mode")


if __name__ == "__main__":
    main()
