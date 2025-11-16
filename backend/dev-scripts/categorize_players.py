"""
Categorize players based on their stats
"""
from database import SessionLocal
from database_models import Player

def categorize_player(runs, wickets, matches):
    """
    Categorize player based on their stats:
    - batsman: primarily scores runs (high runs, low wickets)
    - bowler: primarily takes wickets (high wickets, low runs)
    - all-rounder: contributes with both bat and ball (default for players with no data)

    Note: wicket-keeper is a separate boolean flag, not a player_type
    """
    # Default to all-rounder for players with no matches
    if matches == 0:
        return 'all-rounder'

    # Calculate per-match averages
    runs_per_match = runs / matches
    wickets_per_match = wickets / matches

    # Thresholds for categorization
    SIGNIFICANT_RUNS = 30  # Average runs per match to be considered a batsman
    SIGNIFICANT_WICKETS = 3  # Average wickets per match to be considered a bowler

    # All-rounder: significant contribution in both
    if runs_per_match >= SIGNIFICANT_RUNS and wickets_per_match >= SIGNIFICANT_WICKETS:
        return 'all-rounder'

    # Bowler: more wickets than runs contribution
    elif wickets_per_match >= SIGNIFICANT_WICKETS:
        return 'bowler'

    # Batsman: more runs contribution
    elif runs_per_match >= SIGNIFICANT_RUNS:
        return 'batsman'

    # Edge cases: low contribution but need to classify
    elif wickets > runs / 10:  # If wickets are significant relative to runs
        return 'bowler'
    elif runs > wickets * 10:  # If runs are significant relative to wickets
        return 'batsman'

    # Default to all-rounder if both have some contribution or unclear
    else:
        return 'all-rounder'

def main():
    db = SessionLocal()

    try:
        players = db.query(Player).filter(
            Player.club_id == 'a7a580a7-7d3f-476c-82ea-afa6ae7ee276',
            Player.player_type.is_(None)  # Only update players without a type
        ).all()

        updated_count = 0
        skipped_count = 0

        for player in players:
            if not player.stats:
                skipped_count += 1
                continue

            runs = player.stats.get('runs', 0) or 0
            wickets = player.stats.get('wickets', 0) or 0
            matches = player.stats.get('matches', 0) or 0

            player_type = categorize_player(runs, wickets, matches)
            player.player_type = player_type
            updated_count += 1

            if matches == 0:
                print(f"✓ {player.name}: No stats → {player_type} (default)")
            else:
                print(f"✓ {player.name}: {runs}R, {wickets}W in {matches}M → {player_type}")

        db.commit()
        print(f"\n{'='*60}")
        print(f"Updated: {updated_count} players")
        print(f"Skipped: {skipped_count} players (no stats or already categorized)")
        print(f"{'='*60}")

    finally:
        db.close()

if __name__ == '__main__':
    main()
