-- SPEC-010 Migration: Scrape Jobs Audit Trail
-- FR-003: Complete audit trail for all scraping operations
-- Created: 2025-10-19
-- Priority: P0 - CRITICAL

-- ========================================
-- PHASE 1: Create scrape_jobs table
-- ========================================

BEGIN;

-- Create scrape_jobs audit table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id BIGSERIAL PRIMARY KEY,

    -- Timing
    job_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    job_completed_at TIMESTAMPTZ,
    job_status VARCHAR(20) NOT NULL CHECK (job_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'ABORTED')),

    -- Operator tracking
    operator VARCHAR(255) NOT NULL,
    operator_source VARCHAR(50) NOT NULL,  -- 'cli', 'api', 'cron', 'manual'

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

-- Add comment documenting the table
COMMENT ON TABLE scrape_jobs IS 'SPEC-010 FR-003: Complete audit trail for all scraping operations. Tracks operator, parameters, version control, and results.';

COMMIT;

-- ========================================
-- PHASE 2: Add scrape_job_id to trips
-- ========================================

BEGIN;

-- Add foreign key to trips table
ALTER TABLE trips ADD COLUMN IF NOT EXISTS scrape_job_id BIGINT REFERENCES scrape_jobs(id);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_trips_scrape_job ON trips(scrape_job_id);

-- Add comment
COMMENT ON COLUMN trips.scrape_job_id IS 'SPEC-010 FR-003: Links trip to scrape job for complete audit trail';

COMMIT;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Verify scrape_jobs table exists
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name = 'scrape_jobs';

-- Verify all indexes created
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'scrape_jobs';

-- Verify scrape_job_id column added
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'trips'
  AND column_name = 'scrape_job_id';

-- ========================================
-- ROLLBACK PROCEDURE (if needed)
-- ========================================

-- UNCOMMENT TO ROLLBACK:
-- BEGIN;
-- DROP INDEX IF EXISTS idx_trips_scrape_job;
-- ALTER TABLE trips DROP COLUMN IF EXISTS scrape_job_id;
-- DROP TABLE IF EXISTS scrape_jobs CASCADE;
-- COMMIT;
