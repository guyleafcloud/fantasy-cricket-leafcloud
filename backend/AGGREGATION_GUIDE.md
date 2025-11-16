# Player Aggregation System - Complete Guide

## Overview

The system now includes **season-long aggregation** that automatically:
- ✅ **Discovers players incrementally** as they appear in matches
- ✅ **Accumulates season totals** (runs, wickets, fantasy points)
- ✅ **Calculates averages** (batting avg, strike rate, economy)
- ✅ **Maintains club rosters** (all discovered players per club)
- ✅ **Tracks match history** (every performance)
- ✅ **Prevents duplicates** (idempotent - same match won't be counted twice)

---

## How It Works

### Week-by-Week Example

```
WEEK 1: Monday scrape after weekend matches
├─ Scrapes 3 matches for VRA
├─ Discovers 22 players (11 per team × 2 teams)
├─ Creates player profiles in aggregator
└─ Saves: 22 players, cumulative totals

WEEK 2: Monday scrape
├─ Scrapes 2 new matches
├─ Finds 15 existing players (updates their totals)
├─ Discovers 7 NEW players (bench, rotation)
├─ Aggregates: Match 1 + Match 2 totals
└─ Saves: 29 players total

WEEK 3-4:
├─ Most active players already discovered
├─ Occasional new player (debut, substitute)
├─ Season totals continue accumulating
└─ By end of month: 95% of roster discovered
```

### Player Discovery Pattern

```python
Player: Sean Walsh
├─ Week 1, Match 1: 45 runs, 2 wickets → 95 pts
│   Season Total: 95 pts
│
├─ Week 2, Match 2: 67 runs, 3 wickets → 126 pts
│   Season Total: 95 + 126 = 221 pts
│
├─ Week 3, Match 3: 23 runs, 1 wicket → 47 pts
│   Season Total: 221 + 47 = 268 pts
│
└─ Week 4: Did not play
    Season Total: Still 268 pts (unchanged)
```

---

## File Structure

```
backend/
├── player_aggregator.py        # Core aggregation logic
├── kncb_html_scraper.py         # Match scraper
├── celery_tasks.py              # Automated tasks with aggregation
├── api_endpoints.py             # REST API for accessing stats
├── season_aggregates.json       # Persistent storage (auto-saved)
└── season_aggregates_backup_*.json  # Daily backups
```

---

## Player Data Structure

Each player record contains:

```python
{
    'player_id': '11190879',
    'player_name': 'Sean Walsh',
    'club': 'VRA',
    'first_seen': '2025-04-15T10:30:00',
    'last_updated': '2025-05-20T11:45:00',
    'matches_played': 12,

    'match_history': [
        {
            'match_id': 'match_001',
            'match_date': '2025-04-15',
            'opponent': 'ACC',
            'tier': 'tier1',
            'batting': {'runs': 45, 'balls_faced': 38, 'fours': 6, 'sixes': 1},
            'bowling': {'wickets': 2, 'runs_conceded': 28, 'overs': 8.0},
            'fielding': {'catches': 1},
            'fantasy_points': 95
        },
        # ... more matches
    ],

    'season_totals': {
        'fantasy_points': 1247,
        'batting': {
            'innings': 12,
            'runs': 523,
            'balls_faced': 456,
            'fours': 68,
            'sixes': 12,
            'fifties': 3,
            'centuries': 1,
            'highest_score': 103
        },
        'bowling': {
            'innings': 10,
            'wickets': 18,
            'runs_conceded': 234,
            'overs': 78.2,
            'maidens': 8,
            'five_wicket_hauls': 1,
            'best_figures': {'wickets': 5, 'runs': 23}
        },
        'fielding': {
            'catches': 7,
            'stumpings': 0,
            'runouts': 2
        }
    },

    'averages': {
        'batting_average': 47.5,
        'strike_rate': 114.7,
        'bowling_average': 13.0,
        'economy_rate': 3.0,
        'fantasy_points_per_match': 103.9
    }
}
```

---

## Celery Tasks (Automated)

### 1. Weekly Scrape + Aggregation
**Schedule:** Every Monday at 1:00 AM
**What it does:**
```python
1. Scrapes recent matches for configured clubs
2. Extracts player performances
3. Updates season aggregates:
   - New players: Creates profile
   - Existing players: Adds to cumulative totals
4. Recalculates averages
5. Saves to season_aggregates.json
6. Reports: X new players, Y updated players
```

### 2. Daily Backup
**Schedule:** Every day at 3:00 AM
**What it does:**
```python
1. Saves season_aggregates.json
2. Creates dated backup: season_aggregates_backup_20250520.json
3. Ensures data never lost
```

---

## API Endpoints

### Player Stats

**Get specific player:**
```bash
GET /api/v1/players/11190879

Response:
{
  "player_name": "Sean Walsh",
  "club": "VRA",
  "matches_played": 12,
  "season_totals": {...},
  "averages": {...},
  "match_history": [...]
}
```

**Search players by club:**
```bash
GET /api/v1/players?club=VRA&limit=20

Response: [
  {player1_data},
  {player2_data},
  ...
]
```

### Leaderboards

**Top Fantasy Scorers:**
```bash
GET /api/v1/leaderboards/fantasy-points?limit=10

Response: [
  {
    "player_name": "Sean Walsh",
    "club": "VRA",
    "fantasy_points": 1247,
    "matches_played": 12,
    "avg_per_match": 103.9
  },
  ...
]
```

**Top Run Scorers:**
```bash
GET /api/v1/leaderboards/runs?limit=10
```

**Top Wicket Takers:**
```bash
GET /api/v1/leaderboards/wickets?limit=10
```

### Club Rosters

**Get all players for a club:**
```bash
GET /api/v1/clubs/VRA/roster

Response: [
  {
    "player_name": "Sean Walsh",
    "matches_played": 12,
    "fantasy_points": 1247,
    "runs": 523,
    "wickets": 18
  },
  ...
]
```

### Season Summary

**Get overall statistics:**
```bash
GET /api/v1/season/summary

Response: {
  "total_players": 156,
  "clubs": 5,
  "club_rosters": {
    "VRA": 34,
    "ACC": 28,
    "VOC": 31,
    ...
  },
  "top_scorers": [...]
}
```

### Admin

**Manually trigger scrape:**
```bash
POST /api/v1/admin/scrape-now

Response: {
  "status": "triggered",
  "task_id": "abc-123-def",
  "message": "Scraping task started"
}
```

---

## Usage in Your Code

### Access from Python

```python
from celery_tasks import (
    get_player_stats,
    get_club_roster,
    get_top_fantasy_scorers,
    get_season_summary
)

# Get specific player
sean = get_player_stats('11190879')
print(f"{sean['player_name']}: {sean['season_totals']['fantasy_points']} pts")

# Get club roster
vra_players = get_club_roster('VRA')
print(f"VRA has {len(vra_players)} discovered players")

# Get leaderboard
top_10 = get_top_fantasy_scorers(10)
for player in top_10:
    print(f"{player['player_name']}: {player['season_totals']['fantasy_points']}")
```

### Add to FastAPI

In your `main.py`:

```python
from api_endpoints import router as stats_router

app = FastAPI()

# Include stats endpoints
app.include_router(stats_router)
```

---

## Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Clubs

Edit `celery_tasks.py`:

```python
CONFIGURED_CLUBS = [
    "Your Club 1",
    "Your Club 2",
    "Your Club 3"
]
```

### 3. Start Celery

```bash
# Terminal 1: Worker
celery -A celery_tasks worker --loglevel=info

# Terminal 2: Beat scheduler
celery -A celery_tasks beat --loglevel=info
```

Or add to Docker Compose:

```yaml
celery_worker:
  build: .
  command: celery -A celery_tasks worker --loglevel=info
  volumes:
    - ./backend:/app
  depends_on:
    - fantasy_cricket_redis

celery_beat:
  build: .
  command: celery -A celery_tasks beat --loglevel=info
  volumes:
    - ./backend:/app
  depends_on:
    - fantasy_cricket_redis
```

---

## Data Persistence

### File-Based (Current)

**Automatic:**
- `season_aggregates.json` - Updated after each scrape
- `season_aggregates_backup_YYYYMMDD.json` - Daily backups

**Manual:**
```python
from player_aggregator import PlayerSeasonAggregator

aggregator = PlayerSeasonAggregator()
aggregator.load_from_file('season_aggregates.json')
aggregator.save_to_file('my_backup.json')
```

### Database Integration (TODO)

In `celery_tasks.py`, uncomment:

```python
# After aggregation
db_data = aggregator.export_to_database_format()
sync_to_database(db_data)  # Your DB sync function
```

---

## Key Features

### ✅ Idempotent
Running the same scrape twice won't duplicate data:
```python
# Tracks processed_matches per player
if match_id in player['processed_matches']:
    skip  # Already counted
```

### ✅ Incremental Discovery
Don't need full rosters upfront:
```python
Week 1: Discover 22 players from matches
Week 2: +7 new players
Week 3: +3 new players
Result: Natural roster building
```

### ✅ Cumulative Totals
All stats accumulate automatically:
```python
Match 1: 45 runs → Total: 45
Match 2: 67 runs → Total: 112
Match 3: 23 runs → Total: 135
```

### ✅ Auto-Calculated Averages
Recalculated after each match:
- Batting average
- Strike rate
- Bowling average
- Economy rate
- Fantasy points per match

---

## Testing

Test the aggregator:

```bash
python3 player_aggregator.py
```

Test Celery tasks:

```bash
python3 celery_tasks.py
```

Manual scrape trigger:

```python
from celery_tasks import trigger_scrape_now
task_id = trigger_scrape_now()
```

---

## Monitoring

Check current season state:

```bash
python3 celery_tasks.py
```

Output:
```
📊 Current Season Stats:
   Total players: 156
   Clubs: 5

🏆 Top 5 Fantasy Scorers:
   Sean Walsh: 1247 pts
   John Doe: 1103 pts
   ...
```

View saved data:

```bash
cat season_aggregates.json | jq '.summary'
```

---

## Season Flow

```
April (Season Start)
├─ Week 1: Scrape → 80 players discovered
├─ Week 2: Scrape → +20 players (100 total)
├─ Week 3: Scrape → +15 players (115 total)
└─ Week 4: Scrape → +10 players (125 total)

May
├─ Most players discovered (95%+ coverage)
├─ Occasional new player (debut, substitute)
└─ Season totals growing weekly

June-July
├─ All active players in system
├─ Pure accumulation of stats
└─ Leaderboards solidifying

August-September (Season End)
├─ Final matches scraped
├─ Complete season statistics
└─ Ready for next season reset
```

---

## Answer to Your Question

> "Will this load all players in a club and update their individual points totals weekly?"

**YES!** Here's exactly what happens:

1. **Loading Players:** Discovered incrementally from matches
   - Week 1: Finds ~60-80% of active players
   - Week 2-4: Finds remaining 20-40%
   - After 1 month: Essentially complete club roster

2. **Weekly Updates:** Every Monday at 1 AM
   - Scrapes last 7 days of matches
   - Updates existing players (adds to season totals)
   - Discovers any new players (debuts, substitutes)

3. **Individual Totals:** Automatically accumulated
   - Every match performance adds to season total
   - Averages recalculated automatically
   - Accessible via API or Python functions

4. **Zero Laptop Dependency:** Fully autonomous
   - Runs on server 24/7
   - No manual intervention needed
   - Automatic backups daily

**Result:** Complete, auto-updating player statistics system! 🎯
