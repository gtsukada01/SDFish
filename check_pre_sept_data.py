#!/usr/bin/env python3
"""Check for trips before September 1, 2025"""

from supabase import create_client
from datetime import datetime

# Initialize Supabase
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check trips before Sept 1, 2025
result = supabase.table('trips').select('trip_date', count='exact').lt('trip_date', '2025-09-01').execute()

print(f'Trips before 09/01/2025: {result.count}')

# Get date range if any exist
if result.count > 0:
    earliest = supabase.table('trips').select('trip_date').order('trip_date').limit(1).execute()
    latest_before_sept = supabase.table('trips').select('trip_date').lt('trip_date', '2025-09-01').order('trip_date', desc=True).limit(1).execute()

    print(f'Earliest trip in database: {earliest.data[0]["trip_date"]}')
    print(f'Latest trip before Sept 1: {latest_before_sept.data[0]["trip_date"]}')

    # Show breakdown by month
    print('\nBreakdown by month:')
    months = supabase.table('trips').select('trip_date').lt('trip_date', '2025-09-01').execute()
    from collections import Counter
    month_counts = Counter(date['trip_date'][:7] for date in months.data)
    for month in sorted(month_counts.keys()):
        print(f'  {month}: {month_counts[month]} trips')
else:
    print('✅ No trips found before 09/01/2025 - database is already clean!')
