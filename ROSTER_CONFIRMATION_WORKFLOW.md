# 🎯 Roster Confirmation Workflow

## Overview

The roster confirmation workflow is **FULLY IMPLEMENTED** and will automatically calculate player multipliers from historical KNCB data when you confirm the roster.

---

## 📋 Complete Workflow

### Step 1: CSV Upload
**Action:** Upload ACC roster CSV via admin API

**Endpoint:** `POST /api/admin/players/bulk`

**What Happens:**
- Creates new players not in database
- Updates existing players (matched by name)
- Sets team assignments from CSV
- **Does NOT calculate multipliers yet** (all remain 1.0)

**CSV Format:**
```csv
name,team_name,player_type,multiplier,is_wicket_keeper
MickBoendermaker,ACC 1,batsman,,false
DaanDoorninck,ACC 2,all-rounder,,false
```

**API Response:**
```json
{
  "created_count": 50,
  "updated_count": 450,
  "skipped_count": 3,
  "total_processed": 500
}
```

---

### Step 2: Roster Visible
**Action:** Admin reviews roster in frontend

**What You See:**
- All ACC players listed
- Team assignments
- Roles (batsman, bowler, etc.)
- Multipliers all showing 1.0 (default)
- Youth teams (U13, U15, U17) shown separately

**Admin Can:**
- Review player list
- Check team distributions
- Select which youth teams to include

---

### Step 3: Roster Confirmation
**Action:** Press "Confirm Roster" button in admin UI

**Endpoint:** `POST /api/admin/roster/confirm`

**Request Body:**
```json
{
  "youth_teams": ["U15", "U17"],
  "calculate_multipliers": true
}
```

**What Happens Automatically:**

#### 3.1 Activate/Deactivate Players
- Sets `is_active=true` for:
  - All senior teams (ACC 1-6, ZAMI 1)
  - Selected youth teams (U15, U17 in example)
- Sets `is_active=false` for:
  - Excluded youth teams (U13 in example)

#### 3.2 Calculate Multipliers (The Magic Part!)
**File:** `backend/multiplier_calculator.py`

**Process:**

1. **Check for Stored Data** (Fast)
   - Look at each player's `prev_season_fantasy_points` field
   - If already calculated, use that value

2. **Calculate from Database** (Medium)
   - Check if player has matches in database from previous season
   - Sum up their fantasy points from those matches
   - Store in `prev_season_fantasy_points` field

3. **Scrape KNCB Website** (Slow - This is the critical part!)
   - For players WITHOUT historical data in database
   - **Scrapes KNCB match centre for previous season (2025)**
   - **Finds all ACC matches from past 365 days**
   - **Scrapes each scorecard**
   - **Matches player names** ("M BOENDERMAKER" → "MickBoendermaker")
   - **Sums up fantasy points** from all their performances
   - **Stores result** in `prev_season_fantasy_points`

4. **Calculate Distribution Statistics**
   - Find median fantasy points across all players
   - Find min and max values

5. **Calculate Multipliers**
   - **Median players get 1.0** (baseline)
   - **Above median (stronger) get 0.69-1.0** (lower multiplier = more expensive)
   - **Below median (weaker) get 1.0-5.0** (higher multiplier = cheaper)

   **Formula:**
   ```
   If player_score > median:
     multiplier = 1.0 - ((player_score - median) / (max - median)) * (1.0 - 0.69)

   If player_score < median:
     multiplier = 1.0 + ((median - player_score) / (median - min)) * (5.0 - 1.0)
   ```

6. **Apply to Database**
   - Update each player's `multiplier` field
   - Set `starting_multiplier` (for reference)
   - Set `multiplier_updated_at` timestamp

---

### Step 4: Roster Confirmed
**Action:** System returns confirmation with statistics

**API Response:**
```json
{
  "success": true,
  "active_players": 475,
  "inactive_players": 38,
  "included_youth_teams": ["U15", "U17"],
  "excluded_youth_teams": ["U13"],
  "multipliers_calculated": true,
  "multiplier_stats": {
    "total_players": 475,
    "players_with_data": 450,
    "players_without_data": 25,
    "median_score": 145.5,
    "min_score": 12.0,
    "max_score": 892.3,
    "min_multiplier": 0.69,
    "max_multiplier": 5.0,
    "scraped_from_kncb": 120
  }
}
```

**What This Means:**
- ✅ Roster is now locked and confirmed
- ✅ Players have calculated multipliers (0.69-5.0)
- ✅ System scraped 120 players from KNCB (these had no database history)
- ✅ Ready for league creation

---

## ⏱️ Expected Duration

| Step | Duration | Notes |
|------|----------|-------|
| CSV Upload | 1-5 seconds | Depends on file size (~500 players) |
| Roster Review | N/A | User action |
| **Roster Confirmation** | **5-15 minutes** | **Includes KNCB scraping** |
| - Player activation | <1 second | Database updates |
| - Check stored data | 1-2 seconds | Database queries |
| - Calculate from DB matches | 5-10 seconds | If matches exist |
| - **Scrape KNCB** | **3-12 minutes** | **120+ players × 10-20 matches each** |
| - Calculate multipliers | <1 second | Math operations |
| - Apply to database | 1-2 seconds | Batch update |

**Critical:** The scraping step is **SLOW** because:
- Each player needs 365 days of match history scraped
- KNCB website requires individual page loads per match
- Player name matching happens for each scorecard
- ~100-150 players typically need scraping
- ~10-20 matches per player to check
- **Total: 1000-3000 web page loads**

---

## 🎯 Player Name Matching (How It Works)

This is **CRITICAL** for the system to work correctly.

### The Challenge
**Scorecard format:** "M BOENDERMAKER" (initials + uppercase surname)
**Database format:** "MickBoendermaker" (camelCase full name)

### The Solution
**File:** `backend/scorecard_player_matcher.py`

**Matching Priority:**
1. **Exact match** (normalized) - e.g., "mickboendermaker" == "mickboendermaker"
2. **Manual mapping table** - Predefined difficult cases
3. **Surname match** - "BOENDERMAKER" → "MickBoendermaker"
4. **Initial + Surname** - "M BOENDERMAKER" → "MickBoendermaker"
5. **Fuzzy match** - 80%+ similarity using SequenceMatcher

**Example Matching:**
```python
Scorecard: "M BOENDERMAKER"

Step 1: Normalize → "mboendermaker"
Step 2: Not in manual mappings
Step 3: Extract surname → "BOENDERMAKER"
Step 4: Find players with "boendermaker" in normalized name
Step 5: Found 1 match: "MickBoendermaker"
Step 6: Verify initial "M" matches "Mick" ✓
Result: MATCHED → player_id = "abc123..."
```

**If Multiple Matches:**
- Check initials to disambiguate
- Example: "J DE VRIES" could match "JanDeVries" or "JoostDeVries"
- Uses initials "J" to pick correct one

---

## 🔍 What Gets Scraped

### Date Range
- **Previous calendar year** (e.g., if confirming in 2026, scrapes 2025)
- **Full 365 days** to ensure complete season coverage
- Cricket season is typically April-September, but scrapes full year to be safe

### Data Per Match
For each match where player appears:
- Runs scored
- Balls faced
- Wickets taken
- Overs bowled
- Catches
- Run outs
- Stumpings
- **Fantasy points calculated using game rules**

### Total Points
- Sum of fantasy points across **all matches**
- Stored in `prev_season_fantasy_points`
- Used as basis for multiplier calculation

---

## 📊 Multiplier Distribution Example

Assume 475 active players, here's how multipliers might be distributed:

| Performance Level | Fantasy Points | Player Count | Multiplier Range | Cost Impact |
|-------------------|----------------|--------------|------------------|-------------|
| Elite (top 10%) | 600-900 | 48 | 0.69-0.80 | Most expensive |
| Strong (top 25%) | 400-600 | 71 | 0.80-0.90 | Expensive |
| Above Average | 200-400 | 95 | 0.90-1.00 | Moderate+ |
| **Median** | **145.5** | **~50** | **1.00** | **Baseline** |
| Below Average | 80-145 | 95 | 1.00-2.00 | Moderate- |
| Weak (bottom 25%) | 30-80 | 71 | 2.00-3.50 | Cheap |
| Very Weak (bottom 10%) | 0-30 | 48 | 3.50-5.00 | Very cheap |

**Key Insight:**
- Strong players get **low multipliers** (0.69-1.0) = More expensive to select
- Weak players get **high multipliers** (1.0-5.0) = Cheaper to select
- Forces users to balance team composition (can't afford all stars)

---

## ⚠️ Important Considerations

### 1. First-Time Scraping is Slowest
**First confirmation:** 5-15 minutes (scrapes 100-150 players)
**Subsequent confirmations:** 1-2 minutes (data already stored)

**Why:** `prev_season_fantasy_points` is stored permanently, so:
- Season 1 (2026): Slow (scrape 2025 data)
- Season 2 (2027): Fast (use stored 2026 data from database matches)
- Season 3 (2028): Fast (use stored 2027 data from database matches)

### 2. New Players Mid-Season
If you add new players after roster confirmation:
- They get default multiplier 1.0
- Must manually trigger multiplier recalculation
- Or wait until next season confirmation

### 3. KNCB Website Dependency
**Risk:** If KNCB website is down or changes structure:
- Scraping will fail
- Players will get neutral 1.0 multiplier
- System logs errors but doesn't fail completely

**Mitigation:**
- System stores scraped data permanently
- Only needs to scrape once per player per season
- Future seasons use database history (no scraping needed)

### 4. Player Name Mismatches
**Risk:** Scraper can't match "M BOENDERMAKER" to database

**Impact:**
- Player gets neutral 1.0 multiplier (incorrect)
- Historical performance not counted

**Solution:**
- Add manual mapping in `scorecard_player_matcher.py`
- Example:
  ```python
  MANUAL_MAPPINGS = {
      'M BOENDERMAKER': 'MickBoendermaker',
      'DV DOORNINCK': 'DaanDoorninck',
  }
  ```

### 5. Youth Team Handling
**Choice:** Include U13, U15, U17 or not?

**Impact:**
- Included youth teams get multipliers calculated
- Excluded teams set to `is_active=false` (hidden from leagues)
- Can change selection and re-confirm if needed

---

## 🛠️ Troubleshooting

### Issue: "Multipliers not calculating"

**Diagnosis:**
```bash
# Check API logs
ssh ubuntu@fantcric.fun
docker logs fantasy_cricket_api --tail 200 | grep -i multiplier
```

**Common Causes:**
1. KNCB website down → Check scraper logs
2. Player name mismatch → Add manual mapping
3. No previous season data → Expected for new players

### Issue: "Scraping taking too long (>20 minutes)"

**Diagnosis:**
- Normal for first-time scraping of 500 players
- KNCB website might be slow
- Network connectivity issues

**Action:**
- Wait patiently (system will complete)
- Check progress in logs: `docker logs fantasy_cricket_api -f`
- System won't timeout (no 2-minute limit on this endpoint)

### Issue: "Some players have multiplier 1.0, others have calculated values"

**Explanation:**
- This is **EXPECTED** for new players or those without match history
- Players with no previous season data default to 1.0
- Will be fixed in subsequent seasons when they have performance data

---

## 📱 Frontend Implementation

### Roster Confirmation UI Flow

**Page:** `/admin/roster` (or similar)

**UI Elements:**
1. **Player List**
   - Show all players with current multipliers
   - Indicate which are active/inactive
   - Show team assignments

2. **Youth Team Selection**
   ```jsx
   <CheckboxGroup label="Include Youth Teams">
     <Checkbox value="U13">U13 (48 players)</Checkbox>
     <Checkbox value="U15">U15 (34 players)</Checkbox>
     <Checkbox value="U17">U17 (38 players)</Checkbox>
   </CheckboxGroup>
   ```

3. **Confirm Button**
   ```jsx
   <Button
     onClick={handleConfirmRoster}
     loading={isConfirming}
     disabled={!hasPlayers}
   >
     {isConfirming ? 'Calculating Multipliers...' : 'Confirm Roster'}
   </Button>
   ```

4. **Progress Indicator**
   ```jsx
   {isConfirming && (
     <ProgressMessage>
       Scraping KNCB for historical data...
       This may take 5-15 minutes for first confirmation.
       <Spinner />
     </ProgressMessage>
   )}
   ```

5. **Success Message**
   ```jsx
   {confirmed && (
     <Alert type="success">
       <h3>Roster Confirmed!</h3>
       <p>Active players: {stats.active_players}</p>
       <p>Multipliers calculated: {stats.players_with_data}/{stats.total_players}</p>
       <p>Scraped from KNCB: {stats.scraped_from_kncb}</p>
       <p>Ready to create leagues!</p>
     </Alert>
   )}
   ```

---

## ✅ Verification Checklist

After confirming roster, verify:

- [ ] All active players have multipliers between 0.69-5.0
- [ ] Median players have multiplier ~1.0
- [ ] Top performers have multipliers 0.69-0.90
- [ ] Weak performers have multipliers 2.0-5.0
- [ ] `prev_season_fantasy_points` field populated for most players
- [ ] Excluded youth teams marked `is_active=false`
- [ ] Confirmation response shows scraping statistics

**Query to Check:**
```sql
SELECT
  rl_team,
  COUNT(*) as player_count,
  AVG(multiplier) as avg_multiplier,
  MIN(multiplier) as min_multiplier,
  MAX(multiplier) as max_multiplier,
  COUNT(CASE WHEN prev_season_fantasy_points IS NOT NULL THEN 1 END) as with_history
FROM players
WHERE is_active = true
GROUP BY rl_team
ORDER BY rl_team;
```

---

## 🎉 Summary

### ✅ FULLY IMPLEMENTED
The roster confirmation workflow is **complete and production-ready**:

1. ✅ CSV Upload → Creates/updates players
2. ✅ Roster visible → Admin can review
3. ✅ Confirm button → Triggers calculation
4. ✅ **Automatic KNCB scraping** for historical data
5. ✅ **Player name matching** across formats
6. ✅ **Multiplier calculation** from performance
7. ✅ Database updates with calculated values
8. ✅ Roster locked and ready for leagues

### ⏱️ Expected Experience
1. Upload CSV: **5 seconds**
2. Review roster: **Your pace**
3. Press confirm: **5-15 minutes** (wait for scraping)
4. See results: **Multipliers calculated and ready!**

### 🔑 Key Files
- `backend/admin_endpoints.py` - Roster confirmation endpoint (line 863)
- `backend/multiplier_calculator.py` - Calculation logic
- `backend/kncb_html_scraper.py` - Web scraping
- `backend/scorecard_player_matcher.py` - Name matching

**Everything is ready to go!** Just upload your CSV and press confirm. The system will handle the rest automatically.
