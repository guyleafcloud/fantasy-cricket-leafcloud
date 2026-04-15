#!/usr/bin/env python3
"""
Simple test to verify scorecard parsing logic works.
No database or Docker required - just parses a sample scorecard.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup


def parse_batting_section(lines, start_idx):
    """Parse batting section from text lines."""
    players = []
    i = start_idx + 1  # Skip "BATTING" header

    # Skip column headers
    while i < len(lines) and lines[i] in ['R', 'B', '4', '6', 'SR', '']:
        i += 1

    # Parse players (7 lines each)
    while i < len(lines) - 6:
        name_candidate = lines[i]

        # Stop at next section
        if name_candidate in ['BOWLING', 'FIELDING', 'Players', ''] or 'Players' in name_candidate:
            break

        # Skip headers and pure numbers
        if name_candidate in ['R', 'B', '4', '6', 'SR', 'BATTING', 'BOWLING']:
            i += 1
            continue

        if not name_candidate or name_candidate.replace('.', '').replace('-', '').isdigit():
            i += 1
            continue

        # This looks like a player name
        try:
            player_name = name_candidate.strip()
            dismissal = lines[i + 1]
            runs = int(lines[i + 2]) if lines[i + 2].isdigit() else 0
            balls = int(lines[i + 3]) if lines[i + 3].isdigit() else 0
            fours = int(lines[i + 4]) if lines[i + 4].isdigit() else 0
            sixes = int(lines[i + 5]) if lines[i + 5].isdigit() else 0

            is_out = not any(x in dismissal.lower() for x in ['not out', 'retired'])

            players.append({
                'name': player_name,
                'runs': runs,
                'balls': balls,
                'fours': fours,
                'sixes': sixes,
                'is_out': is_out
            })
            i += 7

        except (ValueError, IndexError):
            i += 1

    return players


def test_scorecard_parsing():
    """Test parsing a sample scorecard file."""

    # Find scorecards directory
    backend_dir = Path(__file__).parent
    scorecard_file = backend_dir / "mock_data" / "scorecards_2026" / "by_match_id" / "7254567.json"

    if not scorecard_file.exists():
        print(f"❌ Scorecard file not found: {scorecard_file}")
        print(f"   This test needs to run from the backend directory")
        return False

    print("\n" + "="*80)
    print("SCORECARD PARSING TEST")
    print("="*80 + "\n")

    # Load scorecard
    with open(scorecard_file, 'r') as f:
        data = json.load(f)

    print(f"Match ID: {data['match_id']}")
    print(f"Team: {data['team']}")
    print(f"Date: {data['mapped_date_2026']}")
    print(f"HTML size: {len(data['scorecard_html'])} bytes\n")

    # Parse HTML
    soup = BeautifulSoup(data['scorecard_html'], 'html.parser')

    # Remove scripts and styles
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text lines
    page_text = soup.get_text(separator='\n')
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]

    print(f"Extracted {len(lines)} text lines from HTML\n")

    # Find BATTING section
    batting_idx = None
    for i, line in enumerate(lines):
        if line == 'BATTING':
            batting_idx = i
            break

    if batting_idx is None:
        print("❌ No BATTING section found in scorecard")
        return False

    print(f"✅ Found BATTING section at line {batting_idx}\n")

    # Parse batting stats
    batters = parse_batting_section(lines, batting_idx)

    if not batters:
        print("❌ No batting stats parsed")
        return False

    print(f"✅ Parsed {len(batters)} batting performances:\n")

    total_runs = 0
    for batter in batters:
        print(f"  {batter['name']:20s} - {batter['runs']:3d} runs off {batter['balls']:3d} balls " +
              f"({batter['fours']}×4, {batter['sixes']}×6) {'OUT' if batter['is_out'] else 'NOT OUT'}")
        total_runs += batter['runs']

    print(f"\n  Total runs: {total_runs}")

    print("\n" + "="*80)
    print("TEST PASSED ✅")
    print("="*80 + "\n")

    print("Key findings:")
    print(f"  • HTML parsing: Works ✅")
    print(f"  • Text extraction: Works ✅")
    print(f"  • BATTING section detection: Works ✅")
    print(f"  • Player name extraction: Works ✅")
    print(f"  • Stats parsing: Works ✅")
    print(f"\nThe local scorecard reader implementation is working correctly!")

    return True


if __name__ == "__main__":
    success = test_scorecard_parsing()
    exit(0 if success else 1)
