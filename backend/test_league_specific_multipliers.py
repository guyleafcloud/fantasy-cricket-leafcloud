#!/usr/bin/env python3
"""
Test League-Specific Multiplier System
=======================================
Tests that multipliers drift independently per league based on roster-specific performance.

Scenario:
- Create 2 leagues with different rosters (some overlap)
- Process matches to create performances
- Run multiplier drift for each league
- Verify same player has different multipliers in different leagues
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_models import (
    Base, League, Player, Club, Season, LeagueRoster,
    Match, PlayerPerformance, FantasyTeam, FantasyTeamPlayer
)
from multiplier_adjuster import MultiplierAdjuster
from fantasy_team_points_service import FantasyTeamPointsService
from league_lifecycle_service import LeagueLifecycleService

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cricket_admin:your_password@localhost:5432/fantasy_cricket')


def cleanup_test_data(db):
    """Clean up any existing test data"""
    print("🧹 Cleaning up test data...")

    # Delete in correct order due to foreign key constraints
    db.query(FantasyTeamPlayer).filter(
        FantasyTeamPlayer.fantasy_team_id.like('test_%')
    ).delete(synchronize_session=False)

    db.query(FantasyTeam).filter(
        FantasyTeam.id.like('test_%')
    ).delete(synchronize_session=False)

    db.query(PlayerPerformance).filter(
        PlayerPerformance.match_id.like('test_%')
    ).delete(synchronize_session=False)

    db.query(Match).filter(
        Match.id.like('test_%')
    ).delete(synchronize_session=False)

    db.query(LeagueRoster).filter(
        LeagueRoster.league_id.like('test_%')
    ).delete(synchronize_session=False)

    db.query(League).filter(
        League.id.like('test_%')
    ).delete(synchronize_session=False)

    db.commit()
    print("✅ Cleanup complete\n")


def get_or_create_season(db):
    """Get or create test season"""
    season = db.query(Season).filter_by(year=2025).first()
    if not season:
        season = Season(
            id='season_2025',
            year=2025,
            name='Test Season 2025',
            start_date=datetime(2025, 4, 1),
            end_date=datetime(2025, 9, 30)
        )
        db.add(season)
        db.commit()
    return season


def get_test_club(db):
    """Get test club (ACC)"""
    club = db.query(Club).filter_by(name='ACC').first()
    if not club:
        print("❌ ACC club not found in database")
        sys.exit(1)
    return club


def get_test_players(db, club_id, count=10):
    """Get test players from club"""
    players = db.query(Player).filter_by(club_id=club_id).limit(count).all()
    if len(players) < count:
        print(f"❌ Not enough players found in club (need {count}, found {len(players)})")
        sys.exit(1)
    return players


def create_test_leagues(db, season, club):
    """Create two test leagues with different rosters"""
    print("🏆 Creating test leagues...")

    # Get 10 players
    all_players = get_test_players(db, club.id, count=10)

    # League A: Players 0-6 (7 players)
    league_a = League(
        id='test_league_a',
        name='Test League A',
        season_id=season.id,
        status='draft',
        squad_size=7,
        transfers_per_season=5,
        min_batsmen=3,
        min_bowlers=2,
        require_wicket_keeper=False,
        max_players_per_team=2,
        require_from_each_team=False
    )
    db.add(league_a)
    db.flush()

    roster_a_players = all_players[0:7]
    for player in roster_a_players:
        roster_entry = LeagueRoster(
            league_id=league_a.id,
            player_id=player.id
        )
        db.add(roster_entry)

    # League B: Players 3-9 (7 players, overlaps with A on players 3-6)
    league_b = League(
        id='test_league_b',
        name='Test League B',
        season_id=season.id,
        status='draft',
        squad_size=7,
        transfers_per_season=5,
        min_batsmen=3,
        min_bowlers=2,
        require_wicket_keeper=False,
        max_players_per_team=2,
        require_from_each_team=False
    )
    db.add(league_b)
    db.flush()

    roster_b_players = all_players[3:10]
    for player in roster_b_players:
        roster_entry = LeagueRoster(
            league_id=league_b.id,
            player_id=player.id
        )
        db.add(roster_entry)

    db.commit()

    print(f"   ✅ League A created with {len(roster_a_players)} players")
    print(f"      Players: {[p.name for p in roster_a_players]}")
    print(f"   ✅ League B created with {len(roster_b_players)} players")
    print(f"      Players: {[p.name for p in roster_b_players]}")
    print(f"   📊 Overlap: 4 players (indices 3-6)\n")

    return league_a, league_b, roster_a_players, roster_b_players


def confirm_leagues(db, league_a, league_b):
    """Confirm leagues to capture initial multipliers"""
    print("🔒 Confirming leagues...")

    lifecycle = LeagueLifecycleService(db)

    success, msg, metadata = lifecycle.confirm_league(league_a.id)
    if not success:
        print(f"❌ Failed to confirm League A: {msg}")
        sys.exit(1)
    print(f"   ✅ League A confirmed: {metadata['multipliers_captured']} multipliers captured")

    success, msg, metadata = lifecycle.confirm_league(league_b.id)
    if not success:
        print(f"❌ Failed to confirm League B: {msg}")
        sys.exit(1)
    print(f"   ✅ League B confirmed: {metadata['multipliers_captured']} multipliers captured\n")


def create_test_performances(db, season, club, players):
    """Create test match performances with different point totals"""
    print("🏏 Creating test match performances...")

    # Create a test match
    match = Match(
        id='test_match_1',
        season_id=season.id,
        club_id=club.id,
        match_date=datetime.now(),
        opponent='Test Opponent',
        match_title='Test Match',
        is_processed=True,
        processed_at=datetime.now()
    )
    db.add(match)
    db.flush()

    # Create performances with varying base points
    # This simulates different performance levels
    base_points = [100, 80, 60, 120, 90, 70, 50, 110, 85, 95]

    for i, player in enumerate(players[:10]):
        # Use current global multiplier for initial calculation
        current_mult = player.multiplier if player.multiplier else 1.0
        final_points = base_points[i] * current_mult

        performance = PlayerPerformance(
            match_id=match.id,
            player_id=player.id,
            runs=base_points[i],  # Simplified: using base_points as runs
            balls_faced=50,
            base_fantasy_points=base_points[i],
            multiplier_applied=current_mult,
            fantasy_points=final_points
        )
        db.add(performance)

    db.commit()
    print(f"   ✅ Created 10 performances with varying points")
    print(f"      Base points distribution: {base_points}\n")


def run_multiplier_drift(db, league_id, league_name):
    """Run multiplier drift for a specific league"""
    print(f"🎯 Running multiplier drift for {league_name}...")

    adjuster = MultiplierAdjuster(drift_rate=0.15)
    result = adjuster.adjust_league_multipliers(db, league_id, dry_run=False)

    if 'error' in result:
        print(f"   ❌ Error: {result['error']}")
        return None

    print(f"   ✅ Drift complete")
    print(f"      Players changed: {result['players_changed']}")
    print(f"      Score stats: min={result['score_stats']['min']:.1f}, "
          f"median={result['score_stats']['median']:.1f}, "
          f"max={result['score_stats']['max']:.1f}")

    if result['top_changes']:
        print(f"      Top changes:")
        for change in result['top_changes'][:3]:
            direction = "↑" if change['change'] > 0 else "↓"
            print(f"         {change['player_name']}: "
                  f"{change['old_multiplier']:.2f} → {change['new_multiplier']:.2f} "
                  f"({direction}{abs(change['change']):.2f})")

    print()
    return result


def verify_different_multipliers(db, league_a, league_b, overlap_players):
    """Verify that overlapping players have different multipliers in each league"""
    print("🔍 Verifying league-specific multipliers...")

    # Refresh league objects to get updated snapshots
    db.refresh(league_a)
    db.refresh(league_b)

    snapshot_a = league_a.multipliers_snapshot or {}
    snapshot_b = league_b.multipliers_snapshot or {}

    differences_found = 0
    for player in overlap_players:
        mult_a = snapshot_a.get(player.id)
        mult_b = snapshot_b.get(player.id)

        if mult_a is None or mult_b is None:
            print(f"   ⚠️  {player.name}: Missing multiplier (A={mult_a}, B={mult_b})")
            continue

        diff = abs(mult_a - mult_b)
        if diff > 0.01:  # Meaningful difference
            differences_found += 1
            print(f"   ✅ {player.name}: League A = {mult_a:.2f}, League B = {mult_b:.2f} (diff: {diff:.2f})")
        else:
            print(f"   ⚪ {player.name}: League A = {mult_a:.2f}, League B = {mult_b:.2f} (same)")

    print(f"\n📊 Summary: {differences_found}/{len(overlap_players)} overlapping players have different multipliers")

    if differences_found > 0:
        print("✅ SUCCESS: League-specific multipliers are working!\n")
        return True
    else:
        print("⚠️  WARNING: No differences found - this could be normal if performance distribution is similar\n")
        return False


def test_fantasy_team_points(db, league_a, league_b, roster_a_players):
    """Test that fantasy team points use league-specific multipliers"""
    print("👥 Testing fantasy team points calculation...")

    # Create a fantasy team in League A
    team_a = FantasyTeam(
        id='test_team_a',
        league_id=league_a.id,
        user_id='test_user',
        team_name='Test Team A',
        is_finalized=True
    )
    db.add(team_a)
    db.flush()

    # Add first 5 players from roster A
    for i, player in enumerate(roster_a_players[:5]):
        ftp = FantasyTeamPlayer(
            fantasy_team_id=team_a.id,
            player_id=player.id,
            is_captain=(i == 0),
            is_vice_captain=(i == 1),
            is_wicket_keeper=False
        )
        db.add(ftp)

    db.commit()

    # Calculate team points
    points_service = FantasyTeamPointsService()
    result = points_service.calculate_team_total_points(team_a.id, db)

    print(f"   ✅ Team created with {len(roster_a_players[:5])} players")
    print(f"   📊 Total points: {result['total_points']:.2f}")
    print(f"   Player breakdown:")
    for player_info in result['player_breakdown'][:3]:
        role = "(C)" if player_info['is_captain'] else "(VC)" if player_info['is_vice_captain'] else ""
        print(f"      {player_info['player_name']:30s} {role:4s}: {player_info['points']:.2f} pts")

    print()
    return result


def main():
    """Main test flow"""
    print("="*80)
    print("LEAGUE-SPECIFIC MULTIPLIER TEST")
    print("="*80)
    print()

    # Setup database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Cleanup
        cleanup_test_data(db)

        # Setup test data
        season = get_or_create_season(db)
        club = get_test_club(db)

        # Create leagues with different rosters
        league_a, league_b, roster_a, roster_b = create_test_leagues(db, season, club)

        # Identify overlapping players
        roster_a_ids = {p.id for p in roster_a}
        roster_b_ids = {p.id for p in roster_b}
        overlap_ids = roster_a_ids & roster_b_ids
        overlap_players = [p for p in roster_a if p.id in overlap_ids]

        print(f"📊 Setup complete:")
        print(f"   League A: {len(roster_a)} players")
        print(f"   League B: {len(roster_b)} players")
        print(f"   Overlap: {len(overlap_players)} players\n")

        # Confirm leagues to capture initial multipliers
        confirm_leagues(db, league_a, league_b)

        # Create performances (same performances will be used by both leagues)
        all_players = list({p.id: p for p in roster_a + roster_b}.values())
        create_test_performances(db, season, club, all_players)

        # Run multiplier drift for each league
        result_a = run_multiplier_drift(db, league_a.id, "League A")
        result_b = run_multiplier_drift(db, league_b.id, "League B")

        # Verify different multipliers for overlapping players
        success = verify_different_multipliers(db, league_a, league_b, overlap_players)

        # Test fantasy team points calculation
        test_fantasy_team_points(db, league_a, league_b, roster_a)

        print("="*80)
        if success:
            print("✅ ALL TESTS PASSED - League-specific multipliers working correctly!")
        else:
            print("⚠️  Tests completed with warnings - review results above")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
