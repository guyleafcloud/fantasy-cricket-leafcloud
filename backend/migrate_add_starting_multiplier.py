#!/usr/bin/env python3
"""
Add starting_multiplier Column to Players Table
================================================
Adds a new column to track the initial multiplier at season start
and populates it with current multiplier values.
"""

import sys
from database import SessionLocal
from sqlalchemy import text

def migrate_add_starting_multiplier():
    """Add starting_multiplier column and populate it"""
    print("="*70)
    print("ADDING starting_multiplier COLUMN TO players TABLE")
    print("="*70)

    db = SessionLocal()

    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='players' AND column_name='starting_multiplier'
        """)

        result = db.execute(check_query)
        column_exists = result.fetchone() is not None

        if column_exists:
            print("\n✅ Column 'starting_multiplier' already exists!")
            return

        print("\n📝 Adding column 'starting_multiplier' to players table...")

        # Add the column
        add_column_query = text("""
            ALTER TABLE players
            ADD COLUMN starting_multiplier FLOAT DEFAULT 1.0
        """)

        db.execute(add_column_query)
        db.commit()

        print("✅ Column added successfully!")

        # Populate starting_multiplier with current multiplier values
        print("\n📊 Populating starting_multiplier with current multiplier values...")

        update_query = text("""
            UPDATE players
            SET starting_multiplier = COALESCE(multiplier, 1.0)
            WHERE starting_multiplier IS NULL
        """)

        result = db.execute(update_query)
        db.commit()

        updated_count = result.rowcount
        print(f"✅ Updated {updated_count} players")

        # Verify
        verify_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(starting_multiplier) as with_starting_mult,
                AVG(starting_multiplier) as avg_starting_mult,
                MIN(starting_multiplier) as min_starting_mult,
                MAX(starting_multiplier) as max_starting_mult
            FROM players
        """)

        result = db.execute(verify_query)
        row = result.fetchone()

        print(f"\n🔍 Verification:")
        print(f"   Total players: {row.total}")
        print(f"   With starting_multiplier: {row.with_starting_mult}")
        print(f"   Average starting_multiplier: {row.avg_starting_mult:.2f}")
        print(f"   Min starting_multiplier: {row.min_starting_mult:.2f}")
        print(f"   Max starting_multiplier: {row.max_starting_mult:.2f}")

        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrate_add_starting_multiplier()
