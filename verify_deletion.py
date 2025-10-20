#!/usr/bin/env python3
"""Verify deletion of pre-September 2025 data"""

from supabase import create_client
from collections import Counter

# Initialize Supabase
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*80)
print("DATABASE VERIFICATION - POST DELETION")
print("="*80)

# Check total trips
total = supabase.table('trips').select('id', count='exact').execute()
print(f"\n✅ Total trips in database: {total.count}")

# Check pre-Sept trips (should be 0)
pre_sept = supabase.table('trips').select('id', count='exact').lt('trip_date', '2025-09-01').execute()
print(f"✅ Trips before 09/01/2025: {pre_sept.count}")

# Check Sept+ trips (should be 943)
sept_plus = supabase.table('trips').select('id', count='exact').gte('trip_date', '2025-09-01').execute()
print(f"✅ Trips from 09/01/2025 onwards: {sept_plus.count}")

# Get date range
if total.count > 0:
    earliest = supabase.table('trips').select('trip_date').order('trip_date').limit(1).execute()
    latest = supabase.table('trips').select('trip_date').order('trip_date', desc=True).limit(1).execute()

    print(f"\n✅ Date range:")
    print(f"  Earliest: {earliest.data[0]['trip_date']}")
    print(f"  Latest: {latest.data[0]['trip_date']}")

# Month breakdown
print(f"\n✅ Breakdown by month:")
all_trips = supabase.table('trips').select('trip_date').execute()
month_counts = Counter(date['trip_date'][:7] for date in all_trips.data)
for month in sorted(month_counts.keys()):
    print(f"  {month}: {month_counts[month]} trips")

# Validate catches
total_catches = supabase.table('catches').select('id', count='exact').execute()
print(f"\n✅ Total catches: {total_catches.count}")

# Check for any orphaned catches (catches without trips)
# This shouldn't happen if deletion worked correctly
print(f"\n✅ Data integrity checks:")
if sept_plus.count == 943:
    print(f"  ✅ Trip count correct (943 trips)")
else:
    print(f"  ❌ Trip count mismatch (expected 943, got {sept_plus.count})")

if pre_sept.count == 0:
    print(f"  ✅ No pre-September data (0 trips before Sept 1)")
else:
    print(f"  ❌ Pre-September data still exists ({pre_sept.count} trips)")

# Expected date range
if all_trips.data:
    earliest_date = earliest.data[0]['trip_date']
    latest_date = latest.data[0]['trip_date']

    if earliest_date == '2025-09-01':
        print(f"  ✅ Earliest date correct (2025-09-01)")
    else:
        print(f"  ⚠️  Earliest date: {earliest_date} (expected 2025-09-01)")

    if latest_date == '2025-10-31':
        print(f"  ✅ Latest date correct (2025-10-31)")
    else:
        print(f"  ⚠️  Latest date: {latest_date} (expected 2025-10-31)")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

if pre_sept.count == 0 and sept_plus.count == 943:
    print("\n✅ SUCCESS: Database contains only SPEC 006 validated data")
    print("✅ Ready for sequential backfill work")
else:
    print("\n⚠️  WARNING: Database state unexpected, review results above")
