# Real-Time Season Simulation - User Guide 🏏

Watch your fantasy cricket team progress through an entire season in just 10-15 minutes!

---

## What This Does

Simulates the complete 2026 season (12 weeks, 136 matches) at accelerated speed:
- ✅ **Week-by-week progression** (~50 seconds per week)
- ✅ **Real match data** from 2025 mapped to 2026
- ✅ **Live updates** to leaderboard and dashboard
- ✅ **Watch your team climb** the ranks in real-time

---

## Quick Start

### Prerequisites

1. **Frontend Running** (Recommended):
   ```bash
   cd /Users/guypa/Github/fantasy-cricket-leafcloud/frontend
   npm run dev
   # Opens at http://localhost:3000
   ```

2. **Backend/Database** must be accessible

3. **Have a team created** in the system
   - If not, create one at http://localhost:3000/teams

---

## Running the Simulation

### Option 1: Automated Script (Easiest)

```bash
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend
./run_season_simulation.sh
```

The script will:
1. ✅ Check all prerequisites
2. ✅ Start mock server automatically
3. ✅ Reset the season
4. ✅ Run the simulation
5. ✅ Show progress in real-time

**Open in browser while it runs**: http://localhost:3000/leaderboard

---

### Option 2: Manual Steps

If you want more control:

#### Step 1: Start Mock Server
```bash
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend
export MOCK_DATA_DIR="./mock_data/scorecards_2026"
python3 mock_kncb_server.py
```

#### Step 2: Run Simulation (in another terminal)
```bash
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend
export SCRAPER_MODE=mock
python3 realtime_season_simulation.py
```

---

## What You'll See

### In Terminal:

```
╔════════════════════════════════════════════════════════════════════════════╗
║        🏏 FANTASY CRICKET - REAL-TIME SEASON SIMULATION 🏏                 ║
╚════════════════════════════════════════════════════════════════════════════╝

This will simulate the entire 2026 season (12 weeks) in ~10-15 minutes
Watch your team progress in real-time on the frontend!
URL: http://localhost:3000

Press ENTER to start simulation...

================================ RESETTING SEASON ================================

✅ Cleared 2666 player performances
✅ Reset 15 fantasy teams to 0 points
✅ Database reset complete!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WEEK 1 - 2025-12-16 17:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Week 1: Processing 12 matches...
   [1/12] Match 7254567 (ACC 1)... ✓ 22 players
   [2/12] Match 7254572 (ACC 2)... ✓ 21 players
   ...

✅ Week 1 Complete!
📊 Performances: 245 | Total: 245
📊 Avg Team Points: 156.3 | Max: 234.5

🏆 Current Top 5 Teams:
Rank  Team Name                     Manager             Points      Last Week
──────────────────────────────────────────────────────────────────────────────
🥇 1   Thunder Strikers              john_doe            234.5       234.5
🥈 2   Royal Challengers             jane_smith          198.2       198.2
🥉 3   Mumbai Warriors               bob_wilson          187.4       187.4
   4   Cricket Kings                 alice_j             176.8       176.8
   5   Amsterdam All-Stars           you                 165.3       165.3

⏱️  Week processed in 8.2s
Week 1/12 [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 8% | 245 matches

⏸️  Next week starts in 50s... (Open http://localhost:3000 to watch!)
```

### In Browser (http://localhost:3000/leaderboard):

You'll see the leaderboard update every ~50 seconds with:
- ✅ New points added to teams
- ✅ Rankings change in real-time
- ✅ Your team moving up/down
- ✅ Player performance statistics

### In Your Dashboard (http://localhost:3000/dashboard):

- ✅ Your team's total points increase
- ✅ Individual player performances
- ✅ Captain/vice-captain bonuses
- ✅ Week-by-week breakdown

---

## Timing

| Phase | Duration | What Happens |
|-------|----------|--------------|
| **Setup** | 5-10 seconds | Reset database, start mock server |
| **Week 1-12** | ~8-15 minutes | Process matches, update points |
| **Per Week** | ~50 seconds | Scrape + Calculate + Display |
| **Total** | **10-15 minutes** | Full season simulation |

---

## Tips for Best Experience

### 1. Open Multiple Browser Windows

- **Window 1**: Leaderboard (http://localhost:3000/leaderboard)
  - Watch rankings change in real-time

- **Window 2**: Your Dashboard (http://localhost:3000/dashboard)
  - See your team's progress

- **Window 3**: Top Players (http://localhost:3000/stats)
  - See which players are performing best

### 2. Refresh Strategy

The simulation updates the database every ~50 seconds. To see updates:

**Option A: Manual Refresh**
- Refresh browser after each week message in terminal

**Option B: Auto-Refresh (Recommended)**
```javascript
// Open browser console (F12) and paste:
setInterval(() => location.reload(), 30000);  // Refresh every 30 seconds
```

### 3. Watch Terminal + Browser

Split your screen:
- **Left**: Terminal showing progress
- **Right**: Browser showing leaderboard

You'll see:
1. Terminal: "✅ Week X Complete!"
2. Browser: Rankings update (after refresh)
3. Your team moves up/down the leaderboard

---

## Customizing the Simulation

### Change Speed

Edit `realtime_season_simulation.py` line ~200:

```python
pause_time = 50  # seconds between weeks

# For faster simulation:
pause_time = 10  # ~2 minutes total

# For slower (more realistic):
pause_time = 120  # ~24 minutes total

# For instant:
pause_time = 0  # ~1 minute total
```

### Change Display

Edit the script to:
- Show more/fewer teams
- Display player statistics
- Add team comparisons
- Show round-by-round breakdowns

---

## Troubleshooting

### "Mock server failed to start"
```bash
# Check if port 5001 is in use
lsof -ti:5001

# Kill process if needed
lsof -ti:5001 | xargs kill

# Restart
./run_season_simulation.sh
```

### "Database connection failed"
```bash
# Check if PostgreSQL is running
pg_isready

# If not, start it (macOS):
brew services start postgresql

# Or Docker:
docker-compose up -d fantasy_cricket_db
```

### "No matches found"
```bash
# Verify mock data exists
ls -la mock_data/scorecards_2026/by_week/

# If missing, load it:
python3 load_2025_scorecards_to_mock.py
```

### Frontend not updating
1. **Check if frontend is running**: http://localhost:3000
2. **Hard refresh browser**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
3. **Clear cache**: Cmd+Option+E (Mac) or Ctrl+Shift+Delete (Windows)

---

## After Simulation

### View Results

```bash
# Check total performances
psql fantasy_cricket -c "SELECT COUNT(*) FROM player_performances;"

# Check team standings
psql fantasy_cricket -c "SELECT team_name, total_points FROM fantasy_teams ORDER BY total_points DESC LIMIT 10;"

# Check your team
psql fantasy_cricket -c "SELECT * FROM fantasy_teams WHERE user_id = YOUR_USER_ID;"
```

### Reset and Run Again

```bash
# The script automatically resets at the start
./run_season_simulation.sh

# Or manually reset
python3 -c "
from realtime_season_simulation import reset_season
import asyncio
asyncio.run(reset_season())
"
```

---

## Files Created

### Main Scripts:
1. **`realtime_season_simulation.py`** (400 lines)
   - Core simulation logic
   - Week-by-week processing
   - Real-time updates

2. **`run_season_simulation.sh`** (Bash script)
   - Automated setup and run
   - Prerequisites checking
   - Mock server management

### Supporting Files:
3. **`REALTIME_SIMULATION_GUIDE.md`** (This file)
   - Complete user guide
   - Troubleshooting
   - Customization options

---

## What Makes This Cool

### Real Data
- ✅ Uses 136 actual 2025 ACC matches
- ✅ Real player names and performances
- ✅ Accurate fantasy points calculations

### Accelerated Time
- ✅ 6-month season in 10 minutes
- ✅ Still feels "real-time" with 50s pauses
- ✅ You can watch rankings change

### Full Integration
- ✅ Updates actual database
- ✅ Frontend shows real data
- ✅ All features work (captain bonuses, multipliers, etc.)

### Production Testing
- ✅ Tests full workflow end-to-end
- ✅ Validates scraper + calculator + database
- ✅ Proves system works for 2026 season

---

## Expected Results

### Typical Season Stats:
- **Total Performances**: ~2,500-3,000
- **Average Team Points**: ~1,200-1,500
- **Top Team Points**: ~2,000-2,500
- **Player Performances/Week**: ~200-250

### Your Team:
- Should see steady point accumulation
- Rankings will fluctuate each week
- Captain/VC bonuses clearly visible
- Player multipliers in effect

---

## Advanced: Monitoring During Simulation

### Watch Database Updates

```bash
# In another terminal, watch table counts
watch -n 10 'psql fantasy_cricket -c "SELECT COUNT(*) FROM player_performances;"'

# Watch leaderboard
watch -n 10 'psql fantasy_cricket -c "SELECT team_name, total_points FROM fantasy_teams ORDER BY total_points DESC LIMIT 5;"'
```

### Mock Server Logs

```bash
# Watch mock server activity
tail -f mock_server.log

# See request counts
grep "GET /match" mock_server.log | wc -l
```

---

## Summary

**This simulation lets you**:
1. ✅ Test the entire system end-to-end
2. ✅ Watch your team progress in real-time
3. ✅ Experience a full season in minutes
4. ✅ Validate everything works for 2026
5. ✅ Demo the app to others

**Just run**:
```bash
./run_season_simulation.sh
```

**And open**:
http://localhost:3000/leaderboard

**Enjoy watching your team compete!** 🏏🏆

---

**Questions or issues?** Check the troubleshooting section above or logs in:
- `mock_server.log` - Mock server activity
- Terminal output - Simulation progress
- Browser console - Frontend errors
