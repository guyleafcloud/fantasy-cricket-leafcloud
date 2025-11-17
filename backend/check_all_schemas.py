#!/usr/bin/env python3
"""
Comprehensive Schema Checker
Check ALL models against database schema to find mismatches
"""

import subprocess
import json

# Define all models and their expected columns from database_models.py
MODELS = {
    "users": ["id", "email", "password_hash", "full_name", "is_active", "is_verified", "is_admin", "created_at", "last_login"],
    "seasons": ["id", "year", "name", "start_date", "end_date", "description", "is_active", "registration_open", "scraping_enabled", "created_at", "updated_at", "created_by"],
    "clubs": ["id", "name", "tier", "location", "founded_year", "created_at", "season_id"],
    "teams": ["id", "club_id", "name", "level", "tier_type", "value_multiplier", "points_multiplier", "created_at", "updated_at"],
    "players": ["id", "name", "club_id", "rl_team", "role", "tier", "base_price", "current_price", "multiplier", "multiplier_updated_at", "matches_played", "runs_scored", "balls_faced", "wickets_taken", "balls_bowled", "catches", "stumpings", "batting_average", "strike_rate", "bowling_average", "economy_rate", "total_fantasy_points", "is_active", "created_at"],
    "player_price_history": ["id", "player_id", "old_value", "new_value", "change_reason", "reason_details", "changed_at", "changed_by"],
    "leagues": ["id", "season_id", "club_id", "name", "description", "league_code", "squad_size", "budget", "currency", "transfers_per_season", "min_players_per_team", "max_players_per_team", "require_from_each_team", "min_batsmen", "min_bowlers", "require_wicket_keeper", "is_public", "max_participants", "created_at", "updated_at", "created_by"],
    "fantasy_teams": ["id", "league_id", "user_id", "team_name", "budget_used", "budget_remaining", "is_finalized", "total_points", "rank", "transfers_used", "extra_transfers_granted", "created_at", "updated_at"],
    "fantasy_team_players": ["id", "fantasy_team_id", "player_id", "purchase_value", "is_captain", "is_vice_captain", "is_wicket_keeper", "position", "total_points", "added_at"],
    "transfers": ["id", "fantasy_team_id", "player_out_id", "player_in_id", "transfer_type", "requires_approval", "is_approved", "approved_by", "proof_url", "created_at", "approved_at"],
    "matches": ["id", "season_id", "club_id", "match_date", "opponent", "match_title", "venue", "matchcentre_id", "scorecard_url", "period_id", "result", "match_type", "is_processed", "processed_at", "raw_scorecard_data", "created_at", "updated_at"],
    "player_performances": ["id", "match_id", "player_id", "runs", "balls_faced", "fours", "sixes", "batting_strike_rate", "is_out", "dismissal_type", "overs_bowled", "maidens", "runs_conceded", "wickets", "bowling_economy", "catches", "run_outs", "stumpings", "fantasy_points", "points_breakdown", "created_at", "updated_at"]
}

def get_db_columns(table_name):
    """Get actual columns from database"""
    cmd = f"""docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position;
    " """

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return None

    columns = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    return columns

def main():
    print("="*80)
    print("COMPREHENSIVE SCHEMA MISMATCH CHECKER")
    print("="*80)
    print()

    all_mismatches = []
    tables_checked = 0
    tables_with_mismatches = 0

    for table_name, model_columns in MODELS.items():
        tables_checked += 1
        print(f"\n{'='*80}")
        print(f"Checking table: {table_name}")
        print(f"{'='*80}")

        db_columns = get_db_columns(table_name)

        if db_columns is None:
            print(f"❌ TABLE DOES NOT EXIST IN DATABASE")
            all_mismatches.append({
                "table": table_name,
                "error": "Table does not exist",
                "model_columns": model_columns,
                "db_columns": []
            })
            tables_with_mismatches += 1
            continue

        model_set = set(model_columns)
        db_set = set(db_columns)

        # Find mismatches
        in_model_not_db = model_set - db_set
        in_db_not_model = db_set - model_set

        if in_model_not_db or in_db_not_model:
            tables_with_mismatches += 1
            print(f"⚠️  MISMATCH FOUND")

            if in_model_not_db:
                print(f"\n  📋 In MODEL but NOT in DATABASE:")
                for col in sorted(in_model_not_db):
                    print(f"     ❌ {col}")

            if in_db_not_model:
                print(f"\n  📋 In DATABASE but NOT in MODEL:")
                for col in sorted(in_db_not_model):
                    print(f"     ❌ {col}")

            all_mismatches.append({
                "table": table_name,
                "in_model_not_db": list(in_model_not_db),
                "in_db_not_model": list(in_db_not_model)
            })
        else:
            print(f"✅ Schema matches perfectly ({len(model_columns)} columns)")

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Tables checked: {tables_checked}")
    print(f"Tables with mismatches: {tables_with_mismatches}")
    print(f"Tables OK: {tables_checked - tables_with_mismatches}")

    if all_mismatches:
        print(f"\n❌ FOUND {len(all_mismatches)} TABLES WITH SCHEMA MISMATCHES")
        print("\nDetails:")
        for mismatch in all_mismatches:
            print(f"\n  Table: {mismatch['table']}")
            if 'error' in mismatch:
                print(f"    Error: {mismatch['error']}")
            else:
                if mismatch.get('in_model_not_db'):
                    print(f"    Missing in DB: {', '.join(mismatch['in_model_not_db'])}")
                if mismatch.get('in_db_not_model'):
                    print(f"    Extra in DB: {', '.join(mismatch['in_db_not_model'])}")
    else:
        print("\n✅ ALL SCHEMAS MATCH PERFECTLY!")

    print(f"\n{'='*80}")

    # Save to file
    with open('/tmp/schema_mismatches.json', 'w') as f:
        json.dump(all_mismatches, f, indent=2)
    print(f"\nDetailed results saved to: /tmp/schema_mismatches.json")

    return len(all_mismatches)

if __name__ == "__main__":
    exit(main())
