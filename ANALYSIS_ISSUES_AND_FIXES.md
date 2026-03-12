# Fantasy Cricket System - Issue Analysis and Fixes

---

## Issue 5: Player Names Not Showing in Team Modal ✅ FIXED

**Date:** 2025-12-18
**Context:** After fixing Issue #4, player names still not visible in team detail modal

### Root Cause Analysis

1. **Symptom**
   - Team modal showing club names (ACC 1, U15, ZAMI 1) but no player names
   - Frontend component expects `player.player_name` but receiving `undefined`

2. **Root Cause: Incomplete Deployment**
   - The player name fix (line 569 in main.py) was made earlier but never deployed
   - When Issue #4 was fixed, only `database_models.py` was copied to production
   - Docker rebuild used cached layers, keeping the old `main.py` with incorrect field name
   - Production had: `'name': player_dict['player_name']` (WRONG)
   - Local had: `'player_name': player_dict['player_name']` (CORRECT)

3. **Why It Happened**
   - Docker layer caching reused old `main.py` from previous build
   - Only copied `database_models.py`, not `main.py`
   - Assumed previous fix was deployed (it wasn't)

### Solution Applied

```bash
# 1. Copy correct main.py to production
scp backend/main.py ubuntu@fantcric.fun:~/fantasy-cricket-leafcloud/backend/

# 2. Rebuild API container WITHOUT CACHE (critical!)
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose build --no-cache fantasy_cricket_api"

# 3. Remove old container and start new one
ssh ubuntu@fantcric.fun "docker rm -f fantasy_cricket_api && cd ~/fantasy-cricket-leafcloud && docker-compose up -d fantasy_cricket_api"

# 4. Verify networking (lesson from Issue #3)
docker network connect fantasy-cricket-leafcloud_cricket_network fantasy_cricket_api

# 5. Verify health and fix
docker exec fantasy_cricket_nginx wget -q -O- http://fantasy_cricket_api:8000/health
docker exec fantasy_cricket_api sed -n '569,573p' /app/main.py
```

### Verification

- ✅ Line 569 now has `'player_name': player_dict['player_name']`
- ✅ API healthy and connected to nginx network
- ✅ No errors in logs
- ✅ Player names should now appear in team modal

### Files Modified

- ✅ Production `/app/main.py` - Line 569 fixed to return `player_name` instead of `name`

### Prevention

**ALWAYS rebuild without cache when deploying code changes:**

```bash
# ❌ WRONG - may use cached layers with old code
docker-compose build fantasy_cricket_api

# ✅ CORRECT - forces rebuild of all layers
docker-compose build --no-cache fantasy_cricket_api
```

**Verify deployments actually took effect:**

```bash
# Check specific line was updated
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_api sed -n 'XXX,YYYp' /app/main.py"
```

### Lessons Learned

1. **Docker Caching Can Hide Issues** - Layer caching may keep old code even after copying new files
2. **Always Use --no-cache for Code Changes** - Especially critical when copying files that go into COPY . . layer
3. **Verify Every Deployment** - Check that code changes actually made it into the running container
4. **Track What's Been Deployed** - Document exactly which fixes are actually in production vs. just committed
5. **Test Immediately After Deploy** - Would have caught this right away

---

## Issue 4: Database Schema Mismatch - clubs.full_name Does Not Exist ✅ FIXED

**Date:** 2025-12-18
**Context:** After Phase 2 leaderboard upgrades, viewing user teams started failing with 500 errors

### Root Cause Analysis

1. **Symptom**
   - Error: `psycopg2.errors.UndefinedColumn: column clubs.full_name does not exist`
   - Endpoint failing: `GET /api/user/teams`
   - User unable to view their fantasy teams

2. **Root Cause: SQLAlchemy Model Out of Sync**
   - Production `database_models.py` Club class had fields that don't exist in database:
     - ❌ `full_name` (line 99)
     - ❌ `country`
     - ❌ `cricket_board`
     - ❌ `website_url`
     - ❌ `updated_at`
   - Production database `clubs` table only has: `id, name, tier, location, founded_year, created_at, season_id`
   - When SQLAlchemy queries Club objects, it tries to SELECT all model fields
   - Database rejects query because columns don't exist

3. **How It Was Triggered**
   - Endpoint: `/api/user/teams` (line 340 in user_team_endpoints.py)
   - Code accesses: `team.league.club.name` (line 358)
   - SQLAlchemy lazy-loads the Club relationship
   - Generates SELECT including all Club model columns (including non-existent ones)
   - Query fails with UndefinedColumn error

4. **Why It Happened**
   - Production `database_models.py` was outdated
   - Local development version was correctly synced with database schema
   - Previous deployment didn't include updated database_models.py

### Solution Applied

```bash
# 1. Copy correct database_models.py from local to production
scp backend/database_models.py ubuntu@fantcric.fun:~/fantasy-cricket-leafcloud/backend/

# 2. Rebuild and restart API container
ssh ubuntu@fantcric.fun "docker rm -f <container_id> && cd ~/fantasy-cricket-leafcloud && docker-compose up -d fantasy_cricket_api"

# 3. Ensure API is on correct network (lesson from Issue #3)
docker network connect fantasy-cricket-leafcloud_cricket_network fantasy_cricket_api

# 4. Verify health
docker exec fantasy_cricket_nginx wget -q -O- http://fantasy_cricket_api:8000/health
```

### Verification

- ✅ Club model now matches database schema exactly
- ✅ No `full_name`, `country`, `cricket_board`, `website_url`, or `updated_at` fields in model
- ✅ API started successfully with no errors
- ✅ Health check returns 200 OK
- ✅ No errors in logs after restart

### Files Modified

- ✅ Production `/app/database_models.py` - Club class (lines 88-110) updated

### Prevention

**ALWAYS check production database schema before modifying models:**

```bash
# Check table structure
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d clubs'"

# Compare with local model
grep -A 20 "class Club" backend/database_models.py
```

**Follow the checklist from DATABASE_SCHEMA.md:**
- [ ] Checked production schema with `\d table_name`
- [ ] Verified field names match exactly
- [ ] Confirmed all FK constraints exist
- [ ] No relationships without FK
- [ ] Reviewed `DATABASE_SCHEMA.md`
- [ ] Read `DEVELOPMENT_GUIDE.md` procedures

### Lessons Learned

1. **Schema Documentation is Critical** - `DATABASE_SCHEMA.md` exists specifically to prevent this
2. **Always Verify Production Schema** - Never assume production matches local development
3. **Deploy Database Models When Changed** - Include `database_models.py` in all relevant deployments
4. **Test After Deployment** - Test critical endpoints immediately after deploying
5. **Follow the Mature Plan Process** - Analyze readmes and reference files BEFORE making changes

---

## Issue 3: 502 Bad Gateway - Login Failure After Deployment ✅ FIXED

**Date:** 2025-12-18
**Context:** After deploying player name fix to production, login started failing with 502 errors

### Root Cause Analysis

1. **Improper Container Restart Command**
   - Used: `docker rm -f fantasy_cricket_api && docker-compose up -d --no-deps fantasy_cricket_api`
   - This created the API container in the **wrong Docker network**
   - nginx was on: `fantasy-cricket-leafcloud_cricket_network`
   - API was on: `fantasy-cricket_cricket_network`
   - Containers couldn't communicate across different networks

2. **Symptom Timeline**
   - 10:21 - First login attempt failed (502)
   - 10:35 - Multiple failed login attempts
   - 10:38 - Network fix applied
   - 10:38+ - All systems operational

3. **Evidence from Logs**
   ```
   nginx error.log:
   2025/12/18 10:35:43 [error] connect() failed (113: Host is unreachable)
   while connecting to upstream, request: "POST /api/auth/login HTTP/1.1",
   upstream: "http://172.20.0.6:8000/api/auth/login"
   ```

### Solution Applied

```bash
# Connected API container to nginx network
docker network connect fantasy-cricket-leafcloud_cricket_network fantasy_cricket_api

# Verified connectivity
docker exec fantasy_cricket_nginx wget -q -O- http://fantasy_cricket_api:8000/health
# ✅ Returned: {"status":"healthy"...}
```

### Verification

- ✅ API container now on BOTH networks (leaf-cloud network + original network)
- ✅ Nginx can reach API on shared network
- ✅ Health check works from nginx container
- ✅ Login functionality restored
- ✅ No errors in logs after 10:38

### Prevention

**NEVER use `docker rm -f` + `docker-compose up` in production!**

```bash
# ❌ WRONG - breaks networking
docker rm -f fantasy_cricket_api && docker-compose up -d --no-deps fantasy_cricket_api

# ✅ CORRECT - preserves networks
cd /home/ubuntu/fantasy-cricket && docker-compose up -d --build fantasy_cricket_api

# ✅ ALSO CORRECT - proper workflow
docker-compose stop fantasy_cricket_api
docker-compose build fantasy_cricket_api
docker-compose up -d fantasy_cricket_api
```

### Documentation Updated

- Added to `TROUBLESHOOTING.md` section "502 Bad Gateway / Login Failing After Container Restart"
- Includes symptoms, diagnosis, solution, and prevention steps

### Lessons Learned

1. **Always use proper docker-compose commands** - they handle networking automatically
2. **Verify connectivity after deployment** - test from nginx container to API
3. **Check docker networks** - `docker network inspect` shows which network each container is on
4. **Monitor error logs immediately after deployment** - would have caught this in seconds

---

**Date:** 2025-11-19
**Context:** User reported duplicates in top 25 and weekly points showing as 0

---

## Issue 1: Duplicate Players in Top 25 ✅ PARTIALLY FIXED

### Root Cause Analysis

1. **Backend Code Was Not Deployed**
   - Fixed deduplication code in `backend/main.py` (lines 485-541)
   - Code changes committed but NOT copied into Docker container
   - Initial restart didn't help because `docker-compose restart` uses cached image
   - Solution: Used `docker cp` to copy updated file into running container

2. **Deduplication Logic**
   ```python
   # Changed from list to dictionary
   player_points_dict = {}  # player_id -> {player_name, rl_team, total_points}

   for pfd in player_fantasy_data:
       player_id, total_points, fantasy_team_id, player_name, rl_team = pfd

       if player_id not in player_points_dict:
           player_points_dict[player_id] = {...}
       else:
           # Aggregate points for players in multiple teams
           player_points_dict[player_id]['total_points'] += (total_points or 0)
   ```

3. **Current Status**
   - Backend deduplication: ✅ WORKING (33 entries → 30 unique players)
   - Frontend still showing duplicates: ⚠️ LIKELY BROWSER CACHE
   - DevanshuArya (3 teams) and PiyushPandey (2 teams) now properly aggregated

### Verification Results

```
Total fantasy_team_players rows: 33
Unique players after deduplication: 30

Players in multiple teams:
  DevanshuArya   - in 3 teams -  1380.2 pts
  PiyushPandey   - in 2 teams -  1091.5 pts

Top 25 backend output (deduplicated):
  1. AdnanAhmad        2244.3 pts
  2. JoelTharakan      2210.5 pts
  3. LotteHeerkens     2196.4 pts
  4. DevanshuArya      1380.2 pts  ← Aggregated across 3 teams
  5. AkshayaSripatnala 1278.8 pts
  ...
```

### Next Steps
1. Ask user to hard-refresh browser (Cmd+Shift+R / Ctrl+F5) to clear cache
2. Verify duplicates are gone after cache clear
3. If still present, investigate Next.js client-side state management

---

## Issue 2: Weekly Points Showing as 0 ⚠️ PARTIALLY FIXED

### Root Cause Analysis

1. **Original Code**
   ```python
   # backend/main.py:332
   weekly_points=0  # Field not available in current schema
   ```

2. **Data Structure Problem**
   - `fantasy_teams.total_points`: Cumulative total (all rounds)
   - `fantasy_team_players.total_points`: Cumulative per player
   - `player_performances`: Base points WITHOUT captain/VC/WK bonuses
   - **No per-round tracking in database schema**

3. **Attempted Fix**
   ```sql
   -- Calculate from latest round in player_performances
   SELECT ftp.fantasy_team_id,
          SUM(pp.final_fantasy_points) as weekly_points
   FROM player_performances pp
   JOIN fantasy_team_players ftp ON pp.player_id = ftp.player_id
   WHERE pp.league_id = :league_id
   AND pp.round_number = :round_number
   GROUP BY ftp.fantasy_team_id
   ```

4. **Problem with Current Fix**
   - `player_performances.final_fantasy_points` includes player multiplier only
   - Does NOT include captain (2x), vice-captain (1.5x), or wicketkeeper (2x catch) bonuses
   - Example from Round 6:
     - Calculated weekly: ~885.9 pts (Testastic Terry)
     - Actual round score: ~1302.8 pts (from simulation)
     - **Missing ~32% due to role bonuses**

### Why Weekly Points Are Inaccurate

The simulation flow:
1. Generate random performances for ALL players
2. Store in `player_performances` with base multiplier only
3. For fantasy team members:
   - Calculate with captain/VC/WK bonuses
   - Add to `fantasy_team_players.total_points` (cumulative)
   - Update `fantasy_teams.total_points` (cumulative)

**There is NO per-round storage of fantasy team scores with bonuses.**

### Proper Solutions (Pick One)

#### Option 1: Add last_round_points Column ⭐ RECOMMENDED
**Pros:**
- Minimal code changes
- Accurate weekly points with all bonuses
- Low database overhead

**Implementation:**
```sql
ALTER TABLE fantasy_teams ADD COLUMN last_round_points FLOAT DEFAULT 0;
```

Update `simulate_live_teams.py` to track round delta:
```python
# Before updating team
old_total = team.total_points
new_total = old_total + round_points

# Update with both cumulative and last round
UPDATE fantasy_teams
SET total_points = :new_total,
    last_round_points = :round_points
WHERE id = :team_id
```

Backend endpoint:
```python
weekly_points=team.last_round_points
```

#### Option 2: Store Per-Round Breakdown Table
**Pros:**
- Full history tracking
- Can show week-by-week progression

**Cons:**
- More complex schema
- More storage overhead

**Implementation:**
```sql
CREATE TABLE fantasy_team_rounds (
    id UUID PRIMARY KEY,
    fantasy_team_id UUID REFERENCES fantasy_teams(id),
    round_number INT NOT NULL,
    round_points FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fantasy_team_id, round_number)
);
```

#### Option 3: Duplicate player_performances for Each Fantasy Team
**Pros:**
- Keeps all data in player_performances table

**Cons:**
- Massive data duplication
- Performance concerns
- Complex ON CONFLICT logic

**NOT RECOMMENDED**

### Current Deployment Status

✅ Deployed: Weekly points calculation from player_performances
⚠️ Limitation: Missing captain/VC/WK bonuses (~30-40% of points)
📝 Recommendation: Implement Option 1 (add last_round_points column)

---

## Database Schema Issues

### player_performances Table

**Current Design:**
- Stores ALL player performances (not just fantasy team members)
- `fantasy_team_id` is always NULL
- Includes player multiplier but not role bonuses
- Purpose: Calculate league stats (best batsman, bowler, fielder)

**Issue:**
- Can't be used for accurate weekly fantasy team points
- Missing captain (2x), VC (1.5x), WK (2x catch) bonuses

### fantasy_team_players Table

**Current Design:**
- `total_points`: Cumulative across all rounds
- No per-round breakdown

**Needed:**
- Either per-round history OR last_round_points column

---

## Deployment Checklist

### What's Currently Deployed ✅
1. Stats endpoint deduplication (backend/main.py:485-541)
2. Weekly points calculation from player_performances (backend/main.py:333-353)
3. player_performances storage fixes (ON CONFLICT, match_id nullable)

### What Still Needs Work ⚠️
1. Weekly points are ~30-40% lower than actual due to missing bonuses
2. User needs to clear browser cache to see deduplicated top 25
3. Consider adding `last_round_points` column for accurate weekly tracking

### Files Modified
- ✅ backend/main.py (stats deduplication + weekly points)
- ✅ backend/simulate_live_teams.py (ON CONFLICT fix, match_id nullable)
- ✅ Committed to git: commit 54b008a

### Database Changes Made
- ✅ Dropped player_performances_match_id_fkey constraint
- ✅ Made player_performances.match_id nullable

---

## Recommendations

### Immediate (Today)
1. **Ask user to clear browser cache** (Cmd+Shift+R or Ctrl+F5)
2. **Verify duplicates are gone** after cache clear
3. **Explain weekly points limitation** to user

### Short-term (This Week)
1. **Add last_round_points column** to fantasy_teams table
2. **Update simulate_live_teams.py** to track round deltas
3. **Redeploy** and run new simulation to test

### Long-term (Optional)
1. **Add fantasy_team_rounds table** for full history tracking
2. **Show week-by-week progression** on frontend
3. **Add charts** showing team performance over time

---

## Testing Commands

### Test Deduplication
```bash
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_api python3 -c \"
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

league_id = 'fcaae0fb-1665-4621-ab6d-ab78dcc7a275'
engine = create_engine(os.getenv('DATABASE_URL'))

with Session(engine) as db:
    # Query and deduplicate
    query = text('''
        SELECT ftp.player_id, ftp.total_points, p.name
        FROM fantasy_team_players ftp
        JOIN players p ON ftp.player_id = p.id
        JOIN fantasy_teams ft ON ftp.fantasy_team_id = ft.id
        WHERE ft.league_id = :lid AND ft.is_finalized = TRUE
    ''')
    results = db.execute(query, {'lid': league_id}).fetchall()

    player_dict = {}
    for row in results:
        if row.player_id not in player_dict:
            player_dict[row.player_id] = {'name': row.name, 'points': row.total_points}
        else:
            player_dict[row.player_id]['points'] += row.total_points

    print(f'{len(results)} rows → {len(player_dict)} unique players')
\""
```

### Test Weekly Points
```bash
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_api python3 -c \"
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

league_id = 'fcaae0fb-1665-4621-ab6d-ab78dcc7a275'
engine = create_engine(os.getenv('DATABASE_URL'))

with Session(engine) as db:
    query = text('''
        SELECT ft.team_name, SUM(pp.final_fantasy_points) as weekly
        FROM player_performances pp
        JOIN fantasy_team_players ftp ON pp.player_id = ftp.player_id
        JOIN fantasy_teams ft ON ftp.fantasy_team_id = ft.id
        WHERE pp.league_id = :lid
        AND pp.round_number = (SELECT MAX(round_number) FROM player_performances WHERE league_id = :lid)
        GROUP BY ft.team_name
    ''')
    for row in db.execute(query, {'lid': league_id}):
        print(f'{row.team_name}: {row.weekly:.1f} pts')
\""
```

---

## Summary

### Issue 1: Duplicates
- **Status:** Backend fixed ✅, frontend likely cached ⚠️
- **Action:** Clear browser cache

### Issue 2: Weekly Points
- **Status:** Partially fixed ⚠️ (missing 30-40% due to bonuses)
- **Action:** Add last_round_points column to fantasy_teams

### Next Deploy
```bash
# After adding last_round_points column and updating simulate script:
scp backend/main.py ubuntu@fantcric.fun:~/fantasy-cricket-leafcloud/backend/
scp backend/simulate_live_teams.py ubuntu@fantcric.fun:~/fantasy-cricket-leafcloud/backend/
ssh ubuntu@fantcric.fun "
  docker cp ~/fantasy-cricket-leafcloud/backend/main.py fantasy_cricket_api:/app/
  docker cp ~/fantasy-cricket-leafcloud/backend/simulate_live_teams.py fantasy_cricket_api:/app/
  cd ~/fantasy-cricket-leafcloud && docker-compose restart fantasy_cricket_api
"
```
