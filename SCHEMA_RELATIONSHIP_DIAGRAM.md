# Database Schema Relationship Diagram

## Complete Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS & LEAGUES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐  ┌──────────────┐   │
│  │   users      │         │   seasons    │  │    clubs     │   │
│  ├──────────────┤         ├──────────────┤  ├──────────────┤   │
│  │ id (PK)      │         │ id (PK)      │  │ id (PK)      │   │
│  │ email        │         │ year         │  │ name         │   │
│  │ password     │         │ name         │  │ tier         │   │
│  │ is_admin     │         │ is_active    │  │ location     │   │
│  └──────────────┘         └──────────────┘  └──────────────┘   │
│         △                          △                  △           │
│         │                          │                  │           │
│         │                          └──────┬───────────┘           │
│         │                                 │ (season_id, club_id)  │
│         │                                 ▼                       │
│         │                          ┌──────────────┐              │
│         │                          │   leagues    │              │
│         │                          ├──────────────┤              │
│         │                          │ id (PK)      │              │
│         │                          │ season_id ───┼──> Season    │
│         │                          │ club_id ─────┼──> Club      │
│         │                          │ name         │              │
│         │                          │ league_code  │              │
│         │                          └──────────────┘              │
│         │                                 │                       │
│         │                                 │                       │
│         └─────────────────┬────────────────┘                     │
│                           │ (league_id)                          │
│                           ▼                                       │
│                    ┌──────────────────┐                          │
│                    │  fantasy_teams   │                          │
│                    ├──────────────────┤                          │
│                    │ id (PK)          │                          │
│                    │ user_id ─────────┼──> User                  │
│                    │ league_id ───────┼──> League                │
│                    │ team_name        │                          │
│                    │ total_points     │                          │
│                    └──────────────────┘                          │
│                           │                                       │
│                           │ (fantasy_team_id)                    │
│                           ▼                                       │
│                ┌──────────────────────────┐                      │
│                │ fantasy_team_players (J) │                      │
│                ├──────────────────────────┤                      │
│                │ id (PK)                  │                      │
│                │ fantasy_team_id ─────────┼──> FantasyTeam      │
│                │ player_id ───────────────┼──> Player            │
│                │ total_points             │                      │
│                │ is_captain               │                      │
│                │ is_vice_captain          │                      │
│                │ is_wicket_keeper         │                      │
│                └──────────────────────────┘                      │
│                           │                                       │
└───────────────────────────┼───────────────────────────────────────┘
                            │ (player_id)
                            ▼
                    ┌──────────────┐
                    │   players    │
                    ├──────────────┤
                    │ id (PK)      │
                    │ name         │
                    │ club_id ─────┼──> Club
                    │ rl_team      │ (STRING, not FK)
                    │ role         │
                    │ current_price│
                    │ multiplier   │
                    └──────────────┘
```

## Matches & Performance Data

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATCH DATA & PERFORMANCE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐  ┌──────────────┐   │
│  │   seasons    │         │    clubs     │  │   players    │   │
│  ├──────────────┤         ├──────────────┤  ├──────────────┤   │
│  │ id (PK)      │         │ id (PK)      │  │ id (PK)      │   │
│  │ year         │         │ name         │  │ name         │   │
│  │ is_active    │         │ tier         │  │ role         │   │
│  └──────────────┘         └──────────────┘  └──────────────┘   │
│         △                          △                  △           │
│         │                          │                  │           │
│         └──────────┬───────────────┘                  │           │
│                    │ (season_id, club_id)            │           │
│                    ▼                                  │           │
│           ┌──────────────────┐                       │           │
│           │     matches      │                       │           │
│           ├──────────────────┤                       │           │
│           │ id (PK)          │                       │           │
│           │ season_id ───────┼──> Season             │           │
│           │ club_id ─────────┼──> Club               │           │
│           │ match_date       │                       │           │
│           │ opponent         │                       │           │
│           │ result           │                       │           │
│           │ is_processed     │                       │           │
│           └──────────────────┘                       │           │
│                    │                                  │           │
│                    │ (match_id)                       │           │
│                    ▼                                  │           │
│         ┌──────────────────────────────┐             │           │
│         │   player_performances        │             │           │
│         ├──────────────────────────────┤             │           │
│         │ id (PK)                      │             │           │
│         │ match_id ────────────────────┼──> Match   │           │
│         │ player_id ───────────────────┼──> Player ─┘           │
│         │ runs                         │                         │
│         │ balls_faced                  │                         │
│         │ wickets                      │                         │
│         │ overs_bowled                 │                         │
│         │ runs_conceded                │                         │
│         │ catches                      │                         │
│         │ fantasy_points               │                         │
│         │ points_breakdown (JSON)      │                         │
│         └──────────────────────────────┘                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## The Critical Problem: Joining League to Performance Data

```
WHAT WE WANT:
For a given league_id, find all player performances

CURRENT (BROKEN) APPROACH:
┌─────────────┐
│   league    │
│  (id=X)     │
└─────────────┘
       │
       │ Try: WHERE m.league_id = :league_id
       │
       ▼
┌─────────────────┐
│    matches      │
│ (NO league_id!) │  ❌ FAILS HERE
└─────────────────┘


CORRECT APPROACH:
┌─────────────────────────────────────────────┐
│            leagues (id=X)                    │
│   - season_id = "season-123"                 │
│   - club_id = "club-456"                     │
└─────────────────────────────────────────────┘
       │
       │ Extract season_id, club_id
       │
       ▼
┌─────────────────────────────────────────────┐
│            matches                           │
│   WHERE season_id = "season-123"             │
│     AND club_id = "club-456"                 │
│                                              │
│   Result: All matches for this league        │
└─────────────────────────────────────────────┘
       │
       │ match_id from results
       │
       ▼
┌─────────────────────────────────────────────┐
│       player_performances                    │
│   WHERE match_id IN (...)                    │
│                                              │
│   Result: All performances for this league   │
└─────────────────────────────────────────────┘
```

## The Fix in SQL

```sql
-- BROKEN QUERY (Current)
SELECT pp.player_id, SUM(pp.runs), SUM(pp.wickets), ...
FROM player_performances pp
JOIN matches m ON pp.match_id = m.id
WHERE m.league_id = :league_id  ❌ Column doesn't exist
GROUP BY pp.player_id;

-- FIXED QUERY (Recommended)
-- Step 1: Get league's season and club
SELECT l.season_id, l.club_id 
FROM leagues l 
WHERE l.id = :league_id;

-- Step 2: Use those to find performances
SELECT pp.player_id, SUM(pp.runs), SUM(pp.wickets), ...
FROM player_performances pp
JOIN matches m ON pp.match_id = m.id
WHERE m.season_id = :season_id ✅
  AND m.club_id = :club_id        ✅
GROUP BY pp.player_id;
```

## Alternative: Single Query Join

```sql
-- Alternative (if you prefer one query)
SELECT pp.player_id, SUM(pp.runs), SUM(pp.wickets), ...
FROM player_performances pp
JOIN matches m ON pp.match_id = m.id
JOIN leagues l ON m.season_id = l.season_id 
                AND m.club_id = l.club_id
WHERE l.id = :league_id
GROUP BY pp.player_id;
```

## Data Isolation Guarantee

This join strategy ensures data isolation:

```
League A (Season 2025, Club ACC)
    → Matches in Season 2025 + Club ACC
        → Performance data only from those matches

League B (Season 2025, Club ACC) 
    → Same matches (same season + club)
        → Would return same performance data
        
League C (Season 2025, Club ZAMI)
    → Only matches in Season 2025 + Club ZAMI
        → Different performance data
```

## Key Takeaway

**The database schema is correct by design:**
- Leagues don't need league_id in Matches
- They can find their matches through the Season + Club relationship
- This prevents data redundancy and maintains integrity

**The code just needed to follow the relationship path correctly.**
