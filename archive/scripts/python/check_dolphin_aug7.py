#!/usr/bin/env python3
"""Check Dolphin trips on Aug 7, 2025."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get all trips for Aug 7, 2025
trips = supabase.table('trips').select('id, trip_date, boat_id, boats(name), trip_duration, anglers').eq('trip_date', '2025-08-07').execute()

print(f"Found {len(trips.data)} trips on 2025-08-07\n")

# Find Dolphin trips
dolphin_trips = [t for t in trips.data if t.get('boats') and 'Dolphin' in t['boats'].get('name', '')]

if dolphin_trips:
    print(f"Found {len(dolphin_trips)} Dolphin trip(s) on 2025-08-07:\n")
    for trip in dolphin_trips:
        trip_id = trip['id']
        trip_duration = trip.get('trip_duration', 'Unknown')
        anglers = trip.get('anglers', 'Unknown')

        # Get catches for this trip
        catches = supabase.table('catches').select('species, count').eq('trip_id', trip_id).execute()

        print(f"Trip ID {trip_id}:")
        print(f"  Duration: {trip_duration}")
        print(f"  Anglers: {anglers}")
        print(f"  Catches:")
        for c in sorted(catches.data, key=lambda x: x['species']):
            print(f"    {c['count']} {c['species']}")
        print()
else:
    print("No Dolphin trips found on 2025-08-07")
