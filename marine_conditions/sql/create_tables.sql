-- Schema for marine conditions ingestion MVP

CREATE TABLE IF NOT EXISTS marine_conditions (
    id BIGSERIAL PRIMARY KEY,
    buoy_id VARCHAR(10) NOT NULL,
    observation_time TIMESTAMP WITH TIME ZONE NOT NULL,
    wind_speed_kts NUMERIC(5,2),
    wind_gust_kts NUMERIC(5,2),
    wind_direction_deg SMALLINT,
    wave_height_m NUMERIC(5,2),
    water_temp_c NUMERIC(5,2),
    air_temp_c NUMERIC(5,2),
    pressure_hpa NUMERIC(6,2),
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (buoy_id, observation_time)
);

CREATE INDEX IF NOT EXISTS idx_marine_conditions_buoy_time
    ON marine_conditions (buoy_id, observation_time);

CREATE TABLE IF NOT EXISTS marine_conditions_daily (
    id BIGSERIAL PRIMARY KEY,
    buoy_id VARCHAR(10) NOT NULL,
    observation_date DATE NOT NULL,
    wind_speed_min_kts NUMERIC(5,2),
    wind_speed_min_time TIMESTAMP WITH TIME ZONE,
    wind_speed_min_time_pst TIMESTAMP WITHOUT TIME ZONE
        GENERATED ALWAYS AS (wind_speed_min_time AT TIME ZONE 'America/Los_Angeles') STORED,
    wind_speed_median_kts NUMERIC(5,2),
    wind_speed_max_kts NUMERIC(5,2),
    wind_speed_max_time TIMESTAMP WITH TIME ZONE,
    wind_speed_max_time_pst TIMESTAMP WITHOUT TIME ZONE
        GENERATED ALWAYS AS (wind_speed_max_time AT TIME ZONE 'America/Los_Angeles') STORED,
    sample_count INTEGER NOT NULL DEFAULT 0,
    valid_count INTEGER NOT NULL DEFAULT 0,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'partial',
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (buoy_id, observation_date)
);

CREATE INDEX IF NOT EXISTS idx_marine_conditions_daily_buoy_date
    ON marine_conditions_daily (buoy_id, observation_date);
