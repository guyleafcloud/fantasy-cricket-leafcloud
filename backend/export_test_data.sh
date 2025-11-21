#!/bin/bash
###############################################################################
# Export Test Data Script
# Exports all data from a test season (e.g., 2026) before cleanup
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================================================================="
echo "📤 EXPORT TEST DATA - Season Data Export"
echo "=================================================================================="
echo ""

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <season_year>${NC}"
    echo ""
    echo "Examples:"
    echo "   $0 2026          # Export 2026 test season data"
    echo "   $0 2025          # Export 2025 production data"
    echo ""
    exit 1
fi

SEASON_YEAR="$1"
EXPORT_DIR="./exports/season_$SEASON_YEAR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="fantasy_cricket_db"

# Check if running on production server
if [ -f "/home/ubuntu/fantasy-cricket-leafcloud/docker-compose.yml" ]; then
    echo "📍 Detected: Production server (fantcric.fun)"
    EXPORT_DIR="/home/ubuntu/fantasy-cricket-leafcloud/backend/exports/season_$SEASON_YEAR"
else
    echo "📍 Detected: Local development environment"
fi

# Create export directory
mkdir -p "$EXPORT_DIR"

echo ""
echo "⚙️  Configuration:"
echo "   Season year: $SEASON_YEAR"
echo "   Export directory: $EXPORT_DIR"
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

# Check if database container exists
if ! docker ps -q -f name="$CONTAINER_NAME" > /dev/null; then
    echo -e "${RED}❌ Database container not running${NC}"
    exit 1
fi
echo "   ✅ Database container running"

# Test database connection
if ! docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database${NC}"
    exit 1
fi
echo "   ✅ Database connection successful"

# Check if season exists
SEASON_EXISTS=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM seasons WHERE year = '$SEASON_YEAR';" 2>/dev/null | tr -d ' ')

if [ "$SEASON_EXISTS" = "0" ]; then
    echo -e "${RED}❌ Season $SEASON_YEAR not found in database${NC}"
    echo ""
    echo "Available seasons:"
    docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "SELECT year, name, is_active FROM seasons ORDER BY year DESC;"
    exit 1
fi
echo "   ✅ Season $SEASON_YEAR found"

# Get season ID
SEASON_ID=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -c "SELECT id FROM seasons WHERE year = '$SEASON_YEAR';" 2>/dev/null | tr -d ' ')
echo "   📋 Season ID: $SEASON_ID"

echo ""
echo "📊 Analyzing season data..."

# Count records
LEAGUES_COUNT=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM leagues WHERE season_id = '$SEASON_ID';" 2>/dev/null | tr -d ' ')
TEAMS_COUNT=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM fantasy_teams WHERE league_id IN (SELECT id FROM leagues WHERE season_id = '$SEASON_ID');" 2>/dev/null | tr -d ' ')
PERFORMANCES_COUNT=$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM player_performances WHERE league_id IN (SELECT id FROM leagues WHERE season_id = '$SEASON_ID');" 2>/dev/null | tr -d ' ')

echo "   📋 Leagues: $LEAGUES_COUNT"
echo "   👥 Fantasy teams: $TEAMS_COUNT"
echo "   🏏 Player performances: $PERFORMANCES_COUNT"

if [ "$LEAGUES_COUNT" = "0" ] && [ "$TEAMS_COUNT" = "0" ] && [ "$PERFORMANCES_COUNT" = "0" ]; then
    echo -e "${YELLOW}⚠️  No data found for season $SEASON_YEAR${NC}"
    echo "   Season exists but has no associated data"
    read -p "Continue with export anyway? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Export cancelled"
        exit 0
    fi
fi

echo ""
echo "📤 Starting export..."

# Export 1: Season metadata
echo ""
echo "1️⃣  Exporting season metadata..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "\COPY (SELECT * FROM seasons WHERE year = '$SEASON_YEAR') TO STDOUT WITH CSV HEADER" > "$EXPORT_DIR/season_metadata_$TIMESTAMP.csv"
echo "   ✅ season_metadata_$TIMESTAMP.csv"

# Export 2: Leagues
echo "2️⃣  Exporting leagues..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "\COPY (SELECT * FROM leagues WHERE season_id = '$SEASON_ID') TO STDOUT WITH CSV HEADER" > "$EXPORT_DIR/leagues_$TIMESTAMP.csv"
echo "   ✅ leagues_$TIMESTAMP.csv"

# Export 3: Fantasy teams
echo "3️⃣  Exporting fantasy teams..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "\COPY (SELECT ft.* FROM fantasy_teams ft JOIN leagues l ON ft.league_id = l.id WHERE l.season_id = '$SEASON_ID') TO STDOUT WITH CSV HEADER" > "$EXPORT_DIR/fantasy_teams_$TIMESTAMP.csv"
echo "   ✅ fantasy_teams_$TIMESTAMP.csv"

# Export 4: Fantasy team players
echo "4️⃣  Exporting fantasy team players..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "\COPY (SELECT ftp.* FROM fantasy_team_players ftp JOIN fantasy_teams ft ON ftp.fantasy_team_id = ft.id JOIN leagues l ON ft.league_id = l.id WHERE l.season_id = '$SEASON_ID') TO STDOUT WITH CSV HEADER" > "$EXPORT_DIR/fantasy_team_players_$TIMESTAMP.csv"
echo "   ✅ fantasy_team_players_$TIMESTAMP.csv"

# Export 5: Player performances
echo "5️⃣  Exporting player performances..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "\COPY (SELECT pp.* FROM player_performances pp WHERE pp.league_id IN (SELECT id FROM leagues WHERE season_id = '$SEASON_ID')) TO STDOUT WITH CSV HEADER" > "$EXPORT_DIR/player_performances_$TIMESTAMP.csv"
echo "   ✅ player_performances_$TIMESTAMP.csv"

# Export 6: Leaderboard summary (JSON)
echo "6️⃣  Exporting leaderboard summary..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -A -F"," -c "SELECT row_to_json(t) FROM (SELECT ft.id, ft.team_name, ft.total_points, ft.rank, ft.user_id, l.name as league_name FROM fantasy_teams ft JOIN leagues l ON ft.league_id = l.id WHERE l.season_id = '$SEASON_ID' ORDER BY ft.rank) t;" > "$EXPORT_DIR/leaderboard_summary_$TIMESTAMP.json"
echo "   ✅ leaderboard_summary_$TIMESTAMP.json"

# Export 7: Top 50 players by performance (JSON)
echo "7️⃣  Exporting top players..."
docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -t -A -F"," -c "SELECT row_to_json(t) FROM (SELECT p.id, p.name, SUM(pp.fantasy_points) as total_points, COUNT(pp.id) as matches_played, AVG(pp.fantasy_points) as avg_points FROM player_performances pp JOIN players p ON pp.player_id = p.id WHERE pp.league_id IN (SELECT id FROM leagues WHERE season_id = '$SEASON_ID') GROUP BY p.id, p.name ORDER BY total_points DESC LIMIT 50) t;" > "$EXPORT_DIR/top_players_$TIMESTAMP.json"
echo "   ✅ top_players_$TIMESTAMP.json"

# Export 8: Create summary report
echo "8️⃣  Creating summary report..."

cat > "$EXPORT_DIR/EXPORT_SUMMARY_$TIMESTAMP.md" << EOF
# Test Data Export Summary - Season $SEASON_YEAR

**Export Date:** $(date)
**Season ID:** $SEASON_ID
**Export Directory:** $EXPORT_DIR

---

## Data Exported

| Data Type | Count | Filename |
|-----------|-------|----------|
| Season Metadata | 1 | season_metadata_$TIMESTAMP.csv |
| Leagues | $LEAGUES_COUNT | leagues_$TIMESTAMP.csv |
| Fantasy Teams | $TEAMS_COUNT | fantasy_teams_$TIMESTAMP.csv |
| Fantasy Team Players | - | fantasy_team_players_$TIMESTAMP.csv |
| Player Performances | $PERFORMANCES_COUNT | player_performances_$TIMESTAMP.csv |
| Leaderboard Summary | - | leaderboard_summary_$TIMESTAMP.json |
| Top 50 Players | 50 | top_players_$TIMESTAMP.json |

---

## File Sizes

\`\`\`
$(ls -lh "$EXPORT_DIR"/*_$TIMESTAMP.* | awk '{print $9 " - " $5}')
\`\`\`

---

## Season Details

\`\`\`sql
$(docker exec "$CONTAINER_NAME" psql -U cricket_admin -d fantasy_cricket -c "SELECT * FROM seasons WHERE year = '$SEASON_YEAR';")
\`\`\`

---

## Export Commands Used

\`\`\`bash
# Season metadata
\\COPY (SELECT * FROM seasons WHERE year = '$SEASON_YEAR') TO STDOUT WITH CSV HEADER

# Leagues
\\COPY (SELECT * FROM leagues WHERE season_id = '$SEASON_ID') TO STDOUT WITH CSV HEADER

# Fantasy teams
\\COPY (SELECT ft.* FROM fantasy_teams ft JOIN leagues l ON ft.league_id = l.id WHERE l.season_id = '$SEASON_ID') TO STDOUT WITH CSV HEADER

# Player performances
\\COPY (SELECT pp.* FROM player_performances pp WHERE pp.league_id IN (SELECT id FROM leagues WHERE season_id = '$SEASON_ID')) TO STDOUT WITH CSV HEADER
\`\`\`

---

## Next Steps

1. **Review exported data:** Check CSV files for completeness
2. **Archive exports:** Move to long-term storage if needed
3. **Delete test data:** Run cleanup SQL to remove season $SEASON_YEAR
4. **Verify cleanup:** Ensure production data intact

---

## Cleanup SQL Commands

To delete all $SEASON_YEAR data after review:

\`\`\`sql
-- This will cascade delete leagues, fantasy_teams, player_performances, etc.
DELETE FROM seasons WHERE year = '$SEASON_YEAR';
\`\`\`

Or use the automated cleanup:

\`\`\`bash
./cleanup_test_season.sh $SEASON_YEAR
\`\`\`

---

**Export completed successfully!** ✅
EOF

echo "   ✅ EXPORT_SUMMARY_$TIMESTAMP.md"

# Calculate total export size
TOTAL_SIZE=$(du -sh "$EXPORT_DIR" | cut -f1)

echo ""
echo "=================================================================================="
echo -e "${GREEN}✅ EXPORT COMPLETE${NC}"
echo "=================================================================================="
echo ""
echo "📊 Export summary:"
echo "   Season: $SEASON_YEAR"
echo "   Leagues: $LEAGUES_COUNT"
echo "   Fantasy teams: $TEAMS_COUNT"
echo "   Player performances: $PERFORMANCES_COUNT"
echo "   Total export size: $TOTAL_SIZE"
echo ""
echo "📁 Files exported to:"
echo "   $EXPORT_DIR"
echo ""
ls -lh "$EXPORT_DIR" | grep "$TIMESTAMP"
echo ""
echo "📝 Next steps:"
echo "   1. Review exported data: cat $EXPORT_DIR/EXPORT_SUMMARY_$TIMESTAMP.md"
echo "   2. Archive if needed: tar czf season_${SEASON_YEAR}_export_${TIMESTAMP}.tar.gz $EXPORT_DIR"
echo "   3. Delete test data: ./cleanup_test_season.sh $SEASON_YEAR"
echo ""
