#!/bin/bash

set -e

echo "ðŸŒ± Fantasy Cricket Platform - LeafCloud Deployment"
echo "================================================="
echo "Amsterdam-based â€¢ EU Sovereign â€¢ Sustainable Computing"
echo ""

# Configuration
DOMAIN_NAME="fantcric.fun"
API_DOMAIN="api.fantcric.fun"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "âŒ Docker not found. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "âŒ Docker Compose not found. Please install Docker Compose first."; exit 1; }

echo "âœ… Prerequisites check passed"

# Create environment file
if [ ! -f .env.production ]; then
    echo "ðŸ“ Creating environment configuration..."
    cp .env.production.template .env.production
    
    echo ""
    echo "âš ï¸  IMPORTANT: Please edit .env.production and set:"
    echo "   - DB_PASSWORD (secure database password)"
    echo "   - JWT_SECRET_KEY (256-bit secret key)" 
    echo "   - SMTP credentials (for email invitations)"
    echo "   - GRAFANA_PASSWORD (admin dashboard password)"
    echo ""
    read -p "Press Enter when you've updated .env.production..."
fi

# Create required directories
mkdir -p {logs,ssl,static}

# Setup SSL certificates (Let's Encrypt) - Skip for local development
echo "🔒 Checking SSL certificates..."
if [ ! -f ssl/${DOMAIN_NAME}.crt ]; then
    echo "⚠️  SSL certificates not found - running in HTTP mode (local development)"
    echo "   For production deployment, set up SSL certificates manually"
    # Create dummy certificates for local testing
    mkdir -p ssl
    touch ssl/${DOMAIN_NAME}.crt
    touch ssl/${DOMAIN_NAME}.key
else
    echo "✅ SSL certificates found"
fi

# Build and deploy containers
echo "ðŸ³ Building and deploying containers..."
docker-compose --env-file .env.production up -d --build

# Wait for services to be ready
echo "â³ Waiting for services to be ready..."
sleep 30

# Check service health
echo "ðŸ” Checking service health..."
for service in fantasy_cricket_db fantasy_cricket_redis fantasy_cricket_api; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "âœ… $service is running"
    else
        echo "âŒ $service failed to start"
        docker-compose logs $service
        exit 1
    fi
done

# Verify API is responding
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$API_STATUS" = "200" ]; then
    echo "âœ… API health check passed"
else
    echo "âŒ API health check failed (HTTP $API_STATUS)"
    echo "Checking API logs..."
    docker-compose logs fantasy_cricket_api
    exit 1
fi

# Setup log rotation
echo "ðŸ“ Setting up log rotation..."
sudo tee /etc/logrotate.d/fantasy-cricket > /dev/null << LOGROTATE
./logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
    postrotate
        docker-compose exec fantasy_cricket_api kill -USR1 1
    endscript
}
LOGROTATE

# Setup system monitoring
echo "ðŸ“Š Setting up monitoring..."
./scripts/setup_monitoring.sh

echo ""
echo "ðŸŽ‰ Deployment Complete!"
echo "======================"
echo ""
echo "ðŸŒ Your Fantasy Cricket platform is now running on LeafCloud's"
echo "   sustainable infrastructure in Amsterdam!"
echo ""
echo "ðŸ“‹ Access URLs:"
echo "   â€¢ Main Application: https://$DOMAIN_NAME"
echo "   â€¢ API Documentation: https://$API_DOMAIN/docs"
echo "   â€¢ Monitoring Dashboard: https://$DOMAIN_NAME:3000"
echo ""
echo "ðŸ”§ Next Steps:"
echo "   1. Visit https://$DOMAIN_NAME to access your platform"
echo "   2. Create an admin account"
echo "   3. Set up your first cricket league"
echo "   4. Import KNCB player data"
echo "   5. Invite club members to join"
echo ""
echo "ðŸŒ± Your servers are now heating Dutch homes while running cricket analytics!"
echo "â™»ï¸  Sustainable computing at its finest - powered by LeafCloud Amsterdam"

# Show status
echo ""
echo "ðŸ“Š Current System Status:"
docker-compose ps