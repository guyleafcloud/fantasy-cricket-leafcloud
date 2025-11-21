#!/bin/bash
###############################################################################
# Automated Weekly Simulation Runner
# Cron-friendly wrapper for running weekly fantasy cricket simulations
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="./logs/simulation"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"  # Set via environment variable
COMPOSE_FILE="../docker-compose.yml"

# Check if running on production
if [ -f "/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml" ]; then
    PRODUCTION=true
    LOG_DIR="/home/ubuntu/fantasy-cricket-leafcloud/backend/logs/simulation"
    COMPOSE_FILE="/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml"
else
    PRODUCTION=false
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/simulation_${TIMESTAMP}.log"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Function to send notification
send_notification() {
    local subject="$1"
    local body="$2"

    if [ -n "$NOTIFY_EMAIL" ]; then
        echo "$body" | mail -s "$subject" "$NOTIFY_EMAIL" 2>/dev/null || true
    fi
}

# Check for round number argument
if [ $# -eq 0 ]; then
    log_error "Round number required"
    echo "Usage: $0 <round_number>"
    echo ""
    echo "Examples:"
    echo "   $0 1    # Run week 1 simulation"
    echo "   $0 12   # Run week 12 simulation"
    echo ""
    exit 1
fi

ROUND_NUMBER=$1

log "=========================================="
log "🏏 AUTOMATED WEEKLY SIMULATION"
log "=========================================="
log ""
log "Configuration:"
log "   Round: $ROUND_NUMBER"
log "   Production: $PRODUCTION"
log "   Log file: $LOG_FILE"
log "   Timestamp: $TIMESTAMP"
log ""

# Pre-flight checks
log "🔍 Running pre-flight checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running"
    send_notification "Simulation Failed - Week $ROUND_NUMBER" "Docker is not running"
    exit 1
fi
log_success "Docker is running"

# Check if API container is running
API_CONTAINER=$(docker ps -q -f name=fantasy_cricket_api)
if [ -z "$API_CONTAINER" ]; then
    log_error "API container not running"
    send_notification "Simulation Failed - Week $ROUND_NUMBER" "API container not running"
    exit 1
fi
log_success "API container is running"

# Check if database is healthy
DB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' fantasy_cricket_db 2>/dev/null || echo "unknown")
if [ "$DB_HEALTH" != "healthy" ]; then
    log_warning "Database health check: $DB_HEALTH"
else
    log_success "Database is healthy"
fi

# Check if mock server is running (for test mode)
MOCK_SERVER=$(docker ps -q -f name=fantasy_cricket_mock_server 2>/dev/null || echo "")
if [ -n "$MOCK_SERVER" ]; then
    log "Mock server detected - running in test mode"
else
    log "No mock server - running in production mode"
fi

# Run simulation
log ""
log "🚀 Starting simulation for Round $ROUND_NUMBER..."
log ""

START_TIME=$(date +%s)

# Execute simulation via existing script
if [ "$PRODUCTION" = true ]; then
    # Production: run via docker-compose
    if docker exec fantasy_cricket_api /app/run_weekly_simulation.sh $ROUND_NUMBER >> "$LOG_FILE" 2>&1; then
        SIMULATION_SUCCESS=true
    else
        SIMULATION_SUCCESS=false
    fi
else
    # Local: run directly
    if ./run_weekly_simulation.sh $ROUND_NUMBER >> "$LOG_FILE" 2>&1; then
        SIMULATION_SUCCESS=true
    else
        SIMULATION_SUCCESS=false
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

log ""
log "=========================================="

if [ "$SIMULATION_SUCCESS" = true ]; then
    log_success "Simulation completed successfully"
    log "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"

    # Get simulation results summary
    log ""
    log "📊 Simulation Results:"

    # Query database for round results
    if [ "$PRODUCTION" = true ]; then
        PERF_COUNT=$(docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM player_performances WHERE round = $ROUND_NUMBER;" 2>/dev/null | tr -d ' ' || echo "unknown")
        TOP_SCORER=$(docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "SELECT p.name, pp.fantasy_points FROM player_performances pp JOIN players p ON pp.player_id = p.id WHERE pp.round = $ROUND_NUMBER ORDER BY pp.fantasy_points DESC LIMIT 1;" 2>/dev/null || echo "unknown")
    else
        PERF_COUNT="Check manually"
        TOP_SCORER="Check manually"
    fi

    log "   Performances recorded: $PERF_COUNT"
    log "   Top scorer: $TOP_SCORER"

    # Send success notification
    NOTIFICATION_BODY="Week $ROUND_NUMBER simulation completed successfully.

Duration: ${DURATION_MIN}m ${DURATION_SEC}s
Performances: $PERF_COUNT
Top scorer: $TOP_SCORER

Log file: $LOG_FILE"

    send_notification "Simulation Success - Week $ROUND_NUMBER" "$NOTIFICATION_BODY"

else
    log_error "Simulation failed"
    log "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
    log ""
    log "Last 20 lines of error log:"
    tail -20 "$LOG_FILE"

    # Send failure notification
    NOTIFICATION_BODY="Week $ROUND_NUMBER simulation FAILED.

Duration: ${DURATION_MIN}m ${DURATION_SEC}s

Check log file: $LOG_FILE

Last error lines:
$(tail -20 "$LOG_FILE")"

    send_notification "Simulation FAILED - Week $ROUND_NUMBER" "$NOTIFICATION_BODY"

    exit 1
fi

log "=========================================="
log ""

# Cleanup old logs (keep last 20)
log "🧹 Cleaning up old logs..."
cd "$LOG_DIR"
ls -t simulation_*.log | tail -n +21 | xargs -r rm -f
log_success "Cleanup complete (kept last 20 logs)"

log ""
log "✅ Automation complete for Round $ROUND_NUMBER"
log "📁 Full log: $LOG_FILE"
log ""

# Print summary to stdout (for cron emails)
echo ""
echo "=========================================="
echo "🏏 Weekly Simulation - Round $ROUND_NUMBER"
echo "=========================================="
echo ""
echo "Status: SUCCESS ✅"
echo "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
echo "Performances: $PERF_COUNT"
echo "Log: $LOG_FILE"
echo ""
