-- Migration: add raw landing slug and trip hash versioning
-- Date: 2025-10-23

ALTER TABLE trips
    ADD COLUMN IF NOT EXISTS raw_landing_slug TEXT,
    ADD COLUMN IF NOT EXISTS trip_hash_version SMALLINT NOT NULL DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_trips_raw_landing_slug
    ON trips (raw_landing_slug);
