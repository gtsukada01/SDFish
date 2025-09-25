"""Ingest historical NOAA buoy data from a specific date range."""

import logging
import os
from datetime import datetime, timedelta
from typing import List
import time

import requests
from dateutil import parser

from ..config import MarineConfig, UTC
from ..core.models import BuoyObservation
from ..core.supabase_client import MarineSupabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Historical data URL pattern (includes all data for the year)
HISTORICAL_URL = "https://www.ndbc.noaa.gov/data/historical/stdmet/{buoy_id}h{year}.txt"
# Alternative: get specific month
MONTHLY_URL = "https://www.ndbc.noaa.gov/data/stdmet/{month}/{buoy_id}.txt"


def fetch_historical_data(buoy_id: str, year: int = 2025) -> List[BuoyObservation]:
    """Fetch historical data for a buoy for the entire year."""
    url = HISTORICAL_URL.format(buoy_id=buoy_id, year=year)
    logger.info(f"Fetching historical data from {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return parse_historical_data(buoy_id, response.text)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Historical data not available for {buoy_id} in {year}")
            # Try monthly approach
            return fetch_monthly_data(buoy_id, year)
        raise


def fetch_monthly_data(buoy_id: str, year: int) -> List[BuoyObservation]:
    """Fetch data month by month for the current year."""
    all_observations = []
    current_date = datetime.now(UTC)

    for month in range(1, current_date.month + 1):
        month_str = f"{year}{month:02d}"
        url = MONTHLY_URL.format(month=month_str, buoy_id=buoy_id)

        try:
            logger.info(f"Fetching {month_str} data for {buoy_id}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            observations = parse_historical_data(buoy_id, response.text)
            all_observations.extend(observations)
            logger.info(f"Got {len(observations)} observations for {month_str}")
            time.sleep(1)  # Be polite to NOAA servers
        except Exception as e:
            logger.warning(f"Could not fetch {month_str}: {e}")

    return all_observations


def parse_historical_data(buoy_id: str, text: str) -> List[BuoyObservation]:
    """Parse historical NOAA buoy data format."""
    lines = text.strip().split('\n')
    observations = []

    # Skip header lines (start with #)
    data_lines = [line for line in lines if line and not line.startswith('#')]

    for line in data_lines:
        try:
            parts = line.split()
            if len(parts) < 14:
                continue

            # Historical format has same structure as realtime
            year = int(parts[0])
            # Handle both 2-digit and 4-digit years
            if year < 100:
                year = 2000 + year if year <= 50 else 1900 + year

            obs_time = datetime(
                year,
                int(parts[1]),  # month
                int(parts[2]),  # day
                int(parts[3]),  # hour
                int(parts[4]),  # minute
                tzinfo=UTC
            )

            # Skip data outside our target range
            if obs_time.year != 2025:
                continue
            if obs_time < datetime(2025, 1, 1, tzinfo=UTC):
                continue
            if obs_time > datetime.now(UTC):
                continue

            wind_speed = parse_float(parts[6])  # WSPD in m/s
            # Convert m/s to knots if needed (1 m/s = 1.94384 knots)
            if wind_speed is not None:
                wind_speed = wind_speed * 1.94384

            observation = BuoyObservation(
                buoy_id=buoy_id,
                observation_time=obs_time,
                wind_speed_kts=wind_speed,
                wind_gust_kts=parse_float(parts[7]) * 1.94384 if parse_float(parts[7]) else None,
                wind_direction_deg=parse_int(parts[5]),
                wave_height_m=parse_float(parts[8]),
                water_temp_c=parse_float(parts[14]),
                air_temp_c=parse_float(parts[13]),
                pressure_hpa=parse_float(parts[12]),
                fetched_at=datetime.now(UTC)
            )
            observations.append(observation)

        except Exception as e:
            logger.debug(f"Could not parse line: {line[:50]}... - {e}")
            continue

    return observations


def parse_float(value: str) -> float:
    """Parse float value, handling missing data markers."""
    if value in ['MM', '99', '999', '99.', '999.', '99.0', '999.0', '']:
        return None
    try:
        return float(value)
    except:
        return None


def parse_int(value: str) -> int:
    """Parse int value, handling missing data markers."""
    if value in ['MM', '999', '99', '']:
        return None
    try:
        return int(value)
    except:
        return None


def main():
    """Main function to ingest historical data."""
    config = MarineConfig.from_env()
    supabase = MarineSupabase(config.supabase_url, config.supabase_key)

    # Target buoys
    buoys = ['46047', '46086']

    start_date = datetime(2025, 1, 1, tzinfo=UTC)
    end_date = datetime.now(UTC)

    logger.info(f"Starting historical ingestion from {start_date.date()} to {end_date.date()}")

    total_inserted = 0
    for buoy_id in buoys:
        try:
            # Fetch historical data
            observations = fetch_historical_data(buoy_id, 2025)

            # Filter to our date range
            filtered_obs = [
                obs for obs in observations
                if start_date <= obs.observation_time <= end_date
            ]

            logger.info(f"Got {len(filtered_obs)} observations for {buoy_id}")

            if filtered_obs:
                # Insert in batches to avoid timeouts
                batch_size = 500
                for i in range(0, len(filtered_obs), batch_size):
                    batch = filtered_obs[i:i+batch_size]
                    supabase.insert_observations(batch)
                    total_inserted += len(batch)
                    logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} records)")
                    time.sleep(0.5)  # Brief pause between batches

        except Exception as e:
            logger.error(f"Failed to process {buoy_id}: {e}")

    logger.info(f"Historical ingestion complete. Total records inserted: {total_inserted}")

    # Show date coverage
    logger.info("\nNow run aggregation for each date:")
    current = start_date
    while current.date() <= end_date.date():
        print(f"MARINE_TARGET_DATE={current.date()} python3 -m marine_conditions.workers.aggregate_daily_wind")
        current += timedelta(days=1)


if __name__ == "__main__":
    main()