# Weekly Administration Procedures

**For Fantasy Cricket League Administrators**

This document outlines the weekly procedures for running the fantasy cricket league during the season.

---

## Overview

The fantasy cricket system requires weekly administration to:
1. Scrape match scorecards from KNCB Matchcentre
2. Calculate fantasy points for all players
3. Update team totals and leaderboard
4. Notify users of updates (optional)

**Timeline**: Matches typically occur on Saturday/Sunday, with results processed by Wednesday.

---

## Weekly Schedule

| Day | Task | Time | Priority |
|-----|------|------|----------|
| **Tuesday** | Scrape scorecards | Evening (after all matches confirmed) | HIGH |
| **Tuesday** | Run simulation | After scraping complete | HIGH |
| **Wednesday** | Verify leaderboard | Morning | MEDIUM |
| **Wednesday** | Notify users | Morning | LOW |

---

## Step-by-Step Procedures

### 1. Connect to Production Server

```bash
# SSH into the production server
ssh ubuntu@fantcric.fun

# Navigate to project directory
cd ~/fantasy-cricket-leafcloud
```

### 2. Check Docker Status

```bash
# Verify all containers are running
docker ps

# Expected output: fantasy_cricket_api, fantasy_cricket_db, fantasy_cricket_frontend (all healthy)
```

### 3. Scrape Weekly Scorecards

**Option A: Automatic Scraping (Recommended)**
```bash
# The Celery worker automatically scrapes weekly on Tuesday at 8 PM
# Check logs to verify it ran:
docker logs fantasy_cricket_worker 2>&1 | grep -A 20 "Weekly scrape"
```

**Option B: Manual Scraping**
```bash
# If automatic scraping failed, run manually:
docker exec fantasy_cricket_api python3 /app/scrape_weekly.py

# This will:
# - Find all matches from the past week
# - Scrape scorecards from KNCB Matchcentre
# - Parse batting, bowling, and fielding stats
# - Store in player_performances table
```

### 4. Run Fantasy Team Simulation

```bash
# Determine the current round number
# Round 1 = Week 1, Round 2 = Week 2, etc.

# Run the simulation for the current round
cd ~/fantasy-cricket-leafcloud/backend
./run_weekly_simulation.sh <round_number>

# Examples:
./run_weekly_simulation.sh 1  # First week of season
./run_weekly_simulation.sh 2  # Second week
./run_weekly_simulation.sh 10 # Tenth week
```

The script will:
- ✅ Fetch all active fantasy teams
- ✅ Load player performances for the week
- ✅ Calculate fantasy points with tiered system
- ✅ Apply player multipliers (0.69-5.0)
- ✅ Apply captain (2x) and vice-captain (1.5x) bonuses
- ✅ Update team totals (cumulative across all rounds)
- ✅ Update leaderboard rankings
- ✅ Generate detailed logs

### 5. Verify Results

**Check Simulation Logs:**
```bash
# View the most recent simulation log
ls -lth ~/fantasy-cricket-leafcloud/logs/simulation_*.log | head -1
cat $(ls -t ~/fantasy-cricket-leafcloud/logs/simulation_*.log | head -1)
```

**Check Leaderboard on Website:**
1. Navigate to https://fantcric.fun
2. Click on your league
3. Verify:
   - Team totals updated
   - Rankings correct
   - Top performers showing

**Check Database Directly:**
```bash
# View current leaderboard
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
SELECT
    ROW_NUMBER() OVER (ORDER BY ft.total_points DESC) as rank,
    ft.team_name,
    COALESCE(u.full_name, u.email) as owner,
    ROUND(ft.total_points::numeric, 1) as points
FROM fantasy_teams ft
JOIN users u ON ft.user_id = u.id
WHERE ft.is_finalized = TRUE
ORDER BY ft.total_points DESC
LIMIT 10;
"

# Check player performances for current round
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
SELECT COUNT(*) as total_performances, round_number
FROM player_performances
GROUP BY round_number
ORDER BY round_number DESC;
"
```

### 6. (Optional) Notify Users

```bash
# Send email notifications to all users about updated leaderboard
# (This feature requires email configuration)
docker exec fantasy_cricket_api python3 /app/send_weekly_update_emails.py

# Or manually post update on league page/social media
```

---

## Troubleshooting

### Issue: Scraper Failed

**Symptoms:**
- No new player performances in database
- Log shows "0 matches found" or timeout errors

**Solutions:**

1. **Check KNCB Matchcentre is accessible:**
   ```bash
   curl -I https://matchcentre.kncb.nl/
   ```

2. **Check if matches were played this week:**
   - Visit https://matchcentre.kncb.nl/
   - Verify ACC matches occurred

3. **Run scraper with debug logging:**
   ```bash
   docker exec fantasy_cricket_api python3 /app/scrape_weekly.py --debug
   ```

4. **Manual fallback:**
   - Find match URLs manually on KNCB Matchcentre
   - Run scraper with specific URLs:
   ```bash
   docker exec fantasy_cricket_api python3 /app/scrape_specific_match.py <match_url>
   ```

### Issue: Simulation Failed

**Symptoms:**
- Script exits with error
- Database not updated
- Logs show exceptions

**Solutions:**

1. **Check database connection:**
   ```bash
   docker exec fantasy_cricket_api python3 -c "
   import os
   from sqlalchemy import create_engine, text
   engine = create_engine(os.getenv('DATABASE_URL'))
   conn = engine.connect()
   result = conn.execute(text('SELECT 1'))
   print('✅ Database connection OK')
   conn.close()
   "
   ```

2. **Check for missing schema columns:**
   ```bash
   # Verify player_performances table exists with all columns
   docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "\d player_performances"
   ```

3. **Re-run with correct round number:**
   - Double-check you're using the right round number
   - Round numbers should be sequential (1, 2, 3, ...)

4. **Check logs for specific errors:**
   ```bash
   tail -100 ~/fantasy-cricket-leafcloud/logs/simulation_*.log
   ```

### Issue: Incorrect Points

**Symptoms:**
- Team totals don't match expected values
- Captain/VC multipliers not applied
- Player multipliers incorrect

**Solutions:**

1. **Verify rules-set-1.py is correct:**
   ```bash
   cat ~/fantasy-cricket-leafcloud/backend/rules-set-1.py
   ```

2. **Check player multipliers in database:**
   ```bash
   docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
   SELECT name, multiplier, is_wicket_keeper
   FROM players
   WHERE name IN ('Boris Gorlee', 'Sikander Zulfiqar', 'Shariz Ahmad')
   ORDER BY multiplier DESC;
   "
   ```

3. **Manually recalculate a few players:**
   - Get their stats from player_performances
   - Run through rules-set-1.py manually
   - Compare with stored final_fantasy_points

4. **Re-run simulation for problematic round:**
   ```bash
   # This will recalculate all points for the round
   ./run_weekly_simulation.sh <round_number>
   ```

### Issue: Database Connection Failed

**Symptoms:**
- "connection refused" errors
- "password authentication failed"

**Solutions:**

1. **Check database container is running:**
   ```bash
   docker ps | grep fantasy_cricket_db
   ```

2. **Restart database if needed:**
   ```bash
   docker-compose restart fantasy_cricket_db
   ```

3. **Verify DATABASE_URL environment variable:**
   ```bash
   docker exec fantasy_cricket_api env | grep DATABASE_URL
   ```

4. **Reset database password if needed:**
   ```bash
   docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
   ALTER USER cricket_admin WITH PASSWORD '<password_from_.env>';
   "
   ```

---

## Emergency Procedures

### Rollback a Round

If a simulation was run incorrectly and you need to rollback:

```bash
# WARNING: This deletes data. Make a backup first!

# 1. Backup current database
docker exec fantasy_cricket_db pg_dump -U cricket_admin fantasy_cricket > backup_$(date +%Y%m%d).sql

# 2. Delete performances for the bad round
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
DELETE FROM player_performances WHERE round_number = <round_to_delete>;
"

# 3. Recalculate team totals from remaining performances
docker exec fantasy_cricket_api python3 /app/recalculate_team_totals.py

# 4. Re-run the simulation with correct data
./run_weekly_simulation.sh <round_number>
```

### Manual Point Adjustment

If you need to manually adjust a team's score (e.g., for an error):

```bash
# Update team total points
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c "
UPDATE fantasy_teams
SET total_points = <new_total>
WHERE team_name = '<team_name>';
"

# Log the manual adjustment
echo \"$(date) - Manual adjustment: <team_name> set to <new_total> points - Reason: <reason>\" >> ~/fantasy-cricket-leafcloud/logs/manual_adjustments.log
```

---

## Maintenance Tasks

### Weekly

- ✅ Run scraper and simulation
- ✅ Verify leaderboard
- ✅ Check error logs

### Monthly

- Check disk space: `df -h`
- Review Docker logs: `docker-compose logs --tail=100`
- Backup database: `docker exec fantasy_cricket_db pg_dump -U cricket_admin fantasy_cricket > backup_monthly_$(date +%Y%m).sql`

### End of Season

- Generate final statistics
- Export leaderboard
- Archive season data
- Prepare for next season

---

## Contact Information

**Technical Issues:**
- GitHub: https://github.com/yourusername/fantasy-cricket-leafcloud
- Logs location: `~/fantasy-cricket-leafcloud/logs/`

**KNCB Matchcentre:**
- Website: https://matchcentre.kncb.nl/
- Contact: (if scraping issues persist)

---

## Quick Reference

```bash
# Weekly commands (in order)
ssh ubuntu@fantcric.fun
cd ~/fantasy-cricket-leafcloud/backend

# 1. Check scraper ran automatically
docker logs fantasy_cricket_worker 2>&1 | tail -50

# 2. Run simulation
./run_weekly_simulation.sh <round_number>

# 3. Verify on website
# Visit: https://fantcric.fun

# 4. Check logs if issues
tail -100 ~/fantasy-cricket-leafcloud/logs/simulation_*.log
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-19 | 1.0 | Initial version |

---

*Generated by Claude Code - Fantasy Cricket League Administration*
