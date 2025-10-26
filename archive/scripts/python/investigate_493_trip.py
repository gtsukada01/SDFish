#!/usr/bin/env python3
"""
Investigate the 493-fish trip shown in Best Moon Phase card
"""

from supabase import create_client

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get moon phase data to identify First Quarter dates
moon_response = supabase.table('ocean_conditions').select(
    'date, moon_phase_name'
).eq('moon_phase_name', 'first_quarter').gte('date', '2024-09-01').lte('date', '2025-11-01').execute()

print("First Quarter moon phase dates:")
for record in moon_response.data[:10]:
    print(f"  {record['date']}")

print("\n" + "="*70 + "\n")

# Find trips with high fish counts (490-500 range)
response = supabase.table('trips').select(
    'id, trip_date, trip_duration, anglers, total_fish, boats(name, landings(name))'
).gte('trip_date', '2024-09-01').lte('trip_date', '2025-11-01').execute()

trips = response.data

high_catch_trips = []
for trip in trips:
    total_fish = trip.get('total_fish') or 0

    if 490 <= total_fish <= 500:
        high_catch_trips.append((total_fish, trip))

high_catch_trips.sort(key=lambda x: x[0], reverse=True)

print(f"Found {len(high_catch_trips)} trips with 490-500 fish:\n")

for total_fish, trip in high_catch_trips:
    print(f"Trip with {total_fish} total fish:")
    print(f"  Boat: {trip.get('boats', {}).get('name', 'Unknown')}")
    print(f"  Date: {trip.get('trip_date')}")
    print(f"  Duration: {trip.get('trip_duration')}")
    print(f"  Anglers: {trip.get('anglers')}")
    print(f"  Landing: {trip.get('boats', {}).get('landings', {}).get('name', 'Unknown')}")

    # Get moon phase for this date
    moon_data = supabase.table('ocean_conditions').select('moon_phase_name').eq('date', trip['trip_date']).execute()
    moon_phase = moon_data.data[0]['moon_phase_name'] if moon_data.data else 'Unknown'
    print(f"  Moon Phase: {moon_phase}")

    # Get catches for this trip
    catches_data = supabase.table('catches').select('species, count').eq('trip_id', trip['id']).execute()
    catches = catches_data.data

    print(f"\n  Species breakdown:")
    for catch in sorted(catches, key=lambda c: c.get('count', 0), reverse=True):
        print(f"    - {catch.get('species')}: {catch.get('count')} fish")

    anglers = trip.get('anglers') or 1
    print(f"\n  Fish per angler: {total_fish / max(anglers, 1):.1f}")
    print(f"  Trip ID: {trip.get('id')}")
    print("\n" + "="*70 + "\n")
