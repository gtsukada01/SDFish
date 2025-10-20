#!/usr/bin/env python3
"""Delete Poseidon trip on Aug 1, 2025 for re-scraping."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get all trips for Aug 1, 2025
trips = supabase.table('trips').select('id, trip_date, boat_id, boats(name)').eq('trip_date', '2025-08-01').execute()

print(f"Found {len(trips.data)} trips on 2025-08-01")

# Find Poseidon trip
poseidon_trips = [t for t in trips.data if t.get('boats') and 'Poseidon' in t['boats'].get('name', '')]

if poseidon_trips:
    for trip in poseidon_trips:
        trip_id = trip['id']
        print(f"Deleting Poseidon trip {trip_id}...")

        # Delete catches first (foreign key constraint)
        supabase.table('catches').delete().eq('trip_id', trip_id).execute()
        print(f"  Deleted catches for trip {trip_id}")

        # Delete trip
        supabase.table('trips').delete().eq('id', trip_id).execute()
        print(f"  Deleted trip {trip_id}")

    print(f"\n✅ Deleted {len(poseidon_trips)} Poseidon trip(s)")
else:
    print("No Poseidon trip found on 2025-08-01")
