# 🎮 Fantasy Cricket Admin Setup Guide

## ✅ What's Been Built

You now have a complete **Admin API** for season setup and management!

### Admin Endpoints Available:

1. **Season Management** (`/api/admin/seasons`)
   - Create seasons
   - Update season settings
   - Activate/deactivate seasons
   - View season status

2. **Club & Team Configuration** (`/api/admin/clubs`)
   - Create clubs
   - Create teams within clubs
   - Set tier multipliers
   - View club rosters

3. **Player Management** (`/api/admin/players`)
   - Assign players to teams
   - Update player values (fantasy cost)
   - Bulk update values
   - View unassigned players

4. **League Templates** (`/api/admin/league-templates`)
   - Create league configuration templates
   - Set tier multipliers
   - Configure default settings

5. **System Management** (`/api/admin/system`)
   - View system status
   - Trigger manual scrapes
   - Check health

---

## 🔐 Admin User Created

**Email:** `admin@fantcric.fun`
**Password:** Contact system administrator (needs to be set via SQL)
**Status:** Admin privileges enabled

### Setting Your Admin Password:

Since the password hashing has an issue in the creation script, set it via API registration instead:

```bash
# 1. First, delete the temporary admin user:
docker-compose exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket \
  -c "DELETE FROM users WHERE email='admin@fantcric.fun';"

# 2. Register via API (use your local machine or inside container):
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fantcric.fun","password":"YourSecurePassword123","full_name":"Admin User"}'

# 3. Upgrade to admin:
docker-compose exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket \
  -c "UPDATE users SET is_admin=true, is_verified=true WHERE email='admin@fantcric.fun';"
```

---

## 🚀 Using the Admin API

### Step 1: Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@fantcric.fun&password=YourPassword"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Save this token!** You'll need it for all admin requests.

### Step 2: Test Admin Access

```bash
TOKEN="your_access_token_here"

curl -X GET "http://localhost:8000/api/admin/health/admin" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 Season Setup Workflow

### 1. Create a Season

```bash
curl -X POST "http://localhost:8000/api/admin/seasons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "year": "2026",
    "name": "Topklasse 2026",
    "start_date": "2026-04-01",
    "end_date": "2026-09-30",
    "description": "2026 Cricket Season"
  }'
```

###2. Create Clubs

```bash
# Create ACC (already exists with 25 players)
curl -X POST "http://localhost:8000/api/admin/clubs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ACC",
    "full_name": "Amsterdamsche Cricket Club",
    "country": "Netherlands"
  }'

# Create VRA
curl -X POST "http://localhost:8000/api/admin/clubs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VRA",
    "full_name": "Volharding Recreatie Acitief",
    "country": "Netherlands"
  }'
```

### 3. Create Teams within Clubs

```bash
# ACC 1st Team (Tier 1 - 1.2x multiplier)
curl -X POST "http://localhost:8000/api/admin/clubs/{club_id}/teams" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ACC 1",
    "level": "1st",
    "tier_type": "senior",
    "multiplier": 1.2
  }'

# ACC 2nd Team (Tier 2 - 1.0x multiplier)
curl -X POST "http://localhost:8000/api/admin/clubs/{club_id}/teams" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ACC 2",
    "level": "2nd",
    "tier_type": "senior",
    "multiplier": 1.0
  }'
```

### 4. Set Player Values

```bash
# Update single player value
curl -X PATCH "http://localhost:8000/api/admin/players/{player_id}/value" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "legacy_xxx",
    "new_value": 35.5,
    "reason": "Top performer in 2025"
  }'

# Bulk update (for later when you have the algorithm)
curl -X POST "http://localhost:8000/api/admin/players/bulk-value-update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"player_id": "player1", "new_value": 45.0},
    {"player_id": "player2", "new_value": 30.0}
  ]'
```

### 5. Configure Tier Multipliers

```bash
curl -X POST "http://localhost:8000/api/admin/tier-multipliers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tier_1": 1.2,
    "tier_2": 1.0,
    "tier_3": 0.8,
    "tier_4": 0.6,
    "social": 0.5
  }'
```

### 6. Create League Template

```bash
curl -X POST "http://localhost:8000/api/admin/league-templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard League",
    "squad_size": 15,
    "budget": 500.0,
    "currency": "EUR",
    "max_from_top_tier": 6,
    "min_from_lower_tiers": 2,
    "min_from_each_team": true
  }'
```

### 7. Activate the Season

```bash
curl -X POST "http://localhost:8000/api/admin/seasons/{season_id}/activate" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Monitoring & Management

### View System Status

```bash
curl -X GET "http://localhost:8000/api/admin/system/status" \
  -H "Authorization: Bearer $TOKEN"
```

### Trigger Manual Scrape

```bash
curl -X POST "http://localhost:8000/api/admin/scrape/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clubs": ["ACC", "VRA"],
    "days_back": 7
  }'
```

### List All Seasons

```bash
curl -X GET "http://localhost:8000/api/admin/seasons" \
  -H "Authorization: Bearer $TOKEN"
```

### List All Clubs

```bash
curl -X GET "http://localhost:8000/api/admin/clubs" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔒 Security Notes

1. **Admin endpoints require authentication** - All `/api/admin/*` endpoints check for `is_admin=true` in the JWT token
2. **403 Forbidden** - Non-admin users will get 403 when trying to access admin endpoints
3. **401 Unauthorized** - Invalid or missing tokens will get 401

---

## 📁 Files Created

- **`backend/admin_endpoints.py`** - All admin API endpoints
- **`backend/create_admin.py`** - Script to create admin users
- **`backend/main.py`** - Updated with `is_admin` field and admin router

---

## 🎯 Next Steps

1. **Set up your admin password** (see above)
2. **Create the 2026 season**
3. **Add more clubs** (VRA, VOC, HCC, etc.)
4. **Create teams** for each club with proper tiers
5. **Load legacy rosters** for other clubs
6. **Set initial player values** (placeholder for now)
7. **Create league templates**
8. **Activate the season**

Then you'll be ready for users to:
- Create leagues
- Build fantasy teams
- Compete when the season starts!

---

## 💡 Tips

- All endpoints return JSON
- Most POST/PATCH endpoints return the created/updated object
- Use `?include_pricing=true` on player endpoints for detailed pricing data
- The system tracks price history automatically
- Legacy rosters are loaded on worker startup from `backend/rosters/`

---

## 🐛 Troubleshooting

**"403 Forbidden"**
→ Check that your user has `is_admin=true` in database
→ Verify JWT token contains `"is_admin": true`

**"401 Unauthorized"**
→ Token expired or invalid
→ Login again to get new token

**"404 Not Found"**
→ Check the endpoint URL
→ Ensure admin router is included in main.py

---

## 📚 API Documentation

Once deployed, visit:
- **Swagger UI**: http://localhost:8000/docs (development only)
- **ReDoc**: http://localhost:8000/redoc (development only)

In production, these are disabled for security.

---

**You're all set to start configuring your fantasy cricket season!** 🏏
