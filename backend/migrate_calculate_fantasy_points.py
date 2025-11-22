#!/usr/bin/env python3
"""
Migrate PlayerPerformance: Calculate fantasy_points from base and multiplier
=============================================================================
Sets fantasy_points = base_fantasy_points × multiplier_applied for all records
where fantasy_points is NULL.
"""

import sys
from database import SessionLocal
from database_models import PlayerPerformance

def migrate_fantasy_points():
    """Calculate fantasy_points for all records"""
    print("="*70)
    print("MIGRATING PLAYER PERFORMANCE FANTASY POINTS")
    print("="*70)

    db = SessionLocal()

    try:
        # Find all records with NULL fantasy_points but has base and multiplier
        records = db.query(PlayerPerformance).filter(
            PlayerPerformance.fantasy_points == None,
            PlayerPerformance.base_fantasy_points != None,
            PlayerPerformance.multiplier_applied != None
        ).all()

        print(f"\n📊 Found {len(records)} records to update")

        if len(records) == 0:
            print("✅ No records need migration!")
            return

        # Calculate fantasy_points for each record
        updated = 0
        for record in records:
            record.fantasy_points = record.base_fantasy_points * record.multiplier_applied
            updated += 1

            if updated % 100 == 0:
                print(f"   Progress: {updated}/{len(records)} records...")

        # Commit changes
        db.commit()

        print(f"\n✅ Migration complete!")
        print(f"   Updated: {updated} records")

        # Verify
        print(f"\n🔍 Verification:")
        sample = db.query(PlayerPerformance).filter(
            PlayerPerformance.fantasy_points != None
        ).first()

        if sample:
            expected = sample.base_fantasy_points * sample.multiplier_applied
            print(f"   Sample calculation: {sample.base_fantasy_points:.2f} × {sample.multiplier_applied:.2f} = {expected:.2f}")
            print(f"   Stored value: {sample.fantasy_points:.2f}")
            print(f"   Match: {abs(sample.fantasy_points - expected) < 0.01}")

        # Count NULL after migration
        null_count = db.query(PlayerPerformance).filter(
            PlayerPerformance.fantasy_points == None
        ).count()

        print(f"\n📈 Final status:")
        print(f"   NULL fantasy_points remaining: {null_count}")

        if null_count == 0:
            print(f"   ✅ All records migrated successfully!")
        else:
            print(f"   ⚠️  {null_count} records still have NULL values")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_fantasy_points()
