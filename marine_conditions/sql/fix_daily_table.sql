-- Fix marine_conditions_daily table by dropping and recreating without problematic generated columns

-- Drop the existing table if it exists
DROP TABLE IF EXISTS marine_conditions_daily;

-- Create a simplified version without generated columns
CREATE TABLE marine_conditions_daily (
    id BIGSERIAL PRIMARY KEY,
    buoy_id VARCHAR(10) NOT NULL,
    observation_date DATE NOT NULL,
    wind_speed_min_kts NUMERIC(5,2),
    wind_speed_min_time TIMESTAMP WITH TIME ZONE,
    wind_speed_median_kts NUMERIC(5,2),
    wind_speed_max_kts NUMERIC(5,2),
    wind_speed_max_time TIMESTAMP WITH TIME ZONE,
    sample_count INTEGER NOT NULL DEFAULT 0,
    valid_count INTEGER NOT NULL DEFAULT 0,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'partial',
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (buoy_id, observation_date)
);

CREATE INDEX idx_marine_conditions_daily_buoy_date
    ON marine_conditions_daily (buoy_id, observation_date);

-- Add a comment explaining the PST conversion should be done in the application layer
COMMENT ON TABLE marine_conditions_daily IS
'Daily wind summaries for buoys. PST conversion handled in application layer to avoid timezone issues.';