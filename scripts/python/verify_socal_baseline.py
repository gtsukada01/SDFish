#!/usr/bin/env python3
"""Verify SoCal (NON-San Diego) baseline - October 2025 and check for existing Jan-Sep 2025 data."""

from supabase import create_client
from collections import Counter

supabase = create_client(
    "https://ulsbtwqhwnrpkourphiq.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
)

print("🔍 Querying SoCal-specific data (www.socalfishreports.com)...\n")

# Get scrape_jobs from socalfishreports.com
jobs_result = supabase.table('scrape_jobs') \
    .select('id, start_date, end_date, source_url_pattern') \
    .like('source_url_pattern', '%socalfishreports%') \
    .execute()

print(f"✅ Found {len(jobs_result.data)} SoCal scrape jobs in database")

if len(jobs_result.data) > 0:
    # Get all SoCal trip IDs from these jobs
    job_ids = [job['id'] for job in jobs_result.data]

    # Get October 2025 SoCal trips
    oct_trips = supabase.table('trips') \
        .select('*') \
        .in_('scrape_job_id', job_ids) \
        .gte('trip_date', '2025-10-01') \
        .lte('trip_date', '2025-10-31') \
        .execute()

    print(f"✅ October 2025 SoCal trips: {len(oct_trips.data)} trips")

    # Get Jan-Sep 2025 SoCal trips
    jan_sep_trips = supabase.table('trips') \
        .select('*') \
        .in_('scrape_job_id', job_ids) \
        .gte('trip_date', '2025-01-01') \
        .lt('trip_date', '2025-10-01') \
        .execute()

    print(f"📊 Jan-Sep 2025 SoCal trips: {len(jan_sep_trips.data)} trips")

    # Show breakdown by month if any exist
    if len(jan_sep_trips.data) > 0:
        months = Counter([trip['trip_date'][:7] for trip in jan_sep_trips.data])
        print('\n📅 Existing SoCal data by month:')
        for month in sorted(months.keys()):
            print(f'  {month}: {months[month]} trips')
    else:
        print('\n✨ No Jan-Sep 2025 SoCal data yet - ready for fresh backfill!')
else:
    print("\n⚠️  No SoCal scrape jobs found - database might be empty or schema different")
