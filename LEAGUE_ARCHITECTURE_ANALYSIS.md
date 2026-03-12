# Fantasy Cricket Platform - Architecture Summary

## Project Overview

This is a **Fantasy Cricket Platform** built with FastAPI (backend) and React (frontend), designed for the Amsterdamsche Cricket Club (ACC) to manage fantasy cricket leagues similar to Fantasy Premier League.

**Current Status**: Production-ready with core functionality (Season, League, Team, Player management)

---

## 1. DATABASE SCHEMA RELATIONSHIPS

### Core Entity Relationships

```
SEASON (annual/tournament seasons)
  ├─→ CLUB (e.g., ACC)
  │    ├─→ TEAM (e.g., ACC 1, ACC 2, U15, U17)
  │    │    ├─ value_multiplier (1.0-5.0)
  │    │    └─ points_multiplier (1.0-5.0)
  │    │
  │    └─→ PLAYER (513 players total)
  │         ├─ rl_team: "ACC 1" (STRING, not FK!)
  │         ├─ role: BATSMAN|BOWLER|ALL_ROUNDER|WICKET_KEEPER
  │         ├─ multiplier: 0.69-5.0 (performance handicap)
  │         ├─ starting_multiplier (initial at season start)
  │         └─ prev_season_fantasy_points (for calculation)
  │
  └─→ LEAGUE (fantasy league competition)
       ├─ season_id, club_id (FK to season + club)
       ├─ league_code (unique join code)
       ├─ squad_size, transfers_per_season
       ├─ Constraints:
       │  ├─ min_batsmen, min_bowlers
       │  ├─ require_wicket_keeper
       │  ├─ max_players_per_team
       │  ├─ require_from_each_team (must have 1 from all 10 teams)
       │
       ├─→ LEAGUE_ROSTER (junction: league ↔ player)
       │    └─ Defines which players available in league
       │
       └─→ FANTASY_TEAM (user's team in league)
            ├─ user_id (owns this team)
            ├─ team_name
            ├─ is_finalized (LOCKED for play once set)
            ├─ total_points (cumulative)
            ├─ rank (updated weekly)
            ├─ captain_id, vice_captain_id
            ├─ transfers_used, extra_transfers_granted
            │
            └─→ FANTASY_TEAM_PLAYER (junction: fantasy_team ↔ player)
                 ├─ purchase_value (legacy, always 0)
                 ├─ is_captain (2x points)
                 ├─ is_vice_captain (1.5x points)
                 ├─ is_wicket_keeper
                 └─ total_points (player's cumulative in this team)
```

### Match & Performance Data

```
MATCH (season_id, club_id - connects to League via Season+Club)
  ├─ match_date, opponent, venue
  ├─ result: "won"|"lost"|"tied"|"no_result"
  ├─ is_processed (has performance data been extracted?)
  ├─ raw_scorecard_data (JSON from KNCB)
  │
  └─→ PLAYER_PERFORMANCE (per-match player stats)
       ├─ Batting: runs, balls_faced, fours, sixes, is_out, dismissal_type
       ├─ Bowling: overs_bowled, maidens, runs_conceded, wickets
       ├─ Fielding: catches, run_outs, stumpings
       ├─ Fantasy Context:
       │  ├─ fantasy_team_id (if part of a team)
       │  ├─ league_id (which league this perf is counted in)
       │  ├─ round_number (week of season)
       │  ├─ is_captain, is_vice_captain, is_wicket_keeper
       │
       └─ Points Breakdown:
          ├─ base_fantasy_points (before multipliers)
          ├─ multiplier_applied (0.69-5.0)
          ├─ captain_multiplier (1.0/1.5/2.0)
          └─ final_fantasy_points (after all multipliers)
```

### CRITICAL: League → Performance Data Join

**Problem**: League has `season_id` and `club_id`, but no direct `league_id` on matches.

**Solution**: Use league's season_id + club_id to find matches:
```
League (id=X, season_id=S, club_id=C)
  → Match WHERE season_id=S AND club_id=C
    → PlayerPerformance WHERE match_id IN (...)
```

### Key Design Points

1. **No team_id FK on Player**: Players use `rl_team` STRING field instead (e.g., "ACC 1", "ACC ZAMI", "U17")
2. **LeagueRoster is essential**: Defines which players are available in each league (leagues can have different rosters)
3. **Player multipliers are performance-based**: 
   - Calculated from previous season fantasy points
   - 0.69 (best performers) ← → 5.0 (worst performers)
   - 1.0 = neutral/median
4. **is_finalized on FantasyTeam**: Once TRUE, team is locked (no more changes)
5. **multiplier + captain_multiplier are separate**: First player handicap, then position bonus

---

## 2. CURRENT MULTIPLIER SYSTEM

### Multiplier Calculation (multiplier_calculator.py)

**Formula:**
- Players below median: Linear scale from MAX (5.0) at min → NEUTRAL (1.0) at median
- Players at median: NEUTRAL_MULTIPLIER (1.0)
- Players above median: Linear scale from NEUTRAL (1.0) → MIN (0.69) at max

**Workflow:**
```
1. Get prev_season_fantasy_points for each player
2. If missing, calculate from previous season matches
3. If still missing and scrape_missing=true, scrape from KNCB
4. Players with no data get 1.0 multiplier
5. Calculate median from players WITH data
6. Generate multipliers relative to median
```

**Data Sources:**
- Primary: `Player.prev_season_fantasy_points` (stored field)
- Secondary: Calculate from `player_performances` table (previous season matches)
- Tertiary: Scrape from KNCB if needed (scrape_missing=true)

**Storage:**
- `Player.multiplier` - Current multiplier
- `Player.starting_multiplier` - Initial multiplier at season start
- `Player.multiplier_updated_at` - Last update timestamp
- `PlayerPerformance.multiplier_applied` - Which multiplier was used for this performance

**Updates:**
- Set at roster confirmation (`/api/admin/roster/confirm` endpoint)
- Can be manually adjusted per-player or bulk updated

---

## 3. LEAGUE LIFECYCLE & STATUS MANAGEMENT

### Season Lifecycle

```
CREATE SEASON (name, year, dates)
  ↓
UPDATE SEASON (name, dates, description)
  ↓
ACTIVATE SEASON (one at a time, deactivates others)
  │ Sets: is_active=true, registration_open=true, scraping_enabled=true
  │
  └─→ LEAGUES can be created for this season
  
DEACTIVATE SEASON
  └─ Sets: is_active=false
```

### League Lifecycle (INCOMPLETE - NO CONFIRM/LAUNCH FOUND)

```
CREATE LEAGUE
  ├─ season_id, club_id (both REQUIRED)
  ├─ name, description, league_code (auto-generated)
  ├─ Rules: squad_size, transfers_per_season, constraints
  ├─ POPULATE LEAGUE_ROSTER (senior + youth teams)
  │  └─ All selected players added to LeagueRoster
  │
  ├─ UPDATE LEAGUE (modify rules)
  │
  └─→ FANTASY_TEAMS can be created by users
       ├─ User selects players from LeagueRoster
       ├─ Must follow league rules
       ├─ SET CAPTAIN/VICE-CAPTAIN
       │
       └─ is_finalized = FALSE (still editable)
```

**ISSUE**: No explicit "confirm" or "launch" step for leagues!
- Leagues can be created but no status field to mark "ready to play"
- No protection against modifying league rules mid-season
- No explicit transition point where teams lock

### Player/Roster Lifecycle

```
CONFIRM ROSTER (admin endpoint: /api/admin/roster/confirm)
  ├─ Input: youth_teams to include
  │
  ├─ DEACTIVATE excluded youth teams
  │ └─ Players with rl_team in excluded list → is_active=false
  │
  ├─ ACTIVATE included youth teams
  │ └─ Players with rl_team in included list → is_active=true
  │
  ├─ ENSURE senior teams active
  │ └─ ACC 1-6, ZAMI 1 → is_active=true
  │
  └─ CALCULATE MULTIPLIERS (if enabled)
     ├─ Get active_player_ids
     ├─ Run calculate_roster_multipliers()
     ├─ Apply multipliers to db
     └─ Set multiplier_updated_at timestamp
```

---

## 4. ADMIN WORKFLOW FILES

### Key Admin Endpoints (admin_endpoints.py)

**Season Management:**
- POST `/api/admin/seasons` - Create season
- GET `/api/admin/seasons` - List all
- GET `/api/admin/seasons/{id}` - Get detail
- PATCH `/api/admin/seasons/{id}` - Update
- POST `/api/admin/seasons/{id}/activate` - Activate (deactivates others)

**Club Management:**
- POST `/api/admin/clubs` - Create club
- GET `/api/admin/clubs` - List all
- POST `/api/admin/clubs/{id}/teams` - Create team

**Player Management:**
- GET `/api/admin/clubs/{id}/players` - List with filters (role, multiplier)
- POST `/api/admin/clubs/{id}/players` - Add manually
- PUT `/api/admin/players/{id}` - Update details
- DELETE `/api/admin/players/{id}` - Remove

**Roster Setup:**
- POST `/api/admin/roster/confirm` - Activate/deactivate teams and calculate multipliers
- POST `/api/admin/setup-season` - Complete season workflow (create season + club + load roster)
- POST `/api/admin/clubs/{id}/load-roster` - Load legacy roster JSON

### Key League Endpoints (league_endpoints.py)

**League Management:**
- POST `/api/admin/leagues` - Create league with roster population
- GET `/api/admin/leagues` - List all
- GET `/api/admin/leagues/{id}` - Get detail with team info
- PATCH `/api/admin/leagues/{id}` - Update rules

**Fantasy Team Management (within league):**
- POST `/api/admin/leagues/{id}/teams/{team_id}/grant-transfer` - Grant extra transfers
- GET `/api/admin/leagues/{id}/transfer-requests` - Get pending requests
- POST `/api/admin/leagues/{id}/transfer-requests/{id}/approve` - Approve transfer request
- GET `/api/admin/leagues/{id}/teams/{team_id}/validate` - Validate team composition

### Weekly Admin Procedures (ADMIN_WEEKLY_PROCEDURES.md)

**Timeline:**
```
Tuesday Evening:
  1. Scrape weekly scorecards (auto via Celery or manual)
  2. Run fantasy team simulation (./run_weekly_simulation.sh <round>)

Wednesday Morning:
  1. Verify leaderboard on website
  2. Check database for correct points
  3. Notify users (optional)
```

**What Happens During Simulation:**
- Fetch all active fantasy teams
- Load PlayerPerformance for current round
- Calculate points: base + multiplier + captain bonus
- Update team totals (cumulative)
- Update leaderboard rankings
- Generate logs

---

## 5. EXISTING "CONFIRM" FUNCTIONALITY

### `is_finalized` on FantasyTeam

```python
class FantasyTeam(Base):
    is_finalized = Column(Boolean, default=False)  # Locked for season
```

**Purpose**: Once TRUE, team cannot be edited (locked in for season)
**Current Usage**: Checked in team validation endpoints
**Missing**: No explicit endpoint to finalize a team (set is_finalized=true)

### Roster Confirmation Endpoint

```
POST /api/admin/roster/confirm
Body:
  - youth_teams: ["U15", "U17"]
  - calculate_multipliers: true (optional)

Does:
  1. Deactivates excluded youth teams' players
  2. Activates included youth teams' players
  3. Ensures senior teams active
  4. Calculates and applies multipliers
```

**Limitation**: This is for ADMIN only, not for users
**When Called**: After loading legacy roster, before league season starts

---

## 6. STATUS/STATE MANAGEMENT PATTERNS

### Season Status Fields

```python
class Season(Base):
    is_active: bool           # Only one can be TRUE
    registration_open: bool   # Can users create teams?
    scraping_enabled: bool    # Auto-scrape scorecards?
```

### League Status Fields

```python
class League(Base):
    is_public: bool           # Joinable by anyone?
    max_participants: int     # Capacity
    # MISSING: status field for draft/active/completed
```

### Player Status Fields

```python
class Player(Base):
    is_active: bool           # In active roster?
    multiplier_updated_at: DateTime  # Timestamp tracking
```

### Team Status Fields

```python
class FantasyTeam(Base):
    is_finalized: bool        # Locked for season?
    rank: int                 # Current ranking
    total_points: float       # Cumulative
    last_round_points: float  # Weekly points
    transfers_used: int       # Transfers spent
```

### Transfer Request Status

```python
class Transfer(Base):
    requires_approval: bool   # Needs admin OK?
    is_approved: bool         # Admin approved?
    approved_by: str          # Admin user ID
    approved_at: DateTime     # When approved
    transfer_type: str        # regular|extra_granted|initial
```

---

## 7. DATA FLOW FOR LEAGUE-SPECIFIC ROSTERS

### Current Implementation

```
League Creation:
1. Admin creates league (season_id, club_id, rules)
2. System generates league_code
3. System populates LeagueRoster with available players
   └─ Senior teams: ACC 1-6, ZAMI 1
   └─ Youth teams: As specified in request

User Team Creation:
1. User selects players from LeagueRoster
2. System validates against league rules:
   ├─ Squad size
   ├─ Min/max per team
   ├─ Role requirements
   ├─ Wicket-keeper requirement
3. Team created with is_finalized=false

Team Finalization:
1. User clicks "confirm" on UI (inferred)
2. is_finalized set to TRUE
3. Captain/vice-captain locked in
4. Team ready for scoring
```

### Issues with Current Design

1. **No explicit league "launch" step**
   - League rules can change even after users join
   - No protection for mid-season rule changes
   
2. **LeagueRoster is point-in-time**
   - Created at league creation
   - If players added later, existing leagues don't get them
   - No way to update league roster dynamically

3. **Team Finalization**
   - No endpoint to finalize a team
   - UI presumably calls some endpoint not visible in code
   - No timestamp tracking when finalized

4. **Multiplier Distribution**
   - Multipliers set at roster confirm
   - Same across all leagues
   - Not league-specific

---

## 8. EXISTING MULTIPLIER STORAGE & USE

### Where Multipliers Are Stored

1. **Player.multiplier** - Current performance multiplier (0.69-5.0)
2. **Player.starting_multiplier** - Initial value at season start
3. **PlayerPerformance.multiplier_applied** - Which multiplier used in this match
4. **Team.value_multiplier** - Team tier multiplier (for player values, not used in scoring)
5. **Team.points_multiplier** - Team tier multiplier (for points, not currently used)

### Where Multipliers Are Used

1. **Point Calculation** (during weekly simulation):
   ```
   base_points × multiplier × captain_multiplier = final_points
   ```

2. **Multiplier Drift**:
   - Multipliers can be adjusted during season
   - Stored in multiplier_calculator
   - Applied retroactively in calculations

3. **Price Valuation** (LEGACY, not used):
   - value_multiplier on Team (tier adjustment)
   - No longer used in current system

---

## SUMMARY TABLE: Key Entities & Their Status Fields

| Entity | Status Field(s) | Lifecycle | Notes |
|--------|-----------------|-----------|-------|
| Season | is_active, registration_open, scraping_enabled | Create → Update → Activate (deactivate others) | Only 1 active at a time |
| League | is_public, max_participants | Create → Update → Play (IMPLICIT) | MISSING explicit status |
| LeagueRoster | created_at | Auto-populated at league creation | Junction table, immutable |
| Player | is_active, multiplier_updated_at | Active/Inactive per season | Set at roster confirm |
| FantasyTeam | is_finalized, rank | Create → Finalize (IMPLICIT) | MISSING explicit finalize endpoint |
| Transfer | requires_approval, is_approved | Pending → Approved → Applied | Can require admin OK |
| PlayerPerformance | round_number, points breakdown | Created during simulation | Immutable once created |

---

## RECOMMENDATIONS FOR LEAGUE CONFIRMATION FEATURE

### 1. Add League Status Field
```python
class League(Base):
    status: str  # "draft" | "active" | "locked" | "completed"
    confirmed_at: DateTime = None
    # Transitions:
    # draft → active: League rules locked, teams can finalize
    # active → locked: Registration closed, no new teams
    # locked → completed: Season ended
```

### 2. Add Team Finalization Endpoint
```
POST /api/leagues/{league_id}/teams/{team_id}/finalize
  - Sets is_finalized = TRUE
  - Validates against league rules
  - Records finalized_at timestamp
  - Locks captain/vice-captain selections
```

### 3. League Confirmation Workflow
```
POST /api/admin/leagues/{league_id}/confirm
  - Validates all active teams are finalized
  - Sets league.status = "active"
  - Locks league rules (copy to frozen_rules)
  - Prevents new team creations after this
  - Records confirmed_at timestamp
```

### 4. League-Specific Multipliers (Future)
```
- Store multipliers per league at confirmation time
- Allows different leagues to have different multipliers
- Protects against mid-season multiplier changes
```

---

## FILE REFERENCES

- **Database Models**: `/backend/database_models.py` (604 lines)
- **Admin Endpoints**: `/backend/admin_endpoints.py` (1320 lines)
- **League Endpoints**: `/backend/league_endpoints.py` (473 lines)
- **Multiplier Calculator**: `/backend/multiplier_calculator.py` (180+ lines)
- **Admin Procedures**: `ADMIN_WEEKLY_PROCEDURES.md`
- **Admin Setup Guide**: `ADMIN_SETUP_GUIDE.md`
- **Schema Docs**: `DATABASE_SCHEMA.md` + `SCHEMA_RELATIONSHIP_DIAGRAM.md`

---

**Generated**: 2025-12-19
**Platform**: Fantasy Cricket (ACC - Amsterdamsche Cricket Club)
**Status**: Production-Ready (Core), Enhancement-Ready (League Confirmation)

