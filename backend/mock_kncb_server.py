#!/usr/bin/env python3
"""
Mock KNCB Match Centre API Server
==================================
Serves simulated match data in the exact format the KNCB API provides.
This allows testing the scraper without depending on real matches.

TWO MODES:
1. RANDOM MODE: Generates random match data on-the-fly (default)
2. PRELOADED MODE: Serves pre-fetched 2025 scorecards as 2026 data

Usage:
    python3 mock_kncb_server.py

The server will run on http://localhost:5001
Configure the scraper to use this URL instead of matchcentre.kncb.nl

Environment Variables:
    MOCK_DATA_DIR: Path to directory with pre-loaded scorecards (optional)
                   If set, server will use PRELOADED MODE
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import logging
import os
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

MOCK_DATA_DIR = os.environ.get('MOCK_DATA_DIR', None)
PRELOADED_MODE = MOCK_DATA_DIR is not None and os.path.exists(MOCK_DATA_DIR)

# KNCB entity ID (standard for all KNCB matches)
# This is used in URL validation: /match/{ENTITY_ID}-{match_id}/scorecard/
ENTITY_ID = "134453"

# Store entity ID in app config for route access
app.config['ENTITY_ID'] = ENTITY_ID

# In-memory cache for preloaded data
preloaded_index = None
preloaded_scorecards = {}


# ============================================================================
# PRELOADED DATA LOADING
# ============================================================================

def load_preloaded_index():
    """Load the index file with all match metadata"""
    global preloaded_index

    if not PRELOADED_MODE:
        return None

    index_path = Path(MOCK_DATA_DIR) / "index.json"

    if not index_path.exists():
        logger.error(f"❌ Index file not found: {index_path}")
        return None

    try:
        with open(index_path, 'r') as f:
            preloaded_index = json.load(f)

        logger.info(f"✅ Loaded preloaded index: {preloaded_index['total_matches']} matches")
        logger.info(f"   Season: {preloaded_index['season_year']}")
        logger.info(f"   Teams: {len(preloaded_index['matches_by_team'])}")
        logger.info(f"   Weeks: {len(preloaded_index['matches_by_week'])}")

        return preloaded_index
    except Exception as e:
        logger.error(f"❌ Failed to load index: {str(e)}")
        return None


def load_scorecard_by_match_id(match_id):
    """Load a specific scorecard by match ID (lazy loading)"""
    if not PRELOADED_MODE:
        return None

    # Check cache first
    if match_id in preloaded_scorecards:
        return preloaded_scorecards[match_id]

    # Load from file
    scorecard_path = Path(MOCK_DATA_DIR) / "by_match_id" / f"{match_id}.json"

    if not scorecard_path.exists():
        logger.warning(f"⚠️  Scorecard not found: {match_id}")
        return None

    try:
        with open(scorecard_path, 'r') as f:
            scorecard_data = json.load(f)

        # Cache it
        preloaded_scorecards[match_id] = scorecard_data

        logger.info(f"📄 Loaded scorecard for match {match_id} ({scorecard_data['team']})")
        return scorecard_data
    except Exception as e:
        logger.error(f"❌ Failed to load scorecard {match_id}: {str(e)}")
        return None


def get_scorecards_by_week(week_number):
    """Get all scorecards for a specific week"""
    if not PRELOADED_MODE:
        return []

    week_path = Path(MOCK_DATA_DIR) / "by_week" / f"week_{week_number:02d}.json"

    if not week_path.exists():
        logger.warning(f"⚠️  Week file not found: week {week_number}")
        return []

    try:
        with open(week_path, 'r') as f:
            week_data = json.load(f)

        logger.info(f"📅 Loaded {len(week_data)} matches for week {week_number}")
        return week_data
    except Exception as e:
        logger.error(f"❌ Failed to load week {week_number}: {str(e)}")
        return []


def get_scorecards_by_team(team_name):
    """Get all scorecards for a specific team"""
    if not PRELOADED_MODE:
        return []

    team_file = team_name.replace(' ', '_') + '.json'
    team_path = Path(MOCK_DATA_DIR) / "by_team" / team_file

    if not team_path.exists():
        logger.warning(f"⚠️  Team file not found: {team_name}")
        return []

    try:
        with open(team_path, 'r') as f:
            team_data = json.load(f)

        logger.info(f"🏏 Loaded {len(team_data)} matches for team {team_name}")
        return team_data
    except Exception as e:
        logger.error(f"❌ Failed to load team {team_name}: {str(e)}")
        return []


# ============================================================================
# SIMULATED DATA GENERATION (Random Mode)
# ============================================================================

# Club names (from your system)
CLUBS = [
    "VRA", "ACC", "Excelsior '20", "VOC", "Quick Haag",
    "HCC", "HBS", "Kampong", "SV Kampong Cricket", "Rood en Wit"
]

# Grade structure
GRADES = [
    {"grade_id": 1, "grade_name": "Hoofdklasse", "season_id": 19},
    {"grade_id": 2, "grade_name": "Topklasse", "season_id": 19},
    {"grade_id": 3, "grade_name": "Eerste Klasse", "season_id": 19},
    {"grade_id": 4, "grade_name": "Tweede Klasse", "season_id": 19},
    {"grade_id": 5, "grade_name": "Derde Klasse", "season_id": 19},
]

# Player name generator - Realistic Dutch and Indian cricket names
DUTCH_FIRST_NAMES = [
    "Pieter", "Jan", "Willem", "Lars", "Bas", "Thijs", "Daan", "Tim",
    "Sander", "Ruben", "Max", "Bram", "Jesse", "Jasper", "Luuk", "Tom",
    "Jeroen", "Martijn", "Stijn", "Floris", "Maarten", "Niels"
]

DUTCH_LAST_NAMES = [
    "de Jong", "van Dijk", "Jansen", "Bakker", "Visser", "de Vries",
    "van den Berg", "Mulder", "Smit", "van Leeuwen", "van der Meer",
    "Hendriks", "de Boer", "Bos", "van Dam", "Dijkstra", "van der Wal"
]

INDIAN_FIRST_NAMES = [
    "Arjun", "Vikram", "Rohan", "Amit", "Rahul", "Sanjay", "Ajay",
    "Aditya", "Kiran", "Nikhil", "Vivek", "Suresh", "Raj", "Ankit",
    "Ravi", "Ashok", "Deepak", "Manoj", "Sandeep", "Pradeep"
]

INDIAN_LAST_NAMES = [
    "Patel", "Kumar", "Singh", "Shah", "Sharma", "Gupta", "Reddy",
    "Nair", "Iyer", "Chopra", "Mehta", "Rao", "Shetty", "Desai",
    "Verma", "Joshi", "Bhat", "Kulkarni", "Menon", "Agarwal"
]

# In-memory storage for simulated matches
simulated_matches = {}
match_counter = 100000  # Start match IDs at 100000


def generate_player_name():
    """Generate realistic Dutch or Indian cricket player name (60% Dutch, 40% Indian - reflects ACC demographics)"""
    if random.random() < 0.6:
        # Dutch name
        first = random.choice(DUTCH_FIRST_NAMES)
        last = random.choice(DUTCH_LAST_NAMES)
        return f"{first} {last}"
    else:
        # Indian name
        first = random.choice(INDIAN_FIRST_NAMES)
        last = random.choice(INDIAN_LAST_NAMES)
        return f"{first} {last}"


def simulate_batting_performance():
    """Simulate a batting performance with realistic stats"""
    # Probability of getting out
    is_out = random.random() < 0.7

    if not is_out:
        # Not out innings (lower scores)
        runs = random.choices(
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45],
            weights=[5, 10, 15, 15, 15, 10, 10, 8, 7, 5]
        )[0]
    else:
        # Out innings (wider range)
        runs = random.choices(
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100],
            weights=[8, 15, 15, 12, 10, 8, 8, 6, 5, 4, 3, 2, 1.5, 1, 0.5, 0.3]
        )[0]

    # Calculate balls faced (SR between 50-200)
    sr = random.uniform(50, 200)
    balls_faced = max(1, int(runs / sr * 100)) if runs > 0 else random.randint(1, 10)

    # Calculate boundaries (roughly)
    fours = runs // 8 + random.randint(0, 2)
    sixes = runs // 20 + (1 if random.random() < 0.2 else 0)

    dismissal_types = ["c", "b", "lbw", "run out", "st", "hit wicket"]
    dismissal = random.choice(dismissal_types) if is_out else "not out"

    return {
        "runs": runs,
        "balls_faced": balls_faced,
        "fours": fours,
        "sixes": sixes,
        "dismissal": dismissal,
        "is_out": is_out
    }


def simulate_bowling_performance(overs_available=10):
    """Simulate a bowling performance"""
    # How many overs bowled (0-10)
    overs_bowled = random.uniform(0, min(overs_available, 10))

    if overs_bowled < 1:
        return None  # Didn't bowl

    # Round to nearest .1 (6 balls per over)
    overs_bowled = round(overs_bowled * 6) / 6

    # Wickets (0-5, heavily weighted toward 0-2)
    wickets = random.choices(
        [0, 1, 2, 3, 4, 5],
        weights=[30, 30, 20, 10, 5, 2]
    )[0]

    # Economy rate (3-9 runs per over)
    economy_rate = random.uniform(3.0, 9.0)
    runs_conceded = int(overs_bowled * economy_rate)

    # Maidens (0-3)
    max_maidens = int(overs_bowled)
    maidens = random.choices(
        range(max_maidens + 1),
        weights=[50] + [20] * max_maidens
    )[0] if max_maidens > 0 else 0

    return {
        "overs": overs_bowled,
        "maidens": maidens,
        "runs_conceded": runs_conceded,
        "wickets": wickets
    }


def simulate_fielding_performance():
    """Simulate fielding stats"""
    # Most players don't take catches/stumpings
    catches = random.choices([0, 1, 2, 3], weights=[70, 20, 8, 2])[0]
    stumpings = random.choices([0, 1], weights=[95, 5])[0]
    runouts = random.choices([0, 1], weights=[90, 10])[0]

    return {
        "catches": catches,
        "stumpings": stumpings,
        "runouts": runouts
    }


def generate_match_scorecard(match_id, home_club, away_club, grade_name):
    """Generate a full match scorecard with realistic data"""

    # Generate teams (11 players each)
    home_players = [generate_player_name() for _ in range(11)]
    away_players = [generate_player_name() for _ in range(11)]

    # Simulate innings
    innings = []

    # First innings (away team bats)
    first_innings = {
        "batting_team": away_club,
        "batting": [],
        "bowling": [],
        "extras": random.randint(5, 25),
        "total": 0,
        "wickets": 0
    }

    # Batting performances
    for i, player in enumerate(away_players):
        perf = simulate_batting_performance()
        batting_order = i + 1

        first_innings["batting"].append({
            "player_name": player,  # Changed from batsman_name
            "batting_position": batting_order,
            "runs": perf["runs"],
            "balls_faced": perf["balls_faced"],
            "fours": perf["fours"],
            "sixes": perf["sixes"],
            "dismissal_type": perf["dismissal"],
            "is_out": perf["is_out"]
        })

        first_innings["total"] += perf["runs"]
        if perf["is_out"]:
            first_innings["wickets"] += 1

    first_innings["total"] += first_innings["extras"]

    # Bowling performances (5-7 bowlers from home team)
    num_bowlers = random.randint(5, 7)
    selected_bowlers = random.sample(home_players, num_bowlers)

    for bowler in selected_bowlers:
        perf = simulate_bowling_performance(overs_available=10)
        if perf:
            first_innings["bowling"].append({
                "player_name": bowler,  # Changed from bowler_name
                "overs": perf["overs"],
                "maidens": perf["maidens"],
                "runs": perf["runs_conceded"],
                "wickets": perf["wickets"]
            })

    innings.append(first_innings)

    # Second innings (home team bats)
    second_innings = {
        "batting_team": home_club,
        "batting": [],
        "bowling": [],
        "extras": random.randint(5, 25),
        "total": 0,
        "wickets": 0
    }

    # Batting performances
    for i, player in enumerate(home_players):
        perf = simulate_batting_performance()
        batting_order = i + 1

        second_innings["batting"].append({
            "player_name": player,  # Changed from batsman_name
            "batting_position": batting_order,
            "runs": perf["runs"],
            "balls_faced": perf["balls_faced"],
            "fours": perf["fours"],
            "sixes": perf["sixes"],
            "dismissal_type": perf["dismissal"],
            "is_out": perf["is_out"]
        })

        second_innings["total"] += perf["runs"]
        if perf["is_out"]:
            second_innings["wickets"] += 1

    second_innings["total"] += second_innings["extras"]

    # Bowling performances (away team)
    num_bowlers = random.randint(5, 7)
    selected_bowlers = random.sample(away_players, num_bowlers)

    for bowler in selected_bowlers:
        perf = simulate_bowling_performance(overs_available=10)
        if perf:
            second_innings["bowling"].append({
                "player_name": bowler,  # Changed from bowler_name
                "overs": perf["overs"],
                "maidens": perf["maidens"],
                "runs": perf["runs_conceded"],
                "wickets": perf["wickets"]
            })

    innings.append(second_innings)

    # Fielding stats (distributed across both teams)
    fielding = []
    all_players = [(p, home_club) for p in home_players] + [(p, away_club) for p in away_players]

    for player, club in all_players:
        perf = simulate_fielding_performance()
        if perf["catches"] > 0 or perf["stumpings"] > 0 or perf["runouts"] > 0:
            fielding.append({
                "player_name": player,  # Changed from fielder_name
                "club_name": club,
                "catches": perf["catches"],
                "stumpings": perf["stumpings"],
                "runouts": perf["runouts"]
            })

    return {
        "match_id": match_id,
        "home_club": home_club,
        "away_club": away_club,
        "grade_name": grade_name,
        "match_date": datetime.now().isoformat(),
        "innings": innings,
        "fielding": fielding,
        "result": f"{home_club} won by {abs(first_innings['total'] - second_innings['total'])} runs"
            if first_innings["total"] > second_innings["total"]
            else f"{away_club} won by {10 - first_innings['wickets']} wickets"
    }


# ============================================================================
# API ENDPOINTS (Mimicking KNCB API)
# ============================================================================

@app.route('/rv/<entity_id>/grades/', methods=['GET'])
def get_grades(entity_id):
    """Return list of grades/leagues"""
    logger.info(f"📋 GET /grades - Returning {len(GRADES)} grades")
    return jsonify(GRADES)


@app.route('/rv/<entity_id>/matches/', methods=['GET'])
def get_matches(entity_id):
    """Return list of matches for a grade"""
    season_id = request.args.get('seasonId', 19, type=int)
    grade_id = request.args.get('gradeId', 1, type=int)

    # Find grade
    grade = next((g for g in GRADES if g['grade_id'] == grade_id), GRADES[0])
    grade_name = grade['grade_name']

    # Generate 10-20 random matches for this grade
    num_matches = random.randint(10, 20)
    matches = []

    global match_counter

    for i in range(num_matches):
        # Random clubs
        home_club = random.choice(CLUBS)
        away_club = random.choice([c for c in CLUBS if c != home_club])

        # Random date in last 30 days
        days_ago = random.randint(0, 30)
        match_date = datetime.now() - timedelta(days=days_ago)

        match_id = match_counter
        match_counter += 1

        match_data = {
            "match_id": match_id,
            "home_club_name": home_club,
            "away_club_name": away_club,
            "match_date_time": match_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "grade_id": grade_id,
            "grade_name": grade_name,
            "season_id": season_id,
            "status": "Complete"
        }

        matches.append(match_data)

        # Store match for later scorecard retrieval
        if match_id not in simulated_matches:
            simulated_matches[match_id] = generate_match_scorecard(
                match_id, home_club, away_club, grade_name
            )

    logger.info(f"📊 GET /matches - Returning {len(matches)} matches for grade {grade_name}")
    return jsonify(matches)


@app.route('/rv/match/<int:match_id>/', methods=['GET'])
def get_match_scorecard(match_id):
    """Return detailed scorecard for a match"""

    # Check if we have this match already
    if match_id in simulated_matches:
        scorecard = simulated_matches[match_id]
    else:
        # Generate on the fly
        home_club = random.choice(CLUBS)
        away_club = random.choice([c for c in CLUBS if c != home_club])
        grade = random.choice(GRADES)

        scorecard = generate_match_scorecard(
            match_id, home_club, away_club, grade['grade_name']
        )
        simulated_matches[match_id] = scorecard

    logger.info(f"📥 GET /match/{match_id} - Returning scorecard")
    return jsonify(scorecard)


@app.route('/match/<path:match_path>/scorecard/', methods=['GET'])
@app.route('/match/<path:match_path>/scorecard', methods=['GET'])
def get_scorecard_html(match_path):
    """
    Return scorecard HTML for a match

    This mimics the KNCB matchcentre.kncb.nl format:
    /match/{entity_id}-{match_id}/scorecard/?period={period_id}

    IMPORTANT: Handles both 2025 and 2026 season URLs
    - 2025: Uses preloaded data (mapped from 2025 to 2026)
    - 2026: Will handle real-time when season starts (April 2026)

    In PRELOADED MODE: Serves pre-fetched 2025 HTML as 2026 data
    In RANDOM MODE: Generates React-style HTML with vertical layout
    """
    # Extract entity_id and match_id from path
    # Expected format: "134453-12345" or just "12345" (backwards compatible)
    entity_id = None
    match_id_str = None

    if '-' in match_path:
        # Standard format: entity_id-match_id
        parts = match_path.rsplit('-', 1)  # Split from right to handle multi-hyphen cases
        entity_id = parts[0]
        match_id_str = parts[1]

        # Validate entity ID matches expected value (134453 for KNCB)
        if entity_id != str(app.config.get('ENTITY_ID', '134453')):
            logger.warning(f"⚠️  URL entity ID '{entity_id}' doesn't match expected '134453'")
            logger.warning(f"   This may indicate a format issue or different entity")
    else:
        # Backwards compatible: just match_id
        match_id_str = match_path
        logger.info(f"📝 URL format note: Using legacy format (match_id only)")
        logger.info(f"   Production URLs should be: /match/134453-{match_id_str}/scorecard/")

    # Parse match_id
    try:
        match_id = int(match_id_str)
    except ValueError:
        logger.error(f"❌ Invalid match ID in path: {match_path}")
        return Response("Invalid match ID", status=404)

    # Check for period parameter (optional, used in 2025 URLs)
    period_id = request.args.get('period')
    if period_id:
        logger.info(f"📅 Period ID provided: {period_id} (2025 season mapping)")

    logger.info(f"📄 GET /match/{match_path}/scorecard/ - Match ID: {match_id}")

    # PRELOADED MODE: Serve pre-fetched scorecard HTML
    if PRELOADED_MODE:
        scorecard_data = load_scorecard_by_match_id(match_id)

        if scorecard_data and 'scorecard_html' in scorecard_data:
            html = scorecard_data['scorecard_html']
            logger.info(f"✅ Serving preloaded scorecard HTML ({len(html)} bytes)")
            return Response(html, mimetype='text/html')
        else:
            logger.warning(f"⚠️  Scorecard {match_id} not found in preloaded data")
            return Response(f"Scorecard not found: {match_id}", status=404)

    # RANDOM MODE: Generate basic HTML with simulated data
    else:
        if match_id in simulated_matches:
            scorecard = simulated_matches[match_id]
        else:
            # Generate on the fly
            home_club = random.choice(CLUBS)
            away_club = random.choice([c for c in CLUBS if c != home_club])
            grade = random.choice(GRADES)
            scorecard = generate_match_scorecard(
                match_id, home_club, away_club, grade['grade_name']
            )
            simulated_matches[match_id] = scorecard

        # Generate simple HTML representation
        html = generate_scorecard_html(scorecard)
        logger.info(f"✅ Serving generated scorecard HTML ({len(html)} bytes)")
        return Response(html, mimetype='text/html')


def generate_scorecard_html(scorecard: Dict) -> str:
    """
    Generate React-style HTML with vertical text layout (matches real KNCB structure)

    This mimics how the real KNCB Match Centre displays data:
    - React SPA structure with <div id="root">
    - Vertical layout (each stat on a separate line, not tables)
    - Section markers: BATTING, BOWLING, FIELDING
    - Metadata text: Result, Venue, Toss info
    - Column headers: R, B, 4, 6, SR for batting

    The scraper parses this by:
    1. Extracting all text with page.inner_text('body')
    2. Finding section markers (BATTING, BOWLING)
    3. Parsing 7 lines per player (name, dismissal, runs, balls, 4s, 6s, SR)
    """

    # Build vertical text content (what scraper sees after React renders)
    content_lines = []

    # Header information
    content_lines.append(f"{scorecard['home_club']} vs {scorecard['away_club']}")
    content_lines.append(f"Grade: {scorecard['grade_name']}")
    content_lines.append(f"Match ID: {scorecard['match_id']}")
    content_lines.append(f"Date: {scorecard['match_date']}")
    content_lines.append(f"Result: {scorecard['result']}")
    content_lines.append(f"Venue: Sportpark Amsterdam")  # Realistic metadata
    content_lines.append(f"Toss won by: {scorecard['home_club']}")
    content_lines.append("")  # Blank line

    # Process each innings
    for idx, innings in enumerate(scorecard['innings'], 1):
        content_lines.append(f"Innings {idx}")
        content_lines.append(f"{innings['batting_team']}")
        content_lines.append(f"TOTAL: {innings['total']}/{innings['wickets']}")
        content_lines.append(f"EXTRAS: {innings['extras']}")
        content_lines.append("")

        # BATTING section (vertical layout)
        content_lines.append("BATTING")
        content_lines.append("R")      # Column headers (each on separate line)
        content_lines.append("B")
        content_lines.append("4")
        content_lines.append("6")
        content_lines.append("SR")
        content_lines.append("")

        # Each player: 7 lines (name, dismissal, runs, balls, 4s, 6s, SR)
        for bat in innings['batting']:
            content_lines.append(bat['player_name'])
            content_lines.append(bat['dismissal_type'])
            content_lines.append(str(bat['runs']))
            content_lines.append(str(bat['balls_faced']))
            content_lines.append(str(bat['fours']))
            content_lines.append(str(bat['sixes']))

            # Calculate strike rate
            if bat['balls_faced'] > 0:
                sr = (bat['runs'] / bat['balls_faced']) * 100
                content_lines.append(f"{sr:.2f}")
            else:
                content_lines.append("0.00")

        content_lines.append("")  # Blank line after batting

        # BOWLING section (vertical layout)
        content_lines.append("BOWLING")
        content_lines.append("O")      # Column headers
        content_lines.append("M")
        content_lines.append("R")
        content_lines.append("W")
        content_lines.append("NB")
        content_lines.append("WD")
        content_lines.append("")

        # Each bowler: 7 lines (name, overs, maidens, runs, wickets, NB, WD)
        for bowl in innings['bowling']:
            content_lines.append(bowl['player_name'])
            content_lines.append(f"{bowl['overs']:.1f}")
            content_lines.append(str(bowl['maidens']))
            content_lines.append(str(bowl['runs']))
            content_lines.append(str(bowl['wickets']))
            content_lines.append("0")  # No balls
            content_lines.append("0")  # Wides

        content_lines.append("")  # Blank line after bowling

    # Add fielding section (if players took catches/stumpings)
    if scorecard.get('fielding'):
        content_lines.append("FIELDING")
        content_lines.append("")
        for fielder in scorecard['fielding']:
            if fielder['catches'] > 0:
                content_lines.append(f"{fielder['player_name']} - {fielder['catches']} catch(es)")
            if fielder['stumpings'] > 0:
                content_lines.append(f"{fielder['player_name']} - {fielder['stumpings']} stumping(s)")
            if fielder['runouts'] > 0:
                content_lines.append(f"{fielder['player_name']} - {fielder['runouts']} runout(s)")

    content_lines.append("")
    content_lines.append("Players")  # Section end marker

    # Join all lines with newlines
    text_content = "\n".join(content_lines)

    # Wrap in React-style HTML structure (mimics real KNCB)
    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no"/>
    <link href="https://fonts.googleapis.com/css?family=Saira+Extra+Condensed:500&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700&display=swap" rel="stylesheet"/>
    <title>Mock KNCB Match Centre - Scorecard</title>
    <style>
        body {{
            font-family: 'Open Sans', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        #root {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            white-space: pre-line;
        }}
    </style>
</head>
<body>
    <noscript>Hi there, this website runs entirely off JavaScript. Please enable JavaScript to view this page.</noscript>
    <div id="root">{text_content}</div>
    <script>
        // Mock React rendering (instant for testing, but structure matches real KNCB)
        console.log('Mock KNCB Match Centre - Scorecard rendered');
    </script>
</body>
</html>
"""
    return html


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "mode": "PRELOADED" if PRELOADED_MODE else "RANDOM",
        "matches_in_memory": len(simulated_matches),
        "preloaded_scorecards_cached": len(preloaded_scorecards),
        "message": "Mock KNCB API Server"
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "service": "Mock KNCB Match Centre API",
        "version": "1.0",
        "endpoints": {
            "grades": "/rv/{entity_id}/grades/?apiid={api_id}&seasonId={season_id}",
            "matches": "/rv/{entity_id}/matches/?apiid={api_id}&seasonId={season_id}&gradeId={grade_id}",
            "scorecard": "/rv/match/{match_id}/?apiid={api_id}",
            "health": "/health"
        },
        "usage": "Point your scraper to http://localhost:5001 instead of api.resultsvault.co.uk"
    })


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 Starting Mock KNCB API Server")
    logger.info("=" * 80)
    logger.info("")

    # Check mode
    if PRELOADED_MODE:
        logger.info("🧪 MODE: PRELOADED (Serving pre-fetched 2025 scorecards as 2026 data)")
        logger.info(f"   Data directory: {MOCK_DATA_DIR}")
        logger.info("")
        logger.info("📌 2026 SEASON READY:")
        logger.info("   - Mock server handles 2026 season format (entity_id-match_id)")
        logger.info("   - When 2026 season starts (April 2026), scraper will fetch live data")
        logger.info("   - Preloaded mode is for testing until live season begins")

        # Load index
        index = load_preloaded_index()

        if index:
            logger.info("")
            logger.info("✅ Preloaded data ready:")
            logger.info(f"   Total matches: {index['total_matches']}")
            logger.info(f"   Season: {index['season_year']}")
            logger.info(f"   Teams: {len(index['matches_by_team'])}")
            logger.info(f"   Weeks: {len(index['matches_by_week'])}")
            logger.info("")
            logger.info("📋 Teams available:")
            for team in sorted(index['matches_by_team'].keys()):
                count = len(index['matches_by_team'][team])
                logger.info(f"   - {team}: {count} matches")
        else:
            logger.error("")
            logger.error("❌ Failed to load preloaded data!")
            logger.error("   Make sure to run load_2025_scorecards_to_mock.py first")
            logger.error("")
            exit(1)
    else:
        logger.info("🎲 MODE: RANDOM (Generating realistic match data with vertical layout)")
        logger.info("   - Matches real KNCB React-style structure")
        logger.info("   - Realistic Dutch/Indian player names")
        logger.info("   - Vertical text layout (not HTML tables)")
        logger.info("")
        logger.info("📌 2026 SEASON COMPATIBLE:")
        logger.info("   - URL format: /match/134453-{match_id}/scorecard/")
        logger.info("   - Entity ID validation enabled")
        logger.info("   - Ready for live 2026 season (April 2026)")
        logger.info("")
        logger.info("   To use preloaded mode, set MOCK_DATA_DIR environment variable:")

    logger.info("")
    logger.info("📍 Server will be available at http://localhost:5001")
    logger.info("")
    logger.info("🔧 Configure scraper to point to:")
    logger.info("   matchcentre_url: http://localhost:5001")
    logger.info("   kncb_api_url: http://localhost:5001/rv")
    logger.info("")
    logger.info("📊 Endpoints:")
    logger.info("   GET /health                                  - Health check")
    logger.info("   GET /                                        - API info")
    logger.info("   GET /match/{entity_id}-{match_id}/scorecard/ - Scorecard HTML")
    logger.info("   GET /rv/{entity_id}/grades/                  - List grades")
    logger.info("   GET /rv/{entity_id}/matches/                 - List matches")
    logger.info("   GET /rv/match/{match_id}/                    - Match details (JSON)")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    app.run(host='0.0.0.0', port=5001, debug=False)
