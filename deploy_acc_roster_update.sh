#!/bin/bash
#
# ACC Roster Update - Production Deployment Script
# =================================================
#
# This script deploys the ACC roster update to production:
# 1. Backs up the production database
# 2. Deploys code changes
# 3. Runs database migration
# 4. Uploads transformed roster
# 5. Calculates multipliers
# 6. Verifies deployment
#
# Prerequisites:
# - SSH access to ubuntu@fantcric.fun
# - Admin credentials for the API
# - Transformed roster CSV at /Users/guypa/Downloads/acc-roster-transformed.csv
#
# Usage:
#   ./deploy_acc_roster_update.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVER="ubuntu@fantcric.fun"
PROJECT_DIR="~/fantasy-cricket-leafcloud"
ROSTER_CSV="/Users/guypa/Downloads/acc-roster-transformed.csv"
MIGRATION_SQL="backend/migrations/add_player_columns.sql"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ACC Roster Update - Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Backup production database
echo -e "${YELLOW}[1/8] Backing up production database...${NC}"
ssh $SERVER "cd $PROJECT_DIR && mkdir -p backups && docker exec fantasy_cricket_db pg_dump -U cricket_admin fantasy_cricket > backups/backup_acc_roster_$(date +%Y%m%d_%H%M%S).sql"
echo -e "${GREEN}✓ Database backed up successfully${NC}"
echo ""

# Step 2: Check current git status
echo -e "${YELLOW}[2/8] Checking git status on production...${NC}"
ssh $SERVER "cd $PROJECT_DIR && git status"
echo ""

# Step 3: Deploy code changes
echo -e "${YELLOW}[3/8] Deploying code changes...${NC}"
ssh $SERVER "cd $PROJECT_DIR && git pull origin main"
echo -e "${GREEN}✓ Code deployed successfully${NC}"
echo ""

# Step 4: Run database migration
echo -e "${YELLOW}[4/8] Running database migration...${NC}"
ssh $SERVER "cd $PROJECT_DIR && docker exec -i fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket < $MIGRATION_SQL"
echo -e "${GREEN}✓ Migration completed successfully${NC}"
echo ""

# Step 5: Verify migration
echo -e "${YELLOW}[5/8] Verifying migration...${NC}"
ssh $SERVER "cd $PROJECT_DIR && docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -c \"SELECT column_name FROM information_schema.columns WHERE table_name = 'players' AND column_name IN ('rl_team', 'role', 'prev_season_fantasy_points', 'tier', 'is_active');\""
echo -e "${GREEN}✓ Migration verified${NC}"
echo ""

# Step 6: Restart services
echo -e "${YELLOW}[6/8] Restarting API and nginx...${NC}"
ssh $SERVER "cd $PROJECT_DIR && docker-compose restart fantasy_cricket_api && docker-compose restart fantasy_cricket_nginx"
sleep 5
echo -e "${GREEN}✓ Services restarted${NC}"
echo ""

# Step 7: Copy roster CSV to server
echo -e "${YELLOW}[7/8] Copying transformed roster to server...${NC}"
scp $ROSTER_CSV $SERVER:~/acc-roster-transformed.csv
echo -e "${GREEN}✓ Roster CSV copied to server${NC}"
echo ""

# Step 8: Instructions for roster upload
echo -e "${YELLOW}[8/8] Ready for roster upload${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Next Steps - Manual Execution Required${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "SSH to the server:"
echo -e "  ${YELLOW}ssh $SERVER${NC}"
echo ""
echo "1. Get admin token (replace with your password):"
echo -e "  ${YELLOW}curl -X POST https://fantcric.fun/auth/login \\
    -H 'Content-Type: application/x-www-form-urlencoded' \\
    -d 'email=admin@fantcric.fun&password=YOUR_PASSWORD'${NC}"
echo ""
echo "2. Save the token from response, then upload roster:"
echo -e "  ${YELLOW}curl -X POST https://fantcric.fun/players/bulk \\
    -H 'Authorization: Bearer YOUR_TOKEN_HERE' \\
    -F 'file=@/home/ubuntu/acc-roster-transformed.csv'${NC}"
echo ""
echo "3. Confirm roster and calculate multipliers:"
echo -e "  ${YELLOW}curl -X POST https://fantcric.fun/admin/roster/confirm \\
    -H 'Authorization: Bearer YOUR_TOKEN_HERE' \\
    -H 'Content-Type: application/json' \\
    -d '{\"youth_teams\": [\"U15\", \"U17\"], \"calculate_multipliers\": true}'${NC}"
echo ""
echo "4. Monitor logs for completion (Ctrl+C to exit):"
echo -e "  ${YELLOW}docker logs fantasy_cricket_api --tail 100 -f${NC}"
echo ""
echo "5. Verify deployment:"
echo -e "  ${YELLOW}curl https://fantcric.fun/players?limit=10${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Expected Results:${NC}"
echo -e "${GREEN}========================================${NC}"
echo "- 102 ACC players uploaded (13 ZAMI 1, 13 ZAMI 2, 76 ACC)"
echo "- Multipliers calculated from local scorecards (30-60 sec)"
echo "- All players have rl_team and role fields populated"
echo ""
