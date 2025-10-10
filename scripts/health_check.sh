#!/bin/bash

cd /home/$USER/fantasy-cricket-leafcloud

echo "ðŸ” Fantasy Cricket Platform Health Check - $(date)"
echo "================================================="

# Check containers
for service in fantasy_cricket_db fantasy_cricket_redis fantasy_cricket_api fantasy_cricket_worker; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "âœ… $service: Running"
    else
        echo "âŒ $service: Down"
        # Try to restart
        docker-compose restart $service
    fi
done

# Check API health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$API_STATUS" = "200" ]; then
    echo "âœ… API: Healthy"
else
    echo "âŒ API: Unhealthy (HTTP $API_STATUS)"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "âœ… Disk Space: ${DISK_USAGE}% used"
else
    echo "âš ï¸  Disk Space: ${DISK_USAGE}% used (Warning)"
fi

# Check memory
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')
echo "ðŸ’¾ Memory Usage: ${MEMORY_USAGE}%"

echo "â™»ï¸  Powered by LeafCloud sustainable infrastructure"
echo "================================================="