# 🏏 Season Setup Guide

## Overview

This guide explains how to set up a new fantasy cricket season as an admin. The season setup workflow loads legacy rosters, calculates player values, and prepares the system for league creation.

---

## Prerequisites

- Admin access token (JWT with `is_admin: true`)
- Docker containers running (`docker-compose up -d`)
- Legacy roster JSON file (e.g., `rosters/acc_2025_complete.json`)

---

## Quick Start - Complete Season Setup

The easiest way to set up a season is using the **single-endpoint workflow**:

### POST `/api/admin/setup-season`

This endpoint does everything in one call:
1. Creates the season
2. Creates the club
3. Creates teams (1st, 2nd, 3rd, social)
4. Loads all 61 players from legacy roster
5. Activates the season

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/admin/setup-season" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "season_name": "Topklasse 2026",
    "start_date": "2026-04-01",
    "end_date": "2026-09-30",
    "club_name": "ACC",
    "club_full_name": "Amsterdamsche Cricket Club",
    "roster_file": "rosters/acc_2025_complete.json",
    "activate": true
  }'
```

**Response:**

```json
{
  "message": "Season 2026 setup complete!",
  "result": {
    "season": {
      "id": "uuid-here",
      "year": "2026",
      "name": "Topklasse 2026",
      "is_active": true
    },
    "club": {
      "id": "uuid-here",
      "name": "ACC",
      "teams_count": 4
    },
    "roster": {
      "club": "ACC",
      "players_loaded": 61,
      "players_skipped": 0,
      "average_value": 35.5,
      "total_value": 2165.5
    }
  }
}
```

---

## Step-by-Step Season Setup

If you prefer manual control, use these endpoints individually:

### 1. Create Season

**POST `/api/admin/seasons`**

```json
{
  "year": "2026",
  "name": "Topklasse 2026",
  "start_date": "2026-04-01",
  "end_date": "2026-09-30",
  "is_active": false
}
```

### 2. Create Club

**POST `/api/admin/clubs`**

```json
{
  "name": "ACC",
  "full_name": "Amsterdamsche Cricket Club",
  "country": "Netherlands",
  "cricket_board": "KNCB"
}
```

### 3. Create Teams

Teams are created automatically when you load the roster, or manually:

**POST `/api/admin/clubs/{club_id}/teams`**

```json
{
  "name": "ACC 1",
  "level": "1st",
  "tier_type": "senior",
  "multiplier": 1.0
}
```

### 4. Load Legacy Roster

**POST `/api/admin/clubs/{club_id}/load-roster`**

Query Parameters:
- `roster_file`: Path to JSON file (e.g., `rosters/acc_2025_complete.json`)

### 5. Activate Season

**POST `/api/admin/seasons/{season_id}/activate`**

This deactivates all other seasons and enables:
- League creation
- Automated scraping
- User registration

---

## Managing Players

### View All Players

**GET `/api/admin/clubs/{club_id}/players`**

Optional filters:
- `team_level`: Filter by team (1st, 2nd, 3rd, social)
- `min_value`: Minimum player value (€20-50)
- `max_value`: Maximum player value (€20-50)

**Example:**
```bash
curl "http://localhost:8000/api/admin/clubs/{club_id}/players?team_level=1st&min_value=40" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Manually Add Player

**POST `/api/admin/clubs/{club_id}/players`**

```json
{
  "name": "New Player",
  "team_level": "1st",
  "fantasy_value": 30.0,
  "stats": {
    "matches": 10,
    "runs": 350,
    "wickets": 12
  }
}
```

### Update Player Value

**PATCH `/api/admin/players/{player_id}/value`**

```json
{
  "player_id": "uuid",
  "new_value": 42.5,
  "reason": "Undervalued by algorithm - key player"
}
```

Changes are tracked in price history.

---

## Database Initialization

### Option 1: Docker Exec (Recommended)

```bash
# Initialize database schema
docker exec fantasy_cricket_api python3 -c "from database import init_db; init_db()"

# Test season setup
docker exec fantasy_cricket_api python3 season_setup_service.py
```

### Option 2: Python Script

```bash
cd backend
python3 -c "from database import init_db; init_db()"
python3 season_setup_service.py
```

---

## File Structure

### Legacy Roster JSON Format

```json
{
  "club": "ACC",
  "season": "2025",
  "total_players": 61,
  "teams": {
    "1st": 18,
    "2nd": 16,
    "3rd": 15,
    "social": 12
  },
  "players": [
    {
      "player_id": "acc_2025_001",
      "name": "Player Name",
      "team_level": "1st",
      "fantasy_value": 45.2,
      "stats": {
        "matches": 12,
        "runs": 450,
        "batting_avg": 37.5,
        "strike_rate": 125.0,
        "wickets": 18,
        "bowling_avg": 22.5,
        "economy": 4.5,
        "catches": 6,
        "run_outs": 1
      }
    }
  ]
}
```

### Database Schema

**Core Tables:**
- `seasons` - Season configurations
- `clubs` - Cricket clubs in each season
- `teams` - Teams within clubs (1st, 2nd, 3rd, social)
- `players` - Players with stats and fantasy values
- `player_price_history` - Tracks all value changes

**Game Tables:**
- `leagues` - User-created fantasy leagues
- `fantasy_teams` - User teams in leagues
- `fantasy_team_players` - Many-to-many relationship

---

## API Endpoints Summary

### Season Management
- `POST /api/admin/setup-season` - Complete setup workflow ⭐
- `POST /api/admin/seasons` - Create season
- `GET /api/admin/seasons` - List all seasons
- `GET /api/admin/seasons/{id}` - Get season details
- `PATCH /api/admin/seasons/{id}` - Update season
- `POST /api/admin/seasons/{id}/activate` - Activate season

### Club Management
- `POST /api/admin/clubs` - Create club
- `GET /api/admin/clubs` - List all clubs
- `POST /api/admin/clubs/{id}/teams` - Create team

### Player Management
- `GET /api/admin/clubs/{id}/players` - View club players
- `POST /api/admin/clubs/{id}/players` - Add player manually
- `POST /api/admin/clubs/{id}/load-roster` - Load legacy roster
- `PATCH /api/admin/players/{id}/value` - Update player value
- `POST /api/admin/players/bulk-value-update` - Bulk update values

### System
- `GET /api/admin/system/status` - System status
- `POST /api/admin/scrape/trigger` - Manual scrape trigger

---

## Workflow Examples

### Example 1: Set Up 2026 Season with ACC

```bash
# 1. Initialize database (first time only)
docker exec fantasy_cricket_api python3 -c "from database import init_db; init_db()"

# 2. Set up complete season
curl -X POST "http://localhost:8000/api/admin/setup-season" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "season_name": "Topklasse 2026",
    "start_date": "2026-04-01",
    "end_date": "2026-09-30",
    "club_name": "ACC",
    "club_full_name": "Amsterdamsche Cricket Club",
    "roster_file": "rosters/acc_2025_complete.json",
    "activate": true
  }'

# 3. Verify setup
curl "http://localhost:8000/api/admin/seasons" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"
```

### Example 2: Add New Player Mid-Season

```bash
# Get club ID
CLUB_ID=$(curl "http://localhost:8000/api/admin/clubs" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  | jq -r '.clubs[0].id')

# Add player
curl -X POST "http://localhost:8000/api/admin/clubs/${CLUB_ID}/players" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Signing",
    "team_level": "1st",
    "fantasy_value": 35.0,
    "stats": {
      "matches": 0,
      "runs": 0,
      "wickets": 0
    }
  }'
```

### Example 3: Adjust Player Values

```bash
# View expensive players
curl "http://localhost:8000/api/admin/clubs/${CLUB_ID}/players?min_value=45" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# Update a player's value
curl -X PATCH "http://localhost:8000/api/admin/players/${PLAYER_ID}/value" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "'${PLAYER_ID}'",
    "new_value": 48.0,
    "reason": "Top performer, undervalued"
  }'
```

---

## Troubleshooting

### Database Connection Issues

If you get "Connection refused" errors:

```bash
# Check if database is running
docker ps | grep postgres

# Initialize database from within Docker
docker exec fantasy_cricket_api python3 -c "from database import init_db; init_db()"
```

### Roster File Not Found

Ensure roster file path is relative to backend directory:
- ✅ `rosters/acc_2025_complete.json`
- ❌ `/Users/path/to/rosters/acc_2025_complete.json`

### Import Errors

If modules aren't found:
```bash
# Install dependencies
docker exec fantasy_cricket_api pip install -r requirements.txt

# Or rebuild containers
docker-compose build
docker-compose up -d
```

---

## Next Steps

After season setup:
1. **Create leagues** - Users can create fantasy leagues
2. **Select teams** - Users pick 15 players within €500 budget
3. **Start scraping** - Weekly updates capture match data
4. **Track points** - Players earn points based on performance

See `TEAM_SELECTION_GUIDE.md` for team building workflow.

---

## Admin Token

To get an admin token, use the create_admin.py script:

```bash
python3 backend/create_admin.py
```

This creates an admin user and prints a JWT token for API access.

---

**The season setup workflow is now complete!** 🎯

All admin endpoints are in `backend/admin_endpoints.py`
Database models are in `backend/database_models.py`
Season logic is in `backend/season_setup_service.py`
