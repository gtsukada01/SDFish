#!/usr/bin/env python3
"""Test the actual duplicate check against the database."""

import os
import sys

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

from supabase import create_client
from boats_scraper import check_trip_exists

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# Get Dolphin boat ID
boat = supabase.table('boats').select('id').eq('name', 'Dolphin').execute()
boat_id = boat.data[0]['id']

print(f"Dolphin boat_id: {boat_id}")
print()

# Trip 2 catches (what should be inserted)
trip2_catches = [
    {'species': 'Barracuda', 'count': 2},
    {'species': 'Cabezon', 'count': 3},
    {'species': 'Calico Bass', 'count': 48},
    {'species': 'Rockfish', 'count': 28},
    {'species': 'Sculpin', 'count': 3}
]

print("Testing check_trip_exists for Trip 2:")
print(f"  boat_id={boat_id}")
print(f"  trip_date='2025-08-07'")
print(f"  trip_duration='1/2 Day PM'")
print(f"  anglers=58")
print(f"  catches={trip2_catches}")
print()

result = check_trip_exists(
    supabase=supabase,
    boat_id=boat_id,
    trip_date='2025-08-07',
    trip_duration='1/2 Day PM',
    anglers=58,
    catches=trip2_catches
)

print(f"check_trip_exists result: {result}")
print()

if result:
    print("❌ PROBLEM: Trip 2 is being marked as duplicate!")
    print("This means the catch comparison is not working as expected in the actual flow.")
else:
    print("✅ Trip 2 is correctly identified as NOT a duplicate")
    print("This means it SHOULD have been inserted... but it wasn't.")
    print()
    print("Possible issues:")
    print("1. The insert failed with an exception (check logs)")
    print("2. There's a database constraint preventing insertion")
    print("3. The trips are being processed in the wrong order")
