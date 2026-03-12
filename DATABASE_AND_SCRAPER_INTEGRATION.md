# Database Architecture & Scraper Integration Plan

**Date:** 2025-11-20
**Status:** 📋 ANALYSIS COMPLETE - Ready for integration design

---

## Executive Summary

The fantasy cricket platform has a **complete database schema** with 514 players across 10 ACC teams. The system currently uses **simulated data** but is structurally ready for **real scorecard integration**. The scraper is working and can extract player performances from 2025 scorecards. This document maps out how to integrate them.

---

## Part 1: Database Architecture

### Current State (Production)

```
📊 DATABASE TABLES:
- users:                    2 rows
- seasons:                  1 row
- clubs:                    1 row (ACC)
- teams:                    10 rows (ACC 1-6, ZAMI, U13-U17)
- players:                  514 rows
- leagues:                  2 rows
- fantasy_teams:            2 rows
- fantasy_team_players:     22 rows
- player_performances:      626 rows (simulated Round 1-2)
- player_price_history:     513 rows
- transfers:                0 rows
```

### Data Model Overview

```
Season (2026)
    ↓
Club (ACC)
    ↓
Teams (10 real-life teams)
    ├── ACC 1 (54 players)
    ├── ACC 2 (38 players)
    ├── ACC 3 (62 players)
    ├── ACC 4 (50 players)
    ├── ACC 5 (40 players)
    ├── ACC 6 (71 players)
    ├── ZAMI 1 (78 players)
    ├── U13 (48 players)
    ├── U15 (34 players)
    └── U17 (38 players)

Players (514 total)
    ├── id (UUID)
    ├── name (e.g., "DevanshuArya")
    ├── team_id (links to Teams)
    ├── player_type (batsman/bowler/all-rounder)
    ├── fantasy_value (25.0-100.0)
    ├── multiplier (0.69-5.0, lower = historically better)
    └── is_wicket_keeper (boolean)

Fantasy Teams (Users' teams)
    ├── 11 players selected
    ├── Captain (2x), Vice-Captain (1.5x)
    ├── total_points (cumulative across rounds)
    └── Players via fantasy_team_players table

Player Performances (Weekly match data)
    ├── player_id
    ├── league_id, round_number
    ├── Batting: runs, balls_faced, is_out
    ├── Bowling: wickets, overs, maidens, runs_conceded
    ├── Fielding: catches, stumpings, run_outs
    ├── base_fantasy_points (before multipliers)
    ├── multiplier_applied (player handicap 0.69-5.0)
    ├── captain_multiplier (1.0/1.5/2.0)
    ├── final_fantasy_points (final score)
    └── is_captain, is_vice_captain, is_wicket_keeper
```

---

## Part 2: Current Data Flow (Simulation)

### How Simulations Work (`simulate_live_teams.py`)

```
1. GET Active Fantasy Teams
   └─> Query fantasy_teams WHERE is_finalized = true

2. GET Players for Each Team
   └─> Query fantasy_team_players with captain/VC/WK roles

3. GENERATE Random Performances
   └─> simulate_weekly_matches() creates mock data for all 514 players

4. CALCULATE Fantasy Points
   ├─> Base points using rules-set-1.py (tiered system)
   ├─> Apply player multiplier (0.69-5.0)
   ├─> Apply captain/VC multiplier (2x/1.5x)
   └─> = Final fantasy points

5. STORE Player Performances
   └─> INSERT INTO player_performances (all 514 players)
       - league_id, round_number
       - All stats + base/multiplier/final points
       - ON CONFLICT (player_id, league_id, round_number) UPDATE

6. UPDATE Fantasy Team Scores
   └─> UPDATE fantasy_teams SET total_points += round_points

7. UPDATE Fantasy Team Player Totals
   └─> UPDATE fantasy_team_players SET total_points += round_points
```

### Key Insight: Separation of Concerns

The system has **two layers**:

1. **Player Performance Layer** (Global)
   - ALL 514 players get performances stored
   - Independent of fantasy teams
   - `player_performances` table with `league_id` + `round_number`
   - One entry per player per round per league

2. **Fantasy Team Layer** (User-specific)
   - Only selected 11 players count
   - Captain/VC bonuses applied here
   - `fantasy_team_players` tracks cumulative points
   - Leaderboard uses `fantasy_teams.total_points`

---

## Part 3: Player Matching System

### How Players are Identified

**Database Structure:**
```sql
players
├── id: UUID (e.g., "c8e6616...")
├── name: varchar (e.g., "DevanshuArya", "SamEikelenboom")
├── team_id: UUID → links to teams table
└── teams.name: varchar (e.g., "ACC 1", "ACC ZAMI", "U17")
```

**Current Names in Database:**
- Concatenated without spaces: `DevanshuArya`, `SamEikelenboom`
- Exact match required for lookup

**Scraper Output Names:**
```
From 2025 scorecards:
- "M BOENDERMAKER"
- "DV DOORNINCK"
- "I ALIM"
- "H ALI"
- "G GABA"
```

### Player Matching Challenge

**Problem:** Scraper names don't match database names exactly

**Examples:**
```
Scraper         Database         Match?
"M BOENDERMAKER" → "MickBoendermaker"  ❓ (partial match)
"I ALIM"         → "IshaqAlim"          ❓ (initial + surname)
"DV DOORNINCK"   → "DaanDoorninck"      ❓ (initials)
"G GABA"         → "GabeGaba"           ❓ (short name)
```

**Matching Strategies:**

1. **Exact Match** (easiest, rarely works)
   ```python
   player = session.query(Player).filter(Player.name == "MBOENDERMAKER").first()
   ```

2. **Surname Match** (most reliable)
   ```python
   surname = "BOENDERMAKER"
   player = session.query(Player).filter(Player.name.ilike(f'%{surname}%')).first()
   ```

3. **Fuzzy Match** (best for variations)
   ```python
   from fuzzywuzzy import fuzz
   best_match = max(all_players, key=lambda p: fuzz.ratio(scraped_name, p.name))
   ```

4. **Manual Mapping** (for problem cases)
   ```python
   NAME_MAPPINGS = {
       'M BOENDERMAKER': 'MickBoendermaker',
       'DV DOORNINCK': 'DaanDoorninck',
       # ...
   }
   ```

---

## Part 4: Scraper Output Format

### What the Scraper Returns

```python
# From scraper.scrape_match_scorecard(7324739)
scorecard = {
    'innings': [{
        'batting': [
            {
                'player_name': 'I ALIM',
                'dismissal': 'c & b S Diwan',
                'runs': 6,
                'balls_faced': 15,
                'fours': 1,
                'sixes': 0,
                'strike_rate': 40.0,
                'is_out': True
            },
            # ... 17 more batters
        ],
        'bowling': [
            {
                'player_name': 'MI KHAN',
                'overs': 5.0,
                'maidens': 2,
                'runs': 12,
                'wickets': 0,
                'no_balls': 0,
                'wides': 0
            },
            # ... 6 more bowlers
        ]
    }]
}

# After extract_player_stats(scorecard, 'ACC', 'tier2')
players = [
    {
        'player_name': 'I ALIM',
        'player_id': None,  # Need to match to database
        'club': 'ACC',
        'tier': 'tier2',
        'batting': {
            'runs': 6,
            'balls_faced': 15,
            'fours': 1,
            'sixes': 0
        },
        'bowling': {},
        'fielding': {},
        'fantasy_points': 2  # Base points calculated
    },
    # ... 18 more players
]
```

### Data Mapping: Scraper → Database

| Scraper Field | Database Field | Notes |
|---|---|---|
| `player_name` | `players.name` | Needs matching logic |
| `club` | `teams.name` | Need to map "ACC" → "ACC 1", etc. |
| `runs` | `player_performances.runs` | Direct |
| `balls_faced` | `player_performances.balls_faced` | Direct |
| `is_out` | `player_performances.is_out` | Direct |
| `wickets` | `player_performances.wickets` | Direct |
| `overs` | `player_performances.overs_bowled` | Direct |
| `runs` (bowling) | `player_performances.runs_conceded` | Direct |
| `maidens` | `player_performances.maidens` | Direct |
| `catches` | `player_performances.catches` | Direct |
| `stumpings` | `player_performances.stumpings` | Direct |
| `runouts` | `player_performances.run_outs` | Direct |
| `fantasy_points` | `player_performances.base_fantasy_points` | Before multipliers |
| *(calculated)* | `player_performances.multiplier_applied` | From `players.multiplier` |
| *(calculated)* | `player_performances.final_fantasy_points` | base × multiplier |

---

## Part 5: Integration Options

### Option 1: Direct Replacement (Simplest)

**Replace simulation with scraper in existing workflow**

```python
# BEFORE (simulate_live_teams.py):
weekly_performances = await simulate_weekly_matches()  # Mock data

# AFTER:
from kncb_html_scraper import KNCBMatchCentreScraper

scraper = KNCBMatchCentreScraper()
matches = await scraper.get_recent_matches_for_club("ACC", days_back=7)

weekly_performances = {}
for match in matches:
    scorecard = await scraper.scrape_match_scorecard(match['match_id'])
    players = scraper.extract_player_stats(scorecard, "ACC", "tier2")

    for player in players:
        # Match player to database
        db_player = match_player_name(player['player_name'])

        if db_player:
            weekly_performances[db_player.id] = {
                'performance': player,
                'player_name': db_player.name,
                'club_name': player['club'],
                'is_wicket_keeper': db_player.is_wicket_keeper
            }

# Rest of workflow stays the same
store_all_player_performances(weekly_performances, league_id, round_number)
```

**Pros:**
- ✅ Minimal code changes
- ✅ Uses existing storage logic
- ✅ Keeps all database structure

**Cons:**
- ❌ Need player name matching
- ❌ Manual for now (not fully automated)

---

### Option 2: Batch Processing with Match Records

**Store matches first, then performances**

```python
# 1. Create Match record
match_record = Match(
    id=generate_uuid(),
    season_id=season_id,
    club_id=club_id,
    match_date=match_date,
    opponent=opponent,
    matchcentre_id=match_id,
    scorecard_url=f"https://matchcentre.kncb.nl/match/{entity_id}-{match_id}/scorecard/",
    is_processed=False,
    raw_scorecard_data=scorecard_json
)
session.add(match_record)
session.commit()

# 2. Process scorecard
players = scraper.extract_player_stats(scorecard, "ACC", "tier2")

# 3. Store performances linked to match
for player in players:
    db_player = match_player_name(player['player_name'])

    if db_player:
        performance = PlayerPerformance(
            match_id=match_record.id,
            player_id=db_player.id,
            league_id=league_id,
            round_number=round_number,
            runs=player['batting']['runs'],
            wickets=player['bowling']['wickets'],
            # ... all stats
            base_fantasy_points=player['fantasy_points'],
            multiplier_applied=db_player.multiplier,
            final_fantasy_points=player['fantasy_points'] * db_player.multiplier
        )
        session.add(performance)

# 4. Mark match as processed
match_record.is_processed = True
session.commit()
```

**Pros:**
- ✅ Full audit trail (matches + performances)
- ✅ Can reprocess if needed
- ✅ Raw scorecard saved for debugging
- ✅ Matches production schema exactly

**Cons:**
- ❌ More database writes
- ❌ More complex logic

---

### Option 3: Hybrid (Recommended)

**Use Match table for audit, but keep simple workflow**

```python
async def scrape_and_store_weekly_performances(league_id, round_number, clubs=["ACC"]):
    """
    Complete workflow: Scrape → Match → Store → Update
    """
    scraper = KNCBMatchCentreScraper()
    session = Session()

    try:
        all_performances = {}

        # 1. Scrape matches for each club
        for club_name in clubs:
            matches = await scraper.get_recent_matches_for_club(club_name, days_back=7)

            for match_info in matches:
                match_id = match_info['match_id']

                # Check if already processed
                existing = session.query(Match).filter(
                    Match.matchcentre_id == str(match_id),
                    Match.is_processed == True
                ).first()

                if existing:
                    print(f"   ⏭️  Match {match_id} already processed")
                    continue

                # Scrape scorecard
                scorecard = await scraper.scrape_match_scorecard(match_id)

                if not scorecard:
                    print(f"   ❌ Failed to scrape match {match_id}")
                    continue

                # Create Match record
                match_record = Match(
                    id=str(uuid.uuid4()),
                    season_id=get_active_season_id(),
                    club_id=get_club_id_by_name(club_name),
                    match_date=match_info.get('match_date_time'),
                    opponent=match_info.get('away_club_name') or match_info.get('home_club_name'),
                    matchcentre_id=str(match_id),
                    scorecard_url=f"https://matchcentre.kncb.nl/match/134453-{match_id}/scorecard/",
                    raw_scorecard_data=scorecard,
                    is_processed=False
                )
                session.add(match_record)

                # Extract player performances
                players = scraper.extract_player_stats(scorecard, club_name, match_info['tier'])

                # Match players to database
                for player_data in players:
                    db_player = match_player_to_database(
                        player_data['player_name'],
                        club_name,
                        session
                    )

                    if db_player:
                        all_performances[db_player.id] = {
                            'performance': {
                                'runs': player_data['batting'].get('runs', 0),
                                'balls_faced': player_data['batting'].get('balls_faced', 0),
                                'is_out': player_data['batting'].get('is_out', False),
                                'wickets': player_data['bowling'].get('wickets', 0),
                                'overs': player_data['bowling'].get('overs', 0.0),
                                'runs_conceded': player_data['bowling'].get('runs', 0),
                                'maidens': player_data['bowling'].get('maidens', 0),
                                'catches': player_data['fielding'].get('catches', 0),
                                'stumpings': player_data['fielding'].get('stumpings', 0),
                                'runouts': player_data['fielding'].get('runouts', 0),
                            },
                            'player_name': db_player.name,
                            'club_name': club_name,
                            'is_wicket_keeper': db_player.is_wicket_keeper,
                            'match_id': match_record.id
                        }
                    else:
                        print(f"   ⚠️  Player not found: {player_data['player_name']}")

                # Mark match as processed
                match_record.is_processed = True
                print(f"   ✅ Processed match {match_id}: {len(players)} players")

        # 2. Store all performances (reuse existing function)
        store_all_player_performances(all_performances, league_id, round_number)

        # 3. Update fantasy team scores (reuse existing function)
        teams = get_active_teams()
        all_team_scores = calculate_team_scores(teams, all_performances)
        update_team_scores_in_db(all_team_scores)

        session.commit()
        print(f"\n✅ Weekly scraping complete: {len(all_performances)} performances")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()
```

**Pros:**
- ✅ Full audit trail with Match records
- ✅ Reuses existing storage functions
- ✅ Prevents duplicate processing
- ✅ Clean separation of concerns
- ✅ Easy to test incrementally

**Cons:**
- ⚠️  Moderate complexity

---

## Part 6: Player Name Matching Implementation

### Strategy: Multi-Level Matching

```python
def match_player_to_database(scraped_name, club_name, session):
    """
    Match scraped player name to database player

    Tries multiple strategies:
    1. Exact match
    2. Surname match
    3. Fuzzy match
    4. Manual mapping
    """

    # Normalize scraped name
    scraped_normalized = scraped_name.replace(' ', '').lower()

    # Get all players from this club's teams
    club_players = session.query(Player).join(Team).join(Club).filter(
        Club.name == club_name  # "ACC" matches club
    ).all()

    # 1. Exact match (rare but try it)
    for player in club_players:
        if player.name.lower() == scraped_normalized:
            return player

    # 2. Surname match (most common)
    # Extract surname (last word in scraped name)
    surname = scraped_name.split()[-1].lower()

    for player in club_players:
        if surname in player.name.lower():
            # Found surname match - but check if unique
            matches = [p for p in club_players if surname in p.name.lower()]
            if len(matches) == 1:
                return player
            # Multiple matches - need more info

    # 3. Fuzzy match (for typos/variations)
    from fuzzywuzzy import fuzz

    best_match = None
    best_score = 0

    for player in club_players:
        score = fuzz.ratio(scraped_normalized, player.name.lower())
        if score > best_score:
            best_score = score
            best_match = player

    # Only use fuzzy match if confidence is high
    if best_score > 80:
        return best_match

    # 4. Manual mapping (for known problem cases)
    NAME_MAPPINGS = {
        'm boendermaker': 'MickBoendermaker',
        'dv doorninck': 'DaanDoorninck',
        'i alim': 'IshaqAlim',
        # Add more as discovered
    }

    if scraped_name.lower() in NAME_MAPPINGS:
        mapped_name = NAME_MAPPINGS[scraped_name.lower()]
        return session.query(Player).filter(
            Player.name == mapped_name
        ).first()

    # No match found
    print(f"⚠️  Could not match player: {scraped_name}")
    return None
```

### Creating Name Mapping Table

For production, create a database table:

```sql
CREATE TABLE player_name_mappings (
    id VARCHAR(50) PRIMARY KEY,
    scraped_name VARCHAR(200),
    player_id VARCHAR(50) REFERENCES players(id),
    confidence VARCHAR(20),  -- 'exact', 'fuzzy', 'manual'
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(50)
);
```

---

## Part 7: Weekly Automation Workflow

### Complete Integration Flow

```
MONDAY 9 AM (Cron Job)
    ↓
1. SCRAPE Recent Matches
   └─> scraper.get_recent_matches_for_club("ACC", days_back=7)
       Returns: List of match_ids from last week

    ↓
2. PROCESS Each Match
   ├─> scraper.scrape_match_scorecard(match_id)
   ├─> Create Match record in database
   ├─> extract_player_stats(scorecard)
   └─> Match players to database

    ↓
3. STORE Performances
   └─> INSERT INTO player_performances
       - All scraped stats
       - base_fantasy_points (from scraper)
       - multiplier_applied (from players.multiplier)
       - final_fantasy_points = base × multiplier
       - league_id, round_number

    ↓
4. CALCULATE Fantasy Team Scores
   ├─> For each fantasy_team:
   │   ├─> Get their 11 players
   │   ├─> Look up performances from step 3
   │   ├─> Apply captain (2x) / VC (1.5x) multipliers
   │   └─> Sum to get team_round_points
   │
   └─> UPDATE fantasy_teams
       SET total_points += team_round_points

    ↓
5. UPDATE Leaderboard
   └─> Recalculate ranks based on total_points

    ↓
6. NOTIFY Users (Optional)
   └─> Email/push notifications with round results
```

### Deployment Script

Create `backend/scrape_weekly_real_data.py`:

```python
#!/usr/bin/env python3
"""
Weekly Scraper for Real Match Data
===================================
Replaces simulation with actual KNCB scorecard scraping
"""

import asyncio
import sys
from kncb_html_scraper import KNCBMatchCentreScraper
from simulate_live_teams import (
    get_active_teams,
    calculate_fantasy_points,
    update_team_scores_in_db,
    store_fantasy_team_player_totals
)
from player_matcher import match_player_to_database  # New module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

async def scrape_weekly_real_data(round_number):
    """Main entry point for weekly scraping"""

    print("="*80)
    print("🏏 WEEKLY SCRAPER - REAL KNCB DATA")
    print("="*80)

    # Initialize scraper
    scraper = KNCBMatchCentreScraper()

    # Get active leagues and clubs
    session = Session()
    try:
        # Get active league
        league = session.query(League).join(Season).filter(
            Season.is_active == True
        ).first()

        if not league:
            print("❌ No active league found")
            return

        print(f"\n📋 League: {league.name}")
        print(f"   Round: {round_number}")

        # Scrape and store
        await scrape_and_store_weekly_performances(
            league.id,
            round_number,
            clubs=["ACC"]  # Can add more clubs
        )

    finally:
        session.close()

if __name__ == "__main__":
    round_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(scrape_weekly_real_data(round_number))
```

---

## Part 8: Testing Strategy

### Phase 1: Manual Testing (Week 1)

1. **Test player matching**
   ```bash
   python3 test_player_matching.py
   # Shows scraped names → database matches
   ```

2. **Test single match scraping**
   ```bash
   python3 test_single_match.py 7324739
   # Scrapes one match, matches players, calculates points
   ```

3. **Test full round (dry run)**
   ```bash
   python3 scrape_weekly_real_data.py 1 --dry-run
   # Scrapes but doesn't write to database
   ```

### Phase 2: Production (Week 2)

1. **Run for real**
   ```bash
   python3 scrape_weekly_real_data.py 1
   ```

2. **Verify data**
   ```sql
   SELECT * FROM player_performances WHERE round_number = 1 AND match_id IS NOT NULL;
   SELECT * FROM fantasy_teams ORDER BY total_points DESC;
   ```

3. **Check leaderboard**
   - Visit frontend
   - Confirm points updated
   - Verify weekly points shown

### Phase 3: Automation (Week 3+)

1. **Set up cron job**
   ```bash
   # /etc/cron.d/fantasy-cricket
   0 9 * * 1 cd /app && python3 scrape_weekly_real_data.py $ROUND_NUMBER >> /var/log/scraper.log 2>&1
   ```

2. **Monitor logs**
   ```bash
   tail -f /var/log/scraper.log
   ```

---

## Part 9: Recommendations

### Immediate (Before April 2026)

1. **✅ DONE: Scraper working**
   - Text parser integrated
   - Tested with 3 real 2025 scorecards
   - Deployed to production

2. **TODO: Player name matching**
   - Create `player_matcher.py` module
   - Test with 2025 data
   - Build manual mapping table for problem cases

3. **TODO: Integration function**
   - Create `scrape_weekly_real_data.py`
   - Test with historical 2025 matches
   - Verify database updates correctly

4. **TODO: Admin interface**
   - Button to trigger scraping
   - View matched/unmatched players
   - Manually map problem names

### Before Season Starts (April 2026)

1. **Player roster updates**
   - Scrape 2026 rosters
   - Add new players to database
   - Update team assignments

2. **Test with Week 1 data**
   - Run scraper on first real matches
   - Verify all players matched
   - Check leaderboard updates

3. **Set up monitoring**
   - Email alerts if scraper fails
   - Slack notifications for weekly runs
   - Dashboard showing scraper status

### During Season (April-September 2026)

1. **Weekly monitoring**
   - Check logs every Monday
   - Verify match counts
   - Monitor unmatched players

2. **Manual interventions**
   - Map new player names
   - Handle special cases
   - Fix any scraping issues

3. **Performance tracking**
   - Monitor scraping time
   - Check database growth
   - Optimize slow queries

---

## Summary: Integration Checklist

### ✅ Already Complete
- [x] Scraper works with 2025 scorecards
- [x] Fantasy points calculator (rules-set-1.py)
- [x] Database schema supports real data
- [x] Player performance storage logic
- [x] Fantasy team scoring logic
- [x] Leaderboard display

### 📋 TODO Before Integration
- [ ] Create `player_matcher.py` with matching logic
- [ ] Test matching with 2025 data
- [ ] Create `scrape_weekly_real_data.py` integration script
- [ ] Add Match record creation to workflow
- [ ] Test end-to-end with historical data

### 🚀 TODO for Production (April 2026)
- [ ] Update player roster for 2026
- [ ] Set up weekly cron job
- [ ] Create admin interface for manual mapping
- [ ] Set up monitoring and alerts
- [ ] Documentation for weekly operations

---

**Status:** 📊 READY FOR INTEGRATION DEVELOPMENT

The database architecture is solid, the scraper works, and we have a clear path to integration. The main work is building the player matching logic and creating the integration script.

**Estimated Time:**
- Player matching: 4-8 hours
- Integration script: 4-6 hours
- Testing: 4-6 hours
- **Total: 12-20 hours** of development before season starts
