"""
Migration: Add is_wicket_keeper field to players table
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fantasy_cricket')

def run_migration():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Adding is_wicket_keeper column to players table...")

        # Add is_wicket_keeper column
        try:
            conn.execute(text("""
                ALTER TABLE players
                ADD COLUMN IF NOT EXISTS is_wicket_keeper BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ Added is_wicket_keeper column")
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()
            return

        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)

if __name__ == '__main__':
    run_migration()
