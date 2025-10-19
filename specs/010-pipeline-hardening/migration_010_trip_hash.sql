-- ============================================================================
-- SPEC-010 Phase 2: FR-005 Deep Deduplication Migration
-- ============================================================================
--
-- Purpose: Add trip_hash column to trips table for phantom duplicate detection
-- Date: October 19, 2025
-- Version: Phase 2 - FR-005
--
-- What this does:
-- - Adds trip_hash column (VARCHAR(16)) to trips table
-- - Creates index on trip_hash for fast duplicate lookups
-- - Backfills trip_hash for existing trips (optional)
--
-- Prerequisites:
-- - Phase 1 migration (scrape_jobs table) must be completed
-- - Supabase project: ulsbtwqhwnrpkourphiq.supabase.co
--
-- Execution Method:
-- 1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq/sql/new
-- 2. Copy this entire file
-- 3. Paste into SQL Editor
-- 4. Click "Run" button
-- 5. Verify with verification queries below
--
-- Rollback:
-- See "Rollback Procedure" section at bottom of file
--
-- ============================================================================

-- PHASE 1: Add trip_hash column to trips table
-- ============================================================================

-- Add trip_hash column (nullable initially for backward compatibility)
ALTER TABLE trips ADD COLUMN IF NOT EXISTS trip_hash VARCHAR(16);

-- Add comment to document purpose
COMMENT ON COLUMN trips.trip_hash IS 'SPEC-010 FR-005: Content hash for phantom duplicate detection (excludes trip_date)';

-- PHASE 2: Create index for fast duplicate lookups
-- ============================================================================

-- Create index on trip_hash for O(log n) duplicate lookups
CREATE INDEX IF NOT EXISTS idx_trips_hash ON trips(trip_hash);

-- Add comment to document purpose
COMMENT ON INDEX idx_trips_hash IS 'SPEC-010 FR-005: Fast duplicate lookup for N-day cross-check';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Query 1: Verify trip_hash column exists
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'trips'
  AND column_name = 'trip_hash';

-- Expected result:
-- column_name | data_type | character_maximum_length | is_nullable
-- trip_hash   | character varying | 16          | YES

-- Query 2: Verify index exists
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'trips'
  AND indexname = 'idx_trips_hash';

-- Expected result:
-- indexname      | indexdef
-- idx_trips_hash | CREATE INDEX idx_trips_hash ON public.trips USING btree (trip_hash)

-- Query 3: Check current trip_hash population
SELECT
    COUNT(*) AS total_trips,
    COUNT(trip_hash) AS trips_with_hash,
    COUNT(*) - COUNT(trip_hash) AS trips_without_hash,
    ROUND(100.0 * COUNT(trip_hash) / COUNT(*), 2) AS hash_coverage_pct
FROM trips;

-- Expected result (before backfill):
-- total_trips | trips_with_hash | trips_without_hash | hash_coverage_pct
-- 7958        | 0               | 7958               | 0.00

-- Expected result (after backfill):
-- total_trips | trips_with_hash | trips_without_hash | hash_coverage_pct
-- 7958        | 7958            | 0                  | 100.00

-- ============================================================================
-- OPTIONAL: Backfill trip_hash for existing trips
-- ============================================================================

-- NOTE: Backfilling trip_hash for existing trips is OPTIONAL
-- New trips will automatically have trip_hash computed by boats_scraper.py
-- Backfill is only needed if you want to detect phantom duplicates in historical data

-- To backfill, you would need to:
-- 1. Export all trips to JSON
-- 2. Compute trip_hash for each trip using Python compute_trip_hash() function
-- 3. UPDATE each trip with computed hash
--
-- Example Python script (not included here):
-- ```python
-- import json
-- import hashlib
-- from supabase import create_client
--
-- def compute_trip_hash(boat_id, trip_duration, anglers, catches):
--     sorted_catches = sorted(catches, key=lambda c: c['species'])
--     hash_input = {
--         'boat_id': boat_id,
--         'trip_duration': trip_duration,
--         'anglers': anglers,
--         'catches': sorted_catches
--     }
--     hash_str = json.dumps(hash_input, sort_keys=True)
--     return hashlib.sha256(hash_str.encode()).hexdigest()[:16]
--
-- # Fetch all trips, compute hashes, update database
-- # ...
-- ```

-- ============================================================================
-- ROLLBACK PROCEDURE
-- ============================================================================

-- WARNING: Rollback will REMOVE trip_hash column and index
-- Only use this if Phase 2 implementation needs to be reverted

-- ROLLBACK STEP 1: Drop index
-- DROP INDEX IF EXISTS idx_trips_hash;

-- ROLLBACK STEP 2: Drop column
-- ALTER TABLE trips DROP COLUMN IF EXISTS trip_hash;

-- ROLLBACK VERIFICATION:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'trips' AND column_name = 'trip_hash';
-- Expected result: 0 rows (column removed)

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- If all verification queries pass:
-- ✅ trip_hash column added to trips table
-- ✅ idx_trips_hash index created for fast lookups
-- ✅ Migration successful - Phase 2 FR-005 database schema complete
--
-- Next steps:
-- 1. New trips will automatically have trip_hash computed
-- 2. Phantom duplicates will be detected during scraping
-- 3. (Optional) Backfill trip_hash for historical trips if needed
--
-- ============================================================================
