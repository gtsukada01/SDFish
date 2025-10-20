-- Remove the unique constraint that prevents multiple trips with same boat/date/type/anglers
-- This allows boats to run multiple trips with identical metadata but different catches

ALTER TABLE trips DROP CONSTRAINT IF EXISTS trips_unique_trip;

-- Note: The scraper now handles duplicate detection using catch comparison
-- at the application level, so we don't need a database-level unique constraint
