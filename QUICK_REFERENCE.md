# Fantasy Cricket Platform - Quick Reference

## Architecture at a Glance

```
SEASON (multiple, only 1 active)
  └─ CLUB (e.g., ACC)
      ├─ TEAM (ACC 1, ACC 2, U15, U17...)
      │  ├─ value_multiplier (1.0-5.0)
      │  └─ points_multiplier (1.0-5.0)
      │
      └─ PLAYER (513 total)
         ├─ multiplier: 0.69-5.0 (performance handicap)
         ├─ rl_team: "ACC 1" (STRING not FK)
         └─ role: BATSMAN|BOWLER|ALL_ROUNDER|WICKET_KEEPER

LEAGUE (competition in a season/club)
  ├─ season_id, club_id (FK pointers)
  ├─ LeagueRoster (which players available)
  │
  └─ FantasyTeam (user's team)
      ├─ is_finalized (locked for season)
      ├─ captain_id, vice_captain_id (2x/1.5x)
      │
      └─ FantasyTeamPlayer (junction)
         ├─ is_captain, is_vice_captain
         └─ is_wicket_keeper

MATCH (season_id, club_id → connects to League)
  └─ PlayerPerformance (per-match stats)
     ├─ Batting/Bowling/Fielding stats
     ├─ fantasy_points (calculated)
     ├─ multiplier_applied (player handicap)
     ├─ captain_multiplier (1.0/1.5/2.0)
     ├─ final_fantasy_points (after all multipliers)
     └─ league_id, round_number (context)
```

## Key Database Fields by Entity

### Season
- `is_active` (only 1 can be TRUE)
- `registration_open` (can users create teams?)
- `scraping_enabled` (auto-scrape scorecards?)

### League
- `status` (MISSING - should be draft|active|locked|completed)
- `season_id, club_id` (FK pointers - how to find matches!)
- `league_code` (unique join code)
- `squad_size, transfers_per_season`
- `min_batsmen, min_bowlers, require_wicket_keeper`
- `max_players_per_team, require_from_each_team`

### Player
- `multiplier` (0.69-5.0, lower = better)
- `starting_multiplier` (initial at season start)
- `prev_season_fantasy_points` (for calculation)
- `is_active` (in active roster?)
- `rl_team` (STRING: "ACC 1", "U17", etc.)
- `role` (BATSMAN|BOWLER|ALL_ROUNDER|WICKET_KEEPER)

### FantasyTeam
- `is_finalized` (locked for season)
- `finalized_at` (MISSING - should track when)
- `total_points` (cumulative)
- `rank` (leaderboard position)
- `captain_id, vice_captain_id`
- `transfers_used, extra_transfers_granted`

### PlayerPerformance
- `base_fantasy_points` (before multipliers)
- `multiplier_applied` (player handicap)
- `captain_multiplier` (1.0/1.5/2.0)
- `final_fantasy_points` (after all)
- `fantasy_team_id, league_id` (context)
- `round_number` (week of season)

## Critical Data Relationships

### League → Match → Performance

**Problem**: League has no direct FK to Match!

**Solution**:
```
League (id=X, season_id=S, club_id=C)
  → Match WHERE season_id=S AND club_id=C
    → PlayerPerformance WHERE match_id IN (...)
```

### LeagueRoster Usage

LeagueRoster is a **junction table** (league ↔ player) that:
- Defines which players are available in each league
- Populated automatically at league creation
- Can vary between leagues
- Used to validate team composition

## Multiplier System

**Formula**:
- Below median: 5.0 (worst) → 1.0 (median)
- Above median: 1.0 (median) → 0.69 (best)

**Data Sources** (in order):
1. `Player.prev_season_fantasy_points` (stored)
2. Calculate from `player_performances` (previous season)
3. Scrape from KNCB (if scrape_missing=true)

**Storage**:
- `Player.multiplier` - Current
- `Player.starting_multiplier` - Initial
- `PlayerPerformance.multiplier_applied` - Used in scoring

**Set At**: `POST /api/admin/roster/confirm`

## Points Calculation

```
base_fantasy_points = [batting + bowling + fielding]
with_multiplier = base_fantasy_points × player.multiplier
with_captain = with_multiplier × captain_multiplier (1.0/1.5/2.0)
final_fantasy_points = with_captain
```

## Admin Endpoints (Essential)

**Season**:
- `POST /api/admin/seasons` - Create
- `GET /api/admin/seasons` - List
- `PATCH /api/admin/seasons/{id}` - Update
- `POST /api/admin/seasons/{id}/activate` - Activate (deactivates others)

**League**:
- `POST /api/admin/leagues` - Create with roster population
- `GET /api/admin/leagues` - List
- `GET /api/admin/leagues/{id}` - Details
- `PATCH /api/admin/leagues/{id}` - Update rules

**Roster**:
- `POST /api/admin/roster/confirm` - Activate players & calculate multipliers
- `POST /api/admin/setup-season` - Complete workflow
- `POST /api/admin/clubs/{id}/load-roster` - Load legacy JSON

**Players**:
- `GET /api/admin/clubs/{id}/players` - List with filters
- `POST /api/admin/clubs/{id}/players` - Add manually
- `PUT /api/admin/players/{id}` - Update
- `DELETE /api/admin/players/{id}` - Remove

**Teams**:
- `POST /api/admin/leagues/{id}/teams/{team_id}/grant-transfer` - Extra transfers
- `GET /api/admin/leagues/{id}/transfer-requests` - Pending approvals
- `POST /api/admin/leagues/{id}/transfer-requests/{id}/approve` - Approve
- `GET /api/admin/leagues/{id}/teams/{team_id}/validate` - Validate composition

## Weekly Admin Workflow

**Tuesday Evening**:
1. Run scraper (auto or manual): `docker exec fantasy_cricket_api python3 scrape_weekly.py`
2. Run simulation: `./run_weekly_simulation.sh <round_number>`

**Wednesday Morning**:
1. Verify leaderboard
2. Check database for correct points
3. Notify users (optional)

## Missing Features

### League Confirmation/Launch

What's needed:
1. `League.status` field (draft|active|locked|completed)
2. `League.frozen_rules` snapshot (prevent mid-season changes)
3. `FantasyTeam.finalized_at` timestamp
4. Endpoints:
   - `POST /api/admin/leagues/{id}/confirm` (draft→active)
   - `POST /api/admin/leagues/{id}/lock` (active→locked)
   - `POST /api/leagues/{league_id}/teams/{team_id}/finalize` (user endpoint)

### League-Specific Multipliers

Currently:
- Multipliers stored globally on `Player`
- Same for all leagues

Needed:
- Capture at confirmation: `League.multipliers_snapshot` (JSON)
- Use in scoring instead of `Player.multiplier`
- Prevents mid-season multiplier changes from affecting old matches

## Status Patterns

### Season Status
```
draft → active (registration_open=true, scraping_enabled=true)
     → inactive
```

### League Status (MISSING)
```
draft → active (rules frozen) → locked (teams locked) → completed
```

### Player Status
```
active ↔ inactive (per season)
```

### Team Status
```
not_finalized → finalized (is_finalized=true)
```

## File Locations

| File | Purpose | Size |
|------|---------|------|
| `/backend/database_models.py` | Core schemas | 604 lines |
| `/backend/admin_endpoints.py` | Admin API | 1320 lines |
| `/backend/league_endpoints.py` | League management | 473 lines |
| `/backend/multiplier_calculator.py` | Multiplier math | 180+ lines |
| `/ADMIN_WEEKLY_PROCEDURES.md` | Weekly tasks | |
| `/ADMIN_SETUP_GUIDE.md` | Setup workflow | |
| `/DATABASE_SCHEMA.md` | Schema docs | |

## Common Queries

```sql
-- Active league with team details
SELECT l.id, l.name, COUNT(ft.id) as teams, l.status
FROM leagues l
LEFT JOIN fantasy_teams ft ON l.id = ft.league_id
WHERE l.status = 'active'
GROUP BY l.id;

-- Player multipliers
SELECT name, multiplier, starting_multiplier, multiplier_updated_at
FROM players
ORDER BY multiplier ASC;

-- Team scores
SELECT team_name, total_points, is_finalized, rank
FROM fantasy_teams
WHERE league_id = '<league_id>'
ORDER BY total_points DESC;

-- Performance this week
SELECT pp.player_id, SUM(pp.fantasy_points) as week_points
FROM player_performances pp
WHERE pp.round_number = <round>
GROUP BY pp.player_id;
```

## Environment Variables

```bash
DATABASE_URL=postgresql://cricket_admin:password@fantasy_cricket_db:5432/fantasy_cricket
REDIS_URL=redis://fantasy_cricket_redis:6379
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=production
FRONTEND_URL=https://fantcric.fun
```

## Points Rules Summary

- **Runs**: 1 point per run
- **Wickets**: 25 points per wicket
- **Catches**: 8 points per catch
- **Stumpings** (WK only): 12 points per stumping
- **Maidens** (bowler): 4 points per maiden
- **Strike Rate Bonus** (batsman): 10 points if SR > 100
- **Economy Bonus** (bowler): 5 points if economy < 6
- **Fifty Bonus** (batsman): 25 points
- **Century Bonus** (batsman): 50 points

## Multipliers in Action

**Example**:
- Player base_points: 50
- Player multiplier: 1.5 (below average)
- Captain multiplier: 2.0
- Calculation: 50 × 1.5 × 2.0 = 150 points

---

**Quick Navigation**:
- Architecture: See `/LEAGUE_ARCHITECTURE_ANALYSIS.md`
- Implementation: See `/IMPLEMENTATION_GUIDE.md`
- Admin procedures: See `/ADMIN_WEEKLY_PROCEDURES.md`
- Database schema: See `/DATABASE_SCHEMA.md`

