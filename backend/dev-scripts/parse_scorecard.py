#!/usr/bin/env python3
"""
Scorecard Parser
================
Parses KNCB Match Centre scorecard pages.
"""

import asyncio
import re
from typing import Dict, List, Tuple
from playwright.async_api import async_playwright


class ScorecardParser:
    """Parse scorecard from KNCB Match Centre"""

    @staticmethod
    def parse_batting_section(lines: List[str], start_idx: int) -> Tuple[List[Dict], int]:
        """
        Parse batting section starting from 'BATTING' line.
        Returns (list of player dicts, next line index to continue from)
        """
        players = []
        i = start_idx

        # Skip "BATTING" header
        if lines[i].strip() == 'BATTING':
            i += 1

        # Skip column headers (R, B, 4, 6, SR)
        while i < len(lines) and lines[i].strip() in ['R', 'B', '4', '6', 'SR', '']:
            i += 1

        # Parse players (each player is 7 lines: name, dismissal, R, B, 4, 6, SR)
        while i < len(lines) - 6:
            # Check if we hit the next section
            if lines[i].strip() in ['BOWLING', 'FIELDING', '']:
                break

            # Check if this looks like a player name (not a pure number or cricket term)
            name_candidate = lines[i].strip()
            if not name_candidate:
                i += 1
                continue

            # Skip if it's a header or section marker
            if name_candidate in ['R', 'B', '4', '6', 'SR', 'BATTING', 'BOWLING', 'FIELDING']:
                i += 1
                continue

            # Skip if it's just a number
            if name_candidate.replace('.', '').isdigit():
                i += 1
                continue

            # This looks like a player name
            player_name = name_candidate

            # Check if we have at least 6 more lines for the stats
            if i + 6 >= len(lines):
                break

            dismissal = lines[i + 1].strip()

            # Try to parse stats (next 5 lines should be: runs, balls, fours, sixes, SR)
            try:
                runs_str = lines[i + 2].strip()
                balls_str = lines[i + 3].strip()
                fours_str = lines[i + 4].strip()
                sixes_str = lines[i + 5].strip()
                sr_str = lines[i + 6].strip()

                # Parse numbers
                runs = int(runs_str) if runs_str.isdigit() else 0
                balls = int(balls_str) if balls_str.isdigit() else 0
                fours = int(fours_str) if fours_str.isdigit() else 0
                sixes = int(sixes_str) if sixes_str.isdigit() else 0
                sr = float(sr_str) if sr_str.replace('.', '').isdigit() else 0.0

                player = {
                    'name': player_name,
                    'dismissal': dismissal,
                    'runs': runs,
                    'balls_faced': balls,
                    'fours': fours,
                    'sixes': sixes,
                    'strike_rate': sr
                }
                players.append(player)

                # Move to next player (skip 7 lines total)
                i += 7

            except (ValueError, IndexError):
                # If parsing fails, just skip this line
                i += 1

        return players, i

    @staticmethod
    def parse_bowling_section(lines: List[str], start_idx: int) -> Tuple[List[Dict], int]:
        """
        Parse bowling section starting from 'BOWLING' line.
        Returns (list of bowler dicts, next line index)
        """
        bowlers = []
        i = start_idx

        # Skip "BOWLING" header
        if lines[i].strip() == 'BOWLING':
            i += 1

        # Skip column headers (O, M, R, W, NB, WD)
        while i < len(lines) and lines[i].strip() in ['O', 'M', 'R', 'W', 'NB', 'WD', '']:
            i += 1

        # Parse bowlers (each bowler is 7 lines: name, overs, maidens, runs, wickets, NB, WD)
        while i < len(lines) - 6:
            # Check if we hit the next section or team name
            if lines[i].strip() in ['FIELDING', 'Players', ''] or 'Players' in lines[i]:
                break

            name_candidate = lines[i].strip()
            if not name_candidate:
                i += 1
                continue

            # Skip headers
            if name_candidate in ['O', 'M', 'R', 'W', 'NB', 'WD', 'BOWLING', 'FIELDING']:
                i += 1
                continue

            # Skip pure numbers
            if name_candidate.replace('.', '').isdigit():
                i += 1
                continue

            # This looks like a bowler name
            bowler_name = name_candidate

            # Check if we have at least 6 more lines for stats
            if i + 6 >= len(lines):
                break

            try:
                overs_str = lines[i + 1].strip()
                maidens_str = lines[i + 2].strip()
                runs_str = lines[i + 3].strip()
                wickets_str = lines[i + 4].strip()
                nb_str = lines[i + 5].strip()
                wd_str = lines[i + 6].strip()

                # Parse numbers
                overs = float(overs_str) if overs_str.replace('.', '').isdigit() else 0.0
                maidens = int(maidens_str) if maidens_str.isdigit() else 0
                runs = int(runs_str) if runs_str.isdigit() else 0
                wickets = int(wickets_str) if wickets_str.isdigit() else 0
                no_balls = int(nb_str) if nb_str.isdigit() else 0
                wides = int(wd_str) if wd_str.isdigit() else 0

                bowler = {
                    'name': bowler_name,
                    'overs': overs,
                    'maidens': maidens,
                    'runs_conceded': runs,
                    'wickets': wickets,
                    'no_balls': no_balls,
                    'wides': wides
                }
                bowlers.append(bowler)

                # Move to next bowler
                i += 7

            except (ValueError, IndexError):
                i += 1

        return bowlers, i

    @staticmethod
    async def scrape_scorecard(url: str) -> Dict:
        """
        Scrape a single scorecard URL and return structured data
        """
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Load the page
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Let React render

            # Get page title and text
            title = await page.title()
            page_text = await page.inner_text('body')
            lines = page_text.split('\n')

            # Extract team names
            teams = []
            team_pattern = r'(ACC[^<>\"]*(?:1|2|3|4|5|6|ZAMI|U\d+)?)'
            content = await page.content()
            team_matches = re.findall(team_pattern, content)
            if team_matches:
                unique_teams = list(set([t.strip() for t in team_matches if 3 < len(t.strip()) < 50]))
                teams = unique_teams

            # Find batting and bowling sections
            batting_players = []
            bowling_players = []

            for i, line in enumerate(lines):
                if line.strip() == 'BATTING':
                    players, next_i = ScorecardParser.parse_batting_section(lines, i)
                    batting_players.extend(players)

                elif line.strip() == 'BOWLING':
                    bowlers, next_i = ScorecardParser.parse_bowling_section(lines, i)
                    bowling_players.extend(bowlers)

            result = {
                'url': url,
                'title': title,
                'teams': teams,
                'batting': batting_players,
                'bowling': bowling_players
            }

            return result

        finally:
            await browser.close()
            await playwright.stop()


async def test_parser():
    """Test the parser on the example scorecard"""
    url = "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194"

    print("🏏 Testing Scorecard Parser")
    print(f"   URL: {url}")
    print()

    result = await ScorecardParser.scrape_scorecard(url)

    print(f"✅ Match: {result['title']}")
    print(f"   Teams: {result['teams']}")
    print()

    print(f"📊 BATTING ({len(result['batting'])} players):")
    for player in result['batting'][:5]:  # Show first 5
        print(f"   {player['name']:<20} {player['runs']:>3}r ({player['balls_faced']}b) "
              f"{player['fours']}×4 {player['sixes']}×6 - {player['dismissal'][:30]}")

    if len(result['batting']) > 5:
        print(f"   ... and {len(result['batting']) - 5} more")

    print()
    print(f"🎯 BOWLING ({len(result['bowling'])} bowlers):")
    for bowler in result['bowling'][:5]:  # Show first 5
        print(f"   {bowler['name']:<20} {bowler['overs']:>4}o {bowler['maidens']}m "
              f"{bowler['runs_conceded']:>3}r {bowler['wickets']}w")

    if len(result['bowling']) > 5:
        print(f"   ... and {len(result['bowling']) - 5} more")

    print()
    print("🔍 Filtering ACC players...")
    acc_batting = [p for p in result['batting'] if any(team in str(result['teams']) for team in ['ACC'])]
    acc_bowling = [p for p in result['bowling'] if any(team in str(result['teams']) for team in ['ACC'])]

    print(f"   ACC batting entries: {len(result['batting'])} (all shown above)")
    print(f"   ACC bowling entries: {len(result['bowling'])} (from opponent)")


if __name__ == "__main__":
    asyncio.run(test_parser())
