#!/usr/bin/env python3
"""Revert Dolphin first trip back to PM to match source exactly (SPEC 006 compliance)."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get both Dolphin trips
trips = supabase.table('trips').select('id, trip_date, boat_id, boats(name), trip_duration, anglers').eq('trip_date', '2025-08-07').execute()
dolphin_trips = [t for t in trips.data if t.get('boats') and 'Dolphin' in t['boats'].get('name', '')]

# Find the AM trip (the one we changed)
am_trip = [t for t in dolphin_trips if 'AM' in t['trip_duration']]

if am_trip:
    trip_id = am_trip[0]['id']
    print(f"Reverting Dolphin trip {trip_id} from '1/2 Day AM' back to '1/2 Day PM'")
    print()
    print("SPEC 006 Compliance: boats.php shows both as PM, so database must match exactly.")
    print()

    supabase.table('trips').update({'trip_duration': '1/2 Day PM'}).eq('id', trip_id).execute()
    print("✅ Reverted to 1/2 Day PM")
    print()
    print("Note: Source likely has data entry error (boats don't run two identical PM trips),")
    print("but SPEC 006 requires storing data AS-IS from source without corrections.")
else:
    print("No AM trip found - already reverted or never changed.")
