#!/bin/bash
# Real-Time Season Simulation Runner
# ==================================
# This script sets up and runs a full season simulation that you can watch in real-time

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║        🏏 FANTASY CRICKET - REAL-TIME SEASON SIMULATION 🏏                 ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "mock_kncb_server.py" ]; then
    echo -e "${RED}❌ Error: Must run from backend directory${NC}"
    echo -e "${YELLOW}   cd /Users/guypa/Github/fantasy-cricket-leafcloud/backend${NC}"
    exit 1
fi

# Check if mock data exists
if [ ! -d "mock_data/scorecards_2026" ]; then
    echo -e "${RED}❌ Error: Mock data not found${NC}"
    echo -e "${YELLOW}   Run: python3 load_2025_scorecards_to_mock.py${NC}"
    exit 1
fi

echo -e "${CYAN}📋 Pre-flight Checklist:${NC}"
echo -e "   ${GREEN}✓${NC} Mock data directory exists"

# Check if mock server is already running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Mock server already running on port 5001${NC}"
    echo -n "   Kill and restart? (y/n): "
    read -r response
    if [[ "$response" == "y" ]]; then
        echo -e "   ${CYAN}Stopping existing mock server...${NC}"
        lsof -ti:5001 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "   ${YELLOW}Using existing mock server${NC}"
    fi
else
    echo -e "   ${GREEN}✓${NC} Port 5001 available"
fi

# Start mock server if not running
if ! lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "\n${CYAN}🚀 Starting mock server...${NC}"
    export MOCK_DATA_DIR="./mock_data/scorecards_2026"
    python3 mock_kncb_server.py > mock_server.log 2>&1 &
    MOCK_PID=$!
    echo -e "   Mock server PID: ${MOCK_PID}"

    # Wait for server to be ready
    echo -n "   Waiting for server..."
    for i in {1..10}; do
        if curl -s http://localhost:5001/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done

    if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo -e " ${RED}✗${NC}"
        echo -e "${RED}❌ Mock server failed to start${NC}"
        echo -e "${YELLOW}   Check mock_server.log for errors${NC}"
        exit 1
    fi

    echo -e "   ${GREEN}✓${NC} Mock server ready at http://localhost:5001"
else
    echo -e "   ${GREEN}✓${NC} Mock server already running"
fi

# Check database connection
echo -ne "\n${CYAN}🔌 Checking database...${NC} "
if python3 -c "from database_models import get_db; next(get_db())" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}❌ Database connection failed${NC}"
    echo -e "${YELLOW}   Make sure PostgreSQL is running${NC}"
    exit 1
fi

# Check if frontend is running
echo -ne "${CYAN}🌐 Checking frontend...${NC} "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    FRONTEND_RUNNING=true
else
    echo -e "${YELLOW}⚠${NC}"
    echo -e "${YELLOW}   Frontend not running at http://localhost:3000${NC}"
    echo -e "${YELLOW}   Start it in another terminal: cd ../frontend && npm run dev${NC}"
    FRONTEND_RUNNING=false
fi

# Summary
echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                          SIMULATION READY                                  ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Mock Server:${NC} http://localhost:5001"
echo -e "${GREEN}✅ Database:${NC} Connected"
if [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "${GREEN}✅ Frontend:${NC} http://localhost:3000"
else
    echo -e "${YELLOW}⚠️  Frontend:${NC} Not running (optional but recommended)"
fi
echo ""
echo -e "${CYAN}📊 Simulation Details:${NC}"
echo -e "   • Duration: ~10-15 minutes"
echo -e "   • Weeks: 12"
echo -e "   • Matches: 136"
echo -e "   • Update interval: ~50 seconds per week"
echo ""
echo -e "${YELLOW}💡 Tip: Open http://localhost:3000/leaderboard in your browser now!${NC}"
echo -e "${YELLOW}    You'll see your team's points update in real-time after each week.${NC}"
echo ""
echo -e "${GREEN}Press ENTER to start the simulation...${NC}"
read -r

# Run the simulation
echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                     STARTING SIMULATION                                    ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

export SCRAPER_MODE=mock
python3 realtime_season_simulation.py

# Cleanup
EXIT_CODE=$?

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                      SIMULATION COMPLETE                                   ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Simulation completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}📊 Next Steps:${NC}"
    echo -e "   • View leaderboard: ${BLUE}http://localhost:3000/leaderboard${NC}"
    echo -e "   • View your team: ${BLUE}http://localhost:3000/dashboard${NC}"
    echo -e "   • View statistics: ${BLUE}http://localhost:3000/admin${NC}"
else
    echo -e "${RED}❌ Simulation ended with errors${NC}"
    echo -e "${YELLOW}   Check output above for details${NC}"
fi

echo ""
echo -e "${YELLOW}Mock server still running. To stop:${NC}"
echo -e "   ${CYAN}lsof -ti:5001 | xargs kill${NC}"
echo ""

exit $EXIT_CODE
