#!/bin/bash
###############################################################################
# Docker Volume Backup Script
# Creates a compressed snapshot of the PostgreSQL database volume
###############################################################################

set -e  # Exit on any error

# Configuration
BACKUP_DIR="./backups/volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VOLUME_NAME="fantasy-cricket-leafcloud_postgres_data"
BACKUP_FILE="db_volume_snapshot_${TIMESTAMP}.tar.gz"
COMPOSE_FILE="../docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================================================="
echo "🗄️  DOCKER VOLUME BACKUP - PostgreSQL Database"
echo "=================================================================================="
echo ""

# Check if running on production server
if [ -f "/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml" ]; then
    echo "📍 Detected: Production server (fantcric.fun)"
    COMPOSE_FILE="/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml"
    BACKUP_DIR="/home/ubuntu/fantasy-cricket-leafcloud/backups/volumes"
else
    echo "📍 Detected: Local development environment"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo ""
echo "⚙️  Configuration:"
echo "   Volume: $VOLUME_NAME"
echo "   Backup location: $BACKUP_DIR/$BACKUP_FILE"
echo "   Timestamp: $TIMESTAMP"
echo ""

# Pre-flight checks
echo "🔍 Pre-flight checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi
echo "   ✅ Docker is running"

# Check if volume exists
if ! docker volume inspect "$VOLUME_NAME" > /dev/null 2>&1; then
    echo -e "${RED}❌ Volume '$VOLUME_NAME' not found${NC}"
    echo "   Available volumes:"
    docker volume ls
    exit 1
fi
echo "   ✅ Volume exists"

# Check available disk space
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    AVAILABLE_SPACE=$(df -g "$BACKUP_DIR" | awk 'NR==2 {print $4}')
else
    # Linux
    AVAILABLE_SPACE=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
fi
VOLUME_SIZE=$(docker system df -v 2>/dev/null | grep "$VOLUME_NAME" | awk '{print $4}' | head -1 || echo "unknown")
echo "   ✅ Available disk space: ${AVAILABLE_SPACE}GB"
echo "   📊 Volume size: ${VOLUME_SIZE}"

# Confirm before proceeding
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will briefly stop the database container${NC}"
echo "   Estimated downtime: 10-30 seconds (depends on data size)"
echo ""
read -p "Continue with backup? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Backup cancelled"
    exit 0
fi

# Get database container name
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

# Stop database for consistent backup
echo ""
echo "🛑 Stopping database container..."
docker stop "$CONTAINER_NAME"

# Create backup
echo ""
echo "💾 Creating volume snapshot..."
echo "   This may take a few moments..."

docker run --rm \
    -v "$VOLUME_NAME":/source:ro \
    -v "$(cd "$BACKUP_DIR" && pwd)":/backup \
    ubuntu:20.04 \
    tar czf "/backup/$BACKUP_FILE" -C /source .

# Restart database
echo ""
echo "▶️  Restarting database container..."
docker start "$CONTAINER_NAME"

# Wait for database to be healthy
echo "⏳ Waiting for database to be healthy..."
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "healthy"; then
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done
echo ""

if [ $WAITED -lt $MAX_WAIT ]; then
    echo -e "${GREEN}✅ Database is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Database started but health check timed out${NC}"
    echo "   Check status: docker ps"
fi

# Verify backup
echo ""
echo "🔍 Verifying backup..."
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created successfully${NC}"
    echo ""
    echo "📊 Backup details:"
    echo "   File: $BACKUP_DIR/$BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE"
    echo "   Created: $(date)"

    # Calculate MD5 for verification
    if command -v md5sum > /dev/null 2>&1; then
        MD5=$(md5sum "$BACKUP_DIR/$BACKUP_FILE" | cut -d' ' -f1)
        echo "   MD5: $MD5"
        # Save MD5 to file
        echo "$MD5  $BACKUP_FILE" > "$BACKUP_DIR/${BACKUP_FILE}.md5"
    fi
else
    echo -e "${RED}❌ Backup file not created${NC}"
    exit 1
fi

# List recent backups
echo ""
echo "📁 Recent backups:"
ls -lht "$BACKUP_DIR" | head -6

# Cleanup old backups (keep last 5)
echo ""
echo "🧹 Cleaning up old backups (keeping last 5)..."
cd "$BACKUP_DIR"
ls -t db_volume_snapshot_*.tar.gz | tail -n +6 | xargs -r rm -f
ls -t db_volume_snapshot_*.tar.gz.md5 | tail -n +6 | xargs -r rm -f
echo "   ✅ Cleanup complete"

echo ""
echo "=================================================================================="
echo -e "${GREEN}✅ BACKUP COMPLETE${NC}"
echo "=================================================================================="
echo ""
echo "📝 Next steps:"
echo "   1. Test the backup: ./restore_docker_volume.sh $BACKUP_FILE"
echo "   2. Proceed with simulation test"
echo "   3. Keep this backup until test completes successfully"
echo ""
echo "🔄 To restore this backup:"
echo "   ./restore_docker_volume.sh $BACKUP_FILE"
echo ""
