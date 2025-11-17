#!/usr/bin/env python3
"""
Test the actual stats API endpoint response
"""
import sys
sys.path.insert(0, '/app')

from main import app, get_db, SessionLocal
from fastapi.testclient import TestClient
from database_models import User
from sqlalchemy import text
import jwt
import json

# Get a league ID
session = SessionLocal()
query = text("SELECT id FROM leagues LIMIT 1")
result = session.execute(query)
league_id = result.scalar()
session.close()

print(f"Testing /api/leagues/{league_id}/stats")

# Create a test token (you'll need a real user)
SECRET_KEY = "your-secret-key-change-in-production"

# Get a real user
session = SessionLocal()
query = text("SELECT id FROM users WHERE is_admin = true LIMIT 1")
result = session.execute(query)
user_id = result.scalar()
session.close()

token = jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm="HS256")

client = TestClient(app)
response = client.get(f"/api/leagues/{league_id}/stats", headers={"Authorization": f"Bearer {token}"})

print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nTop players count: {len(data.get('top_players', []))}")
    print("\nTop 10 players:")
    for i, player in enumerate(data.get('top_players', [])[:10], 1):
        pname = player.get('player_name', 'Unknown')
        tname = player.get('team_name', 'Unknown')
        pts = player.get('total_points', 0)
        print(f"{i}. {pname:30s} ({tname:10s}) - {pts:.1f} pts")
else:
    print(f"Error: {response.text}")
