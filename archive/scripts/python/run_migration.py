#!/usr/bin/env python3
"""
Run database migration: Add landing_id to trips table

Usage:
    python3 run_migration.py

This migration adds landing_id column to trips table to support historical accuracy.
Boats can move between landings over time, so we need to track landing per trip.
"""

import sys

print("="*80)
print("DATABASE MIGRATION: Add landing_id to trips table")
print("="*80)
print()
print("MANUAL STEPS REQUIRED:")
print()
print("1. Open Supabase Dashboard:")
print("   https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq")
print()
print("2. Navigate to: SQL Editor")
print()
print("3. Click 'New Query'")
print()
print("4. Copy and paste the SQL from: migrations/add_landing_to_trips.sql")
print()
print("5. Run the query")
print()
print("6. Verify output shows:")
print("   - total_trips: [current count]")
print("   - trips_with_landing: [current count]")
print("   - trips_without_landing: 0")
print()
print("="*80)
print()

response = input("Have you completed the migration in Supabase dashboard? (y/n): ")

if response.lower() == 'y':
    print()
    print("✅ Great! Verifying schema change...")
    print()

    from supabase import create_client

    SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Check if landing_id column exists
    result = supabase.table('trips').select('*').limit(1).execute()
    if result.data and 'landing_id' in result.data[0]:
        print("✅ VERIFIED: landing_id column exists in trips table")
        print()
        print("Columns in trips table:")
        for col in result.data[0].keys():
            print(f"  - {col}")
        print()
        print("✅ Migration successful! Ready to update scraper.")
        sys.exit(0)
    else:
        print("❌ ERROR: landing_id column not found in trips table")
        print("Please verify the SQL was executed correctly in Supabase dashboard.")
        sys.exit(1)
else:
    print()
    print("⏸️  Migration cancelled. Run this script again when ready.")
    print()
    sys.exit(0)
