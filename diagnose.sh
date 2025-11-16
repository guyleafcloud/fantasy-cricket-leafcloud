#!/bin/bash

##############################################################################
# Fantasy Cricket Platform - Diagnostic Script
##############################################################################

echo "🔍 Fantasy Cricket Platform - Diagnostics"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Check Docker containers
echo -e "\n${YELLOW}1️⃣  Docker Containers Status:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Check Nginx specifically
echo -e "\n${YELLOW}2️⃣  Nginx Container:${NC}"
if docker ps | grep -q "fantasy_cricket_nginx"; then
    echo -e "${GREEN}✅ Nginx container is running${NC}"
    docker logs fantasy_cricket_nginx --tail 20
else
    echo -e "${RED}❌ Nginx container is NOT running${NC}"
    echo "Attempting to check logs:"
    docker logs fantasy_cricket_nginx --tail 50 || echo "No logs available"
fi

# 3. Check if Nginx is listening on ports
echo -e "\n${YELLOW}3️⃣  Port Listening Status:${NC}"
sudo netstat -tlnp | grep -E ':80|:443' || ss -tlnp | grep -E ':80|:443'

# 4. Check UFW firewall
echo -e "\n${YELLOW}4️⃣  Firewall Status:${NC}"
sudo ufw status

# 5. Test local connectivity
echo -e "\n${YELLOW}5️⃣  Local Connectivity Tests:${NC}"
echo "Testing localhost:80..."
curl -I http://localhost:80 2>&1 | head -5 || echo "Failed to connect to port 80"

echo -e "\nTesting localhost:443..."
curl -Ik https://localhost:443 2>&1 | head -5 || echo "Failed to connect to port 443"

echo -e "\nTesting API container directly (port 8000)..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Failed to connect to API"

# 6. Check DNS resolution
echo -e "\n${YELLOW}6️⃣  DNS Resolution:${NC}"
echo "Resolving fantcric.fun..."
nslookup fantcric.fun || dig fantcric.fun

echo -e "\nResolving api.fantcric.fun..."
nslookup api.fantcric.fun || dig api.fantcric.fun

# 7. Check SSL certificates
echo -e "\n${YELLOW}7️⃣  SSL Certificates:${NC}"
if [ -d "/etc/letsencrypt/live/fantcric.fun" ]; then
    echo -e "${GREEN}✅ Certificates exist${NC}"
    sudo certbot certificates
else
    echo -e "${RED}❌ No certificates found${NC}"
fi

# 8. Check nginx config
echo -e "\n${YELLOW}8️⃣  Nginx Configuration Test:${NC}"
docker exec fantasy_cricket_nginx nginx -t 2>&1 || echo "Cannot test nginx config"

# 9. Check if SSL directory is mounted
echo -e "\n${YELLOW}9️⃣  SSL Directory Mount:${NC}"
ls -la ./ssl/ || echo "SSL directory not found locally"
docker exec fantasy_cricket_nginx ls -la /etc/nginx/ssl/ 2>&1 || echo "Cannot check SSL in container"

# 10. Summary
echo -e "\n=========================================="
echo -e "${YELLOW}📋 Quick Fixes:${NC}"
echo ""
echo "If Nginx is not running:"
echo "  docker-compose restart fantasy_cricket_nginx"
echo ""
echo "If SSL certificates are missing:"
echo "  sudo ./setup-ssl.sh"
echo ""
echo "If ports are not listening:"
echo "  docker-compose down && docker-compose up -d"
echo ""
echo "Check full nginx logs:"
echo "  docker logs fantasy_cricket_nginx"
echo ""
echo "Restart all services:"
echo "  docker-compose restart"
