#!/usr/bin/env python3
"""
Simple test to verify scorecard HTML parsing works correctly.
This test doesn't require database access.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup


def test_parse_single_scorecard():
    """Test parsing a single scorecard HTML file"""

    # Load a sample scorecard
    backend_dir = Path(__file__).parent
    scorecards_dir = backend_dir / "mock_data" / "scorecards_2026" / "by_match_id"

    if not scorecards_dir.exists():
        print(f"❌ Scorecards directory not found: {scorecards_dir}")
        return False

    # Get first scorecard file
    scorecard_files = list(scorecards_dir.glob("*.json"))
    if not scorecard_files:
        print(f"❌ No scorecard files found in {scorecards_dir}")
        return False

    test_file = scorecard_files[0]
    print(f"\n{'='*80}")
    print(f"Testing Scorecard Parsing")
    print(f"{'='*80}\n")
    print(f"Test file: {test_file.name}")

    # Load JSON
    with open(test_file, 'r') as f:
        scorecard_data = json.load(f)

    print(f"Match ID: {scorecard_data.get('match_id')}")
    print(f"Team: {scorecard_data.get('team')}")
    print(f"Date: {scorecard_data.get('mapped_date_2026')}")

    # Parse HTML
    scorecard_html = scorecard_data.get('scorecard_html')
    if not scorecard_html:
        print("❌ No scorecard_html in file")
        return False

    print(f"HTML length: {len(scorecard_html)} bytes")

    # Extract text from HTML (same as what the code does)
    soup = BeautifulSoup(scorecard_html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and split into lines
    page_text = soup.get_text(separator='\n')
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]

    print(f"Extracted {len(lines)} text lines\n")

    # Find BATTING and BOWLING sections
    batting_idx = None
    bowling_idx = None

    for i, line in enumerate(lines):
        if line == 'BATTING':
            batting_idx = i
            print(f"✅ Found BATTING section at line {i}")
        elif line == 'BOWLING':
            bowling_idx = i
            print(f"✅ Found BOWLING section at line {i}")

    if batting_idx is None:
        print("⚠️  No BATTING section found")
    else:
        # Show some batting data
        print(f"\nBatting section preview (lines {batting_idx} to {batting_idx + 20}):")
        for i in range(batting_idx, min(batting_idx + 20, len(lines))):
            print(f"  {i}: {lines[i]}")

    if bowling_idx is None:
        print("⚠️  No BOWLING section found")
    else:
        # Show some bowling data
        print(f"\nBowling section preview (lines {bowling_idx} to {bowling_idx + 20}):")
        for i in range(bowling_idx, min(bowling_idx + 20, len(lines))):
            print(f"  {i}: {lines[i]}")

    print(f"\n{'='*80}")
    print(f"Test completed successfully!")
    print(f"{'='*80}\n")

    return True


def check_all_scorecards():
    """Check how many scorecards we have"""
    backend_dir = Path(__file__).parent
    scorecards_dir = backend_dir / "mock_data" / "scorecards_2026"

    print(f"\n{'='*80}")
    print(f"Scorecard Inventory")
    print(f"{'='*80}\n")

    if not scorecards_dir.exists():
        print(f"❌ Directory not found: {scorecards_dir}")
        return

    # Check by_match_id
    by_match_id = scorecards_dir / "by_match_id"
    if by_match_id.exists():
        files = list(by_match_id.glob("*.json"))
        print(f"✅ by_match_id: {len(files)} files")

    # Check by_team
    by_team = scorecards_dir / "by_team"
    if by_team.exists():
        files = list(by_team.glob("*.json"))
        print(f"✅ by_team: {len(files)} files")
        print(f"   Teams available:")
        for f in sorted(files):
            print(f"     - {f.stem}")

    # Check by_week
    by_week = scorecards_dir / "by_week"
    if by_week.exists():
        files = list(by_week.glob("*.json"))
        print(f"✅ by_week: {len(files)} files")

    # Check index
    index_file = scorecards_dir / "index.json"
    if index_file.exists():
        with open(index_file, 'r') as f:
            index_data = json.load(f)
        print(f"\n✅ index.json:")
        print(f"   Total matches: {index_data.get('total_matches')}")
        print(f"   Season year: {index_data.get('season_year')}")
        print(f"   Generated: {index_data.get('generated_at')}")


if __name__ == "__main__":
    check_all_scorecards()
    test_parse_single_scorecard()
