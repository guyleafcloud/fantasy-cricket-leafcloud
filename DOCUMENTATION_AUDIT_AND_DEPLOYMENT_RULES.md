# Documentation Audit & Deployment Safety Rules

## 🚨 CRITICAL DEPLOYMENT RULES

### Rule #1: ALWAYS Read Documentation FIRST
Before ANY deployment or production change:
1. ✅ Read TROUBLESHOOTING.md (deployment issues section)
2. ✅ Read ADMIN_WEEKLY_PROCEDURES.md (production procedures)
3. ✅ Read QUICK_REFERENCE.md (system architecture)
4. ✅ Verify production URLs and server information

### Rule #2: Production Server Information
- **Production URL**: https://fantcric.fun (NOT koffieeneenpeuk.online)
- **SSH Access**: `ssh ubuntu@fantcric.fun`
- **Project Path**: `~/fantasy-cricket-leafcloud`
- **Docker Compose Path**: `~/fantasy-cricket-leafcloud/docker-compose.yml`

### Rule #3: NEVER Use Dangerous Docker Commands
```bash
# ❌ WRONG - Breaks networking, causes 502 errors
docker rm -f fantasy_cricket_api && docker-compose up -d --no-deps fantasy_cricket_api
docker rm -f fantasy_cricket_frontend && docker-compose up -d fantasy_cricket_frontend

# ✅ CORRECT - Preserves networks and configurations
cd ~/fantasy-cricket-leafcloud
docker-compose up -d --build fantasy_cricket_api
docker-compose up -d --build fantasy_cricket_frontend

# ✅ ALSO CORRECT - Proper compose workflow
docker-compose stop fantasy_cricket_api
docker-compose build fantasy_cricket_api
docker-compose up -d fantasy_cricket_api
```

**Why**: Using `docker rm -f` removes containers from their networks, causing nginx to lose connectivity (502 Bad Gateway errors).

### Rule #4: Always Restart Nginx After Container Recreation
```bash
# After recreating API or frontend containers
docker-compose restart fantasy_cricket_nginx
```

**Why**: Nginx caches DNS lookups. When containers get new IPs, nginx keeps trying old IPs causing 502 errors.

### Rule #5: Deployment Workflow (Frontend Changes)
```bash
# 1. SSH to production
ssh ubuntu@fantcric.fun

# 2. Navigate to project
cd ~/fantasy-cricket-leafcloud

# 3. Pull latest code
git pull origin main

# 4. Option A: Restart only (if no build needed)
docker-compose restart fantasy_cricket_frontend

# 5. Option B: Rebuild (if dependencies changed)
docker-compose up -d --build fantasy_cricket_frontend

# 6. ALWAYS restart nginx after container changes
docker-compose restart fantasy_cricket_nginx

# 7. Verify deployment
curl https://fantcric.fun/api/health
# Check website in browser with hard refresh (Ctrl+Shift+R)
```

### Rule #6: Deployment Workflow (Backend Changes)
```bash
# 1. SSH to production
ssh ubuntu@fantcric.fun

# 2. Navigate to project
cd ~/fantasy-cricket-leafcloud

# 3. Pull latest code
git pull origin main

# 4. Rebuild API container
docker-compose up -d --build fantasy_cricket_api

# 5. ALWAYS restart nginx
docker-compose restart fantasy_cricket_nginx

# 6. Check logs for errors
docker logs fantasy_cricket_api --tail 100

# 7. Verify API health
curl https://fantcric.fun/api/health
```

## 📋 PERCEIVED INACCURACIES IN DOCUMENTATION

### 1. DEPLOYMENT_COMPLETE.md
**Inaccuracy**: References localhost URLs and local deployment
```markdown
# Deploy in 3 Steps
./deploy.sh
```

**Reality**: Production is on fantcric.fun, not localhost. No `deploy.sh` script exists in project root.

**Recommendation**: Update to reference actual production deployment workflow.

---

### 2. ADMIN_WEEKLY_PROCEDURES.md
**Status**: ✅ ACCURATE
- Correctly references `ssh ubuntu@fantcric.fun`
- Correctly references production procedures
- Good troubleshooting steps

**Note**: This is one of the few files with CORRECT production information.

---

### 3. TROUBLESHOOTING.md
**Status**: ✅ MOSTLY ACCURATE
- Correctly documents 502 Bad Gateway issue
- Correctly warns against `docker rm -f` + `docker-compose up`
- Correctly references fantcric.fun

**Minor Issue**: Some examples still show localhost URLs for local testing, but correctly labeled as local.

---

### 4. BUILD_AND_DEPLOY.md (backend/)
**Inaccuracy**: Focuses on initial setup, not ongoing deployment
- References Dockerfile changes that are already done
- References docker-compose.yml changes that are already done
- No mention of production server

**Reality**: System is already deployed. Need ongoing deployment procedures, not initial setup.

**Recommendation**: Create PRODUCTION_DEPLOYMENT_GUIDE.md for ongoing deployments.

---

### 5. QUICK_REFERENCE.md
**Inaccuracy**: References missing database fields
```markdown
League.status field (MISSING - should be draft|active|locked|completed)
```

**Reality**: Need to verify if this field exists now. If not, document as TODO.

**Inaccuracy**: References localhost
```markdown
curl http://localhost:8000/health
```

**Recommendation**: Add production examples:
```bash
curl https://fantcric.fun/api/health  # Production
curl http://localhost:8000/health     # Local dev
```

---

### 6. General Issue: Multiple Outdated Markdown Files
Many .md files in root and backend/ reference:
- Old architecture
- Localhost-only examples
- Initial setup procedures
- Missing features that may now exist

**Recommendation**: Create a DOCUMENTATION_STATUS.md that marks each file as:
- ✅ Current and accurate
- ⚠️ Partially outdated
- ❌ Superseded / archived

---

## 🎯 MANDATORY PRE-DEPLOYMENT CHECKLIST

Before EVERY deployment to production, Claude MUST:

### Phase 1: Research (MANDATORY)
- [ ] Read TROUBLESHOOTING.md sections 280-312 (502 Bad Gateway issues)
- [ ] Read ADMIN_WEEKLY_PROCEDURES.md for production procedures
- [ ] Verify production URL is fantcric.fun (NOT koffieeneenpeuk.online)
- [ ] Verify SSH access: `ssh ubuntu@fantcric.fun`

### Phase 2: Pre-Deployment Validation (MANDATORY)
- [ ] Test changes locally if possible
- [ ] Review git diff before committing
- [ ] Check for TypeScript/build errors
- [ ] Verify no hardcoded localhost URLs in new code

### Phase 3: Deployment Execution (MANDATORY)
- [ ] Use ONLY approved docker-compose commands (see Rule #3)
- [ ] NEVER use `docker rm -f` on production
- [ ] ALWAYS restart nginx after container changes
- [ ] Check logs immediately after deployment

### Phase 4: Post-Deployment Verification (MANDATORY)
- [ ] Verify API health: `curl https://fantcric.fun/api/health`
- [ ] Test affected endpoints
- [ ] Check for 502 errors
- [ ] Monitor logs for 2-3 minutes

### Phase 5: Rollback Plan (MANDATORY)
- [ ] Know the last working commit hash
- [ ] Have rollback commands ready:
  ```bash
  cd ~/fantasy-cricket-leafcloud
  git reset --hard <last_working_commit>
  docker-compose up -d --build fantasy_cricket_frontend
  docker-compose restart fantasy_cricket_nginx
  ```

---

## 🔍 SPECIFIC ISSUES IDENTIFIED IN CURRENT SESSION

### Issue #1: Deployed to Wrong Server
**What Happened**: Initially deployed to 45.135.59.210 (koffieeneenpeuk.online) instead of fantcric.fun

**Root Cause**: Did not read ADMIN_WEEKLY_PROCEDURES.md first

**Prevention**: ALWAYS verify production URL from documentation before deployment

---

### Issue #2: Build Error Not Anticipated
**What Happened**: TypeScript build failed with PlayerComparisonModal import error

**Root Cause**: Attempted to rebuild without checking if build was necessary

**Prevention**:
- For simple code changes, restart container first (no rebuild)
- Only rebuild if dependencies changed
- Check for TypeScript errors before pushing

---

### Issue #3: Deployment Approach
**What Happened**: Restarted container instead of rebuilding after code change

**Outcome**: Actually worked because changes were simple UI updates

**Best Practice**:
- Simple React/Next.js component changes: Restart is often sufficient (Next.js hot reload in production)
- Dependency changes: Rebuild required
- Backend changes: Rebuild usually required

---

## 📚 DOCUMENTATION HIERARCHY (Priority Order)

When Claude needs deployment information, read in this order:

1. **TROUBLESHOOTING.md** (lines 233-312) - 502 errors, deployment issues
2. **ADMIN_WEEKLY_PROCEDURES.md** (lines 34-42) - Production server info
3. **QUICK_REFERENCE.md** - System architecture overview
4. **LEAGUE_ARCHITECTURE_ANALYSIS.md** - Database relationships
5. **BUILD_AND_DEPLOY.md** - Initial setup (less relevant for ongoing work)

---

## ✅ RECOMMENDED DOCUMENTATION IMPROVEMENTS

### 1. Create PRODUCTION_DEPLOYMENT_GUIDE.md
Should contain:
- Production server details (fantcric.fun)
- SSH access procedures
- Safe docker-compose commands
- Deployment workflows for frontend/backend
- Post-deployment verification steps
- Rollback procedures

### 2. Update QUICK_REFERENCE.md
Add sections:
- Production vs Local URLs
- Common deployment commands
- Quick troubleshooting for 502 errors

### 3. Create DOCUMENTATION_STATUS.md
List all .md files with:
- Current status (accurate/outdated/archived)
- Last verified date
- Primary audience (dev/admin/ops)

### 4. Archive Old Guides
Move to `/docs/archive/`:
- DEPLOYMENT_COMPLETE.md (initial setup, not ongoing)
- BUILD_AND_DEPLOY.md (superseded by actual deployment)
- Various session summaries (historical)

---

## 🎓 LEARNING FROM THIS SESSION

### What Went Wrong
1. ❌ Deployed to wrong server (koffieeneenpeuk.online vs fantcric.fun)
2. ❌ Did not read documentation first
3. ❌ Attempted rebuild when restart was sufficient
4. ✅ Eventually corrected and deployed successfully

### What Went Right
1. ✅ Committed changes to git before deployment
2. ✅ Verified deployment after correction
3. ✅ Used safe docker-compose restart command

### Improvements for Future
1. **ALWAYS** read TROUBLESHOOTING.md and ADMIN_WEEKLY_PROCEDURES.md FIRST
2. **ALWAYS** verify production URL from documentation
3. **ALWAYS** use approved docker-compose commands (no `docker rm -f`)
4. **ALWAYS** restart nginx after container changes
5. **ALWAYS** verify deployment with health check and browser test

---

## 🚀 DEPLOYMENT COMMAND REFERENCE CARD

Keep this visible during ANY production work:

```bash
# ===== PRODUCTION INFO =====
Production URL: https://fantcric.fun
SSH: ssh ubuntu@fantcric.fun
Path: ~/fantasy-cricket-leafcloud

# ===== SAFE DEPLOYMENT =====
# Frontend changes (simple)
git pull origin main
docker-compose restart fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# Frontend changes (with rebuild)
git pull origin main
docker-compose up -d --build fantasy_cricket_frontend
docker-compose restart fantasy_cricket_nginx

# Backend changes
git pull origin main
docker-compose up -d --build fantasy_cricket_api
docker-compose restart fantasy_cricket_nginx

# ===== VERIFICATION =====
curl https://fantcric.fun/api/health
# Check website with hard refresh (Ctrl+Shift+R)

# ===== LOGS =====
docker logs fantasy_cricket_api --tail 100
docker logs fantasy_cricket_frontend --tail 100
docker logs fantasy_cricket_nginx --tail 50

# ===== NEVER USE =====
# ❌ docker rm -f <container>
# ❌ docker-compose up -d --no-deps
```

---

## 📝 FINAL CHECKLIST FOR CLAUDE

Before ANY production deployment, Claude MUST:

1. [ ] Read TROUBLESHOOTING.md (deployment sections)
2. [ ] Read ADMIN_WEEKLY_PROCEDURES.md (production info)
3. [ ] Verify production URL is fantcric.fun
4. [ ] Use ONLY safe docker-compose commands
5. [ ] ALWAYS restart nginx after container changes
6. [ ] Verify deployment with health check
7. [ ] Monitor logs for 2-3 minutes after deployment

---

**Last Updated**: 2025-01-19
**Status**: Living document - update after each deployment lesson
**Priority**: CRITICAL - Read before EVERY production change
