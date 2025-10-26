-- Migration: create quarantine table for re-scrape backups
-- Date: 2025-10-23

CREATE TABLE IF NOT EXISTS trips_quarantine AS
SELECT *,
       NOW() AS quarantined_at,
       NULL::TEXT AS reason
FROM trips
WHERE FALSE;

CREATE INDEX IF NOT EXISTS idx_trips_quarantine_trip_date
    ON trips_quarantine (trip_date);
