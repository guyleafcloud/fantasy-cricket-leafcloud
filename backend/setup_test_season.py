#!/usr/bin/env python3
"""
Setup Test Season for 2026 Simulation
======================================
Creates a test season and league for running the 12-week beta test.

This script:
1. Creates a 2026 test season
2. Creates a beta test league
3. Sets appropriate dates and status
4. Outputs IDs needed for simulation

Usage:
    python3 setup_test_season.py
"""

import sys
import os
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Get database URL from environment
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://cricket_admin:dev_password_change_in_prod@localhost:5432/fantasy_cricket'
)

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print('='*80 + '\n')

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def setup_test_season():
    """Create 2026 test season and league"""

    print_header("🏏 Setup 2026 Test Season")

    # Connect to database
    print("Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        print_success("Connected to database")
    except Exception as e:
        print_error(f"Failed to connect to database: {str(e)}")
        return False

    try:
        # Check if test season already exists
        print("\nChecking for existing test season...")
        existing = session.execute(text("""
            SELECT id, name, year, status
            FROM seasons
            WHERE year = 2026 AND name LIKE '%Test%'
        """)).fetchone()

        if existing:
            print_warning(f"Test season already exists: {existing[1]} (ID: {existing[0]}, Status: {existing[3]})")
            season_id = existing[0]

            # Ask if we should continue
            response = input("\nDo you want to use this existing season? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled")
                return False
        else:
            # Create new season
            print("\n📅 Creating 2026 test season...")

            result = session.execute(text("""
                INSERT INTO seasons (name, year, start_date, end_date, status, created_at, updated_at)
                VALUES
                    ('2026 Beta Test Season', 2026, '2026-04-01', '2026-10-03', 'active', NOW(), NOW())
                RETURNING id, name, year
            """))
            session.commit()

            season = result.fetchone()
            season_id = season[0]
            print_success(f"Created season: {season[1]} (Year: {season[2]}, ID: {season_id})")

        # Check for existing league
        print("\nChecking for existing test league...")
        existing_league = session.execute(text("""
            SELECT id, name, code, status
            FROM leagues
            WHERE season_id = :season_id
        """), {"season_id": season_id}).fetchone()

        if existing_league:
            print_warning(f"Test league already exists: {existing_league[1]} (Code: {existing_league[2]}, Status: {existing_league[3]})")
            league_id = existing_league[0]
            league_code = existing_league[2]
        else:
            # Generate unique league code
            import random
            import string
            league_code = 'TEST' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            # Create league
            print("\n🏆 Creating beta test league...")

            result = session.execute(text("""
                INSERT INTO leagues (
                    name, code, season_id, status,
                    max_teams, current_round, total_rounds,
                    created_at, updated_at
                )
                VALUES
                    (
                        'Beta Test League 2026',
                        :code,
                        :season_id,
                        'active',
                        100,
                        0,
                        12,
                        NOW(),
                        NOW()
                    )
                RETURNING id, name, code
            """), {"code": league_code, "season_id": season_id})
            session.commit()

            league = result.fetchone()
            league_id = league[0]
            print_success(f"Created league: {league[1]}")
            print_success(f"League code: {league[2]} (Share this with beta testers)")

        # Get current round count
        round_count = session.execute(text("""
            SELECT COUNT(DISTINCT round)
            FROM player_performances
            WHERE league_id = :league_id
        """), {"league_id": league_id}).scalar() or 0

        # Summary
        print_header("✅ Setup Complete")

        print("📊 Test Season Details:")
        print(f"   Season ID: {season_id}")
        print(f"   Season Name: 2026 Beta Test Season")
        print(f"   Year: 2026")
        print(f"   Dates: 2026-04-01 to 2026-10-03")
        print("")
        print("🏆 Test League Details:")
        print(f"   League ID: {league_id}")
        print(f"   League Name: Beta Test League 2026")
        print(f"   League Code: {league_code}")
        print(f"   Current Round: {round_count}/12")
        print("")

        # Get team count
        team_count = session.execute(text("""
            SELECT COUNT(*) FROM fantasy_teams WHERE league_id = :league_id
        """), {"league_id": league_id}).scalar() or 0

        print(f"👥 Teams in league: {team_count}")

        if team_count == 0:
            print_warning("No teams yet - beta testers need to join with code: " + league_code)

        print("")
        print("📝 Next Steps:")
        print(f"   1. Share league code with beta testers: {league_code}")
        print("   2. Wait for testers to create their teams")
        print(f"   3. Run simulation: ./automate_weekly_simulation.sh {round_count + 1}")
        print("")
        print("🔧 To run simulation with MOCK mode:")
        print(f"   export SCRAPER_MODE=mock")
        print(f"   ./run_weekly_simulation.sh {round_count + 1}")
        print("")

        # Save IDs to file for easy access
        with open('test_season_ids.txt', 'w') as f:
            f.write(f"SEASON_ID={season_id}\n")
            f.write(f"LEAGUE_ID={league_id}\n")
            f.write(f"LEAGUE_CODE={league_code}\n")
            f.write(f"CURRENT_ROUND={round_count}\n")

        print_success("Saved IDs to test_season_ids.txt")

        session.close()
        return True

    except Exception as e:
        print_error(f"Error during setup: {str(e)}")
        session.rollback()
        session.close()
        return False


if __name__ == "__main__":
    success = setup_test_season()
    sys.exit(0 if success else 1)
