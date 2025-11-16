# Legacy Roster System - Complete Guide

## Overview

The legacy roster system allows you to **seed the aggregator with players from previous seasons**. This means:

✅ **Start with known roster** instead of empty database
✅ **Automatic matching** when legacy players play in new season
✅ **Immediate recognition** of returning players by name
✅ **Still discovers new players** as they debut
✅ **Preserves roster** even for players who haven't played yet

---

## How It Works

### Before Season (November - March)

```
1. Create legacy roster JSON files for each club
   └─ rosters/acc_2024_roster.json
   └─ rosters/vra_2024_roster.json
   └─ etc.

2. On startup, Celery loads all legacy rosters
   └─ Creates "shell" profiles for each player
   └─ Zero stats (will accumulate as they play)
   └─ Marked as legacy import

3. System ready with full rosters before season starts!
```

### During Season (April - September)

```
Week 1: First match scraped
├─ Boris Gorlee appears in match
├─ System matches "Boris Gorlee" to legacy import
├─ Marks as active player (no longer legacy)
├─ Adds match performance to his stats
└─ Season total: 108 pts ✅

Week 2: Another match scraped
├─ "S. Zulfiqar" appears (abbreviated name)
├─ Fuzzy matching: "S. Zulfiqar" → "Sikander Zulfiqar"
├─ Matches to legacy player!
├─ Adds match performance
└─ Season total: 40 pts ✅

Week 3: New player debuts
├─ Tom de Grooth appears (NOT in legacy roster)
├─ System creates new player profile
├─ Adds to ACC roster
└─ Tracks like any other player ✅
```

### Result

```
ACC Roster after 3 weeks:
├─ Boris Gorlee - 3 matches, 324 pts (was legacy, now active)
├─ Sikander Zulfiqar - 3 matches, 187 pts (was legacy, now active)
├─ Tom de Grooth - 3 matches, 156 pts (new player)
├─ Shariz Ahmad - 0 matches, 0 pts (legacy, hasn't played yet)
└─ 21 other legacy players waiting to play...
```

---

## Creating Legacy Rosters

### Format

Create JSON files in `backend/rosters/` directory:

```json
{
  "club": "ACC",
  "club_full_name": "Amsterdamsche Cricket Club",
  "season": "2025",
  "notes": "Legacy roster from 2025 season for 2026",
  "roster_compiled_date": "2025-11-05",
  "players": [
    {
      "name": "Boris Gorlee",
      "club": "ACC",
      "role": "all-rounder",
      "last_season_stats": {
        "note": "Optional stats from 2024"
      }
    },
    {
      "name": "Sikander Zulfiqar",
      "club": "ACC",
      "role": "batsman"
    }
  ]
}
```

### Required Fields

- `name`: Player full name (used for matching)
- `club`: Club abbreviation (must match configured clubs)

### Optional Fields

- `id`: Player ID if known (helps with matching)
- `role`: Position ("batsman", "bowler", "all-rounder", "wicket-keeper")
- `last_season_stats`: Reference stats from previous season (not used, just for info)

### File Naming Convention

Format: `{club}_{year}_roster.json`

Examples:
- `acc_2025_roster.json` (2025 season data for 2026 use)
- `vra_2025_roster.json`
- `voc_2025_roster.json`

System auto-discovers all files matching `rosters/*_roster.json`

---

## Name Matching Logic

The system intelligently matches scraped players to legacy roster:

### 1. Exact Match

```
Legacy: "Boris Gorlee"
Scraped: "Boris Gorlee"
→ ✅ MATCH (exact)
```

### 2. Abbreviated First Name

```
Legacy: "Sikander Zulfiqar"
Scraped: "S. Zulfiqar"
→ ✅ MATCH (fuzzy - "S." is abbreviation of "Sikander")
```

### 3. Partial Name

```
Legacy: "Jonathan Smith"
Scraped: "J. Smith"
→ ✅ MATCH (fuzzy - "J." abbreviates "Jonathan", "Smith" matches)
```

### 4. Name Variations

```
Legacy: "Robert Johnson"
Scraped: "Rob Johnson"
→ ✅ MATCH (fuzzy - "Rob" is start of "Robert", "Johnson" matches)
```

### 5. No Match → New Player

```
Legacy: (no match found)
Scraped: "Tom de Grooth"
→ Creates NEW player profile
```

---

## Example: ACC Legacy Roster

We've created a real ACC roster at `backend/rosters/acc_2025_roster.json` with 25 players from the 2025 season:

- Boris Gorlee
- Sikander Zulfiqar
- Shariz Ahmad
- Musa Ahmad
- Saqib Zulfiqar
- Asad Zulfiqar
- Kashif Naseem
- Roel Verhagen
- Victor Lubbers
- Olivier Elenbaas
- Sebastiaan Braat
- Arnav Jain
- Jitse Wilders
- Niels Etman
- Tom de Grooth
- Quirijn Gunning
- Daniel Watson
- Sjoerd Stolk
- Robin van Manen
- Mitchell Koot
- Julian de Mey
- Tobias Visee
- Maarten Boers
- Rohan Chopra
- Tim Gruijters

---

## Creating Rosters for Your Clubs

### Option 1: Manual Creation

Create JSON file following the format above:

```bash
# Create roster file
cat > rosters/vra_2025_roster.json <<'EOF'
{
  "club": "VRA",
  "season": "2025",
  "players": [
    {"name": "Player 1", "club": "VRA", "role": "batsman"},
    {"name": "Player 2", "club": "VRA", "role": "bowler"}
  ]
}
EOF
```

### Option 2: Use Template Generator

```python
from legacy_roster_loader import LegacyRosterLoader

loader = LegacyRosterLoader()
loader.create_legacy_roster_template("VRA", "rosters/vra_2025_roster.json")

# Edit the generated file with actual player names
```

### Option 3: Export from Previous Season Data

If you have data from last season's scraping:

```python
from player_aggregator import PlayerSeasonAggregator
import json

# Load last season's data
aggregator = PlayerSeasonAggregator()
aggregator.load_from_file('season_2025_final.json')

# Get players for a club
vra_players = aggregator.get_players_by_club('VRA')

# Create legacy roster
legacy_roster = {
    "club": "VRA",
    "season": "2025",
    "players": [
        {
            "name": p['player_name'],
            "club": p['club'],
            "id": p['player_id'],
            "last_season_stats": {
                "matches": p['matches_played'],
                "fantasy_points": p['season_totals']['fantasy_points']
            }
        }
        for p in vra_players
    ]
}

# Save
with open('rosters/vra_2025_roster.json', 'w') as f:
    json.dump(legacy_roster, f, indent=2)
```

---

## Loading Process

### Automatic (on Celery startup)

```python
# In celery_tasks.py (already configured)

# System automatically:
1. Looks for files matching rosters/*_roster.json
2. Loads each roster file
3. Imports players into aggregator
4. Reports: "Imported 25 players from ACC roster"
```

### Manual (for testing)

```python
from player_aggregator import PlayerSeasonAggregator
from legacy_roster_loader import LegacyRosterLoader

aggregator = PlayerSeasonAggregator()
loader = LegacyRosterLoader()

# Load specific roster
legacy_players = loader.load_from_json('rosters/acc_2025_roster.json')
count = loader.import_to_aggregator(aggregator, legacy_players)

print(f"Imported {count} players")
```

---

## Testing

### Test Legacy Loading

```bash
python3 legacy_roster_loader.py
```

Output:
```
✅ Loaded 3 legacy players from acc_legacy_roster.json
📥 Imported legacy player: Boris Gorlee (ACC)
📥 Imported legacy player: Sikander Zulfiqar (ACC)
...
```

### Test Integration with Scraping

```bash
python3 test_legacy_integration.py
```

Output shows:
- Legacy players loaded
- Scraped data matched to legacy
- New players added
- Verification results

---

## API Access

### Get Legacy Players

```bash
# All ACC players (including legacy)
GET /api/v1/clubs/ACC/roster

Response:
[
  {
    "player_name": "Boris Gorlee",
    "matches_played": 0,  # Legacy, not played yet
    "fantasy_points": 0
  },
  ...
]
```

### Check if Player is Legacy

```bash
GET /api/v1/players/{player_id}

Response:
{
  "player_name": "Shariz Ahmad",
  "is_legacy_import": true,  # ← Still legacy
  "matches_played": 0,
  ...
}
```

### After Player Plays

```bash
GET /api/v1/players/{player_id}

Response:
{
  "player_name": "Boris Gorlee",
  "is_legacy_import": false,  # ← No longer legacy!
  "first_match_date": "2025-04-15",
  "matches_played": 3,
  "season_totals": {
    "fantasy_points": 324
  }
}
```

---

## Best Practices

### 1. Create Rosters Before Season

Create legacy rosters in November/December before new season starts.

### 2. Use Full Names

Use complete player names in legacy roster for best matching:
```json
{"name": "Sikander Zulfiqar"}  // ✅ Good
{"name": "S. Zulfiqar"}         // ⚠️  Will work but less reliable
```

### 3. Verify Matching

After first scrape, check that players matched correctly:

```python
from celery_tasks import aggregator

acc = aggregator.get_players_by_club('ACC')
for p in acc:
    if p['matches_played'] > 0:
        print(f"{p['player_name']}: {p['matches_played']} matches")
```

### 4. Update Annually

At end of season, export current roster as next year's legacy:

```bash
# Export 2025 season for 2026 use
python3 export_season_to_legacy.py --season 2025 --club ACC
```

---

## Benefits

### vs. Empty Start

**Without Legacy:**
```
Week 1: Discover 22 players from 2 matches
Week 2: +7 players (29 total)
Week 3: +4 players (33 total)
Week 4: +3 players (36 total)
→ Takes 4 weeks to build roster
```

**With Legacy:**
```
Week 0: Load 25 players from legacy roster
Week 1: Match 15 returning players, +3 new (28 total)
Week 2: Match 5 more returning, +2 new (30 total)
Week 3: All active players already in system!
→ Complete roster from day 1
```

### vs. Manual Entry

**Manual Entry:**
- ❌ Time consuming
- ❌ Error prone
- ❌ Hard to update

**Legacy Roster:**
- ✅ One-time JSON file creation
- ✅ Automatic matching
- ✅ Easy to maintain

---

## Troubleshooting

### Player Not Matching

If scraped player doesn't match legacy:

1. **Check name spelling:**
   ```
   Legacy: "Sikander Zulfiqar"
   Scraped: "Sikandar Zulfiqar"  // ❌ Typo
   ```

2. **Check club name:**
   ```json
   {"name": "Boris Gorlee", "club": "ACC"}  // ✅
   {"name": "Boris Gorlee", "club": "acc"}  // ❌ Case mismatch
   ```

3. **Add player ID:**
   ```json
   {
     "name": "Player Name",
     "id": "known_player_id",  // Helps with matching
     "club": "ACC"
   }
   ```

### Duplicate Players

If you see duplicate players:

```python
# Check for duplicates
from celery_tasks import aggregator

acc = aggregator.get_players_by_club('ACC')
names = [p['player_name'] for p in acc]
duplicates = [n for n in names if names.count(n) > 1]

if duplicates:
    print(f"Duplicates found: {duplicates}")
```

Fix by improving name matching or removing duplicate from legacy roster.

---

## Summary

The legacy roster system gives you a **complete starting roster** that:
- ✅ Seeds aggregator with known players before season
- ✅ Automatically matches returning players by name
- ✅ Handles name variations (abbreviations, nicknames)
- ✅ Still discovers new players dynamically
- ✅ Preserves roster even for inactive players

**Setup:** Create one JSON file per club
**Maintenance:** Update annually after season ends
**Result:** Complete, auto-updating player database from day 1!
