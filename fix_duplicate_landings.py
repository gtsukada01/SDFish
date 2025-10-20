#!/usr/bin/env python3
"""
Fix duplicate landings in the database
Merges city-name landings into proper sportfishing landing entries
"""

from supabase import create_client

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define duplicate landing mappings:
# "duplicate_name" -> "correct_name"
LANDING_MERGES = {
    "Dana Point, CA": "Dana Wharf Sportfishing",
    "Newport Beach, CA": "Newport Landing",  # Keep Newport Landing as primary
    "Long Beach, CA": "Long Beach Sportfishing",
}

def fix_duplicate_landings(dry_run=True):
    """
    Merge duplicate landings by:
    1. Moving boats from duplicate landing to correct landing
    2. Deleting the duplicate landing
    """

    print("=" * 80)
    print("🔧 DUPLICATE LANDING CLEANUP")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'PRODUCTION (will modify database)'}")
    print()

    for duplicate_name, correct_name in LANDING_MERGES.items():
        print(f"Processing: {duplicate_name} → {correct_name}")

        # Get both landings
        duplicate = supabase.table('landings').select('id, name').eq('name', duplicate_name).execute()
        correct = supabase.table('landings').select('id, name').eq('name', correct_name).execute()

        if not duplicate.data:
            print(f"  ⚠️  Duplicate landing '{duplicate_name}' not found, skipping")
            continue

        if not correct.data:
            print(f"  ⚠️  Correct landing '{correct_name}' not found, skipping")
            continue

        duplicate_id = duplicate.data[0]['id']
        correct_id = correct.data[0]['id']

        # Get boats under duplicate landing
        boats = supabase.table('boats').select('id, name').eq('landing_id', duplicate_id).execute()

        print(f"  Found {len(boats.data)} boats to move:")

        for boat in boats.data:
            # Get trip count
            trips = supabase.table('trips').select('id', count='exact').eq('boat_id', boat['id']).execute()
            print(f"    - {boat['name']} ({trips.count} trips)")

            if not dry_run:
                # Move boat to correct landing
                update_result = supabase.table('boats').update({
                    'landing_id': correct_id
                }).eq('id', boat['id']).execute()
                print(f"      ✅ Moved to landing ID {correct_id}")

        if boats.data and not dry_run:
            # Delete duplicate landing
            delete_result = supabase.table('landings').delete().eq('id', duplicate_id).execute()
            print(f"  ✅ Deleted duplicate landing '{duplicate_name}' (ID {duplicate_id})")
        elif dry_run:
            print(f"  [DRY RUN] Would delete landing '{duplicate_name}' (ID {duplicate_id})")

        print()

    print("=" * 80)
    print("Summary:")
    if dry_run:
        print("  This was a DRY RUN - no changes made")
        print("  Run with dry_run=False to apply changes")
    else:
        print("  ✅ All duplicate landings merged successfully")
        print("  🔄 Restart your dashboard to see the changes")
    print("=" * 80)

if __name__ == "__main__":
    import sys

    # Check for --execute flag
    execute = '--execute' in sys.argv

    if not execute:
        print()
        print("⚠️  DRY RUN MODE - No changes will be made")
        print("   Add --execute flag to actually apply changes")
        print()

    fix_duplicate_landings(dry_run=not execute)

    if not execute:
        print()
        print("To apply these changes, run:")
        print("  python3 fix_duplicate_landings.py --execute")
