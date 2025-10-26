#!/usr/bin/env python3
"""Fix the first Dolphin trip to be 1/2 Day AM (data entry error on source)."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get the current Dolphin trip on Aug 7
trips = supabase.table('trips').select('id, trip_date, boat_id, boats(name), trip_duration, anglers').eq('trip_date', '2025-08-07').execute()

dolphin_trips = [t for t in trips.data if t.get('boats') and 'Dolphin' in t['boats'].get('name', '')]

if dolphin_trips:
    trip = dolphin_trips[0]
    trip_id = trip['id']

    print(f"Found Dolphin trip {trip_id} on 2025-08-07")
    print(f"  Current trip_duration: {trip['trip_duration']}")
    print()

    print("Updating to '1/2 Day AM' (first trip listed is likely AM)...")
    supabase.table('trips').update({'trip_duration': '1/2 Day AM'}).eq('id', trip_id).execute()
    print("✅ Updated to 1/2 Day AM")
    print()
    print("Now the second trip (1/2 Day PM) can be inserted without constraint violation.")
else:
    print("No Dolphin trip found on 2025-08-07")
