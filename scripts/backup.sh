#!/bin/bash

BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "ðŸ’¾ Creating backup: cricket_backup_$DATE"

# Database backup
docker-compose exec -T fantasy_cricket_db pg_dump -U cricket_admin fantasy_cricket | gzip > "$BACKUP_DIR/cricket_db_$DATE.sql.gz"

# Application logs backup
tar -czf "$BACKUP_DIR/cricket_logs_$DATE.tar.gz" logs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "cricket_*" -mtime +7 -delete

echo "âœ… Backup completed: $BACKUP_DIR/cricket_backup_$DATE"