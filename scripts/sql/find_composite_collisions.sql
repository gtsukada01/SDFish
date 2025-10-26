-- Detect composite key collisions where identical metadata wraps different catches
-- Usage: run in Supabase SQL editor or psql

WITH normalized AS (
    SELECT
        t.trip_date,
        b.name AS boat_name,
        t.trip_duration,
        t.anglers,
        COALESCE(t.raw_landing_slug, 'legacy') AS landing_key,
        jsonb_agg(
            jsonb_build_object(
                'species', lower(c.species),
                'count', c.count
            )
            ORDER BY lower(c.species)
        ) AS catches
    FROM trips t
    JOIN boats b ON t.boat_id = b.id
    JOIN catches c ON c.trip_id = t.id
    WHERE t.trip_date BETWEEN :start_date AND :end_date
    GROUP BY t.id, b.name, t.trip_date, t.trip_duration, t.anglers, landing_key
),
grouped AS (
    SELECT
        trip_date,
        boat_name,
        trip_duration,
        anglers,
        landing_key,
        catches,
        COUNT(*) OVER (PARTITION BY trip_date, boat_name, trip_duration, anglers, landing_key) AS collision_count
    FROM normalized
)
SELECT *
FROM grouped
WHERE collision_count > 1
ORDER BY trip_date, boat_name;
