#!/usr/bin/env python3
"""
Find the 493-fish trip shown in Best Moon Phase card for Aztec boat
"""

from supabase import create_client
from datetime import datetime, timedelta

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Calculate 30-day window (matching dashboard default)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

print(f"Date range: {start_date} to {end_date}")
print("="*70)

# Get Aztec boat
aztec_boat = supabase.table('boats').select('id, name').ilike('name', '%aztec%').execute()
if not aztec_boat.data:
    print("Aztec boat not found!")
    exit(1)

boat_id = aztec_boat.data[0]['id']
boat_name = aztec_boat.data[0]['name']
print(f"\nBoat: {boat_name} (ID: {boat_id})")
print("="*70)

# Get all trips for Aztec in the 30-day window
trips_response = supabase.table('trips').select('id, trip_date, trip_duration, anglers').eq(
    'boat_id', boat_id
).gte('trip_date', str(start_date)).lte('trip_date', str(end_date)).execute()

print(f"\nFound {len(trips_response.data)} trips\n")

# For each trip, get catches and calculate total
trip_details = []
for trip in trips_response.data:
    catches_response = supabase.table('catches').select('species, count').eq('trip_id', trip['id']).execute()
    catches = catches_response.data

    total_fish = sum(c['count'] for c in catches)
    trip_details.append({
        'id': trip['id'],
        'date': trip['trip_date'],
        'duration': trip['trip_duration'],
        'anglers': trip['anglers'],
        'total_fish': total_fish,
        'catches': catches
    })

# Sort by total fish descending
trip_details.sort(key=lambda t: t['total_fish'], reverse=True)

# Show all trips
print("All Aztec trips (sorted by fish count):\n")
for trip in trip_details:
    print(f"{trip['total_fish']:>4} fish | {trip['date']} | {trip['duration']:<15} | {trip['anglers']} anglers")

print("\n" + "="*70)

# Find the 493-fish trip (or closest)
print("\nInvestigating highest catch trip:\n")
top_trip = trip_details[0]

print(f"Trip ID: {top_trip['id']}")
print(f"Date: {top_trip['date']}")
print(f"Duration: {top_trip['duration']}")
print(f"Anglers: {top_trip['anglers']}")
print(f"Total Fish: {top_trip['total_fish']}")

# Get moon phase for this date
moon_response = supabase.table('ocean_conditions').select('moon_phase_name').eq('date', top_trip['date']).execute()
moon_phase = moon_response.data[0]['moon_phase_name'] if moon_response.data else 'Unknown'
print(f"Moon Phase: {moon_phase}")

print(f"\nSpecies breakdown (top 10):")
sorted_catches = sorted(top_trip['catches'], key=lambda c: c['count'], reverse=True)
for catch in sorted_catches[:10]:
    print(f"  {catch['count']:>3} × {catch['species']}")

if len(sorted_catches) > 10:
    remaining = sum(c['count'] for c in sorted_catches[10:])
    print(f"  {remaining:>3} × (other species)")

print(f"\nFish per angler: {top_trip['total_fish'] / max(top_trip['anglers'] or 1, 1):.1f}")

# Verify this matches source
print("\n" + "="*70)
print("\nNOTE: Verify this trip at:")
print(f"https://www.sandiegofishreports.com (date: {top_trip['date']})")
print("\nIf this is 493 fish from a single trip, check if this is:")
print("  1. A legitimate high-catch day (offshore, good conditions)")
print("  2. A data quality issue (parser bug, duplicate catches)")
print("  3. An aggregation error (multiple trips combined)")
