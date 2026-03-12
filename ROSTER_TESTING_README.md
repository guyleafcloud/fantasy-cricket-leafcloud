# 🧪 Roster Data Testing Guide

## Purpose

Test whether the scraped player data (513 players in database) is accurate by comparing against ground truth CSV roster from ACC.

---

## What We're Testing

### 1. **Roster Accuracy** (CSV vs Scraped Data)
**Question:** How many of the 513 players are actually ACC players vs opposition?

**Test:** Compare database export against ground truth CSV
- Coverage: % of real ACC players found by scraper
- Precision: % of scraped players that are actually ACC players
- False Positives: Opposition players incorrectly included
- False Negatives: Real ACC players scraper missed

**Tool:** `compare_roster_sources.py`

---

### 2. **Player Matching Accuracy** (Critical for Points Assignment)
**Question:** Can the scraper match scorecard names to database players?

**Why This Matters:**
- CSV upload defines WHO is in the roster
- Scraper must MATCH names from scorecards to assign points
- Player might be "ACC 1" in roster but play for "ACC 2" that week
- Scraper needs to find the right player ID regardless of team

**Example:**
```
Database:    "MickBoendermaker" (ACC 1)
Scorecard:   "M BOENDERMAKER" (playing for ACC 2 this week)
Scraper:     Must match these → Same player ID → Points assigned
```

**Test:** Generate name variations and test matching
- Full name: "MickBoendermaker"
- Initial + Surname: "M Boendermaker"
- Surname only: "BOENDERMAKER"
- Scorecard format: "M BOENDERMAKER"

**Tool:** `test_player_matching.py`

---

### 3. **Data Quality** (Opposition Player Detection)
**Question:** What data quality issues exist in current 513 players?

**Checks:**
- Invalid names (dates, scorecard text, dismissal codes)
- Default multipliers (1.0 = never calculated from matches = likely opposition)
- Duplicate players
- Opposition team names in player names
- Suspicious patterns

**Tool:** Quality Check API endpoint `GET /api/admin/players/quality-check`

---

## Architecture Understanding

### CSV Upload Role
✅ **Source of truth for roster membership**
- Defines which players belong to ACC
- Sets their "home" team (ACC 1-6, U13, U15, U17, ZAMI)
- Sets their roles (batsman, bowler, all-rounder, wicket keeper)
- Can update existing or create new players

### Scraper Role
✅ **Matches names to assign points from matches**
- Scrapes KNCB scorecards for match data
- Extracts player performances
- **Matches scorecard name → database player ID**
- Assigns fantasy points to player ID
- **Doesn't care which ACC team they played for that week**

### Key Insight
🎯 **Players can play across teams, points still go to their player ID**

Example scenario:
1. CSV Upload: Creates player "MickBoendermaker" with home team "ACC 1"
2. Week 1: Mick plays for ACC 1 → Scorecard shows "M BOENDERMAKER" → Scraper matches → Points assigned
3. Week 2: Mick plays for ACC 2 → Scorecard shows "M BOENDERMAKER" → Scraper matches same player → Points assigned
4. Week 3: Mick plays for ZAMI → Scorecard shows "M BOENDERMAKER" → Scraper matches same player → Points assigned

**Result:** All points go to the same player ID, regardless of which team he played for.

---

## Files Created

### 1. Database Export
**File:** `current_roster_export.csv`
**Content:** Current 513 players from production database
**Columns:** id, name, club_id, role, tier, base_price, current_price, multiplier, rl_team, is_active

**Distribution:**
- ZAMI 1: 78 players
- ACC 6: 71 players
- ACC 3: 62 players
- ACC 1: 54 players
- ACC 4: 50 players
- U13: 48 players
- Others: <40 each

### 2. Comparison Script
**File:** `backend/compare_roster_sources.py`
**Purpose:** Compare scraped data vs ground truth CSV

**Features:**
- Exact name matching (normalized)
- Fuzzy name matching (80%+ similarity)
- Calculates coverage and precision metrics
- Identifies false positives and false negatives
- Team distribution analysis
- Generates JSON report with recommendations

**Usage:**
```bash
python backend/compare_roster_sources.py \
  current_roster_export.csv \
  ground_truth.csv
```

**Output:**
- Console report with statistics
- `roster_comparison_results.json` - Detailed results

### 3. Player Matching Test
**File:** `backend/test_player_matching.py`
**Purpose:** Test if scraper can match name variations to database

**Tests:**
- Full names vs initials
- Surname-only matching
- Scorecard format (uppercase with initials)
- CamelCase vs spaced names

**Usage:**
```bash
cd backend
python test_player_matching.py
```

**Output:**
- Match accuracy percentage
- Correct/wrong/not found counts
- Examples of successful and failed matches

### 4. Quality Check Endpoint
**File:** `backend/player_endpoints.py` (lines 306-482)
**Endpoint:** `GET /api/admin/players/quality-check`

**Checks:**
- Invalid name patterns (dates, scorecard text)
- Default multiplier players (opposition)
- Duplicates
- Missing team assignments
- Opposition team names
- Suspicious patterns

**Usage:**
```bash
curl "https://api.fantcric.fun/api/admin/players/quality-check" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Output:**
```json
{
  "summary": {
    "total_players": 513,
    "total_issues": 42,
    "health_score": 91.8,
    "status": "good"
  },
  "issues": {
    "invalid_names": [...],
    "default_multipliers": [...],
    "duplicates": [...],
    ...
  },
  "recommendations": [...]
}
```

---

## Testing Workflow

### Step 1: Quality Check (Do This First)
Run quality check on current production data to identify obvious issues:

```bash
# Via SSH
ssh ubuntu@fantcric.fun
cd ~/fantasy-cricket-leafcloud
docker exec fantasy_cricket_api curl http://localhost:8000/api/admin/players/quality-check
```

This will show:
- How many players have default multipliers (likely opposition)
- How many have invalid names
- How many duplicates exist

### Step 2: Comparison (When CSV Available)
Compare scraped data vs ground truth:

```bash
python backend/compare_roster_sources.py \
  current_roster_export.csv \
  your_acc_roster.csv
```

This will show:
- Coverage: Did scraper find most real ACC players?
- Precision: Are most scraped players actually ACC players?
- False positives: Opposition players to remove
- False negatives: Real players scraper missed

### Step 3: Player Matching Test
Test if scraper can identify players from scorecard formats:

```bash
cd backend
python test_player_matching.py
```

This will show:
- Match accuracy for name variations
- Which formats work well
- Which formats fail

### Step 4: CSV Upload (Production Update)
Upload ground truth CSV to update production:

```bash
curl -X POST "https://api.fantcric.fun/api/admin/players/bulk" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "file=@your_acc_roster.csv" \
  -F "club_id=625f1c55-6d5b-40a9-be1d-8f7abe6fa00e"
```

This will:
- Create new players (not in database)
- Update existing players (matched by name)
- Report created/updated/skipped counts

### Step 5: Verify Update
Re-run quality check to confirm improvements:

```bash
curl "https://api.fantcric.fun/api/admin/players/quality-check" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## Expected Results

### Good Scraper Accuracy
- ✅ Coverage: 85-95% (found most real ACC players)
- ✅ Precision: 70-85% (some opposition players, but mostly accurate)
- ✅ Matching: 85%+ (can identify most name variations)

### Poor Scraper Accuracy
- ❌ Coverage: <70% (missed many real players)
- ❌ Precision: <60% (lots of opposition players)
- ❌ Matching: <70% (struggles with name variations)

---

## Next Steps Based on Results

### If Coverage is Low (<80%)
**Problem:** Scraper missed real ACC players

**Solutions:**
- Check scraper date range (maybe didn't scrape enough matches)
- Check name filtering (too aggressive, filtered out real players)
- Manual addition of missing players via CSV

### If Precision is Low (<70%)
**Problem:** Too many opposition players in database

**Solutions:**
- Improve scraper filtering logic
- Add opposition team patterns to filter list
- Remove false positives using quality check results
- Rely on CSV upload as source of truth

### If Matching is Low (<75%)
**Problem:** Scraper can't match scorecard names to database

**Solutions:**
- Add manual name mappings for common variations
- Improve fuzzy matching threshold
- Add surname-only matching fallback
- Create mapping table for problem cases

---

## Manual Name Mappings

If certain players consistently fail to match, create manual mappings:

**File:** `backend/scorecard_player_matcher.py` (around line 50)

```python
MANUAL_MAPPINGS = {
    'M BOENDERMAKER': 'MickBoendermaker',
    'DV DOORNINCK': 'DaanDoorninck',
    'I ALIM': 'IshaqAlim',
    # Add more as needed
}
```

---

## Summary

### What We Know
- ✅ 513 players currently in production database
- ✅ All assigned to ACC club
- ✅ All have multiplier=1.0 (suspicious - might not be calculated)
- ⚠️  Likely includes some opposition players
- ⚠️  Team assignments may be incorrect/inconsistent

### What We Need to Test
1. **How accurate is the scraped roster?** (CSV comparison)
2. **Can scraper match players across name formats?** (Matching test)
3. **How many opposition players are in the 513?** (Quality check)

### Why This Matters
- CSV defines WHO is in ACC roster (ground truth)
- Scraper must FIND these players on scorecards to assign points
- Player matching must work regardless of which ACC team they play for
- Points assignment is the critical functionality for the game to work

---

**Ready to test when you provide the CSV!**
