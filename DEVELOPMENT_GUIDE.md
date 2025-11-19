# Development Guide

## Core Principles

### 1. Think Before You Code
**STOP. THINK. PLAN. THEN CODE.**

Before fixing any bug or adding any feature:

1. **Understand the full scope**
   - What is the root cause?
   - What other components does this affect?
   - Are there related systems that might break?

2. **Check the documentation**
   - Read `PROJECT_SCOPE.md` to understand the big picture
   - Read `DATABASE_SCHEMA.md` before touching models
   - Review `TROUBLESHOOTING.md` for known issues

3. **Verify assumptions**
   - Is production schema the same as local?
   - Do all related tests still pass?
   - Will this break existing user workflows?

4. **Plan the approach**
   - What's the minimal change needed?
   - What's the safest implementation?
   - What could go wrong?

### 2. Never Assume - Always Verify

❌ **NEVER DO THIS:**
```python
# "I assume team_id exists in production"
player.team_id = some_value
```

✅ **ALWAYS DO THIS:**
```bash
# Check production schema first
ssh ubuntu@fantcric.fun
docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d players'
```

### 3. Minimal Changes Philosophy

**The best fix is the smallest fix that solves the problem completely.**

- Don't refactor unrelated code
- Don't add "nice to have" features while fixing bugs
- Don't change working systems to match new patterns
- One commit should solve one problem

### 4. Test in Context

Don't just fix the immediate error. Test the entire user flow:

```
❌ "The API returns 200 now"
✅ "Users can create teams, add players, and see their dashboard"
```

## Database Changes - The Safe Way

### Before Changing database_models.py

1. **Document current state**
   ```bash
   # Production schema
   ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d table_name'" > prod_schema.txt

   # Local schema
   docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c '\d table_name' > local_schema.txt

   # Compare
   diff prod_schema.txt local_schema.txt
   ```

2. **Identify differences**
   - What fields are different?
   - What FK constraints differ?
   - What indexes exist in each?

3. **Decide on approach**
   - **Option A**: Change model to match production (safest)
   - **Option B**: Migrate production to match local (risky)
   - **Option C**: Make them compatible (best long-term)

### Making Model Changes

#### Step 1: Read the schema docs
```bash
cat DATABASE_SCHEMA.md
# Pay special attention to "Common Mistakes to Avoid"
```

#### Step 2: Make changes to models
```python
# database_models.py
class Player(Base):
    # Only add fields that ACTUALLY EXIST in production
    role = Column(String(50), nullable=False)  # Verified exists
```

#### Step 3: Test locally
```bash
# Start fresh containers
docker-compose down
docker-compose up -d

# Test the change
python backend/test_models.py
```

#### Step 4: Check for cascading effects
```bash
# Search for all references to the changed field
grep -r "player_type" backend/
grep -r "team_id" backend/

# Fix ALL references
```

#### Step 5: Deploy carefully
```bash
# Commit with detailed message
git add backend/database_models.py
git commit -m "Fix: Change player_type to role to match production schema

PROBLEM: SQLAlchemy was trying to query player_type but production
database has 'role' field instead.

SOLUTION: Updated Player model to use 'role' field.

VERIFIED: Checked production schema with \d players

IMPACT: No database migration needed (field already exists)"

# Push and deploy
git push origin main
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && git pull && docker-compose build fantasy_cricket_api && docker-compose up -d fantasy_cricket_api"
```

## Code Change Workflow

### For Bug Fixes

1. **Reproduce the bug**
   - Can you make it happen reliably?
   - What's the exact error message?
   - What's the user flow that triggers it?

2. **Find the root cause**
   - Don't fix symptoms, fix causes
   - Trace the error back to its source
   - Check if it's a data issue vs. code issue

3. **Write a failing test (if possible)**
   ```python
   def test_add_player_to_team():
       # This should work but currently fails
       team.add_player(player)
       assert len(team.players) == 1
   ```

4. **Fix the bug minimally**
   - Change only what's necessary
   - Don't refactor while fixing
   - Keep the diff small

5. **Verify the fix**
   - Test passes
   - User flow works end-to-end
   - No new errors in logs

6. **Check for side effects**
   - Run full test suite
   - Test related features manually
   - Check error logs after deploy

### For New Features

1. **Design first**
   - Sketch the user flow
   - Identify database changes needed
   - Plan API endpoints
   - Consider edge cases

2. **Start with data model**
   ```python
   # Add to database_models.py
   # But ONLY if you've verified the schema!
   ```

3. **Build backend API**
   ```python
   # Add endpoint in appropriate file
   # user_team_endpoints.py, admin_endpoints.py, etc.
   ```

4. **Build frontend UI**
   ```typescript
   // Add page or component
   ```

5. **Test integration**
   - Does the full flow work?
   - Are errors handled gracefully?
   - Is the UX smooth?

## Git Workflow

### Commit Messages

Use structured commit messages:

```
Type: Brief description (max 50 chars)

PROBLEM: What was broken or missing?

SOLUTION: What did you change?

VERIFIED: How did you test it?

IMPACT: What might this affect?

Optional: Breaking changes, migration steps
```

Example:
```
Fix: Player model uses 'role' instead of 'player_type'

PROBLEM: 500 errors when querying players because SQLAlchemy
model used player_type but production database has role field.

SOLUTION: Updated Player model to use role field, updated all
code references from player.player_type to player.role.

VERIFIED:
- Checked production schema with \d players
- Tested add player to team flow
- Checked admin roster page

IMPACT: Changes to database_models.py and user_team_endpoints.py

NO DATABASE MIGRATION NEEDED - field already exists in production
```

### Branch Strategy

**For this project, we use main branch directly:**

- All changes go to `main`
- Test locally before pushing
- Deploy immediately after merge
- Hotfixes also go to `main`

### Before Pushing

Checklist:
- [ ] Tests pass locally
- [ ] Code runs without errors
- [ ] Commit message is clear
- [ ] No sensitive data in commit
- [ ] Read the diff one more time

## Deployment Process

### Local Testing
```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Check logs
docker logs fantasy_cricket_api --tail 50
docker logs fantasy_cricket_frontend --tail 50

# Test the feature
curl http://localhost:8000/health
open http://localhost:3000
```

### Production Deployment
```bash
# 1. Push to GitHub
git push origin main

# 2. Pull on production
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && git pull origin main"

# 3. Rebuild affected services
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose build fantasy_cricket_api fantasy_cricket_frontend"

# 4. Restart services
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud && docker-compose up -d fantasy_cricket_api fantasy_cricket_frontend"

# 5. Verify deployment
ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_api --tail 20"

# 6. Test live site
curl https://fantcric.fun/api/health
# Open https://fantcric.fun and test manually
```

### Rollback Procedure

If something breaks:

```bash
# 1. SSH to production
ssh ubuntu@fantcric.fun "cd ~/fantasy-cricket-leafcloud"

# 2. Check last working commit
git log --oneline -10

# 3. Revert to last working commit
git reset --hard <commit-hash>

# 4. Rebuild and restart
docker-compose build fantasy_cricket_api fantasy_cricket_frontend
docker-compose up -d fantasy_cricket_api fantasy_cricket_frontend

# 5. Verify
docker logs fantasy_cricket_api --tail 20
```

## Debugging Strategies

### When You See a 500 Error

1. **Check production API logs**
   ```bash
   ssh ubuntu@fantcric.fun "docker logs fantasy_cricket_api 2>&1 | tail -100"
   ```

2. **Look for the traceback**
   - What's the exact error?
   - What line of code?
   - What's the root cause?

3. **Check if it's a schema mismatch**
   ```bash
   # Common: "column X does not exist"
   # Solution: Check DATABASE_SCHEMA.md
   ```

4. **Reproduce locally**
   - Can you make the same error happen?
   - If not, it's a production-specific issue

5. **Fix and deploy carefully**

### When Data Seems Wrong

1. **Check the database directly**
   ```bash
   ssh ubuntu@fantcric.fun "docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket"

   # Run queries
   SELECT COUNT(*) FROM players;
   SELECT * FROM players LIMIT 5;
   ```

2. **Compare with expectations**
   - Should there be 513 players? (yes)
   - Should seasons be active? (at least one)
   - Should leagues exist?

3. **Don't delete data rashly**
   - Investigate first
   - Backup before fixing
   - Consider if it's a display issue vs. data issue

## Common Patterns

### Adding an API Endpoint

```python
# In appropriate endpoints file (e.g., user_team_endpoints.py)

@router.post("/teams/{team_id}/action")
async def do_action(
    team_id: str,
    request: RequestModel,
    user: dict = Depends(verify_token),  # Auth
    db: Session = Depends(get_db)  # Database
):
    """
    Clear docstring explaining what this does
    """
    # 1. Validate user owns the resource
    team = db.query(FantasyTeam).filter_by(
        id=team_id,
        user_id=user["sub"]
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 2. Validate request data
    if request.value < 0:
        raise HTTPException(status_code=400, detail="Invalid value")

    # 3. Perform action
    team.some_field = request.value
    db.commit()

    # 4. Return response
    return {
        "message": "Success",
        "data": {
            "team_id": team.id,
            "updated_field": team.some_field
        }
    }
```

### Adding a Frontend Page

```typescript
// app/new-feature/page.tsx

'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';

export default function NewFeaturePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getData();
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {/* Your UI here */}
    </div>
  );
}
```

## Performance Considerations

### Database Queries

```python
# ❌ N+1 queries
for team in teams:
    print(team.league.name)  # Queries database each time

# ✅ Eager loading
teams = db.query(FantasyTeam).options(
    joinedload(FantasyTeam.league)
).all()
for team in teams:
    print(team.league.name)  # No extra queries
```

### API Response Size

```python
# ❌ Returning too much data
return {
    "players": [
        {"id": p.id, "name": p.name, "stats": p.full_stats, "history": p.history}
        for p in all_513_players
    ]
}

# ✅ Return only what's needed
return {
    "players": [
        {"id": p.id, "name": p.name, "role": p.role, "price": p.current_price}
        for p in players[:50]  # Paginate
    ],
    "total": total_count,
    "page": page_number
}
```

## Security Checklist

- [ ] All endpoints check user authentication
- [ ] Users can only access their own resources
- [ ] Admin endpoints check `is_admin` flag
- [ ] No SQL injection vulnerabilities (use SQLAlchemy properly)
- [ ] No sensitive data in logs or error messages
- [ ] Passwords are hashed (never plain text)
- [ ] JWT tokens are validated

## Code Quality Standards

### Python (Backend)
- Use type hints
- Document complex functions
- Keep functions short and focused
- Use meaningful variable names
- Follow PEP 8 style guide

### TypeScript (Frontend)
- Use TypeScript strictly (no `any` types)
- Use functional components with hooks
- Keep components small and reusable
- Use proper error handling
- Follow React best practices

## When Things Go Wrong

### Stay Calm and Systematic

1. **Don't panic** - You can always rollback
2. **Don't guess** - Check logs and data
3. **Don't rush** - Think through the fix
4. **Don't stack fixes** - One problem at a time
5. **Don't hide issues** - Document what broke and why

### Recovery Steps

1. Check if site is down → rollback immediately
2. Check if data is corrupted → restore from backup
3. Check if it's a display bug → fix can wait
4. Check if users are affected → prioritize fix
5. Check if it's a minor issue → fix in next deploy

## Documentation Maintenance

**Keep these docs updated:**

- `PROJECT_SCOPE.md` - When adding major features
- `DATABASE_SCHEMA.md` - When schema changes
- `DEVELOPMENT_GUIDE.md` - When finding new patterns
- `TROUBLESHOOTING.md` - When solving new issues

**Good documentation = fewer mistakes = faster development**

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Questions to Ask Before Coding

1. Have I read the relevant documentation?
2. Do I understand the full scope?
3. Have I checked the production schema?
4. What could this break?
5. Is there a simpler solution?
6. How will I test this?
7. What happens if this fails?
8. Have I thought about edge cases?

**If you can't answer all 8 questions, you're not ready to code yet.**
