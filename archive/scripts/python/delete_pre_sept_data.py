#!/usr/bin/env python3
"""
Delete all trips before September 1, 2025

CRITICAL: This will delete 7,475 unvalidated trips from the database.
Only SPEC 006 validated data (Sept 1+ 2025) will remain.
"""

from supabase import create_client
import sys

# Initialize Supabase
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    print("\n" + "="*80)
    print("DELETE PRE-SEPTEMBER 2025 DATA")
    print("="*80)

    # Check current state
    before_count = supabase.table('trips').select('id', count='exact').lt('trip_date', '2025-09-01').execute()
    after_count = supabase.table('trips').select('id', count='exact').gte('trip_date', '2025-09-01').execute()
    total_count = supabase.table('trips').select('id', count='exact').execute()

    print(f"\nCurrent database state:")
    print(f"  Total trips: {total_count.count}")
    print(f"  Trips before 09/01/2025: {before_count.count}")
    print(f"  Trips from 09/01/2025 onwards: {after_count.count}")

    if before_count.count == 0:
        print("\n✅ No trips to delete - database already clean!")
        return

    print(f"\n⚠️  WARNING: This will delete {before_count.count} trips")
    print(f"⚠️  Only {after_count.count} trips (Sept 1+ 2025) will remain")
    print(f"\nThis action CANNOT be undone!")

    # Confirmation
    response = input("\nType 'DELETE' to confirm deletion: ")

    if response != 'DELETE':
        print("\n❌ Deletion cancelled")
        sys.exit(0)

    print("\n🗑️  Deleting trips before 09/01/2025...")

    # Delete using date filter (much simpler and faster)
    # Catches will cascade delete if FK is set to CASCADE
    try:
        print("  Deleting catches for trips before 09/01/2025...")

        # Delete in batches by continuously fetching the first N records until none remain
        # This avoids issues with range/offset when deleting
        batch_size = 100
        batch_num = 0
        total_deleted_catches = 0
        total_deleted_trips = 0

        while True:
            # Always get the first batch (limit, no offset)
            # After deletion, the "next" batch becomes the "first" batch
            trips_batch = supabase.table('trips') \
                .select('id') \
                .lt('trip_date', '2025-09-01') \
                .limit(batch_size) \
                .execute()

            if not trips_batch.data:
                break

            batch_num += 1
            trip_ids = [t['id'] for t in trips_batch.data]

            # Delete catches for this batch
            catches_result = supabase.table('catches').delete().in_('trip_id', trip_ids).execute()
            deleted_catches = len(catches_result.data) if catches_result.data else 0
            total_deleted_catches += deleted_catches

            # Delete trips for this batch
            trips_result = supabase.table('trips').delete().in_('id', trip_ids).execute()
            deleted_trips = len(trips_result.data) if trips_result.data else 0
            total_deleted_trips += deleted_trips

            print(f"  Batch {batch_num}: Deleted {deleted_trips} trips, {deleted_catches} catches")

        print(f"\n  ✅ Total deleted: {total_deleted_trips} trips, {total_deleted_catches} catches")
        print("\n✅ Deletion complete!")

        # Verify
        remaining = supabase.table('trips').select('id', count='exact').lt('trip_date', '2025-09-01').execute()
        after_deletion = supabase.table('trips').select('id', count='exact').gte('trip_date', '2025-09-01').execute()

        print(f"\nFinal database state:")
        print(f"  Trips before 09/01/2025: {remaining.count}")
        print(f"  Trips from 09/01/2025 onwards: {after_deletion.count}")

        if remaining.count == 0:
            print(f"\n✅ SUCCESS: All pre-September data deleted")
            print(f"✅ Database now contains only SPEC 006 validated data ({after_deletion.count} trips)")
        else:
            print(f"\n⚠️  WARNING: {remaining.count} trips still remain before Sept 1")

    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
