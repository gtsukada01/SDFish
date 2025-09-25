"""Daily aggregation job for buoy wind statistics."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from ..config import MarineConfig, UTC
from ..core.aggregation import summarize_daily_wind
from ..core.supabase_client import MarineSupabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config = MarineConfig.from_env()
    supabase = MarineSupabase(config.supabase_url, config.supabase_key)

    target_date = _resolve_target_date()
    logger.info("Aggregating wind summaries for %s", target_date)

    all_observations = []
    for buoy_id in config.priority_buoys:
        observations = supabase.fetch_observations_for_date(buoy_id, target_date)
        logger.info(
            "Fetched %d raw observations for buoy %s on %s",
            len(observations),
            buoy_id,
            target_date,
        )
        all_observations.extend(observations)

    summaries = summarize_daily_wind(all_observations)

    if not summaries:
        logger.warning("No observations found to summarize for %s", target_date)
        return

    for summary in summaries:
        supabase.upsert_daily_summary(summary)
        logger.info(
            "Upserted wind summary for %s on %s (min %.1f / median %.1f / max %.1f)",
            summary.buoy_id,
            summary.observation_date,
            summary.wind_speed_min_kts or float("nan"),
            summary.wind_speed_median_kts or float("nan"),
            summary.wind_speed_max_kts or float("nan"),
        )

    logger.info("Aggregation complete at %s", datetime.now(tz=UTC).isoformat())


def _resolve_target_date() -> datetime.date:
    env_override = os.environ.get("MARINE_TARGET_DATE")
    if env_override:
        return datetime.strptime(env_override, "%Y-%m-%d").date()
    # Default to "yesterday" UTC so the job can run shortly after midnight
    return (datetime.now(tz=UTC) - timedelta(days=1)).date()


if __name__ == "__main__":
    main()
