"""Aggregate wind summaries for all dates with data."""

import logging
import os
from datetime import datetime, date
import time

from ..config import MarineConfig, UTC
from ..core.supabase_client import MarineSupabase
from ..core.aggregation import summarize_daily_wind

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Aggregate all dates that have data."""
    config = MarineConfig.from_env()
    supabase = MarineSupabase(config.supabase_url, config.supabase_key)

    # Get all unique dates from the database
    from supabase import create_client
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    sb = create_client(url, key)

    result = sb.table('marine_conditions').select('observation_time').execute()
    unique_dates = sorted(set(row['observation_time'][:10] for row in result.data))

    logger.info(f"Found {len(unique_dates)} unique dates with data")
    logger.info(f"Date range: {unique_dates[0]} to {unique_dates[-1]}")

    successful = 0
    failed = 0

    for date_str in unique_dates:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Processing {date_str}...")

            # Fetch observations for all buoys for this date
            all_obs = []
            for buoy_id in config.priority_buoys:
                observations = supabase.fetch_observations_for_date(buoy_id, target_date)
                if observations:
                    all_obs.extend(observations)
                    logger.debug(f"Got {len(observations)} observations for {buoy_id}")

            if not all_obs:
                logger.debug(f"No observations for {target_date}")
                continue

            # Summarize the day's wind data
            summaries = summarize_daily_wind(all_obs)

            for summary in summaries:
                supabase.upsert_daily_summary(summary)
                logger.info(
                    f"  ✓ {summary.buoy_id}: min {summary.wind_speed_min_kts:.1f} / "
                    f"median {summary.wind_speed_median_kts:.1f} / "
                    f"max {summary.wind_speed_max_kts:.1f} kts"
                )
                successful += 1

            # Brief pause to avoid overwhelming the database
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to process {date_str}: {e}")
            failed += 1

    logger.info(f"\n✅ Aggregation complete!")
    logger.info(f"  Successful: {successful} summaries")
    logger.info(f"  Failed: {failed} dates")

    # Verify the results
    logger.info("\nVerifying daily summaries in database...")
    result = sb.table('marine_conditions_daily').select('*', count='exact').execute()
    logger.info(f"Total daily summaries in database: {result.count}")


if __name__ == "__main__":
    main()