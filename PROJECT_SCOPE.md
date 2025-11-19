# Fantasy Cricket - Project Scope

## Overview
A fantasy cricket game for ACC (Amsterdam Cricket Club) where users create fantasy teams from real ACC players and compete in leagues based on actual match performance.

## Core Concept
- **Real Players**: All players are from ACC's actual roster (513 players)
- **Fantasy Teams**: Users build teams within budget and squad constraints
- **Scoring**: Points awarded based on real match statistics (runs, wickets, catches, etc.)
- **Leagues**: Users compete in private or public leagues
- **Admin Tools**: Comprehensive admin console for managing seasons, leagues, and players

## Tech Stack
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLAlchemy ORM
- **Database**: PostgreSQL
- **Deployment**: Docker Compose on Ubuntu VPS
- **Domain**: https://fantcric.fun

## Architecture

### Frontend (`/frontend`)
- Next.js app with App Router
- Pages:
  - `/login`, `/register` - Authentication
  - `/dashboard` - User dashboard
  - `/teams` - User's fantasy teams
  - `/teams/[team_id]/build` - Team building interface
  - `/leagues` - Browse and join leagues
  - `/leagues/[league_id]/leaderboard` - League standings
  - `/admin/*` - Admin console (seasons, leagues, roster, users)
  - `/how-to-play` - Rules and scoring guide
  - `/calculator` - Points calculator tool

### Backend (`/backend`)
- FastAPI REST API
- Endpoints grouped by domain:
  - `user_auth_endpoints.py` - Login, register, JWT auth
  - `user_team_endpoints.py` - Team creation, player management
  - `league_endpoints.py` - League operations
  - `player_endpoints.py` - Player stats and info
  - `admin_endpoints.py` - Admin operations
- Database models in `database_models.py`
- Background tasks with Celery

### Database
- PostgreSQL with SQLAlchemy ORM
- See `DATABASE_SCHEMA.md` for complete schema
- **CRITICAL**: Production and local dev may have different schemas

## User Flows

### Player Flow
1. Register/Login → Dashboard
2. Create Fantasy Team (select league, budget, squad rules)
3. Build Team (select 11 players within constraints)
4. Submit Team
5. View League Leaderboard (updated after matches)

### Admin Flow
1. Create Season (e.g., "ACC 2025 Season")
2. Manage Roster (confirm 513 ACC players)
3. Create Leagues (set budget, squad size, rules)
4. Enable Registration
5. Monitor leagues and teams
6. Update player stats after matches

## Key Features

### Fantasy Team Building
- Squad size limits (typically 11 players)
- Role requirements (min batsmen, min bowlers)
- Player multipliers based on historical performance (lower = better)
- Captain/Vice-Captain bonuses (2x and 1.5x points)

### Scoring System (Rules Set 1)
**Batting:**
- Tiered run points: 1-30 runs (1.0), 31-49 (1.25), 50-99 (1.5), 100+ (1.75 pts/run)
- Milestones: 30 runs (+10), 50 runs (+15), 100 runs (+30)

**Bowling:**
- Tiered wicket points: 1-2 wickets (15 each), 3-4 (20), 5-10 (30)
- Maidens: 15 pts
- Milestones: 3 wickets (+10), 5 wickets (+20)

**Fielding:**
- Catches: 10 pts (20 pts for wicketkeepers)
- Stumpings: 15 pts

### Player Multipliers
- Lower multiplier = better historical performance
- Affects player pricing
- Range typically 0.69 (elite) to 1.0+ (average)

## Admin Console Features
- Season Management (create, edit, activate)
- League Management (create, edit, delete, set rules)
- Roster Management (view 513 players, confirm roster)
- User Management (view, delete users)
- Team Management (view, delete teams)

## Important Constraints

### Squad Building Rules
- Squad size (typically 11 players)
- Minimum batsmen (usually 3-4)
- Minimum bowlers (usually 3-4)
- Max players per real-life team (optional, disabled in production)
- No budget constraints - select any players within role requirements

### Data Integrity
- Cannot modify finalized teams
- Cannot delete seasons with active leagues
- Must validate squad composition before finalizing (role requirements, squad size)

## Deployment

### Local Development
```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Production (fantcric.fun)
- VPS: Ubuntu 22.04
- HTTPS via Let's Encrypt
- Nginx reverse proxy
- Docker Compose orchestration
- PostgreSQL data persisted in volumes

## Critical Rules

### Making Database Changes
1. **NEVER** assume production and local schemas match
2. **ALWAYS** check production schema before changing models
3. **READ** `DATABASE_SCHEMA.md` before touching `database_models.py`
4. Test changes locally first, then carefully deploy to production
5. See `DEVELOPMENT_GUIDE.md` for detailed procedures

### Making Code Changes
1. Understand the full scope before fixing
2. Check if change affects multiple components
3. Test user flows end-to-end
4. Don't break working features to fix one issue
5. Document breaking changes

## Success Metrics
- Users can create and manage fantasy teams
- Admin can run complete seasons
- Scoring system works accurately
- No data loss or corruption
- Stable deployment on production

## Future Enhancements (Not Yet Implemented)
- Live score updates during matches
- Player statistics from web scraping
- Mobile app
- Social features (chat, team sharing)
- Historical season data and analytics
