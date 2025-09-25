"""Fetch all available data from NOAA realtime feed (last ~45 days)."""

import logging
import os
from datetime import datetime, timedelta

from ..config import MarineConfig, UTC
from ..core.buoy_client import BuoyClient
from ..core.supabase_client import MarineSupabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Fetch ALL available data from realtime feed
FETCH_LIMIT = 10000  # Get everything available


def main():
    """Fetch all available recent data from NOAA."""
    config = MarineConfig.from_env()
    client = BuoyClient()
    supabase = MarineSupabase(config.supabase_url, config.supabase_key)

    buoys = ['46047', '46086']
    total_inserted = 0

    for buoy_id in buoys:
        try:
            logger.info(f"Fetching all available data for {buoy_id}")

            # Fetch all available observations
            observations = client.fetch_recent_observations(buoy_id, limit=FETCH_LIMIT)

            if observations:
                # Get date range
                dates = sorted(set(obs.observation_time.date() for obs in observations))
                logger.info(f"Got {len(observations)} observations for {buoy_id}")
                logger.info(f"Date range: {dates[0]} to {dates[-1]}")

                # Insert all at once
                supabase.insert_observations(observations)
                total_inserted += len(observations)
                logger.info(f"Inserted {len(observations)} observations for {buoy_id}")
            else:
                logger.warning(f"No observations found for {buoy_id}")

        except Exception as e:
            logger.error(f"Error processing {buoy_id}: {e}")

    logger.info(f"Total observations inserted: {total_inserted}")

    # Get unique dates for aggregation
    logger.info("\nChecking what dates we have data for...")

    # Query database to see what dates we have
    from supabase import create_client
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    sb = create_client(url, key)

    result = sb.table('marine_conditions').select('observation_time').execute()
    unique_dates = sorted(set(row['observation_time'][:10] for row in result.data))

    logger.info(f"Dates with data: {unique_dates[:5]} ... {unique_dates[-5:]}")
    logger.info(f"Total dates: {len(unique_dates)}")

    # Generate aggregation commands
    logger.info("\nRun these commands to aggregate all dates:")
    for date_str in unique_dates:
        print(f"MARINE_TARGET_DATE={date_str} python3 -m marine_conditions.workers.aggregate_daily_wind")


if __name__ == "__main__":
    main()