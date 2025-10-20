#!/usr/bin/env python3
"""Remove the trips_unique_trip constraint to allow multiple trips with same metadata but different catches."""

import os
from supabase import create_client

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U'

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

print("Removing trips_unique_trip constraint...")
print()

sql = "ALTER TABLE trips DROP CONSTRAINT IF EXISTS trips_unique_trip;"

try:
    result = supabase.rpc('exec_sql', {'sql': sql}).execute()
    print("✅ SUCCESS: Unique constraint removed!")
    print()
    print("Now multiple trips with same (boat, date, trip_duration, anglers) can exist")
    print("as long as they have different catches.")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    print("Alternative: Use Supabase dashboard SQL editor to run:")
    print(f"  {sql}")
