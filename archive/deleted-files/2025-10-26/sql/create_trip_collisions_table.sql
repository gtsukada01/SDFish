-- Phase 1.1: Create trip_collisions telemetry table

CREATE TABLE IF NOT EXISTS trip_collisions (
    id BIGSERIAL PRIMARY KEY,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Trip metadata
    boat_name TEXT NOT NULL,
    trip_date DATE NOT NULL,
    trip_duration TEXT NOT NULL,
    anglers INT,

    -- Landing information (the smoking gun)
    raw_landing_slug TEXT,           -- e.g., "daveys_locker", "newport_landing"
    normalized_landing TEXT,          -- e.g., "Newport Landing" (after normalization)

    -- Existing trip details
    existing_trip_id BIGINT,
    existing_catches JSONB,           -- Array of {species, count}

    -- New trip details
    new_catches JSONB,                -- Array of {species, count}

    -- Deduplication metadata
    composite_key_hash TEXT,          -- For debugging
    trip_hash TEXT,                   -- Current trip_hash value

    -- Resolution tracking
    resolution TEXT CHECK (resolution IN ('skipped', 'overwrote', 'flagged', 'logged')),

    -- Audit trail
    scraper_version TEXT,
    git_sha TEXT,

    CONSTRAINT unique_collision UNIQUE(trip_date, boat_name, trip_duration, anglers, detected_at)
);

-- Indexes for querying collisions
CREATE INDEX IF NOT EXISTS idx_trip_collisions_date ON trip_collisions(trip_date);
CREATE INDEX IF NOT EXISTS idx_trip_collisions_boat ON trip_collisions(boat_name);
CREATE INDEX IF NOT EXISTS idx_trip_collisions_detected_at ON trip_collisions(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_trip_collisions_resolution ON trip_collisions(resolution);

-- View for easy collision analysis
CREATE OR REPLACE VIEW collision_summary AS
SELECT
    trip_date,
    boat_name,
    trip_duration,
    anglers,
    COUNT(*) as collision_count,
    MIN(detected_at) as first_detected,
    MAX(detected_at) as last_detected,
    array_agg(DISTINCT resolution) as resolutions
FROM trip_collisions
GROUP BY trip_date, boat_name, trip_duration, anglers
ORDER BY trip_date DESC, collision_count DESC;

COMMENT ON TABLE trip_collisions IS 'Telemetry for composite key collisions during scraping. Captures when same boat/date/type/anglers composite key maps to different catch payloads.';
COMMENT ON COLUMN trip_collisions.raw_landing_slug IS 'Original landing slug from source URL before normalization (e.g., daveys_locker)';
COMMENT ON COLUMN trip_collisions.normalized_landing IS 'Landing name after normalization rules applied (e.g., Newport Landing)';
COMMENT ON COLUMN trip_collisions.resolution IS 'Action taken: skipped (duplicate), overwrote (replaced), flagged (needs review), logged (telemetry only)';
