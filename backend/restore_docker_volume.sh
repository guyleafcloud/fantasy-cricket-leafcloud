#!/bin/bash
###############################################################################
# Docker Volume Restore Script
# Restores PostgreSQL database volume from a compressed snapshot
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================================================================="
echo "♻️  DOCKER VOLUME RESTORE - PostgreSQL Database"
echo "=================================================================================="
echo ""

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: Backup file required${NC}"
    echo ""
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Examples:"
    echo "   $0 backups/volumes/db_volume_snapshot_20251121_143022.tar.gz"
    echo "   $0 db_volume_snapshot_20251121_143022.tar.gz"
    echo ""
    echo "Available backups:"
    ls -1t ./backups/volumes/db_volume_snapshot_*.tar.gz 2>/dev/null | head -5 || echo "   No backups found"
    echo ""
    exit 1
fi

BACKUP_FILE="$1"
VOLUME_NAME="fantasy-cricket-leafcloud_postgres_data"
COMPOSE_FILE="../docker-compose.yml"

# Check if running on production server
if [ -f "/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml" ]; then
    echo "📍 Detected: Production server (fantcric.fun)"
    COMPOSE_FILE="/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml"
    # Handle relative paths
    if [[ "$BACKUP_FILE" != /* ]]; then
        BACKUP_FILE="/home/ubuntu/fantasy-cricket-leafcloud/backend/$BACKUP_FILE"
    fi
else
    echo "📍 Detected: Local development environment"
    # Handle relative paths
    if [[ "$BACKUP_FILE" != /* ]]; then
        BACKUP_FILE="$(pwd)/$BACKUP_FILE"
    fi
fi

echo ""
echo "⚙️  Configuration:"
echo "   Volume: $VOLUME_NAME"
echo "   Backup file: $BACKUP_FILE"
echo ""

# Pre-flight checks
echo "🔍 Pre-flight checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi
echo "   ✅ Docker is running"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    echo ""
    echo "Available backups in ./backups/volumes/:"
    ls -1t ./backups/volumes/db_volume_snapshot_*.tar.gz 2>/dev/null || echo "   No backups found"
    exit 1
fi
echo "   ✅ Backup file exists"

# Check backup file integrity (if MD5 exists)
MD5_FILE="${BACKUP_FILE}.md5"
if [ -f "$MD5_FILE" ]; then
    echo "   🔍 Verifying backup integrity..."
    if command -v md5sum > /dev/null 2>&1; then
        BACKUP_DIR=$(dirname "$BACKUP_FILE")
        BACKUP_NAME=$(basename "$BACKUP_FILE")
        cd "$BACKUP_DIR"
        if md5sum -c "$BACKUP_NAME.md5" > /dev/null 2>&1; then
            echo "   ✅ Backup integrity verified"
        else
            echo -e "${RED}❌ Backup integrity check failed!${NC}"
            echo "   The backup file may be corrupted"
            read -p "Continue anyway? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                echo "❌ Restore cancelled"
                exit 1
            fi
        fi
        cd - > /dev/null
    fi
fi

# Show backup details
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE" 2>/dev/null || stat -c "%y" "$BACKUP_FILE" 2>/dev/null | cut -d'.' -f1)
echo "   📊 Backup size: $BACKUP_SIZE"
echo "   📅 Backup date: $BACKUP_DATE"

# Check if volume exists
if ! docker volume inspect "$VOLUME_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Volume '$VOLUME_NAME' not found${NC}"
    echo "   Creating new volume..."
    docker volume create "$VOLUME_NAME"
fi
echo "   ✅ Volume exists"

# Get current volume size (for comparison)
CURRENT_SIZE=$(docker system df -v 2>/dev/null | grep "$VOLUME_NAME" | awk '{print $4}' | head -1 || echo "unknown")
echo "   📊 Current volume size: $CURRENT_SIZE"

# CRITICAL WARNING
echo ""
echo "=================================================================================="
echo -e "${RED}⚠️  CRITICAL WARNING ⚠️${NC}"
echo "=================================================================================="
echo ""
echo "This will:"
echo "   1. Stop the database container"
echo "   2. DELETE all current database data"
echo "   3. Restore data from backup: $(basename "$BACKUP_FILE")"
echo "   4. Restart the database"
echo ""
echo -e "${YELLOW}ALL CURRENT DATA WILL BE LOST!${NC}"
echo ""
echo "Current database details:"
echo "   Volume: $VOLUME_NAME"
echo "   Size: $CURRENT_SIZE"
echo ""
echo "Backup details:"
echo "   File: $(basename "$BACKUP_FILE")"
echo "   Size: $BACKUP_SIZE"
echo "   Date: $BACKUP_DATE"
echo ""
echo "=================================================================================="
echo ""

read -p "Type 'RESTORE' in capitals to confirm: " confirmation

if [ "$confirmation" != "RESTORE" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

# Get database container
DB_CONTAINER=$(docker-compose -f "$COMPOSE_FILE" ps -q fantasy_cricket_db 2>/dev/null || echo "")
if [ -z "$DB_CONTAINER" ]; then
    # Try direct container name
    DB_CONTAINER=$(docker ps -q -f name=fantasy_cricket_db)
fi

if [ -z "$DB_CONTAINER" ]; then
    echo -e "${RED}❌ Database container not found${NC}"
    exit 1
fi

CONTAINER_NAME=$(docker inspect --format='{{.Name}}' "$DB_CONTAINER" | sed 's/\///')
echo ""
echo "📦 Database container: $CONTAINER_NAME"

# Stop database
echo ""
echo "🛑 Stopping database container..."
docker stop "$CONTAINER_NAME"

# Remove all data from volume
echo ""
echo "🗑️  Removing current data from volume..."
docker run --rm \
    -v "$VOLUME_NAME":/data \
    ubuntu:20.04 \
    sh -c "rm -rf /data/*"

echo "   ✅ Volume cleared"

# Restore from backup
echo ""
echo "♻️  Restoring data from backup..."
echo "   This may take a few moments..."

# Get absolute path to backup file
BACKUP_ABS_PATH=$(cd "$(dirname "$BACKUP_FILE")" && pwd)/$(basename "$BACKUP_FILE")

docker run --rm \
    -v "$VOLUME_NAME":/data \
    -v "$(dirname "$BACKUP_ABS_PATH")":/backup:ro \
    ubuntu:20.04 \
    tar xzf "/backup/$(basename "$BACKUP_FILE")" -C /data

echo "   ✅ Data restored"

# Restart database
echo ""
echo "▶️  Restarting database container..."
docker start "$CONTAINER_NAME"

# Wait for database to be healthy
echo "⏳ Waiting for database to be healthy..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    if [ "$HEALTH" = "healthy" ]; then
        break
    elif [ "$HEALTH" = "unhealthy" ]; then
        echo ""
        echo -e "${RED}❌ Database health check failed${NC}"
        echo "   Showing last 20 log lines:"
        docker logs --tail 20 "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done
echo ""

if [ $WAITED -lt $MAX_WAIT ]; then
    echo -e "${GREEN}✅ Database is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Health check timed out${NC}"
    echo "   Database may still be starting up"
    echo "   Check status: docker ps"
    echo "   Check logs: docker logs $CONTAINER_NAME"
fi

# Verify restore
echo ""
echo "🔍 Verifying restore..."

# Try to connect and get basic stats
sleep 2  # Give it a moment to be fully ready

CONNECT_TEST=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "SELECT COUNT(*) FROM players;" 2>/dev/null || echo "ERROR")

if [[ "$CONNECT_TEST" == *"ERROR"* ]]; then
    echo -e "${YELLOW}⚠️  Could not verify database connection${NC}"
    echo "   The restore completed but database may need more time to start"
else
    PLAYER_COUNT=$(echo "$CONNECT_TEST" | grep -o '[0-9]\+' | head -1)
    echo "   ✅ Database connection successful"
    echo "   📊 Player count: $PLAYER_COUNT"
fi

# Get restored volume size
RESTORED_SIZE=$(docker system df -v 2>/dev/null | grep "$VOLUME_NAME" | awk '{print $4}' | head -1 || echo "unknown")
echo "   📊 Restored volume size: $RESTORED_SIZE"

echo ""
echo "=================================================================================="
echo -e "${GREEN}✅ RESTORE COMPLETE${NC}"
echo "=================================================================================="
echo ""
echo "📊 Summary:"
echo "   Backup used: $(basename "$BACKUP_FILE")"
echo "   Backup size: $BACKUP_SIZE"
echo "   Backup date: $BACKUP_DATE"
echo "   Restored to: $VOLUME_NAME"
echo "   Volume size: $RESTORED_SIZE"
echo ""
echo "📝 Next steps:"
echo "   1. Verify application is working: curl http://localhost:8000/health"
echo "   2. Check database contents: docker exec $CONTAINER_NAME psql -U cricket_admin fantasy_cricket"
echo "   3. Test critical endpoints"
echo ""
echo "⚠️  Note: All data after backup timestamp has been lost"
echo "   Backup timestamp: $BACKUP_DATE"
echo ""
