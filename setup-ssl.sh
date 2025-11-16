#!/bin/bash

##############################################################################
# Fantasy Cricket Platform - SSL and Security Setup Script
# Sets up Let's Encrypt SSL certificates and firewall
##############################################################################

set -e  # Exit on error

echo "🔒 Fantasy Cricket Platform - SSL & Security Setup"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration from .env
DOMAIN_NAME=${DOMAIN_NAME:-"fantcric.fun"}
API_DOMAIN=${API_DOMAIN:-"api.fantcric.fun"}

echo -e "\n${YELLOW}Domains to secure:${NC}"
echo "  - $DOMAIN_NAME"
echo "  - $API_DOMAIN"

# Step 1: Install Certbot
echo -e "\n${YELLOW}1️⃣  Installing Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅ Certbot installed${NC}"
else
    echo -e "${GREEN}✅ Certbot already installed${NC}"
fi

# Step 2: Configure Firewall
echo -e "\n${YELLOW}2️⃣  Configuring UFW Firewall...${NC}"

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    echo "Installing UFW..."
    sudo apt-get install -y ufw
fi

# Configure firewall rules
echo "Setting up firewall rules..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt verification)
sudo ufw allow 443/tcp  # HTTPS

# Enable firewall (will ask for confirmation)
echo -e "${YELLOW}About to enable firewall. This will ask for confirmation.${NC}"
sudo ufw --force enable

echo -e "${GREEN}✅ Firewall configured${NC}"
sudo ufw status

# Step 3: Stop Nginx temporarily for certificate generation
echo -e "\n${YELLOW}3️⃣  Stopping Nginx temporarily...${NC}"
docker-compose stop fantasy_cricket_nginx || true
echo -e "${GREEN}✅ Nginx stopped${NC}"

# Step 4: Obtain SSL Certificates
echo -e "\n${YELLOW}4️⃣  Obtaining SSL certificates from Let's Encrypt...${NC}"
echo -e "${YELLOW}This will use standalone mode for certificate generation${NC}"

# Check if certificates already exist
if [ -d "/etc/letsencrypt/live/$DOMAIN_NAME" ]; then
    echo -e "${YELLOW}Certificates already exist. Renewing...${NC}"
    sudo certbot renew
else
    echo -e "${YELLOW}Obtaining new certificates...${NC}"
    sudo certbot certonly --standalone \
        -d $DOMAIN_NAME \
        -d $API_DOMAIN \
        --non-interactive \
        --agree-tos \
        --email admin@${DOMAIN_NAME} \
        --preferred-challenges http
fi

echo -e "${GREEN}✅ SSL certificates obtained${NC}"

# Step 5: Update Nginx configuration to use Let's Encrypt certificates
echo -e "\n${YELLOW}5️⃣  Updating Nginx configuration...${NC}"

# Create symbolic links to Let's Encrypt certificates
sudo mkdir -p ./ssl
sudo ln -sf /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem ./ssl/fantcric.fun.crt
sudo ln -sf /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem ./ssl/fantcric.fun.key

echo -e "${GREEN}✅ Nginx configuration updated${NC}"

# Step 6: Restart Nginx
echo -e "\n${YELLOW}6️⃣  Restarting Nginx with SSL...${NC}"
docker-compose up -d fantasy_cricket_nginx
sleep 5

# Check if Nginx is running
if docker ps | grep -q "fantasy_cricket_nginx"; then
    echo -e "${GREEN}✅ Nginx is running with SSL${NC}"
else
    echo -e "${RED}❌ Nginx failed to start${NC}"
    docker-compose logs fantasy_cricket_nginx
    exit 1
fi

# Step 7: Setup automatic certificate renewal
echo -e "\n${YELLOW}7️⃣  Setting up automatic certificate renewal...${NC}"

# Create renewal hook script
cat > /tmp/renew-hook.sh << 'EOF'
#!/bin/bash
# Reload Nginx after certificate renewal
cd /home/ubuntu/fantasy-cricket
docker-compose restart fantasy_cricket_nginx
EOF

chmod +x /tmp/renew-hook.sh
sudo mv /tmp/renew-hook.sh /etc/letsencrypt/renewal-hooks/deploy/fantasy-cricket-reload.sh

# Test renewal process (dry run)
echo "Testing certificate renewal (dry run)..."
sudo certbot renew --dry-run

echo -e "${GREEN}✅ Automatic renewal configured${NC}"

# Step 8: Security Summary
echo -e "\n=============================================="
echo -e "${GREEN}🎉 SSL and Security Setup Complete!${NC}"
echo -e "=============================================="
echo ""
echo "🔒 SSL/TLS:"
echo "   - Certificates obtained from Let's Encrypt"
echo "   - HTTPS enabled for $DOMAIN_NAME and $API_DOMAIN"
echo "   - Auto-renewal configured (runs twice daily)"
echo ""
echo "🛡️  Firewall (UFW):"
echo "   - Port 22 (SSH): Open"
echo "   - Port 80 (HTTP): Open (redirects to HTTPS)"
echo "   - Port 443 (HTTPS): Open"
echo "   - All other ports: Blocked"
echo ""
echo "🧪 Test Your Setup:"
echo "   https://$DOMAIN_NAME"
echo "   https://$API_DOMAIN/health"
echo ""
echo "📋 SSL Certificate Info:"
sudo certbot certificates
echo ""
echo "🔄 Manual Certificate Renewal:"
echo "   sudo certbot renew"
echo ""
echo -e "${GREEN}✅ Your Fantasy Cricket platform is now secure!${NC}"
