#!/bin/bash

echo "ðŸ“Š Setting up monitoring and alerting..."

# Create Grafana dashboards directory
mkdir -p monitoring/grafana/dashboards

# Create basic dashboard for Fantasy Cricket metrics
cat > monitoring/grafana/dashboards/fantasy-cricket.json << 'JSON'
{
  "dashboard": {
    "id": null,
    "title": "Fantasy Cricket Platform",
    "tags": ["fantasy-cricket", "leafcloud"],
    "timezone": "Europe/Amsterdam",
    "panels": [
      {
        "title": "API Response Time",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(http_request_duration_seconds)",
            "legendFormat": "Avg Response Time"
          }
        ]
      },
      {
        "title": "Weekly Updates Status",
        "type": "table",
        "targets": [
          {
            "expr": "fantasy_cricket_weekly_updates_total",
            "legendFormat": "Updates"
          }
        ]
      }
    ]
  }
}
JSON

# Setup system monitoring
crontab -l | { cat; echo "*/5 * * * * /home/$USER/fantasy-cricket-leafcloud/scripts/health_check.sh"; } | crontab -

echo "âœ… Monitoring setup complete"