#!/usr/bin/env python3
"""
Mock KNCB Match Centre API Server
==================================
Serves simulated match data in the exact format the KNCB API provides.
This allows testing the scraper without depending on real matches.

Usage:
    python3 mock_kncb_server.py

The server will run on http://localhost:5001
Configure the scraper to use this URL instead of api.resultsvault.co.uk
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============================================================================
# SIMULATED DATA GENERATION
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

# Player name generator
FIRST_NAMES = [
    "Jason", "Michael", "David", "Tom", "Max", "Ryan", "Ben", "Chris",
    "Alex", "Arjun", "Vikram", "Rohan", "Amit", "Rahul", "Sanjay",
    "Lars", "Pieter", "Jan", "Willem", "Bas", "Thijs", "Daan"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Davis", "Miller",
    "Patel", "Kumar", "Singh", "Shah", "Sharma", "Gupta",
    "de Jong", "van Dijk", "Jansen", "Bakker", "Visser", "de Vries"
]

# In-memory storage for simulated matches
simulated_matches = {}
match_counter = 100000  # Start match IDs at 100000


def generate_player_name():
    """Generate a realistic player name"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


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


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "matches_in_memory": len(simulated_matches),
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
    logger.info("🚀 Starting Mock KNCB API Server")
    logger.info("📍 Server will be available at http://localhost:5001")
    logger.info("🔧 Configure scraper to use this URL instead of api.resultsvault.co.uk")

    app.run(host='0.0.0.0', port=5001, debug=True)
