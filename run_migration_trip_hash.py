#!/usr/bin/env python3
"""
Execute SPEC-010 Phase 2 migration: Add trip_hash column and index
"""

import sys
import psycopg2
from urllib.parse import urlparse

# Supabase connection details
PROJECT_REF = "ulsbtwqhwnrpkourphiq"
# For direct PostgreSQL connection, we need the database password
# The service role key won't work with psycopg2

# Note: This script requires direct database access
# For security reasons, database password should be in environment variable
# or the migration should be run through Supabase SQL Editor

print("="*80)
print("SPEC-010 Phase 2 Migration: Add trip_hash column and index")
print("="*80)
print()
print("⚠️  This migration requires direct database access.")
print()
print("RECOMMENDED METHOD: Use Supabase SQL Editor")
print("1. Open: https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq/sql/new")
print("2. Copy the migration SQL from: specs/010-pipeline-hardening/migration_010_trip_hash.sql")
print("3. Paste into SQL Editor and click 'Run'")
print()
print("ALTERNATIVE: This script can execute the migration if you provide DB password")
print()

# Ask user for database password
import getpass
db_password = getpass.getpass("Enter database password (or press Enter to skip): ")

if not db_password:
    print()
    print("❌ No password provided. Please use Supabase SQL Editor to execute migration.")
    print()
    print("Migration SQL to execute:")
    print("-" * 80)
    with open('specs/010-pipeline-hardening/migration_010_trip_hash.sql', 'r') as f:
        content = f.read()
        # Print only the essential SQL (skip comments)
        lines = [line for line in content.split('\n')
                if line.strip() and not line.strip().startswith('--')
                and not line.strip().startswith('SELECT')]
        print('\n'.join(lines[:20]))
    print("-" * 80)
    sys.exit(0)

# If password provided, attempt connection
try:
    # Construct connection string
    conn_string = f"postgresql://postgres:{db_password}@db.ulsbtwqhwnrpkourphiq.supabase.co:5432/postgres"

    print("Connecting to database...")
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    print("✅ Connected successfully!")
    print()

    # Execute migration
    print("Executing migration SQL...")

    # Step 1: Add trip_hash column
    print("  - Adding trip_hash column...")
    cur.execute("ALTER TABLE trips ADD COLUMN IF NOT EXISTS trip_hash VARCHAR(16);")

    print("  - Adding column comment...")
    cur.execute("COMMENT ON COLUMN trips.trip_hash IS 'SPEC-010 FR-005: Content hash for phantom duplicate detection (excludes trip_date)';")

    print("  - Creating index idx_trips_hash...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trips_hash ON trips(trip_hash);")

    print("  - Adding index comment...")
    cur.execute("COMMENT ON INDEX idx_trips_hash IS 'SPEC-010 FR-005: Fast duplicate lookup for N-day cross-check';")

    # Commit changes
    conn.commit()

    print()
    print("✅ Migration executed successfully!")
    print()

    # Verification
    print("Verifying migration...")
    print()

    # Verify column exists
    print("1. Checking trip_hash column:")
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'trips' AND column_name = 'trip_hash'
    """)
    result = cur.fetchone()
    if result:
        print(f"   ✅ Column exists: {result[0]} ({result[1]}({result[2]}), nullable={result[3]})")
    else:
        print("   ❌ Column not found!")

    print()

    # Verify index exists
    print("2. Checking idx_trips_hash index:")
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'trips' AND indexname = 'idx_trips_hash'
    """)
    result = cur.fetchone()
    if result:
        print(f"   ✅ Index exists: {result[0]}")
        print(f"      Definition: {result[1]}")
    else:
        print("   ❌ Index not found!")

    print()

    # Check hash coverage
    print("3. Checking trip_hash coverage:")
    cur.execute("""
        SELECT
            COUNT(*) AS total_trips,
            COUNT(trip_hash) AS trips_with_hash,
            COUNT(*) - COUNT(trip_hash) AS trips_without_hash,
            ROUND(100.0 * COUNT(trip_hash) / COUNT(*), 2) AS hash_coverage_pct
        FROM trips
    """)
    result = cur.fetchone()
    print(f"   Total trips: {result[0]}")
    print(f"   Trips with hash: {result[1]}")
    print(f"   Trips without hash: {result[2]}")
    print(f"   Coverage: {result[3]}%")

    print()
    print("="*80)
    print("✅ PHASE 2 MIGRATION COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("1. New trips will automatically have trip_hash computed")
    print("2. Phantom duplicates will be detected during scraping")
    print("3. Test safeguards with: python3 boats_scraper.py --start-date 2025-10-17 --end-date 2025-10-17 --dry-run")
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
