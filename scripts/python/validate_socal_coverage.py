#!/usr/bin/env python3
"""Validate SoCal database coverage"""

import os
from supabase import create_client
from datetime import datetime

# Initialize Supabase
url = os.getenv("SUPABASE_URL", "https://ulsbtwqhwnrpkourphiq.supabase.co")
key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U")
supabase = create_client(url, key)

print("=" * 80)
print("📊 SOCAL DATABASE COVERAGE REPORT")
print("=" * 80)

# SoCal landing names from the scraper log
socal_landing_names = [
    'Channel Islands Sportfishing',
    'Marina Del Rey Sportfishing',
    'Long Beach Sportfishing',
    '22nd Street Landing',
    'Newport Landing',
    "Davey's Locker",
    'Dana Wharf Sportfishing',
    'Hooks Landing',
    'Newport Beach, CA'
]

# Get all landings
all_landings = supabase.table('landings').select('*').execute()

# Categorize landings
socal_landings = [l for l in all_landings.data if l['name'] in socal_landing_names]
sd_landings = [l for l in all_landings.data if l['name'] not in socal_landing_names]

print(f"\n🏢 Landings Summary:")
print(f"  - Total landings: {len(all_landings.data)}")
print(f"  - SoCal landings: {len(socal_landings)}")
print(f"  - San Diego landings: {len(sd_landings)}")

# Get boats for each landing type
socal_landing_ids = [l['id'] for l in socal_landings]
sd_landing_ids = [l['id'] for l in sd_landings]

socal_boats = supabase.table('boats').select('id').in_('landing_id', socal_landing_ids).execute()
sd_boats = supabase.table('boats').select('id').in_('landing_id', sd_landing_ids).execute()

socal_boat_ids = [b['id'] for b in socal_boats.data]
sd_boat_ids = [b['id'] for b in sd_boats.data]

print(f"\n🚤 Boats:")
print(f"  - SoCal boats: {len(socal_boat_ids)}")
print(f"  - San Diego boats: {len(sd_boat_ids)}")

# Get trip counts
socal_trips = supabase.table('trips').select('id', count='exact').in_('boat_id', socal_boat_ids).execute()
sd_trips = supabase.table('trips').select('id', count='exact').in_('boat_id', sd_boat_ids).execute()

print(f"\n🎣 Trips:")
print(f"  - SoCal trips: {socal_trips.count}")
print(f"  - San Diego trips: {sd_trips.count}")
print(f"  - Total trips: {socal_trips.count + sd_trips.count}")

# Breakdown by landing
print(f"\n🌊 SoCal Landings Details:")
for landing in sorted(socal_landings, key=lambda x: x['name']):
    boats = supabase.table('boats').select('id').eq('landing_id', landing['id']).execute()
    if boats.data:
        boat_ids = [b['id'] for b in boats.data]
        trips = supabase.table('trips').select('id', count='exact').in_('boat_id', boat_ids).execute()
        print(f"  - {landing['name']}: {trips.count} trips ({len(boat_ids)} boats)")

# Get date range coverage for SoCal
if socal_boat_ids:
    print(f"\n📅 SoCal Date Coverage:")
    trips_with_dates = supabase.table('trips')\
        .select('trip_date')\
        .in_('boat_id', socal_boat_ids)\
        .execute()

    if trips_with_dates.data:
        dates = sorted(set(t['trip_date'] for t in trips_with_dates.data))
        print(f"  - Earliest: {dates[0]}")
        print(f"  - Latest: {dates[-1]}")
        print(f"  - Unique dates: {len(dates)}")
        print(f"  - Expected range: 2025-09-15 to 2025-10-15 (31 days)")

        # Check September coverage
        sept_dates = [d for d in dates if d.startswith('2025-09')]
        oct_dates = [d for d in dates if d.startswith('2025-10')]
        print(f"  - September 2025: {len(sept_dates)} dates")
        print(f"  - October 2025: {len(oct_dates)} dates")

print("\n" + "=" * 80)
