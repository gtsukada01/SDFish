#!/usr/bin/env python3
"""Fix the PM Dolphin trip catches (it got wrong data)."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get the PM Dolphin trip
trips = supabase.table('trips').select('id, trip_date, boat_id, boats(name), trip_duration, anglers').eq('trip_date', '2025-08-07').execute()
dolphin_trips = [t for t in trips.data if t.get('boats') and 'Dolphin' in t['boats'].get('name', '')]

pm_trip = [t for t in dolphin_trips if '1/2 Day PM' in t['trip_duration']][0]
trip_id = pm_trip['id']

print(f"Found PM Dolphin trip ID: {trip_id}")
print()

# Delete wrong catches
print("Deleting incorrect catches...")
supabase.table('catches').delete().eq('trip_id', trip_id).execute()
print("✅ Deleted")
print()

# Insert correct catches for Trip 2 (PM)
correct_catches = [
    {'trip_id': trip_id, 'species': 'Barracuda', 'count': 2},
    {'trip_id': trip_id, 'species': 'Cabezon', 'count': 3},
    {'trip_id': trip_id, 'species': 'Calico Bass', 'count': 48},
    {'trip_id': trip_id, 'species': 'Rockfish', 'count': 28},
    {'trip_id': trip_id, 'species': 'Sculpin', 'count': 3}
]

print("Inserting correct PM catches:")
print("  2 Barracuda")
print("  3 Cabezon")
print("  48 Calico Bass")
print("  28 Rockfish")
print("  3 Sculpin")
print()

supabase.table('catches').insert(correct_catches).execute()
print("✅ Correct catches inserted!")
