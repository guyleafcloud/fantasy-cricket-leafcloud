#!/bin/bash
################################################################################
# Weekly Fantasy Cricket Simulation Runner
################################################################################
# This script runs the weekly fantasy team simulation after matches are complete.
#
# Usage:
#   ./run_weekly_simulation.sh <round_number>
#
# Example:
#   ./run_weekly_simulation.sh 1    # Run Round 1
#   ./run_weekly_simulation.sh 2    # Run Round 2
#
# This script should be run:
#   - After all weekly matches are scraped (Tuesday evening)
#   - Before users view the updated leaderboard (Wednesday morning)
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/simulation_${TIMESTAMP}.log"

# Docker configuration
CONTAINER_NAME="fantasy_cricket_api"
SIMULATION_SCRIPT="/app/simulate_live_teams.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

################################################################################
# Validation
################################################################################

# Check if round number is provided
if [ $# -ne 1 ]; then
    error "Usage: $0 <round_number>"
    error "Example: $0 1"
    exit 1
fi

ROUND_NUMBER=$1

# Validate round number is a positive integer
if ! [[ "$ROUND_NUMBER" =~ ^[0-9]+$ ]] || [ "$ROUND_NUMBER" -lt 1 ]; then
    error "Round number must be a positive integer (got: $ROUND_NUMBER)"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

################################################################################
# Pre-flight Checks
################################################################################

log "================================================================================  "
log "WEEKLY FANTASY CRICKET SIMULATION - ROUND $ROUND_NUMBER"
log "================================================================================"
log ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if container exists and is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    error "Container '$CONTAINER_NAME' is not running."
    error "Start the container with: docker-compose up -d"
    exit 1
fi

success "Docker container is running"

# Check if simulation script exists in container
if ! docker exec "$CONTAINER_NAME" test -f "$SIMULATION_SCRIPT"; then
    error "Simulation script not found: $SIMULATION_SCRIPT"
    exit 1
fi

success "Simulation script found"

################################################################################
# Run Simulation
################################################################################

log ""
log "Starting simulation for Round $ROUND_NUMBER..."
log "Logs will be saved to: $LOG_FILE"
log ""

# Run the simulation
if docker exec "$CONTAINER_NAME" python3 "$SIMULATION_SCRIPT" "$ROUND_NUMBER" 2>&1 | tee -a "$LOG_FILE"; then
    success "Simulation completed successfully!"
else
    error "Simulation failed. Check logs at: $LOG_FILE"
    exit 1
fi

################################################################################
# Post-Simulation Verification
################################################################################

log ""
log "Verifying simulation results..."

# Check if performances were stored
PERF_COUNT=$(docker exec "$CONTAINER_NAME" python3 -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM player_performances WHERE round_number = :round'), {'round': $ROUND_NUMBER})
    print(result.scalar())
" 2>/dev/null)

if [ "$PERF_COUNT" -gt 0 ]; then
    success "Stored $PERF_COUNT player performances for Round $ROUND_NUMBER"
else
    warning "No performances stored. This might be expected if no matches were played."
fi

# Get leaderboard standings
log ""
log "Current Leaderboard:"
log "-------------------"

docker exec "$CONTAINER_NAME" python3 -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT
            ROW_NUMBER() OVER (ORDER BY ft.total_points DESC) as rank,
            ft.team_name,
            COALESCE(u.full_name, u.email) as owner,
            ROUND(ft.total_points::numeric, 1) as points
        FROM fantasy_teams ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.is_finalized = TRUE
        ORDER BY ft.total_points DESC
        LIMIT 10
    '''))

    for row in result:
        print(f'   {row[0]:2d}. {row[1]:30s} ({row[2]:20s}) - {row[3]:8.1f} pts')
" 2>/dev/null | tee -a "$LOG_FILE"

################################################################################
# Completion
################################################################################

log ""
log "================================================================================"
success "Round $ROUND_NUMBER simulation complete!"
log "================================================================================"
log ""
log "Next steps:"
log "  1. Review logs at: $LOG_FILE"
log "  2. Check leaderboard on website: https://fantcric.fun"
log "  3. Verify team scores are correct"
log ""

exit 0
