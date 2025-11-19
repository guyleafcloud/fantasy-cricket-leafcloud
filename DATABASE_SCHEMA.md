# Database Schema Documentation

## CRITICAL WARNING ⚠️

**PRODUCTION AND LOCAL DEV DATABASES MAY HAVE DIFFERENT SCHEMAS**

Always check production schema before modifying `database_models.py`. Never assume your local development database matches production!

## How to Check Production Schema

```bash
# SSH to production
ssh ubuntu@fantcric.fun

# Check table structure
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d table_name'

# List all tables
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\dt'

# Check enum types
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "SELECT enum_range(NULL::enum_name);"
```

## Production Schema (fantcric.fun)

### Core Tables

#### players
The heart of the system - all ACC cricket players.

```sql
Column                | Type                        | Nullable | Notes
----------------------|----------------------------|----------|------------------
id                    | VARCHAR                    | NOT NULL | Primary key
name                  | VARCHAR                    | NOT NULL | Player full name
club_id               | VARCHAR                    | NOT NULL | FK to clubs.id
role                  | playerrole (ENUM)          | NOT NULL | See ENUM below
tier                  | crickettier (ENUM)         | NOT NULL | HOOFDKLASSE, etc.
base_price            | INTEGER                    | NOT NULL | Starting price
current_price         | INTEGER                    | NOT NULL | Current market price
matches_played        | INTEGER                    | NULL     | Season stats
runs_scored           | INTEGER                    | NULL     | Season stats
balls_faced           | INTEGER                    | NULL     | Season stats
wickets_taken         | INTEGER                    | NULL     | Season stats
balls_bowled          | INTEGER                    | NULL     | Season stats
catches               | INTEGER                    | NULL     | Season stats
stumpings             | INTEGER                    | NULL     | Season stats (WK only)
batting_average       | DOUBLE PRECISION           | NULL     | Calculated stat
strike_rate           | DOUBLE PRECISION           | NULL     | Calculated stat
bowling_average       | DOUBLE PRECISION           | NULL     | Calculated stat
economy_rate          | DOUBLE PRECISION           | NULL     | Calculated stat
total_fantasy_points  | DOUBLE PRECISION           | NULL     | Cumulative points
is_active             | BOOLEAN                    | NULL     | Is player active
created_at            | TIMESTAMP                  | NULL     | Record creation
multiplier            | DOUBLE PRECISION           | NULL     | Performance multiplier (default 1.0)
multiplier_updated_at | TIMESTAMP                  | NULL     | Last multiplier update
rl_team               | VARCHAR(50)                | NULL     | Real-life team (e.g., "ACC 1", "ACC ZAMI")

Foreign Keys:
  - club_id → clubs.id

Referenced By:
  - fantasy_team_players.player_id
  - fantasy_teams.captain_id
  - fantasy_teams.vice_captain_id
  - player_performances.player_id
  - transfers.player_in_id, player_out_id
```

**IMPORTANT NOTES:**
- **NO team_id field** - players do NOT have foreign key to teams table
- Uses `role` field (NOT `player_type`)
- `role` is a PostgreSQL ENUM type called `playerrole`
- `rl_team` is a string field for real-life team assignment

**playerrole ENUM Values:**
- `BATSMAN`
- `BOWLER`
- `ALL_ROUNDER`
- `WICKET_KEEPER`

#### fantasy_teams
User-created fantasy teams.

```sql
Column             | Type         | Notes
-------------------|--------------|------------------------
id                 | VARCHAR      | Primary key
team_name          | VARCHAR      | User-chosen name
user_id            | VARCHAR      | FK to users.id
league_id          | VARCHAR      | FK to leagues.id
budget_used        | INTEGER      | LEGACY - not used
budget_remaining   | INTEGER      | LEGACY - not used
squad_size         | INTEGER      | Number of players
captain_id         | VARCHAR      | FK to players.id (2x points)
vice_captain_id    | VARCHAR      | FK to players.id (1.5x points)
is_finalized       | BOOLEAN      | Team locked for play
total_points       | DOUBLE PRECISION | Cumulative score
created_at         | TIMESTAMP    |
updated_at         | TIMESTAMP    |

**NOTE:** budget_used and budget_remaining are legacy fields kept for schema compatibility.
The game does NOT use budgets. Players are selected based on role requirements only.

Foreign Keys:
  - user_id → users.id
  - league_id → leagues.id
  - captain_id → players.id
  - vice_captain_id → players.id
```

#### fantasy_team_players
Junction table linking fantasy teams to players.

```sql
Column             | Type              | Notes
-------------------|-------------------|---------------------------
id                 | VARCHAR           | Primary key
fantasy_team_id    | VARCHAR           | FK to fantasy_teams.id
player_id          | VARCHAR           | FK to players.id
purchase_value     | INTEGER           | LEGACY - not used (always 0)
is_captain         | BOOLEAN           | 2x point multiplier
is_vice_captain    | BOOLEAN           | 1.5x point multiplier
is_wicket_keeper   | BOOLEAN           | For catch bonuses
joined_at          | TIMESTAMP         |

**NOTE:** purchase_value is a legacy field kept for schema compatibility. Always set to 0.

Unique Constraint: (fantasy_team_id, player_id)
```

#### leagues
Competitions where fantasy teams compete.

```sql
Column                  | Type      | Notes
------------------------|-----------|--------------------------------
id                      | VARCHAR   | Primary key
name                    | VARCHAR   | League name
season_id               | VARCHAR   | FK to seasons.id
club_id                 | VARCHAR   | FK to clubs.id
total_budget            | INTEGER   | Budget for team building
squad_size              | INTEGER   | Number of players per team
max_players_per_team    | INTEGER   | Max from same real team (optional)
min_batsmen             | INTEGER   | Required batsmen
min_bowlers             | INTEGER   | Required bowlers
require_from_each_team  | BOOLEAN   | All real teams represented
min_players_per_team    | INTEGER   | Min per real team
is_public               | BOOLEAN   | Publicly joinable
created_at              | TIMESTAMP |
```

#### seasons
Annual or tournament seasons.

```sql
Column      | Type      | Notes
------------|-----------|---------------------------
id          | VARCHAR   | Primary key
name        | VARCHAR   | "ACC 2025 Season"
start_date  | DATE      | Season start
end_date    | DATE      | Season end
is_active   | BOOLEAN   | Currently active
created_at  | TIMESTAMP |
```

#### clubs
Cricket clubs (mainly just ACC).

```sql
Column      | Type      | Notes
------------|-----------|---------------------------
id          | VARCHAR   | Primary key
name        | VARCHAR   | "ACC"
city        | VARCHAR   | "Amsterdam"
created_at  | TIMESTAMP |
```

#### users
Registered users.

```sql
Column         | Type      | Notes
---------------|-----------|---------------------------
id             | VARCHAR   | Primary key
email          | VARCHAR   | Unique, for login
username       | VARCHAR   | Display name
password_hash  | VARCHAR   | Hashed password
is_admin       | BOOLEAN   | Admin privileges
is_active      | BOOLEAN   | Account status
created_at     | TIMESTAMP |
```

### Supporting Tables

#### teams
Real-life cricket teams (e.g., ACC 1, ACC 2, ACC ZAMI, U17).

```sql
Column      | Type      | Notes
------------|-----------|---------------------------
id          | VARCHAR   | Primary key
name        | VARCHAR   | Team name
club_id     | VARCHAR   | FK to clubs.id
level       | VARCHAR   | "First Team", "Second Team", etc.
created_at  | TIMESTAMP |

Unique Constraint: (club_id, level)
```

**CRITICAL**: The `teams` table exists but is **NOT directly linked to players**.
- Players have `rl_team` (string) instead of `team_id` (FK)
- Team-based validation rules use the `rl_team` string field (e.g., "ACC 1", "ACC 2", "ZAMI 1")

#### player_performances
Match-by-match player statistics.

```sql
Column             | Type             | Notes
-------------------|------------------|------------------------
id                 | VARCHAR          | Primary key
player_id          | VARCHAR          | FK to players.id
match_id           | VARCHAR          | FK to matches.id
runs               | INTEGER          |
balls_faced        | INTEGER          |
wickets            | INTEGER          |
balls_bowled       | INTEGER          |
catches            | INTEGER          |
stumpings          | INTEGER          |
fantasy_points     | DOUBLE PRECISION | Points for this match
created_at         | TIMESTAMP        |
```

#### matches
Cricket matches.

```sql
Column      | Type      | Notes
------------|-----------|---------------------------
id          | VARCHAR   | Primary key
season_id   | VARCHAR   | FK to seasons.id
home_team   | VARCHAR   | Team name
away_team   | VARCHAR   | Team name
match_date  | DATE      | When played
venue       | VARCHAR   | Location
status      | VARCHAR   | "scheduled", "completed", etc.
created_at  | TIMESTAMP |
```

#### transfers
Player transfers (add/remove from team).

```sql
Column          | Type      | Notes
----------------|-----------|------------------------
id              | VARCHAR   | Primary key
fantasy_team_id | VARCHAR   | FK to fantasy_teams.id
player_out_id   | VARCHAR   | FK to players.id
player_in_id    | VARCHAR   | FK to players.id
transfer_cost   | INTEGER   | Transaction cost
transfer_date   | TIMESTAMP |
```

## SQLAlchemy Model Mapping

### Critical Rules for `database_models.py`

1. **Column Names Must Match Exactly**
   - Database: `role` → Model: `Column(..., name='role')`
   - NOT `player_type` or any other name

2. **Enum Types**
   - Database has PostgreSQL ENUMs
   - SQLAlchemy uses String columns, not custom enums
   - Validation happens at app layer

3. **Foreign Keys**
   - Only define FKs that exist in production
   - `team_id` does NOT exist on players table
   - Don't add relationships without FKs

4. **Relationships**
   - Only define if both FK exists AND is needed
   - `Player.team` relationship is NOT valid (no FK)
   - Use `back_populates` for bidirectional relationships

### Current Production Model (Correct)

```python
class Player(Base):
    __tablename__ = "players"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    club_id = Column(String(50), ForeignKey("clubs.id"), nullable=False)

    # String field, NOT FK
    rl_team = Column(String(50), nullable=True)

    # Called 'role', NOT 'player_type'
    role = Column(String(50), nullable=False)
    tier = Column(String(50), nullable=False)

    # Legacy pricing fields (NOT USED - kept for schema compatibility)
    base_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False)

    # Note: NO fantasy_value fields in production
    # These were added in local dev but don't exist in production
    # Note: The game does NOT use budgets or player pricing

    # Performance multiplier
    multiplier = Column(Float, default=1.0)
    multiplier_updated_at = Column(DateTime, nullable=True)

    # Season stats
    matches_played = Column(Integer, nullable=True)
    runs_scored = Column(Integer, nullable=True)
    # ... etc

    # Relationships
    club = relationship("Club", back_populates="players")
    fantasy_team_players = relationship("FantasyTeamPlayer", back_populates="player")

    # NO team relationship - team_id doesn't exist!
```

## Common Mistakes to Avoid

### ❌ WRONG - Adding Fields That Don't Exist
```python
class Player(Base):
    team_id = Column(String(50), ForeignKey("teams.id"))  # Does NOT exist!
    player_type = Column(String(50))  # Should be 'role'!
    fantasy_value = Column(Float)  # Does NOT exist in production!
```

### ✅ CORRECT - Match Production Schema
```python
class Player(Base):
    role = Column(String(50), nullable=False)  # Matches production
    rl_team = Column(String(50), nullable=True)  # String, not FK
    # No team_id, no fantasy_value
```

### ❌ WRONG - Invalid Relationships
```python
class Player(Base):
    team = relationship("Team", foreign_keys=[team_id])  # NO!
```

### ✅ CORRECT - Only Valid Relationships
```python
class Player(Base):
    club = relationship("Club", back_populates="players")  # Has FK
    fantasy_team_players = relationship("FantasyTeamPlayer", back_populates="player")  # Has FK
```

## Schema Migration Strategy

If you need to add fields to production:

1. **Check if field already exists** (might be in DB but not in model)
2. **Write Alembic migration** (don't modify models first)
3. **Test migration locally**
4. **Backup production database**
5. **Run migration on production**
6. **Update SQLAlchemy models**
7. **Deploy code**

## Verification Checklist

Before deploying database model changes:

- [ ] Checked production schema with `\d table_name`
- [ ] Verified field names match exactly
- [ ] Confirmed all FK constraints exist
- [ ] No relationships without FK
- [ ] Tested locally with production-like schema
- [ ] Reviewed `DATABASE_SCHEMA.md` (this document)
- [ ] Read `DEVELOPMENT_GUIDE.md` procedures

## Quick Reference

### ACC Club ID (Production)
```
625f1c55-6d5b-40a9-be1d-8f7abe6fa00e
```

### Total Players in Production
```
513 players
```

### Database Connection Details
- **Host**: fantasy_cricket_db (Docker)
- **Database**: fantasy_cricket
- **User**: cricket_admin
- **Port**: 5432 (internal)

## Additional Resources

- See `PROJECT_SCOPE.md` for project overview
- See `DEVELOPMENT_GUIDE.md` for development workflows
- See `TROUBLESHOOTING.md` for common issues
