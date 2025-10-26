#!/usr/bin/env python3
"""Quick verification of October 2025 baseline and existing Jan-Sep 2025 data."""

from supabase import create_client
from collections import Counter

supabase = create_client(
    "https://ulsbtwqhwnrpkourphiq.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
)

# Check October 2025 baseline
result = supabase.table('socal_trips').select('*').gte('trip_date', '2025-10-01').lte('trip_date', '2025-10-31').execute()
print(f'✅ October 2025: {len(result.data)} trips in database')

# Check for any existing Jan-Sep 2025 data
result_jan_sep = supabase.table('socal_trips').select('*').gte('trip_date', '2025-01-01').lt('trip_date', '2025-10-01').execute()
print(f'📊 Jan-Sep 2025 existing: {len(result_jan_sep.data)} trips')

# Show breakdown by month if any exist
if len(result_jan_sep.data) > 0:
    months = Counter([trip['trip_date'][:7] for trip in result_jan_sep.data])
    print('\nExisting data by month:')
    for month in sorted(months.keys()):
        print(f'  {month}: {months[month]} trips')
else:
    print('\n✨ No Jan-Sep 2025 data yet - ready for fresh backfill!')
