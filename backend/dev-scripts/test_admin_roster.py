#!/usr/bin/env python3
"""
Test Admin Roster Management Endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTNkMzAxYS1jNTQ4LTQyOWQtOGU2OS0wODdjMzk5YTMzNjEiLCJpc19hZG1pbiI6dHJ1ZSwiZXhwIjoxNzY0OTYzNzc5fQ.YcVNmhxT-2Iqm3gGBakz0HSyspTpjl_MjIeO0KOnNOI"
CLUB_ID = "a7a580a7-7d3f-476c-82ea-afa6ae7ee276"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🏏 Testing Admin Roster Management Endpoints\n")

# Test 1: GET all players
print("1️⃣ GET all players (first 5)...")
response = requests.get(
    f"{BASE_URL}/api/admin/clubs/{CLUB_ID}/players",
    headers=headers
)
result = response.json()
print(f"   Status: {response.status_code}")
print(f"   Total players: {result['total_players']}")
print(f"   First 5 players:")
for player in result['players'][:5]:
    print(f"     - {player['name']} (multiplier: {player['multiplier']}, team: {player['team_name']})")

# Save a player ID for testing
test_player_id = result['players'][0]['id']
test_player_name = result['players'][0]['name']
print(f"\n   Using {test_player_name} ({test_player_id}) for testing...\n")

# Test 2: PUT update player
print("2️⃣ PUT update player details...")
update_data = {
    "player_type": "all-rounder",
    "multiplier": 0.70
}
response = requests.put(
    f"{BASE_URL}/api/admin/players/{test_player_id}",
    headers=headers,
    json=update_data
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    updated = response.json()['player']
    print(f"   Updated player: {updated['name']}")
    print(f"   New multiplier: {updated['multiplier']}")
    print(f"   Player type: {updated['player_type']}")
else:
    print(f"   Error: {response.json()}")

# Test 3: GET players with filter
print("\n3️⃣ GET players filtered by multiplier (0.69-0.85)...")
response = requests.get(
    f"{BASE_URL}/api/admin/clubs/{CLUB_ID}/players?min_multiplier=0.69&max_multiplier=0.85",
    headers=headers
)
result = response.json()
print(f"   Status: {response.status_code}")
print(f"   Filtered players: {result['total_players']}")
for player in result['players'][:5]:
    print(f"     - {player['name']} (multiplier: {player['multiplier']})")

# Test 4: POST add new player
print("\n4️⃣ POST add new test player...")
# Get a team ID first
teams_response = requests.get(
    f"{BASE_URL}/api/admin/clubs/{CLUB_ID}/teams",
    headers=headers
)
team_id = teams_response.json()['teams'][0]['id'] if teams_response.status_code == 200 else None

if team_id:
    new_player_data = {
        "name": "TestPlayer_AutoAdded",
        "team_id": team_id,
        "player_type": "batsman",
        "multiplier": 1.5,
        "stats": {"matches": 0, "runs": 0}
    }
    response = requests.post(
        f"{BASE_URL}/api/admin/clubs/{CLUB_ID}/players",
        headers=headers,
        json=new_player_data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        new_player = response.json()['player']
        print(f"   Added player: {new_player['name']}")
        print(f"   Player ID: {new_player['id']}")
        test_delete_player_id = new_player['id']

        # Test 5: DELETE the test player
        print("\n5️⃣ DELETE test player...")
        response = requests.delete(
            f"{BASE_URL}/api/admin/players/{test_delete_player_id}",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Deleted: {response.json()['player_name']}")
        else:
            print(f"   Error: {response.json()}")
    else:
        print(f"   Error: {response.json()}")
else:
    print("   Skipped: Could not get team ID")

print("\n✅ All tests completed!")
