#!/usr/bin/env python3
"""Manually insert the second Dolphin trip."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get Dolphin boat ID
boat = supabase.table('boats').select('id').eq('name', 'Dolphin').execute()
boat_id = boat.data[0]['id']

# Get Fisherman's Landing ID
landing = supabase.table('landings').select('id').eq('name', "Fisherman's Landing").execute()
landing_id = landing.data[0]['id']

print(f"Dolphin boat_id: {boat_id}")
print(f"Fisherman's Landing landing_id: {landing_id}")
print()

# Trip 2 data
trip_data = {
    'boat_id': boat_id,
    'landing_id': landing_id,
    'trip_date': '2025-08-07',
    'trip_duration': '1/2 Day PM',
    'anglers': 58
}

print("Inserting Trip 2...")
print(f"  {trip_data}")

try:
    trip_result = supabase.table('trips').insert(trip_data).execute()
    trip_id = trip_result.data[0]['id']
    print(f"✅ Trip inserted with ID: {trip_id}")
    print()

    # Insert catches for Trip 2
    catch_data = [
        {'trip_id': trip_id, 'species': 'Barracuda', 'count': 2},
        {'trip_id': trip_id, 'species': 'Cabezon', 'count': 3},
        {'trip_id': trip_id, 'species': 'Calico Bass', 'count': 48},
        {'trip_id': trip_id, 'species': 'Rockfish', 'count': 28},
        {'trip_id': trip_id, 'species': 'Sculpin', 'count': 3}
    ]

    print("Inserting catches...")
    supabase.table('catches').insert(catch_data).execute()
    print("✅ Catches inserted")
    print()

    print("SUCCESS! Trip 2 has been manually inserted.")
    print("Now let's re-run QC validation to see if it passes.")

except Exception as e:
    print(f"❌ INSERT FAILED: {e}")
    print()
    print("This explains why the scraper couldn't insert Trip 2!")
