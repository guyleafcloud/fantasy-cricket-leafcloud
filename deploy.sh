#!/bin/bash

##############################################################################
# Fantasy Cricket Deployment Script
##############################################################################

set -e  # Exit on error

echo "🏏 Fantasy Cricket Platform - Deployment Script"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}1️⃣ Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cat > .env <<EOF
# Database
DB_PASSWORD=change_this_secure_password

# JWT
JWT_SECRET_KEY=change_this_to_a_random_32_char_string

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Monitoring (optional)
GRAFANA_PASSWORD=admin_password
SENTRY_DSN=

# Environment
ENVIRONMENT=production
EOF
    echo -e "${YELLOW}⚠️  Please edit .env file with your secrets before deploying!${NC}"
    echo -e "${YELLOW}   Run: nano .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ .env file found${NC}"

# Check legacy rosters
echo -e "\n${YELLOW}2️⃣ Checking legacy rosters...${NC}"

ROSTER_COUNT=$(find backend/rosters -name "*_roster.json" 2>/dev/null | wc -l | tr -d ' ')

if [ "$ROSTER_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠️  No legacy rosters found in backend/rosters/${NC}"
    echo -e "${YELLOW}   System will start with empty roster and discover players during season.${NC}"
else
    echo -e "${GREEN}✅ Found $ROSTER_COUNT legacy roster(s)${NC}"
    find backend/rosters -name "*_roster.json" -exec basename {} \; | sed 's/^/   - /'
fi

# Build images
echo -e "\n${YELLOW}3️⃣ Building Docker images...${NC}"
docker-compose build

echo -e "${GREEN}✅ Images built successfully${NC}"

# Stop existing containers
echo -e "\n${YELLOW}4️⃣ Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "\n${YELLOW}5️⃣ Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}6️⃣ Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "\n${YELLOW}7️⃣ Checking service health...${NC}"

if docker ps | grep -q "fantasy_cricket_db"; then
    echo -e "${GREEN}✅ Database is running${NC}"
else
    echo -e "${RED}❌ Database failed to start${NC}"
    docker-compose logs fantasy_cricket_db
    exit 1
fi

if docker ps | grep -q "fantasy_cricket_redis"; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
    exit 1
fi

if docker ps | grep -q "fantasy_cricket_api"; then
    echo -e "${GREEN}✅ API server is running${NC}"
else
    echo -e "${RED}❌ API server failed to start${NC}"
    docker-compose logs fantasy_cricket_api
    exit 1
fi

if docker ps | grep -q "fantasy_cricket_worker"; then
    echo -e "${GREEN}✅ Celery worker is running${NC}"
else
    echo -e "${RED}❌ Celery worker failed to start${NC}"
    docker-compose logs fantasy_cricket_worker
    exit 1
fi

if docker ps | grep -q "fantasy_cricket_scheduler"; then
    echo -e "${GREEN}✅ Celery scheduler is running${NC}"
else
    echo -e "${RED}❌ Celery scheduler failed to start${NC}"
    docker-compose logs fantasy_cricket_scheduler
    exit 1
fi

# Check if legacy rosters were loaded
echo -e "\n${YELLOW}8️⃣ Checking legacy roster loading...${NC}"
sleep 5

if docker-compose logs fantasy_cricket_worker 2>&1 | grep -q "Legacy roster loading complete"; then
    LOADED=$(docker-compose logs fantasy_cricket_worker 2>&1 | grep "Legacy roster loading complete" | tail -1)
    echo -e "${GREEN}✅ $LOADED${NC}"
else
    echo -e "${YELLOW}⚠️  Legacy roster loading not detected (check logs if rosters should be loaded)${NC}"
fi

# Test API
echo -e "\n${YELLOW}9️⃣ Testing API...${NC}"
sleep 2

if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
fi

# Show summary
echo -e "\n=============================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "=============================================="
echo ""
echo "📊 Service Status:"
echo "   API:        http://localhost:8000"
echo "   Grafana:    http://localhost:3000"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "📝 Quick Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   View worker logs: docker-compose logs -f fantasy_cricket_worker"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""
echo "🧪 Test API Endpoints:"
echo "   curl http://localhost:8000/api/v1/season/summary"
echo "   curl http://localhost:8000/api/v1/clubs/ACC/roster"
echo ""
echo "📅 Scheduled Tasks:"
echo "   - Weekly scrape: Every Monday at 1:00 AM"
echo "   - Daily backup:  Every day at 3:00 AM"
echo ""
echo -e "${GREEN}✅ System is ready for the 2026 cricket season!${NC}"
