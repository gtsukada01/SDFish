"""NOAA/NDBC buoy client for pulling realtime observations."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

import requests
from dateutil import tz

from .models import BuoyObservation
from ..config import UTC

BASE_URL = "https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt"

# Standard meteorological columns exposed by NDBC
HEADERS = [
    "YY",
    "MM",
    "DD",
    "hh",
    "mm",
    "WDIR",
    "WSPD",
    "GST",
    "WVHT",
    "DPD",
    "APD",
    "MWD",
    "PRES",
    "PTDY",
    "ATMP",
    "WTMP",
    "DEWP",
    "VIS",
    "TIDE",
]


class BuoyClient:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def fetch_recent_observations(self, buoy_id: str, limit: int | None = None) -> List[BuoyObservation]:
        url = BASE_URL.format(buoy_id=buoy_id)
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return list(_parse_ndbc_text(buoy_id, response.text, limit=limit))


def _parse_ndbc_text(buoy_id: str, body: str, *, limit: int | None = None) -> Iterable[BuoyObservation]:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    # Skip header rows that begin with '#'
    data_lines = [line for line in lines if not line.startswith("#")]
    observations: List[BuoyObservation] = []

    for raw_line in data_lines:
        parts = raw_line.split()
        if len(parts) < len(HEADERS):
            continue
        record = dict(zip(HEADERS, parts))
        obs_time = _parse_timestamp(record)
        observation = BuoyObservation(
            buoy_id=buoy_id,
            observation_time=obs_time,
            wind_speed_kts=_float_or_none(record.get("WSPD")),
            wind_gust_kts=_float_or_none(record.get("GST")),
            wind_direction_deg=_int_or_none(record.get("WDIR")),
            wave_height_m=_float_or_none(record.get("WVHT")),
            water_temp_c=_float_or_none(record.get("WTMP")),
            air_temp_c=_float_or_none(record.get("ATMP")),
            pressure_hpa=_float_or_none(record.get("PRES")),
            fetched_at=datetime.now(tz=UTC),
        )
        observations.append(observation)
        if limit and len(observations) >= limit:
            break

    return observations


def _parse_timestamp(record: dict[str, str]) -> datetime:
    year_val = int(record["YY"])
    # NOAA now provides 4-digit years in the YY field (e.g., 2025)
    # Handle both 2-digit and 4-digit years
    if year_val > 100:
        year = year_val  # Already a 4-digit year like 2025
    else:
        # For 2-digit years, use standard windowing: 00-79 -> 2000-2079, 80-99 -> 1980-1999
        year = 2000 + year_val if year_val <= 79 else 1900 + year_val

    timestamp = datetime(
        year,
        int(record["MM"]),
        int(record["DD"]),
        int(record["hh"]),
        int(record["mm"]),
        tzinfo=tz.UTC,
    )
    return timestamp.astimezone(UTC)


def _float_or_none(value: str | None) -> float | None:
    if value is None or value in {"MM", "999", "99"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int_or_none(value: str | None) -> int | None:
    if value is None or value in {"MM", "999", "99"}:
        return None
    try:
        return int(value)
    except ValueError:
        return None
