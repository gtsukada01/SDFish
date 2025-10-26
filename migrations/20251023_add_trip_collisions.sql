-- Migration: add trip_collisions telemetry table
-- Date: 2025-10-23

CREATE TABLE IF NOT EXISTS trip_collisions (
    id BIGSERIAL PRIMARY KEY,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    scrape_job_id BIGINT REFERENCES scrape_jobs(id),
    boat_name TEXT,
    trip_date DATE,
    trip_duration TEXT,
    anglers INTEGER,
    raw_landing_slug TEXT,
    normalized_landing TEXT,
    existing_trip_id BIGINT REFERENCES trips(id),
    existing_catches JSONB,
    new_catches JSONB,
    composite_key_hash TEXT,
    trip_hash TEXT,
    resolution TEXT DEFAULT 'skipped',
    scraper_version TEXT,
    git_sha TEXT
);

CREATE INDEX IF NOT EXISTS idx_trip_collisions_trip_date
    ON trip_collisions (trip_date);

CREATE INDEX IF NOT EXISTS idx_trip_collisions_boat_date
    ON trip_collisions (boat_name, trip_date);

CREATE INDEX IF NOT EXISTS idx_trip_collisions_composite_hash
    ON trip_collisions (composite_key_hash);
