# Build and Deploy Guide

## 🎯 What You're Deploying

A **fully autonomous fantasy cricket platform** with:
- ✅ Weekly automated scraping (Mondays 1 AM)
- ✅ Season-long player stat aggregation
- ✅ Legacy roster loading (2025 → 2026)
- ✅ REST API for all player data
- ✅ Fantasy points calculation with tier multipliers
- ✅ Automatic name matching for returning players

---

## 📦 System Components

```
Backend Service
├── FastAPI (main.py) - REST API server
├── Celery Worker - Background scraping tasks
├── Celery Beat - Task scheduler
├── PostgreSQL - Database
├── Redis - Task queue & caching
└── Playwright - Browser automation for scraping
```

---

## 🚀 Quick Deploy (Docker Compose)

### Step 1: Prerequisites

```bash
cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend

# Ensure Docker is running
docker --version
docker-compose --version
```

### Step 2: Update Docker Compose

Add Celery services to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Existing services (keep these)
  fantasy_cricket_db:
    image: postgres:15
    environment:
      POSTGRES_DB: fantasy_cricket
      POSTGRES_USER: cricket_admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  fantasy_cricket_redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # FastAPI Backend
  fantasy_cricket_api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://cricket_admin:${DB_PASSWORD}@fantasy_cricket_db:5432/fantasy_cricket
      - REDIS_URL=redis://fantasy_cricket_redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - fantasy_cricket_db
      - fantasy_cricket_redis
    volumes:
      - ./backend:/app
      - ./backend/rosters:/app/rosters
      - ./backend/season_aggregates.json:/app/season_aggregates.json

  # NEW: Celery Worker (runs scraping tasks)
  fantasy_cricket_celery_worker:
    build: .
    command: celery -A celery_tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://cricket_admin:${DB_PASSWORD}@fantasy_cricket_db:5432/fantasy_cricket
      - REDIS_URL=redis://fantasy_cricket_redis:6379
    depends_on:
      - fantasy_cricket_redis
      - fantasy_cricket_db
    volumes:
      - ./backend:/app
      - ./backend/rosters:/app/rosters
      - ./backend/season_aggregates.json:/app/season_aggregates.json

  # NEW: Celery Beat (schedules tasks)
  fantasy_cricket_celery_beat:
    build: .
    command: celery -A celery_tasks beat --loglevel=info
    environment:
      - REDIS_URL=redis://fantasy_cricket_redis:6379
    depends_on:
      - fantasy_cricket_redis
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
  redis_data:
```

### Step 3: Update Dockerfile

Create/update `Dockerfile` in backend directory:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/rosters /app/logs

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 4: Environment Variables

Create `.env` file:

```bash
cat > .env <<'EOF'
DB_PASSWORD=your_secure_password_here
SECRET_KEY=your_secret_key_here_min_32_chars
ENVIRONMENT=production
EOF
```

### Step 5: Configure Clubs

Edit `celery_tasks.py` line 46:

```python
CONFIGURED_CLUBS = [
    "ACC",      # Amsterdamsche Cricket Club
    "VRA",      # Add your clubs
    "VOC",
    "HCC",
    # Add more clubs as needed
]
```

### Step 6: Add API Endpoints to main.py

Add this to your `main.py`:

```python
# At the top with other imports
from api_endpoints import router as stats_router

# After creating FastAPI app
app = FastAPI(title="Fantasy Cricket Platform")

# Include stats endpoints
app.include_router(stats_router)
```

### Step 7: Build and Deploy

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f fantasy_cricket_celery_worker
```

### Step 8: Verify Deployment

```bash
# Check API is running
curl http://localhost:8000/api/v1/season/summary

# Check Celery worker
docker-compose logs fantasy_cricket_celery_worker | grep "Legacy roster"

# Should see: "✅ Legacy roster loading complete: 25 players imported"
```

---

## 🧪 Testing the Deployment

### 1. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Season summary (should show legacy players)
curl http://localhost:8000/api/v1/season/summary

# ACC roster (should show 25 players)
curl http://localhost:8000/api/v1/clubs/ACC/roster

# Leaderboards (empty until season starts)
curl http://localhost:8000/api/v1/leaderboards/fantasy-points
```

### 2. Manual Trigger Scrape (for testing)

```bash
curl -X POST http://localhost:8000/api/v1/admin/scrape-now
```

Response:
```json
{
  "status": "triggered",
  "task_id": "abc-123-def",
  "message": "Scraping task started"
}
```

### 3. Check Celery Logs

```bash
# Watch worker logs
docker-compose logs -f fantasy_cricket_celery_worker

# Should see:
# - Legacy roster loaded: 25 players
# - Scheduled tasks registered
# - Worker ready
```

---

## 📁 File Checklist

Make sure these files exist:

```bash
backend/
├── main.py                              ✅ (update with stats_router)
├── celery_tasks.py                      ✅ (created)
├── player_aggregator.py                 ✅ (created)
├── kncb_html_scraper.py                 ✅ (created)
├── legacy_roster_loader.py              ✅ (created)
├── api_endpoints.py                     ✅ (created)
├── requirements.txt                     ✅ (updated with playwright)
├── Dockerfile                           ⚠️  (create if missing)
├── docker-compose.yml                   ⚠️  (update with celery services)
├── .env                                 ⚠️  (create with secrets)
│
├── rosters/
│   └── acc_2025_roster.json             ✅ (25 players)
│
└── Documentation/
    ├── BUILD_AND_DEPLOY.md              ✅ (this file)
    ├── QUICK_START.md                   ✅
    ├── AGGREGATION_GUIDE.md             ✅
    ├── LEGACY_ROSTER_GUIDE.md           ✅
    └── LEGACY_ROSTER_SUMMARY.md         ✅
```

---

## 🔧 Local Development (No Docker)

If you want to run locally for testing:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start PostgreSQL
# (or use Docker: docker run -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15)

# Terminal 3: Start FastAPI
cd backend
uvicorn main:app --reload --port 8000

# Terminal 4: Start Celery Worker
cd backend
celery -A celery_tasks worker --loglevel=info

# Terminal 5: Start Celery Beat
cd backend
celery -A celery_tasks beat --loglevel=info
```

---

## 📅 Scheduled Tasks

Once deployed, tasks run automatically:

```
Every Monday at 1:00 AM (Amsterdam time):
└─ Scrape last 7 days of matches
   ├─ Extract player performances
   ├─ Match to legacy players
   ├─ Add new players
   ├─ Update season totals
   └─ Save aggregated data

Every Day at 3:00 AM:
└─ Backup season aggregates
   └─ Creates dated backup file
```

---

## 🎮 Admin Operations

### View Current Season Stats

```python
# Python console in container
docker-compose exec fantasy_cricket_celery_worker python3

>>> from celery_tasks import aggregator
>>> summary = aggregator.get_season_summary()
>>> print(f"Total players: {summary['total_players']}")
>>> print(f"Clubs: {summary['clubs']}")
```

### Manual Scrape Trigger

```python
>>> from celery_tasks import trigger_scrape_now
>>> task_id = trigger_scrape_now()
>>> print(f"Task started: {task_id}")
```

### View Player Stats

```python
>>> from celery_tasks import get_club_roster
>>> acc_players = get_club_roster('ACC')
>>> for p in acc_players[:5]:
...     print(f"{p['player_name']}: {p['season_totals']['fantasy_points']} pts")
```

### Export Season Data

```python
>>> from celery_tasks import aggregator
>>> aggregator.save_to_file('season_2026_export.json')
```

---

## 🚨 Troubleshooting

### Celery Worker Won't Start

```bash
# Check logs
docker-compose logs fantasy_cricket_celery_worker

# Common issues:
# 1. Redis not accessible
docker-compose ps fantasy_cricket_redis

# 2. Python module errors
docker-compose exec fantasy_cricket_celery_worker pip list

# 3. Playwright not installed
docker-compose exec fantasy_cricket_celery_worker playwright install chromium
```

### Legacy Roster Not Loading

```bash
# Check roster file exists
docker-compose exec fantasy_cricket_celery_worker ls -la rosters/

# Check file format
docker-compose exec fantasy_cricket_celery_worker cat rosters/acc_2025_roster.json | head

# Check worker logs for import messages
docker-compose logs fantasy_cricket_celery_worker | grep "Legacy"
```

### Scraping Returns No Matches

This is EXPECTED in November 2025 (off-season). Scraper will work when season starts in April 2026.

To test scraping logic:
```python
# Use the test scripts
python3 test_legacy_integration.py
```

### API Returns Empty Data

Before season starts, this is normal:
- Legacy players: ✅ Loaded (25 for ACC)
- Match history: Empty (season hasn't started)
- Fantasy points: Zero (no matches yet)

---

## 🎯 Production Checklist

Before going live:

- [ ] Update `.env` with secure passwords
- [ ] Configure all clubs in `celery_tasks.py`
- [ ] Create legacy rosters for all clubs
- [ ] Update `main.py` with stats router
- [ ] Set up SSL/HTTPS for API
- [ ] Configure domain DNS
- [ ] Set up monitoring/alerting
- [ ] Test manual scrape trigger
- [ ] Verify legacy rosters loaded
- [ ] Check scheduled tasks registered

---

## 🎉 Deployment Complete!

Your system is now:
- ✅ Running 24/7 on server
- ✅ ACC legacy roster loaded (25 players)
- ✅ Scheduled to scrape weekly
- ✅ Automatically aggregating stats
- ✅ Matching returning players
- ✅ Discovering new players
- ✅ Accessible via REST API

When season starts (April 2026), scraping will automatically begin and player stats will accumulate!

---

## 📚 Next Steps

1. **Add more club rosters** (VRA, VOC, HCC, etc.)
2. **Customize fantasy points** if needed
3. **Set up monitoring** (logs, alerts)
4. **Create frontend** to consume API
5. **Wait for season** to start! 🏏

---

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f [service_name]`
2. Review documentation in this directory
3. Test with provided test scripts
4. Check GitHub issues at https://github.com/anthropics/claude-code/issues

**System is ready to deploy!** 🚀
