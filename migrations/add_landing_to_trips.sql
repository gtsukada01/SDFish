-- Migration: Add landing_id to trips table for historical accuracy
-- Date: 2025-10-16
-- Reason: Boats move between landings over time. Need to store landing per trip, not per boat.
-- Example: Constitution was at H&M Landing in 2024, moved to Fisherman's Landing in 2025.

-- Step 1: Add landing_id column to trips table
ALTER TABLE trips
ADD COLUMN IF NOT EXISTS landing_id INTEGER REFERENCES landings(id);

-- Step 2: Create index for performance
CREATE INDEX IF NOT EXISTS idx_trips_landing_id ON trips(landing_id);

-- Step 3: Backfill existing trips with landing from boats table (temporary measure)
-- This assigns current boat landing to historical trips - not perfect but prevents NULL values
UPDATE trips
SET landing_id = boats.landing_id
FROM boats
WHERE trips.boat_id = boats.id
  AND trips.landing_id IS NULL;

-- Step 4: Verify the migration
SELECT
    COUNT(*) as total_trips,
    COUNT(landing_id) as trips_with_landing,
    COUNT(*) - COUNT(landing_id) as trips_without_landing
FROM trips;

-- Note: After this migration, re-scrape historical data to get accurate landing associations
