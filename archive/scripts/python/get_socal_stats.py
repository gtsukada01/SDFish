#!/usr/bin/env python3
"""Get daily SoCal landing statistics for Oct 1-21, 2025"""

from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SoCal landing names (from scraper source)
SOCAL_LANDINGS = [
    # Channel Islands region
    'Ventura Harbor Sportfishing',
    'Channel Islands Sportfishing',
    'Hooks Landing',                             # Oxnard
    # Los Angeles region
    'Marina Del Rey Sportfishing',
    'Redondo Sportfishing',
    'Redondo Beach Sportfishing',                # Redondo Beach
    # Long Beach / San Pedro region
    'Long Beach Sportfishing',
    'Pierpoint Landing',
    '22nd Street Landing',
    'LA Waterfront Cruises and Sportfishing',  # San Pedro
    # Orange County region
    "Davey's Locker",
    'Newport Landing',
    'Dana Wharf Sportfishing'
]

# EXCLUDE Northern California landings (these should not be in SoCal counts)
# Patriot Sportfishing = Avila Beach (Northern CA)

# Get all trips from Oct 1-21 with landing info
result = supabase.table('trips').select(
    'trip_date, boat_id, boats(landing_id, landings(name))'
).gte('trip_date', '2025-10-01').lte('trip_date', '2025-10-21').execute()

# Filter for SoCal landings only
socal_trips = []
for trip in result.data:
    if trip['boats'] and trip['boats']['landings']:
        landing_name = trip['boats']['landings']['name']
        if landing_name in SOCAL_LANDINGS:
            socal_trips.append(trip)

# Count boats per day
daily_counts = defaultdict(int)
for trip in socal_trips:
    daily_counts[trip['trip_date']] += 1

# Sort by date and print
print()
print('SoCal Landing Activity (Oct 1-21, 2025)')
print('=' * 50)
print('Date         Boats/Trips')
print('-' * 50)

total = 0
for date in sorted(daily_counts.keys()):
    count = daily_counts[date]
    total += count
    print(f'{date:12} {count:>15}')

print('-' * 50)
print(f'TOTAL        {total:>15}')
print(f'Average/Day  {total/21:>15.1f}')
print()
