"""Scheduled worker that ingests NOAA buoy observations into Supabase."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Tuple

from ..config import MarineConfig, UTC
from ..core.buoy_client import BuoyClient
from ..core.models import BuoyObservation
from ..core.supabase_client import MarineSupabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FETCH_LIMIT = int(os.environ.get("MARINE_FETCH_LIMIT", "96"))


def _fetch_with_fallback(
    client: BuoyClient, buoy_id: str, config: MarineConfig
) -> Tuple[List[BuoyObservation], str]:
    """Fetch observations for a buoy, falling back when primary data is missing."""
    observations = client.fetch_recent_observations(buoy_id, limit=FETCH_LIMIT)
    if _has_valid_wind(observations):
        return observations, buoy_id

    fallback = config.fallback_buoys.get(buoy_id)
    if not fallback:
        logger.warning("No valid wind data for %s and no fallback configured", buoy_id)
        return observations, buoy_id

    logger.warning(
        "Primary buoy %s returned no valid wind readings; attempting fallback %s",
        buoy_id,
        fallback,
    )
    try:
        fallback_observations = client.fetch_recent_observations(fallback, limit=FETCH_LIMIT)
        if _has_valid_wind(fallback_observations):
            return fallback_observations, fallback
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallback buoy %s fetch failed: %s", fallback, exc)
    # Return whatever we managed to collect (may be empty) so caller logs metrics
    return observations, buoy_id


def _has_valid_wind(observations: List[BuoyObservation]) -> bool:
    return any(obs.wind_speed_kts is not None for obs in observations)


def main() -> None:
    config = MarineConfig.from_env()
    session = BuoyClient()
    supabase = MarineSupabase(config.supabase_url, config.supabase_key)

    logger.info("Starting buoy ingestion for %s", ", ".join(config.priority_buoys))

    total_inserted = 0
    for buoy_id in config.priority_buoys:
        try:
            observations, source_id = _fetch_with_fallback(session, buoy_id, config)
            supabase.insert_observations(observations)
            total_inserted += len(observations)
            logger.info(
                "Upserted %d observations for buoy %s (source: %s)",
                len(observations),
                buoy_id,
                source_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed ingest for buoy %s: %s", buoy_id, exc)

    logger.info("Ingestion complete at %s; attempted rows: %d", datetime.now(tz=UTC).isoformat(), total_inserted)


if __name__ == "__main__":
    main()
