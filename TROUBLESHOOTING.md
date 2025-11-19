# Troubleshooting Guide

## Common Issues and Solutions

### Database and Schema Issues

#### Issue: "column players.team_id does not exist"

**Cause**: SQLAlchemy model references a field that doesn't exist in production database.

**Solution**:
1. Check production schema:
   ```bash
   ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d players'"
   ```

2. Update `database_models.py` to match production:
   ```python
   # Remove:
   team_id = Column(String(50), ForeignKey("teams.id"))

   # If the code uses team_id, refactor to use rl_team (string) instead
   ```

3. Search for all references:
   ```bash
   grep -r "team_id" backend/
   ```

4. Update or comment out code that uses the missing field.

**Prevention**: Always check `DATABASE_SCHEMA.md` before modifying models.

---

#### Issue: "column players.player_type does not exist"

**Cause**: Production uses `role` field, not `player_type`.

**Solution**:
1. Update model to use `role`:
   ```python
   role = Column(String(50), nullable=False)  # NOT player_type
   ```

2. Update all code references:
   ```python
   # Change from:
   if player.player_type == 'batsman':

   # To:
   if player.role == 'batsman':
   ```

**Prevention**: Check production schema. Production has `playerrole` enum with values: `BATSMAN`, `BOWLER`, `ALL_ROUNDER`, `WICKET_KEEPER`.

---

#### Issue: "AttributeError: 'Player' object has no attribute 'team'"

**Cause**: Code tries to access `player.team` relationship, but it doesn't exist (no `team_id` FK).

**Solution**:
1. Remove the relationship from model:
   ```python
   # Remove this line:
   team = relationship("Team", foreign_keys=[team_id])
   ```

2. Update code that uses it:
   ```python
   # Change from:
   team_name = player.team.name

   # To:
   team_name = player.rl_team  # String field, not relationship
   ```

**Prevention**: Only define relationships where FK constraints exist.

---

#### Issue: "No players showing in roster" or "Player count is 0"

**Cause**: Using wrong club_id.

**Solution**:
1. Check the correct ACC club ID:
   ```bash
   ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c \"SELECT id, name FROM clubs WHERE name = 'ACC';\""
   ```

2. Production club ID is: `a7a580a7-7d3f-476c-82ea-afa6ae7ee276`

3. Update code to use correct ID:
   ```typescript
   const CLUB_ID = 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276';
   ```

**Prevention**: Document the club ID in code comments and use constants.

---

### API and Backend Issues

#### Issue: 500 Internal Server Error

**Diagnosis Steps**:
1. Check production API logs:
   ```bash
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_api 2>&1 | tail -100"
   ```

2. Look for the exception traceback
3. Identify the exact error line
4. Check if it's a schema mismatch (see above)

**Common Causes**:
- Database schema mismatch
- Missing environment variables
- Null pointer errors
- Invalid foreign keys

**Solution Template**:
1. Identify root cause from logs
2. Check if it's in `database_models.py`
3. Verify production schema matches model
4. Fix the model or code
5. Test locally
6. Deploy carefully

---

#### Issue: "404 Not Found" on API endpoint

**Cause**: Endpoint doesn't exist or wrong route.

**Solution**:
1. Check if endpoint exists in backend:
   ```bash
   grep -r "@router.delete.*teams" backend/
   ```

2. If missing, add the endpoint:
   ```python
   @router.delete("/teams/{team_id}")
   async def delete_team(team_id: str, ...):
       # Implementation
   ```

3. Make sure router is included in `main.py`:
   ```python
   app.include_router(admin_router, prefix="/api/admin")
   ```

4. Rebuild and restart:
   ```bash
   docker-compose build fantasy_cricket_api
   docker-compose up -d fantasy_cricket_api
   ```

---

#### Issue: Authentication errors or "Invalid token"

**Diagnosis**:
```bash
# Check if JWT secret is set
docker exec fantasy_cricket_api env | grep JWT_SECRET
```

**Solution**:
1. Ensure `.env` file exists with JWT_SECRET
2. Restart API to pick up environment variable
3. Clear browser cookies and login again

---

### Frontend Issues

#### Issue: "Failed to fetch" or CORS errors

**Cause**: Frontend can't reach backend API.

**Solution**:
1. Check if API is running:
   ```bash
   curl http://localhost:8000/health  # Local
   curl https://fantcric.fun/api/health  # Production
   ```

2. Check CORS settings in `main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Or specific domains
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. Check API client base URL:
   ```typescript
   // lib/api.ts
   const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
   ```

---

#### Issue: Changes not appearing after deploy

**Cause**: Browser cache or build not updated.

**Solution**:
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Try incognito/private browsing
4. Verify the build actually ran:
   ```bash
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_frontend 2>&1 | grep 'npm run build'"
   ```

5. If build didn't run, rebuild:
   ```bash
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose build fantasy_cricket_frontend && docker-compose up -d fantasy_cricket_frontend"
   ```

---

### Docker and Deployment Issues

#### Issue: Container won't start

**Diagnosis**:
```bash
docker ps -a  # See all containers
docker logs <container_name>  # Check logs
```

**Common Causes**:
- Port already in use
- Build failed
- Missing dependencies
- Database connection failed

**Solution**:
```bash
# Stop all containers
docker-compose down

# Remove old containers
docker-compose rm -f

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d

# Check status
docker-compose ps
docker logs fantasy_cricket_api --tail 50
```

---

#### Issue: Database connection failed

**Diagnosis**:
```bash
# Check if database container is running
docker ps | grep fantasy_cricket_db

# Try connecting manually
docker exec -it fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket
```

**Solution**:
1. Ensure database container is running
2. Check environment variables:
   ```bash
   docker exec fantasy_cricket_api env | grep DB
   ```

3. Verify connection string in code
4. Check network connectivity between containers

---

### Data Issues

#### Issue: "No active season" or "Seasons show as inactive"

**Diagnosis**:
```bash
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c 'SELECT id, name, is_active FROM seasons;'"
```

**Solution**:
1. If seasons exist but all inactive, activate one:
   ```sql
   UPDATE seasons SET is_active = true WHERE id = '<season_id>';
   ```

2. If no seasons exist, create one via admin console:
   - Login as admin
   - Go to /admin/seasons
   - Click "Create Season"

---

#### Issue: "Step 4 not lighting up" in admin console

**Cause**: Missing leagues or players.

**Diagnosis**:
```bash
# Check leagues
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c 'SELECT COUNT(*) FROM leagues;'"

# Check players
ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c 'SELECT COUNT(*) FROM players;'"
```

**Solution**:
Step 4 requires BOTH:
- At least 1 league (create via /admin/leagues)
- At least 1 player (should be 513)

Check admin page logic in `frontend/app/admin/page.tsx:190`:
```typescript
const step4Disabled = stats.leagues_count === 0 || stats.players_count === 0;
```

---

### Performance Issues

#### Issue: Slow page loads

**Diagnosis**:
1. Check network tab in browser DevTools
2. Look for slow API calls
3. Check database query performance

**Solutions**:
- Add database indexes
- Use eager loading for relationships
- Implement pagination for large datasets
- Add caching where appropriate

---

#### Issue: High memory usage

**Diagnosis**:
```bash
docker stats
```

**Solutions**:
- Limit container resources in `docker-compose.yml`
- Optimize database queries (avoid loading all 513 players at once)
- Add pagination
- Clear unused data

---

## Emergency Procedures

### Site is Down

1. **Check if containers are running**:
   ```bash
   ssh ubuntu@fantcric.fun "docker ps"
   ```

2. **Restart all services**:
   ```bash
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose restart"
   ```

3. **If still down, check logs**:
   ```bash
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_api --tail 100"
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_frontend --tail 100"
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_db --tail 100"
   ```

4. **Last resort - full restart**:
   ```bash
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose down && docker-compose up -d"
   ```

---

### Data Corruption

1. **STOP - Don't make it worse**
2. **Assess damage**:
   ```bash
   ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket"
   # Run SELECT queries to see what data exists
   ```

3. **If you have backup**:
   ```bash
   # Restore from backup
   docker exec -i fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket < backup.sql
   ```

4. **If no backup**:
   - Document what's broken
   - Try to recover data from logs
   - Worst case: re-import player data from CSV

---

### Bad Deploy

1. **Rollback immediately**:
   ```bash
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && git log --oneline -5"
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && git reset --hard <last_working_commit>"
   ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose build && docker-compose up -d"
   ```

2. **Verify rollback worked**:
   ```bash
   curl https://fantcric.fun/api/health
   # Test critical user flows
   ```

3. **Fix the issue locally** before redeploying

---

## Debugging Checklist

When something breaks:

- [ ] Read the error message completely
- [ ] Check the logs (don't guess)
- [ ] Verify assumptions (check schema, check data)
- [ ] Reproduce locally if possible
- [ ] Check recent changes (git log)
- [ ] Search this troubleshooting guide
- [ ] Check DATABASE_SCHEMA.md
- [ ] Test the fix thoroughly
- [ ] Deploy carefully
- [ ] Verify the fix works in production
- [ ] Document the issue (add to this file if new)

## Prevention > Cure

**How to avoid issues**:

1. ✅ Read documentation before coding
2. ✅ Check production schema before model changes
3. ✅ Test locally before deploying
4. ✅ Make small, focused changes
5. ✅ Review diffs before committing
6. ✅ Test in production after deploying
7. ✅ Monitor logs after changes
8. ✅ Document new issues in this file

## Getting Help

If you're stuck:

1. Read `PROJECT_SCOPE.md` for context
2. Read `DATABASE_SCHEMA.md` for schema info
3. Read `DEVELOPMENT_GUIDE.md` for patterns
4. Check logs for errors
5. Search this troubleshooting guide
6. Check GitHub issues
7. Document what you tried

## Known Limitations

- Team-based validation disabled (no team_id in production)
- Max players per team rules not enforced
- Require from each team rules not enforced
- Player statistics require manual entry (no web scraping yet)
- No live score updates during matches

These are by design due to schema constraints. Don't try to "fix" them without schema migration.
