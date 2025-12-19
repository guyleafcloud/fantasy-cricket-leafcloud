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

## League Lifecycle Management

After season setup, admins manage leagues through a lifecycle workflow:

### League Status Flow

```
draft → active → locked → completed
```

### 1. Create League (Status: `draft`)

Users can create leagues with custom rules:

**POST `/api/leagues`**

```json
{
  "name": "Office League",
  "season_id": "season_2026",
  "squad_size": 15,
  "transfers_per_season": 5,
  "min_batsmen": 4,
  "min_bowlers": 3,
  "require_wicket_keeper": true,
  "max_players_per_team": 3,
  "require_from_each_team": false
}
```

In `draft` status:
- Rules can be edited
- Roster can be modified
- No teams can join yet

### 2. Confirm League (Status: `draft` → `active`)

Admin confirms league to lock rules and capture initial multipliers:

**POST `/api/admin/leagues/{league_id}/confirm`**

This action:
- ✅ Validates roster size meets squad requirements
- ✅ Freezes all league rules (can't be changed)
- ✅ Captures initial player multipliers for this league
- ✅ Opens league for user team registration

**Example Response:**

```json
{
  "success": true,
  "message": "League confirmed and rules frozen",
  "metadata": {
    "roster_count": 61,
    "min_multiplier": 0.69,
    "max_multiplier": 5.0,
    "multipliers_captured": 61,
    "frozen_rules": {
      "squad_size": 15,
      "transfers_per_season": 5,
      "min_batsmen": 4,
      "min_bowlers": 3
    }
  }
}
```

**Important:** Multipliers captured at confirmation are the STARTING point. They will drift weekly based on league-specific performance (see FANTASY_POINTS_RULES.md).

### 3. Lock League (Status: `active` → `locked`)

Before season starts, lock league to prevent new registrations:

**POST `/api/admin/leagues/{league_id}/lock`**

This action:
- ✅ Prevents new team registration
- ✅ Validates all existing teams are finalized
- ✅ Prepares league for season start

**Requirements:**
- All teams must have finalized their squads
- At least 1 team must have joined

### 4. Complete League (Status: `locked` → `completed`)

After season ends, mark league as completed:

**POST `/api/admin/leagues/{league_id}/complete`**

This action:
- ✅ Marks league as finished
- ✅ Stops weekly multiplier updates for this league
- ✅ Preserves final standings

### Get League Status

Check league readiness and validation errors:

**GET `/api/admin/leagues/{league_id}/status`**

**Response:**

```json
{
  "league_id": "uuid",
  "league_name": "Office League",
  "status": "active",
  "confirmed_at": "2026-04-01T10:00:00Z",
  "teams_total": 8,
  "teams_finalized": 6,
  "teams_not_finalized": 2,
  "roster_size": 61,
  "squad_size": 15,
  "multipliers_captured": 61,
  "can_confirm": false,
  "can_lock": false,
  "can_complete": false,
  "validation_errors": [
    "2 teams not finalized yet"
  ]
}
```

### League-Specific Multipliers

Each league has its own `multipliers_snapshot` that:
- **Starts** with current player multipliers at confirmation
- **Drifts** weekly (15% per week) based on league roster performance
- **Updates** every Monday 2 AM via automated task

This means the same player can have different multipliers in different leagues, reflecting their relative value within each league's roster context.

**Example:**
- Player A in League 1 (many stars): multiplier = 1.2 (above average)
- Player A in League 2 (fewer stars): multiplier = 0.85 (below average)

See `FANTASY_POINTS_RULES.md` for complete multiplier documentation.

---

## Next Steps

After season setup:
1. **Create leagues** - Users can create fantasy leagues
2. **Confirm leagues** - Admin confirms to lock rules and capture multipliers
3. **Select teams** - Users pick squads within budget
4. **Lock leagues** - Admin locks before season starts
5. **Start scraping** - Weekly updates capture match data
6. **Track points** - Players earn points based on performance
7. **Complete leagues** - Admin marks as finished after season

See `LEAGUE_MULTIPLIERS.md` for detailed multiplier system documentation.

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
