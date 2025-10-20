#!/usr/bin/env python3
"""
Trip Duration Normalization Script
===================================

Normalizes trip_duration values by removing geographic qualifiers
and consolidating duplicate trip types.

Normalization Rules:
- Remove geographic qualifiers: Local, Coronado Islands, Mexican Waters, Offshore, Islands
- Consolidate Reverse Overnight → Overnight (same duration, different departure time)
- Consolidate Extended 1.5 Day → 1.75 Day
- Keep Lobster as-is (crustacean fishing category)

Total Impact: 43 unique durations → 16 standard categories (~310 trips updated)

Author: Fishing Intelligence Platform
Date: October 18, 2025
"""

from supabase import create_client
from collections import Counter

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

# Normalization mapping
NORMALIZATION_MAP = {
    # Half Day AM
    "1/2 Day AMCoronado Islands": "1/2 Day AM",
    "1/2 Day AMMexican Waters": "1/2 Day AM",

    # Half Day Twilight
    "1/2 Day TwilightLocal": "1/2 Day Twilight",

    # Three-Quarter Day
    "3/4 Day Islands": "3/4 Day",
    "3/4 Day Local": "3/4 Day",
    "3/4 DayCoronado Islands": "3/4 Day",
    "3/4 DayMexican Waters": "3/4 Day",

    # Full Day
    "Full Day Coronado Islands": "Full Day",
    "Full Day Coronado IslandsCoronado Islands": "Full Day",
    "Full Day Local": "Full Day",
    "Full Day Offshore": "Full Day",
    "Full DayCoronado Islands": "Full Day",
    "Full DayMexican Waters": "Full Day",

    # Overnight (consolidate Reverse Overnight)
    "OvernightCoronado Islands": "Overnight",
    "OvernightIsland Freelance": "Overnight",
    "Reverse Overnight": "Overnight",  # Same duration, different departure time

    # 1.5 Day
    "1.5 Day Local": "1.5 Day",
    "1.5 Day Offshore": "1.5 Day",

    # 1.75 Day
    "Extended 1.5 Day": "1.75 Day",

    # 2 Day
    "2 Day Offshore": "2 Day",
    "2 DayIsland Freelance": "2 Day",
    "2 DayMexican Waters": "2 Day",

    # 3 Day
    "3 Day Offshore": "3 Day",
}

def main():
    """Execute trip duration normalization."""

    print("=" * 80)
    print("TRIP DURATION NORMALIZATION")
    print("=" * 80)
    print()

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get current state
    print("📊 Current database state:")
    result = supabase.table('trips').select('trip_duration').execute()
    trips = result.data
    duration_counts = Counter(trip['trip_duration'] for trip in trips if trip.get('trip_duration'))

    print(f"   Total trips: {len(trips)}")
    print(f"   Unique durations: {len(duration_counts)}")
    print()

    # Show what will be updated
    print("🔄 Normalization mappings to apply:")
    print("-" * 80)

    total_to_update = 0
    for old_duration, new_duration in sorted(NORMALIZATION_MAP.items()):
        count = duration_counts.get(old_duration, 0)
        if count > 0:
            print(f"   {old_duration:45} → {new_duration:20} ({count} trips)")
            total_to_update += count

    print("-" * 80)
    print(f"   Total trips to update: {total_to_update}")
    print()

    # Ask for confirmation
    response = input("Proceed with normalization? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Normalization cancelled.")
        return

    print()
    print("🚀 Applying normalization...")
    print("-" * 80)

    # Apply each mapping
    updated_total = 0
    for old_duration, new_duration in NORMALIZATION_MAP.items():
        count = duration_counts.get(old_duration, 0)
        if count > 0:
            try:
                # Update trips with this duration
                result = supabase.table('trips').update({
                    'trip_duration': new_duration
                }).eq('trip_duration', old_duration).execute()

                updated = len(result.data) if result.data else 0
                updated_total += updated
                print(f"   ✅ {old_duration:45} → {new_duration:20} ({updated} trips)")

            except Exception as e:
                print(f"   ❌ Error updating {old_duration}: {e}")

    print("-" * 80)
    print(f"   Total trips updated: {updated_total}")
    print()

    # Verify final state
    print("✅ Verification:")
    print("-" * 80)
    result = supabase.table('trips').select('trip_duration').execute()
    trips = result.data
    duration_counts_after = Counter(trip['trip_duration'] for trip in trips if trip.get('trip_duration'))

    print(f"   Total trips: {len(trips)}")
    print(f"   Unique durations: {len(duration_counts_after)}")
    print()
    print("   Standard categories:")

    for duration, count in sorted(duration_counts_after.items()):
        print(f"      {duration:30} {count:>6} trips")

    print("=" * 80)
    print("✅ Normalization complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
