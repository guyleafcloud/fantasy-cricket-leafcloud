"""
Migration: Add player type constraints to leagues table
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fantasy_cricket')

def run_migration():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Adding player type constraint columns to leagues table...")

        # Add min_batsmen column
        try:
            conn.execute(text("""
                ALTER TABLE leagues
                ADD COLUMN IF NOT EXISTS min_batsmen INTEGER DEFAULT 3
            """))
            conn.commit()
            print("✓ Added min_batsmen column")
        except Exception as e:
            print(f"Error adding min_batsmen column: {e}")
            conn.rollback()
            return

        # Add min_bowlers column
        try:
            conn.execute(text("""
                ALTER TABLE leagues
                ADD COLUMN IF NOT EXISTS min_bowlers INTEGER DEFAULT 3
            """))
            conn.commit()
            print("✓ Added min_bowlers column")
        except Exception as e:
            print(f"Error adding min_bowlers column: {e}")
            conn.rollback()
            return

        # Add require_wicket_keeper column
        try:
            conn.execute(text("""
                ALTER TABLE leagues
                ADD COLUMN IF NOT EXISTS require_wicket_keeper BOOLEAN DEFAULT TRUE
            """))
            conn.commit()
            print("✓ Added require_wicket_keeper column")
        except Exception as e:
            print(f"Error adding require_wicket_keeper column: {e}")
            conn.rollback()
            return

        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)

if __name__ == '__main__':
    run_migration()
