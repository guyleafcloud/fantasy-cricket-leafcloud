# Fantasy Cricket Beta Test Plan
## Season Simulation Using 2025 Scorecards as Proxy Data

**Status:** Production Ready
**Date:** November 22, 2025
**Environment:** https://fantcric.fun

---

## 🎯 Test Objectives

1. **Validate Complete Season Flow**
   - League creation and management
   - Team building and roster management
   - Weekly scorecard processing
   - Points calculation with multipliers
   - Multiplier drift system (15% per week)
   - Leaderboard updates

2. **Test User Experience**
   - Registration and login
   - Team building interface
   - Points tracking and transparency
   - Mobile responsiveness
   - Dark/light mode

3. **Verify Data Integrity**
   - Player stats aggregation
   - Fantasy points accuracy
   - Multiplier calculations
   - Transfer system

---

## 📊 Current Production Status

### ✅ **Database**
- **Players:** 513 (with multipliers from 2024 season)
- **Clubs:** 2 (VRA, ACC)
- **Seasons:** 2
- **Player Performances:** 999 (2025 data imported)
- **Leagues:** 1 (test league)

### ✅ **Systems Operational**
- Frontend: Running, healthy
- API: Running, healthy
- Database: Running, healthy
- Redis: Running, healthy
- Nginx: Running with SSL
- Celery Worker: Running
- Celery Scheduler: Running

### ✅ **Recent Fixes Applied**
- ✅ Dark mode fixed across all pages
- ✅ Finalize team button improved (centered, mobile-friendly)
- ✅ Player multiplier system implemented
- ✅ Multiplier drift system working
- ✅ Fantasy points calculated (base × multiplier)
- ✅ 999 historical performances migrated

---

## 🔄 Beta Test Workflow

### **Phase 1: Pre-Test Setup** (Admin Only)
**Duration:** 1 hour

#### 1.1 Create Beta Test League
```bash
League Name: "ACC Beta Test - 2025 Season Simulation"
Description: "Testing full season with 2025 historical data"
Season: 2025 Season
Club: ACC (Amsterdam Cricket Club)
Settings:
  - Squad Size: 11 players
  - Transfers per Season: 10
  - Public: No (private, invite-only)
  - Max Participants: 10
```

#### 1.2 Generate Invite Code
- Admin creates league
- Copy league code
- Share with beta testers

#### 1.3 Verify Data Readiness
```bash
# Check on production:
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_api python3 -c "
from database import SessionLocal
from database_models import Player, PlayerPerformance
db = SessionLocal()
print(f'Players ready: {db.query(Player).count()}')
print(f'Performances ready: {db.query(PlayerPerformance).count()}')
perfs_with_multiplier = db.query(PlayerPerformance).filter(
    PlayerPerformance.fantasy_points != None
).count()
print(f'Performances with multipliers: {perfs_with_multiplier}')
"
```

---

### **Phase 2: Beta Tester Onboarding** (Day 1)
**Duration:** 2-3 hours

#### 2.1 User Registration
**Testers should:**
1. Go to https://fantcric.fun/register
2. Create account with email/password
3. Complete Cloudflare Turnstile verification
4. Verify email (if enabled)

**Test Points:**
- [ ] Registration form works
- [ ] Turnstile loads correctly
- [ ] Dark mode toggle works
- [ ] Mobile responsive

#### 2.2 Join League
**Testers should:**
1. Go to https://fantcric.fun/leagues
2. Click "Join League"
3. Enter league code
4. Create fantasy team name
5. Confirm joining

**Test Points:**
- [ ] League code validation
- [ ] Team name creation
- [ ] Redirect to team builder

#### 2.3 Build Initial Squad
**Testers should:**
1. Review available ACC players
2. Select 11 players within constraints:
   - Minimum 4 batsmen
   - Minimum 4 bowlers
   - Rest can be all-rounders
3. Assign captain (2x points)
4. Assign vice-captain (1.5x points)
5. Designate wicketkeeper (2x catch points)
6. Click "Finalize Team"

**Test Points:**
- [ ] Player list loads with multipliers shown
- [ ] Squad builder enforces role constraints
- [ ] Progress bar updates correctly
- [ ] Captain/VC/WK selection works
- [ ] Finalize button prominent and works
- [ ] Mobile usability good

---

### **Phase 3: Week 1 Simulation** (Day 2)
**Duration:** 1 hour admin work

#### 3.1 Admin Processes Week 1 Scorecards
**Admin runs:**
```bash
# On production server
ssh ubuntu@fantcric.fun
cd ~/fantasy-cricket-leafcloud/backend

# Process Week 1 scorecards (manually select 3-4 matches)
docker exec fantasy_cricket_api python3 -c "
from match_performance_service import MatchPerformanceService
from database import SessionLocal

# Example: Process specific match IDs from 2025 data
service = MatchPerformanceService()
# ... process selected matches
"
```

#### 3.2 Verify Points Calculation
**Check:**
- Base points calculated correctly
- Player multipliers applied
- Captain/VC bonuses working
- Final points = base × player_mult × captain_mult

#### 3.3 Update Fantasy Team Points
**System should automatically:**
- Calculate points for each player in fantasy teams
- Sum total team points
- Update leaderboard

**Test Points:**
- [ ] Points appear on team page
- [ ] Leaderboard updates
- [ ] Point breakdown visible

---

### **Phase 4: Weekly Cycle** (Weeks 2-10)
**Duration:** 10 weeks (can accelerate)

For each week, repeat:

#### 4.1 Process Scorecards
- Admin selects and processes 3-4 matches from 2025 data
- System calculates fantasy points

#### 4.2 Run Multiplier Drift
```bash
# Monday morning (or manual trigger)
docker exec fantasy_cricket_api python3 -c "
from multiplier_adjuster import MultiplierAdjuster
from database import SessionLocal

db = SessionLocal()
adjuster = MultiplierAdjuster(drift_rate=0.15)
result = adjuster.adjust_multipliers(db, dry_run=False)
print(result)
"
```

#### 4.3 Testers Make Transfers (Optional)
**Testers can:**
- View their team performance
- Make transfers (max 10 per season)
- See how multiplier changes affect strategy

**Test Points:**
- [ ] Transfer system works
- [ ] Transfer count decrements
- [ ] New players use current multipliers

---

### **Phase 5: Analysis & Feedback** (After Week 10)
**Duration:** 1 week

#### 5.1 Data Analysis
**Admin reviews:**
```bash
# Check multiplier drift over season
docker exec fantasy_cricket_api python3 -c "
from database import SessionLocal
from database_models import Player
import statistics

db = SessionLocal()
players = db.query(Player).all()

print('Multiplier Distribution After 10 Weeks:')
multipliers = [p.multiplier for p in players]
print(f'  Min: {min(multipliers):.2f}')
print(f'  Median: {statistics.median(multipliers):.2f}')
print(f'  Max: {max(multipliers):.2f}')

# Show biggest changes
# (Compare to initial multipliers if stored)
"
```

#### 5.2 Beta Tester Survey
**Questions:**
1. How intuitive was team building? (1-5)
2. Did you understand the multiplier system? (Y/N)
3. Was points calculation transparent? (1-5)
4. Mobile experience rating? (1-5)
5. Would you play in a real season? (Y/N)
6. Top 3 improvements needed?

---

## 📋 Testing Checklist

### **Critical Features to Test**

#### Registration & Authentication
- [ ] User registration works
- [ ] Login works
- [ ] Cloudflare Turnstile functions
- [ ] Password reset (if implemented)
- [ ] Session persistence

#### League Management
- [ ] Admin can create private league
- [ ] Invite code generation
- [ ] Users can join with code
- [ ] League settings enforced

#### Team Building
- [ ] Player list loads
- [ ] Multipliers visible
- [ ] Squad constraints enforced
- [ ] Captain/VC/WK selection
- [ ] Finalize button works
- [ ] Mobile responsive

#### Points Calculation
- [ ] Base points accurate
- [ ] Player multiplier applied
- [ ] Captain 2x bonus works
- [ ] VC 1.5x bonus works
- [ ] WK 2x catch bonus works
- [ ] Total points correct

#### Multiplier Drift
- [ ] Drift calculated weekly
- [ ] Uses final fantasy points
- [ ] 15% drift rate applied
- [ ] Median-based targeting
- [ ] Min/max bounds respected (0.69-5.0)

#### Leaderboard
- [ ] Updates after each week
- [ ] Rankings correct
- [ ] Points display accurate
- [ ] Real-time or near-real-time

#### Transfers
- [ ] Transfer system works
- [ ] Count decrements
- [ ] Points recalculated
- [ ] Transfer history visible

#### UI/UX
- [ ] Dark mode works everywhere
- [ ] Mobile responsive
- [ ] No white-on-white text
- [ ] Finalize button prominent
- [ ] Error messages clear

---

## 🐛 Known Issues / Limitations

1. **Celery Workers Show "Unhealthy"**
   - **Status:** Non-blocking, workers are functional
   - **Impact:** None, tasks execute correctly
   - **Fix:** Update healthcheck configuration

2. **No Real-Time Match Updates**
   - **Expected:** Admin manually processes scorecards
   - **Impact:** Not truly "live" during beta
   - **Future:** Automated scraping for live season

3. **Email Notifications Not Configured**
   - **Impact:** No email confirmations or alerts
   - **Workaround:** Manual communication via other channels

---

## 🚀 Go-Live Criteria

Before declaring production-ready:

- [ ] 5+ beta testers complete full season
- [ ] Zero critical bugs reported
- [ ] Multiplier drift validated over 10+ weeks
- [ ] Mobile experience rated 4+ / 5
- [ ] Points calculation verified accurate
- [ ] Performance acceptable (< 2s page loads)
- [ ] Security audit passed
- [ ] Backup/restore tested
- [ ] Monitoring dashboards configured

---

## 📞 Support During Beta

**Admin Contact:** [Your contact info]
**Bug Reporting:** GitHub Issues
**Questions:** [Discord/Slack channel]

**Response Time:** Within 24 hours

---

## 🎉 Success Metrics

- **Participation:** 80%+ of testers complete 10 weeks
- **Engagement:** 60%+ make at least 1 transfer
- **Satisfaction:** 4+ / 5 average rating
- **Accuracy:** 100% points calculation accuracy
- **Uptime:** 99%+ during test period

---

## 📅 Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Setup | 1 hour | Admin creates league |
| Onboarding | Day 1 | Testers join and build teams |
| Week 1 | Day 2 | First scorecard processing |
| Weeks 2-10 | 10 days* | Weekly cycle (accelerated) |
| Analysis | 1 week | Review and feedback |

*Can be accelerated by processing multiple "weeks" per day

---

## ✅ Ready to Launch Beta Test

**System is ready for beta testing!** 🚀

**Next Steps:**
1. Create the beta test league via admin panel
2. Generate and distribute invite codes
3. Schedule kickoff meeting with testers
4. Begin Phase 1

