# 🚨 CLAUDE: READ THIS FIRST - EVERY TIME

## Critical Context File
**Purpose**: This file MUST be read whenever:
- Context is compacted/reset
- Starting a new session
- About to make ANY production change
- User asks about deployment
- User asks about the system architecture

---

## 🎯 PRODUCTION ENVIRONMENT - MEMORIZE THIS

```
Production URL: https://fantcric.fun (NOT koffieeneenpeuk.online, NOT localhost)
SSH Access: ssh ubuntu@fantcric.fun
Project Path: ~/fantasy-cricket-leafcloud
Docker Compose: ~/fantasy-cricket-leafcloud/docker-compose.yml
```

**NEVER**:
- Deploy to koffieeneenpeuk.online
- Use 45.135.59.210 IP (that's the wrong server)
- Use `docker rm -f` on production
- Skip reading documentation before deployment

---

## 📚 MANDATORY READING ORDER

Before ANY production work, read these files in this exact order:

### 1. TROUBLESHOOTING.md (Lines 233-312)
**Why**: Documents 502 Bad Gateway issues, dangerous docker commands
**Key Info**:
- NEVER use `docker rm -f` + `docker-compose up` (breaks networking)
- ALWAYS restart nginx after container changes
- Safe deployment commands

### 2. ADMIN_WEEKLY_PROCEDURES.md (Lines 34-42)
**Why**: Contains correct production server info
**Key Info**:
- `ssh ubuntu@fantcric.fun` (correct)
- Weekly maintenance procedures
- Troubleshooting steps

### 3. DOCUMENTATION_AUDIT_AND_DEPLOYMENT_RULES.md
**Why**: Master reference for deployment safety
**Key Info**:
- All deployment rules in one place
- Deployment command reference card
- Pre-deployment checklist

### 4. QUICK_REFERENCE.md
**Why**: System architecture overview
**Key Info**:
- Database relationships
- League → Match → Performance linkage
- Admin endpoints

### 5. LEAGUE_ARCHITECTURE_ANALYSIS.md
**Why**: Deep dive into database schema
**Key Info**:
- League-specific multipliers
- Table relationships
- Missing fields

---

## ⛔ NEVER DO THIS ON PRODUCTION

```bash
# ❌ WRONG - Breaks container networking
docker rm -f fantasy_cricket_api
docker rm -f fantasy_cricket_frontend
docker-compose up -d --no-deps <service>

# ❌ WRONG - Server addresses
ssh ubuntu@45.135.59.210
ssh ubuntu@koffieeneenpeuk.online

# ❌ WRONG - URLs
https://koffieeneenpeuk.online
http://localhost:8000 (in production code)
```

---

## ✅ ALWAYS DO THIS ON PRODUCTION

```bash
# ✅ CORRECT - Safe deployment workflow
ssh ubuntu@fantcric.fun
cd ~/fantasy-cricket-leafcloud
git pull origin main

# Frontend changes (simple)
docker-compose restart fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# Frontend changes (rebuild)
docker-compose up -d --build fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# Backend changes
docker-compose up -d --build fantasy_cricket_api
docker-compose restart fantasy_cricket_nginx

# Verify
curl https://fantcric.fun/api/health
# Browser check with hard refresh (Ctrl+Shift+R)
```

---

## 🧠 SYSTEM ARCHITECTURE (Essential Context)

### Database Structure
```
SEASON (1 active)
  └─ CLUB (e.g., ACC)
      └─ PLAYER (513 total)
          ├─ multiplier: 0.69-5.0
          ├─ rl_team: "ACC 1" (STRING, not FK)
          └─ role: BATSMAN|BOWLER|ALL_ROUNDER|WICKET_KEEPER

LEAGUE (competition)
  ├─ season_id, club_id (FK)
  ├─ status: draft|active|locked|completed
  ├─ multipliers_snapshot (JSON, league-specific)
  └─ LeagueRoster (available players)
      └─ FantasyTeam (user's team)
          ├─ captain_id, vice_captain_id
          └─ FantasyTeamPlayer (junction)

MATCH (season_id, club_id)
  └─ PlayerPerformance
      ├─ base_fantasy_points
      ├─ multiplier_applied (league-specific!)
      ├─ final_fantasy_points
      └─ league_id, round_number
```

### Key Insight: League-Specific Multipliers
- Each league has its OWN multipliers (stored in `League.multipliers_snapshot`)
- Same player can have DIFFERENT multipliers in different leagues
- Multipliers drift weekly (15%) based on performance within each league
- Weekly task: `adjust_multipliers_weekly()` runs every Monday 2 AM

---

## 📋 PRE-DEPLOYMENT CHECKLIST (MANDATORY)

Before EVERY deployment:

### Research Phase
- [ ] Read TROUBLESHOOTING.md (lines 233-312)
- [ ] Read ADMIN_WEEKLY_PROCEDURES.md
- [ ] Read DOCUMENTATION_AUDIT_AND_DEPLOYMENT_RULES.md
- [ ] Verify production URL: fantcric.fun

### Validation Phase
- [ ] Test locally if possible
- [ ] Review `git diff` before committing
- [ ] Check for build/TypeScript errors
- [ ] Verify no hardcoded localhost URLs

### Execution Phase
- [ ] SSH to correct server: `ssh ubuntu@fantcric.fun`
- [ ] Navigate to project: `cd ~/fantasy-cricket-leafcloud`
- [ ] Pull code: `git pull origin main`
- [ ] Use ONLY safe docker-compose commands
- [ ] ALWAYS restart nginx after container changes

### Verification Phase
- [ ] Check API health: `curl https://fantcric.fun/api/health`
- [ ] Test affected functionality in browser
- [ ] Check for 502 errors
- [ ] Monitor logs: `docker logs fantasy_cricket_api --tail 100`

---

## 🚨 COMMON MISTAKES TO AVOID

### Mistake #1: Wrong Server
**What**: Deploying to 45.135.59.210 or koffieeneenpeuk.online
**Why Wrong**: That's the wrong server
**Correct**: SSH to fantcric.fun

### Mistake #2: Dangerous Docker Commands
**What**: Using `docker rm -f` + `docker-compose up`
**Why Wrong**: Breaks container networking, causes 502 errors
**Correct**: Use `docker-compose up -d --build`

### Mistake #3: Forgetting Nginx Restart
**What**: Not restarting nginx after container recreation
**Why Wrong**: Nginx caches old container IPs, causes 502 errors
**Correct**: ALWAYS run `docker-compose restart fantasy_cricket_nginx`

### Mistake #4: Not Reading Documentation
**What**: Making changes without reading docs first
**Why Wrong**: Repeat preventable mistakes
**Correct**: ALWAYS read mandatory files FIRST

---

## 📖 QUICK REFERENCE: FILE PURPOSES

| File | When to Read | Key Info |
|------|--------------|----------|
| **CLAUDE_START_HERE.md** | EVERY session start | This file |
| **TROUBLESHOOTING.md** | Before deployment | 502 errors, safe commands |
| **ADMIN_WEEKLY_PROCEDURES.md** | Before admin tasks | Production server, procedures |
| **DOCUMENTATION_AUDIT_AND_DEPLOYMENT_RULES.md** | Before deployment | Complete deployment guide |
| **QUICK_REFERENCE.md** | Understanding system | Architecture overview |
| **LEAGUE_ARCHITECTURE_ANALYSIS.md** | Database questions | Schema details |
| **LEAGUE_MULTIPLIERS.md** | Multiplier questions | How multipliers work |
| **SEASON_SETUP_GUIDE.md** | Setup questions | League lifecycle |
| **FANTASY_POINTS_RULES.md** | Points questions | Scoring rules |

---

## 🔄 CONTEXT RECOVERY PROTOCOL

If you find yourself:
- Not knowing the production URL
- About to use `docker rm -f`
- Unsure which server to deploy to
- Making changes without reading docs

**STOP** and:
1. Read this file (CLAUDE_START_HERE.md)
2. Read TROUBLESHOOTING.md (lines 233-312)
3. Read DOCUMENTATION_AUDIT_AND_DEPLOYMENT_RULES.md
4. Verify you understand production URL and safe commands
5. Then proceed with caution

---

## 💡 LEARNING FROM PAST MISTAKES

### Session 2025-01-19: Deployment Errors
**Mistakes Made**:
1. ❌ Deployed to wrong server (koffieeneenpeuk.online)
2. ❌ Did not read documentation first
3. ❌ Attempted rebuild when restart sufficient

**Lessons**:
1. ✅ ALWAYS verify production URL from docs
2. ✅ ALWAYS read mandatory files FIRST
3. ✅ Use safe docker-compose commands ONLY

**Result**: Eventually corrected, no data loss, system working

---

## 🎯 CURRENT PROJECT STATUS

### Completed Work
- ✅ League-specific multiplier system (backend)
- ✅ Weekly multiplier drift task
- ✅ League confirmation endpoint
- ✅ Admin UI for league management (Phase 1 & 3)

### Deployed to Production
- ✅ Frontend changes (admin dashboard, league management)
- ✅ Deployed to fantcric.fun (correct server)
- ✅ Container restarted successfully

### Pending Work
- ⏳ Phase 2: League Detail/Status Page
- ⏳ Phase 4: Remove/Update Old Roster Confirmation
- ⏳ Phase 5: Add Confirmation Dialogs & Feedback

---

## 🎓 DEPLOYMENT COMMAND CHEAT SHEET

Keep this visible during ALL production work:

```bash
# ===== CONNECT =====
ssh ubuntu@fantcric.fun
cd ~/fantasy-cricket-leafcloud

# ===== DEPLOY FRONTEND (simple) =====
git pull origin main
docker-compose restart fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# ===== DEPLOY FRONTEND (rebuild) =====
git pull origin main
docker-compose up -d --build fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# ===== DEPLOY BACKEND =====
git pull origin main
docker-compose up -d --build fantasy_cricket_api
docker-compose restart fantasy_cricket_nginx

# ===== CHECK HEALTH =====
curl https://fantcric.fun/api/health
docker logs fantasy_cricket_api --tail 100
docker logs fantasy_cricket_nginx --tail 50

# ===== ROLLBACK =====
git reset --hard <commit_hash>
docker-compose up -d --build <service>
docker-compose restart fantasy_cricket_nginx
```

---

## ⚡ EMERGENCY PROCEDURES

### Site is Down (502 Error)
1. Check nginx is connected to containers:
   ```bash
   docker network connect fantasy-cricket-leafcloud_cricket_network fantasy_cricket_api
   ```
2. Restart nginx:
   ```bash
   docker-compose restart fantasy_cricket_nginx
   ```
3. Check logs:
   ```bash
   docker logs fantasy_cricket_nginx --tail 50
   ```

### Bad Deployment
1. Note current commit: `git log --oneline -1`
2. Rollback: `git reset --hard <last_working_commit>`
3. Rebuild: `docker-compose up -d --build <service>`
4. Restart nginx: `docker-compose restart fantasy_cricket_nginx`
5. Verify: `curl https://fantcric.fun/api/health`

---

## 🎯 REMEMBER

1. **Production URL**: fantcric.fun (NOT koffieeneenpeuk.online)
2. **Read docs FIRST** (this file + TROUBLESHOOTING.md + ADMIN_WEEKLY_PROCEDURES.md)
3. **Safe commands ONLY** (no `docker rm -f`)
4. **Always restart nginx** after container changes
5. **Verify deployment** with health check and browser test

---

**Last Updated**: 2025-01-19
**Purpose**: Prevent context loss and deployment mistakes
**Priority**: CRITICAL - Read at EVERY session start

---

## 📝 SELF-CHECK BEFORE ANY WORK

Ask yourself:
- [ ] Have I read this file?
- [ ] Have I read TROUBLESHOOTING.md?
- [ ] Do I know the production URL? (fantcric.fun)
- [ ] Do I know the safe docker commands?
- [ ] Am I about to use `docker rm -f`? (STOP if yes)
- [ ] Will I restart nginx after container changes?

If ANY answer is "no" or "unsure", READ THE DOCS FIRST.

---

**THIS FILE EXISTS TO PREVENT MISTAKES. READ IT. FOLLOW IT. EVERY TIME.**
