#!/usr/bin/env python3
"""
Database Migration: Add Transfer Support to Leagues
====================================================
Adds transfer tracking columns to leagues and fantasy_teams tables,
and creates the transfers table.
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import sys

def run_migration():
    """Run the migration to add transfer support"""
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            print("Starting migration...")

            # 1. Add transfers_per_season to leagues table
            print("\n1. Adding transfers_per_season to leagues table...")
            try:
                conn.execute(text("""
                    ALTER TABLE leagues
                    ADD COLUMN transfers_per_season INTEGER DEFAULT 4
                """))
                conn.commit()
                print("   ✓ Added transfers_per_season column")
            except Exception as e:
                if "already exists" in str(e):
                    print("   ⚠ Column already exists, skipping")
                else:
                    raise

            # 2. Add transfer tracking to fantasy_teams table
            print("\n2. Adding transfer tracking to fantasy_teams table...")
            try:
                conn.execute(text("""
                    ALTER TABLE fantasy_teams
                    ADD COLUMN transfers_used INTEGER DEFAULT 0,
                    ADD COLUMN extra_transfers_granted INTEGER DEFAULT 0
                """))
                conn.commit()
                print("   ✓ Added transfers_used and extra_transfers_granted columns")
            except Exception as e:
                if "already exists" in str(e):
                    print("   ⚠ Columns already exist, skipping")
                else:
                    raise

            # 3. Create transfers table
            print("\n3. Creating transfers table...")
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS transfers (
                        id VARCHAR(50) PRIMARY KEY,
                        fantasy_team_id VARCHAR(50) NOT NULL REFERENCES fantasy_teams(id) ON DELETE CASCADE,
                        player_out_id VARCHAR(50) REFERENCES players(id) ON DELETE SET NULL,
                        player_in_id VARCHAR(50) NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                        transfer_type VARCHAR(50) DEFAULT 'regular',
                        requires_approval BOOLEAN DEFAULT FALSE,
                        is_approved BOOLEAN DEFAULT FALSE,
                        approved_by VARCHAR(50),
                        proof_url VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        approved_at TIMESTAMP
                    )
                """))
                conn.commit()
                print("   ✓ Created transfers table")
            except Exception as e:
                print(f"   ⚠ Error creating transfers table: {e}")

            # 4. Create indexes
            print("\n4. Creating indexes...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transfer_team ON transfers(fantasy_team_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transfer_approval
                    ON transfers(requires_approval, is_approved)
                """))
                conn.commit()
                print("   ✓ Created indexes")
            except Exception as e:
                print(f"   ⚠ Error creating indexes: {e}")

            print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    run_migration()
