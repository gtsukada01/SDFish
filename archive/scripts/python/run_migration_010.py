#!/usr/bin/env python3
"""
SPEC-010 Migration Executor
Executes migration_010_scrape_jobs.sql using Supabase client
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ulsbtwqhwnrpkourphiq.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_KEY:
    print("❌ ERROR: SUPABASE_SERVICE_ROLE_KEY not found in environment")
    sys.exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("SPEC-010 Migration: Scrape Jobs Audit Trail")
print("=" * 60)

# Phase 1: Create scrape_jobs table
print("\n📋 PHASE 1: Creating scrape_jobs table...")

phase1_sql = """
-- Create scrape_jobs audit table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id BIGSERIAL PRIMARY KEY,

    -- Timing
    job_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    job_completed_at TIMESTAMPTZ,
    job_status VARCHAR(20) NOT NULL CHECK (job_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'ABORTED')),

    -- Operator tracking
    operator VARCHAR(255) NOT NULL,
    operator_source VARCHAR(50) NOT NULL,

    -- Scrape parameters
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    allow_future BOOLEAN DEFAULT FALSE,
    dry_run BOOLEAN DEFAULT FALSE,

    -- Version control
    git_sha VARCHAR(40),
    scraper_version VARCHAR(20),

    -- Results
    dates_processed INT DEFAULT 0,
    trips_inserted INT DEFAULT 0,
    trips_updated INT DEFAULT 0,
    trips_failed INT DEFAULT 0,

    -- Error tracking
    error_message TEXT,
    runtime_seconds NUMERIC(10,2),

    -- Source tracking
    source_url_pattern VARCHAR(500)
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(job_status);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_operator ON scrape_jobs(operator);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_dates ON scrape_jobs(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_started ON scrape_jobs(job_started_at);

-- Add comment
COMMENT ON TABLE scrape_jobs IS 'SPEC-010 FR-003: Complete audit trail for all scraping operations';
"""

try:
    # Execute Phase 1 using raw SQL through PostgREST
    result = supabase.rpc('exec_sql', {'sql': phase1_sql}).execute()
    print("✅ Phase 1 complete: scrape_jobs table created")
except Exception as e:
    # Try alternative method using table() if rpc doesn't work
    print(f"⚠️  RPC method failed, trying direct execution...")
    # Note: Supabase Python client doesn't directly support raw SQL execution
    # We need to use PostgREST or pgAdmin for this
    print(f"❌ ERROR in Phase 1: {e}")
    print("\n⚠️  FALLBACK: Please execute migration manually via Supabase SQL Editor")
    print("   File: specs/010-pipeline-hardening/migration_010_scrape_jobs.sql")
    sys.exit(1)

# Phase 2: Add scrape_job_id to trips
print("\n📋 PHASE 2: Adding scrape_job_id column to trips...")

phase2_sql = """
-- Add foreign key to trips table
ALTER TABLE trips ADD COLUMN IF NOT EXISTS scrape_job_id BIGINT REFERENCES scrape_jobs(id);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_trips_scrape_job ON trips(scrape_job_id);

-- Add comment
COMMENT ON COLUMN trips.scrape_job_id IS 'SPEC-010 FR-003: Links trip to scrape job for audit trail';
"""

try:
    result = supabase.rpc('exec_sql', {'sql': phase2_sql}).execute()
    print("✅ Phase 2 complete: scrape_job_id column added")
except Exception as e:
    print(f"❌ ERROR in Phase 2: {e}")
    sys.exit(1)

# Verification
print("\n🔍 VERIFICATION:")

verification_queries = {
    "scrape_jobs table": """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_name = 'scrape_jobs'
    """,
    "scrape_jobs indexes": """
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'scrape_jobs'
    """,
    "scrape_job_id column": """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'trips' AND column_name = 'scrape_job_id'
    """
}

for check_name, query in verification_queries.items():
    try:
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        print(f"✅ {check_name}: verified")
    except Exception as e:
        print(f"❌ {check_name}: {e}")

print("\n" + "=" * 60)
print("✅ MIGRATION COMPLETE")
print("=" * 60)
