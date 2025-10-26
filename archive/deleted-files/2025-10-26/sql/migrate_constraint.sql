-- ============================================================================
-- SPEC 006 Database Migration: Update trips_unique_trip Constraint
-- ============================================================================
--
-- PROBLEM: Current constraint doesn't include 'anglers' field
-- Current: UNIQUE (boat_id, trip_date, trip_duration)
-- Needed:  UNIQUE (boat_id, trip_date, trip_duration, anglers)
--
-- IMPACT: Blocks multiple trips per boat/date/type with different angler counts
-- Example: New Seaforth on 2025-04-12 had TWO "1/2 Day PM" trips (53 + 20 anglers)
--
-- STEPS TO RUN:
-- 1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq
-- 2. Navigate to SQL Editor
-- 3. Paste and run this entire script
-- 4. Verify success (should see "ALTER TABLE" confirmation)
-- ============================================================================

-- Step 1: Drop existing constraint
ALTER TABLE trips DROP CONSTRAINT IF EXISTS trips_unique_trip;

-- Step 2: Add new constraint with anglers field
ALTER TABLE trips ADD CONSTRAINT trips_unique_trip
  UNIQUE (boat_id, trip_date, trip_duration, anglers);

-- Step 3: Verify constraint exists
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
JOIN pg_class cl ON cl.oid = c.conrelid
WHERE
    cl.relname = 'trips'
    AND conname = 'trips_unique_trip';

-- Expected output:
-- constraint_name: trips_unique_trip
-- constraint_definition: UNIQUE (boat_id, trip_date, trip_duration, anglers)
