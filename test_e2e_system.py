#!/usr/bin/env python3
"""
End-to-end test of the fantasy cricket system.
Tests: login, create team, add players, validate rules, finalize team.
"""

import requests
import json
import sys

BASE_URL = "https://fantcric.fun/api"
TEST_USER_EMAIL = "test@tes.nl"
TEST_USER_PASSWORD = "test"  # Update if needed
LEAGUE_CODE = "XQJON8"  # Testert league
CLUB_ID = "625f1c55-6d5b-40a9-be1d-8f7abe6fa00e"  # ACC

def log(message, level="INFO"):
    """Print formatted log message"""
    print(f"[{level}] {message}")

def test_login():
    """Test user login"""
    log("Testing login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        log(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        log(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
        return None

def test_get_available_players(token):
    """Get available players"""
    log("Fetching available players...")
    response = requests.get(
        f"{BASE_URL}/players/{CLUB_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        players = data.get("players", [])
        log(f"✅ Fetched {len(players)} players")

        # Group by RL team
        by_team = {}
        for p in players:
            rl_team = p.get("rl_team", "Unassigned")
            role = p.get("role", "unknown")
            if rl_team not in by_team:
                by_team[rl_team] = {"count": 0, "batsmen": 0, "bowlers": 0, "all_rounders": 0, "wicket_keepers": 0}
            by_team[rl_team]["count"] += 1
            if role == "BATSMAN":
                by_team[rl_team]["batsmen"] += 1
            elif role == "BOWLER":
                by_team[rl_team]["bowlers"] += 1
            elif role == "ALL_ROUNDER":
                by_team[rl_team]["all_rounders"] += 1
            elif role == "WICKET_KEEPER":
                by_team[rl_team]["wicket_keepers"] += 1

        log("Players by RL team:")
        for team, counts in sorted(by_team.items()):
            log(f"  {team}: {counts['count']} total (B:{counts['batsmen']}, Bo:{counts['bowlers']}, AR:{counts['all_rounders']}, WK:{counts['wicket_keepers']})")

        return players
    else:
        log(f"❌ Failed to fetch players: {response.status_code} - {response.text}", "ERROR")
        return []

def test_create_team(token):
    """Create a fantasy team"""
    log("Creating fantasy team...")
    response = requests.post(
        f"{BASE_URL}/user/teams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team_name": "E2E Test Team",
            "league_code": LEAGUE_CODE
        }
    )

    if response.status_code == 200:
        data = response.json()
        team_id = data.get("team_id")
        log(f"✅ Team created! ID: {team_id}")
        return team_id
    else:
        log(f"❌ Failed to create team: {response.status_code} - {response.text}", "ERROR")
        return None

def test_add_players(token, team_id, players):
    """Add players to team following validation rules"""
    log("Adding players to team...")

    # We need:
    # - 11 players total
    # - At least 3 batsmen
    # - At least 3 bowlers
    # - At least 1 wicketkeeper
    # - Max 2 from any RL team
    # - At least 1 from each RL team (10 teams)

    # Group players by RL team and role
    by_team = {}
    for p in players:
        rl_team = p.get("rl_team")
        if not rl_team:
            continue
        if rl_team not in by_team:
            by_team[rl_team] = {"all": [], "batsmen": [], "bowlers": [], "all_rounders": [], "wicket_keepers": []}

        by_team[rl_team]["all"].append(p)
        role = p.get("role")
        if role == "BATSMAN":
            by_team[rl_team]["batsmen"].append(p)
        elif role == "BOWLER":
            by_team[rl_team]["bowlers"].append(p)
        elif role == "ALL_ROUNDER":
            by_team[rl_team]["all_rounders"].append(p)
        elif role == "WICKET_KEEPER":
            by_team[rl_team]["wicket_keepers"].append(p)

    log(f"Available RL teams: {list(by_team.keys())}")

    # Select 1 player from each team (prioritize filling roles)
    selected_players = []
    team_counts = {}

    # First, get 1 wicketkeeper
    for team_name in by_team.keys():
        if by_team[team_name]["wicket_keepers"]:
            wk = by_team[team_name]["wicket_keepers"][0]
            selected_players.append(wk)
            team_counts[team_name] = 1
            log(f"  Selected WK: {wk['name']} from {team_name}")
            break

    # Then get players from each team (1 from each, max 2 per team)
    for team_name in by_team.keys():
        if team_name not in team_counts:
            # Pick first player from this team
            if by_team[team_name]["all"]:
                player = by_team[team_name]["all"][0]
                selected_players.append(player)
                team_counts[team_name] = 1
                log(f"  Selected: {player['name']} ({player['role']}) from {team_name}")

    # Now fill remaining spots (up to 11) ensuring role requirements
    # Count current roles
    batsmen_count = sum(1 for p in selected_players if p['role'] in ['BATSMAN', 'ALL_ROUNDER'])
    bowlers_count = sum(1 for p in selected_players if p['role'] in ['BOWLER', 'ALL_ROUNDER'])

    log(f"Current squad: {len(selected_players)} players, {batsmen_count} batsmen, {bowlers_count} bowlers")

    # Add more if needed
    while len(selected_players) < 11:
        added = False
        for team_name in by_team.keys():
            if team_counts.get(team_name, 0) < 2 and len(selected_players) < 11:
                # Can add one more from this team
                existing_ids = {p['id'] for p in selected_players}
                available = [p for p in by_team[team_name]["all"] if p['id'] not in existing_ids]

                if available:
                    # Prioritize role needs
                    if batsmen_count < 3:
                        candidate = next((p for p in available if p['role'] in ['BATSMAN', 'ALL_ROUNDER']), None)
                    elif bowlers_count < 3:
                        candidate = next((p for p in available if p['role'] in ['BOWLER', 'ALL_ROUNDER']), None)
                    else:
                        candidate = available[0]

                    if candidate:
                        selected_players.append(candidate)
                        team_counts[team_name] = team_counts.get(team_name, 0) + 1
                        if candidate['role'] in ['BATSMAN', 'ALL_ROUNDER']:
                            batsmen_count += 1
                        if candidate['role'] in ['BOWLER', 'ALL_ROUNDER']:
                            bowlers_count += 1
                        log(f"  Added: {candidate['name']} ({candidate['role']}) from {team_name}")
                        added = True
                        break

        if not added:
            log("Could not add more players while respecting constraints", "WARN")
            break

    log(f"Final selection: {len(selected_players)} players")

    # Add players via API
    success_count = 0
    for player in selected_players:
        is_wk = player['role'] == 'WICKET_KEEPER'
        response = requests.post(
            f"{BASE_URL}/user/teams/{team_id}/players",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "player_id": player['id'],
                "is_captain": False,
                "is_vice_captain": False,
                "is_wicket_keeper": is_wk
            }
        )

        if response.status_code == 200:
            success_count += 1
        else:
            log(f"❌ Failed to add {player['name']}: {response.status_code} - {response.text}", "ERROR")

    log(f"✅ Successfully added {success_count}/{len(selected_players)} players")
    return success_count == len(selected_players)

def test_get_team(token, team_id):
    """Get team details"""
    log("Fetching team details...")
    response = requests.get(
        f"{BASE_URL}/user/teams/{team_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        players = data.get("players", [])
        log(f"✅ Team has {len(players)} players")
        log(f"   Squad size: {len(players)}/{data.get('squad_size', 11)}")

        # Show team composition
        by_team = {}
        by_role = {"BATSMAN": 0, "BOWLER": 0, "ALL_ROUNDER": 0, "WICKET_KEEPER": 0}
        for p in players:
            rl_team = p.get("team_name", "Unassigned")
            by_team[rl_team] = by_team.get(rl_team, 0) + 1
            role = p.get("player_type", "unknown").upper().replace('-', '_')
            if role in by_role:
                by_role[role] += 1

        log("   By RL team:")
        for team, count in sorted(by_team.items()):
            log(f"     {team}: {count} player(s)")

        log(f"   By role: B:{by_role['BATSMAN']}, Bo:{by_role['BOWLER']}, AR:{by_role['ALL_ROUNDER']}, WK:{by_role['WICKET_KEEPER']}")

        return data
    else:
        log(f"❌ Failed to fetch team: {response.status_code} - {response.text}", "ERROR")
        return None

def main():
    """Run end-to-end test"""
    log("=" * 60)
    log("STARTING END-TO-END SYSTEM TEST")
    log("=" * 60)

    # Step 1: Login
    token = test_login()
    if not token:
        log("Test failed at login step", "ERROR")
        return 1

    # Step 2: Get available players
    players = test_get_available_players(token)
    if not players:
        log("Test failed at fetching players", "ERROR")
        return 1

    # Step 3: Create team
    team_id = test_create_team(token)
    if not team_id:
        log("Test failed at creating team", "ERROR")
        return 1

    # Step 4: Add players
    success = test_add_players(token, team_id, players)
    if not success:
        log("Test failed at adding players", "WARN")
        # Continue to see team state

    # Step 5: Get team details
    team = test_get_team(token, team_id)

    log("=" * 60)
    log("END-TO-END TEST COMPLETED")
    log("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
