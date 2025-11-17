#!/bin/bash
# Generate SQL UPDATE statements from CSV and execute them

CSV_FILE="/tmp/acc_cleaned_players.csv"
DB_NAME="fantasy_cricket"
DB_USER="cricket_admin"

# Skip header and generate UPDATE statements
tail -n +2 "$CSV_FILE" | while IFS=',' read -r team player_name player_type multiplier player_id; do
    # Escape single quotes in team names if any
    team_escaped=$(echo "$team" | sed "s/'/''/g")

    psql -U "$DB_USER" -d "$DB_NAME" -c "UPDATE players SET rl_team = '$team_escaped' WHERE id = '$player_id';"
done

# Show summary
echo "✅ rl_team update complete!"
echo ""
psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT rl_team, COUNT(*) as player_count FROM players WHERE rl_team IS NOT NULL GROUP BY rl_team ORDER BY rl_team;"
