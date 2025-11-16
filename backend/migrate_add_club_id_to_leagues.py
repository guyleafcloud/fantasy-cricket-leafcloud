#!/usr/bin/env python3
"""
Database Migration: Add club_id to leagues table

This migration adds a club_id foreign key column to the leagues table.
For existing leagues without a club_id, it will set it to the first available club.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection - use environment variable from docker-compose
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    """Add club_id column to leagues table"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Starting migration: add club_id to leagues...")

        # Check if column already exists
        result = session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='leagues' AND column_name='club_id'
        """))

        if result.fetchone():
            print("club_id column already exists, skipping migration")
            return

        # Add club_id column (nullable at first)
        print("Adding club_id column...")
        session.execute(text("""
            ALTER TABLE leagues
            ADD COLUMN club_id VARCHAR(50)
        """))
        session.commit()

        # Get the first available club ID
        result = session.execute(text("SELECT id FROM clubs LIMIT 1"))
        first_club = result.fetchone()

        if first_club:
            default_club_id = first_club[0]
            print(f"Setting default club_id to: {default_club_id}")

            # Update existing leagues to have the default club_id
            session.execute(text(f"""
                UPDATE leagues
                SET club_id = :club_id
                WHERE club_id IS NULL
            """), {"club_id": default_club_id})
            session.commit()

        # Add foreign key constraint
        print("Adding foreign key constraint...")
        session.execute(text("""
            ALTER TABLE leagues
            ADD CONSTRAINT fk_leagues_club_id
            FOREIGN KEY (club_id) REFERENCES clubs(id)
        """))
        session.commit()

        # Make column NOT NULL
        print("Making club_id NOT NULL...")
        session.execute(text("""
            ALTER TABLE leagues
            ALTER COLUMN club_id SET NOT NULL
        """))
        session.commit()

        # Add index
        print("Adding index...")
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_league_club ON leagues(club_id)
        """))
        session.commit()

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
