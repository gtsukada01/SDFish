"""Aggregation helpers for daily wind statistics."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Iterable, List

from .models import BuoyObservation, DailyWindSummary
from ..config import UTC


def summarize_daily_wind(observations: Iterable[BuoyObservation]) -> List[DailyWindSummary]:
    """Group observations by (buoy_id, observation_date) and compute wind stats."""
    buckets: dict[tuple[str, datetime.date], List[BuoyObservation]] = defaultdict(list)
    for obs in observations:
        observation_date = obs.observation_time.date()
        buckets[(obs.buoy_id, observation_date)].append(obs)

    summaries: List[DailyWindSummary] = []
    for (buoy_id, observation_date), bucket in buckets.items():
        wind_samples = [obs.wind_speed_kts for obs in bucket if obs.wind_speed_kts is not None]
        sample_count = len(bucket)
        valid_count = len(wind_samples)
        quality_status = "complete" if valid_count >= 32 else "partial"

        if wind_samples:
            min_value = min(wind_samples)
            max_value = max(wind_samples)
            med_value = median(wind_samples)

            min_time = _time_for_value(bucket, min_value)
            max_time = _time_for_value(bucket, max_value)
        else:
            min_value = max_value = med_value = None
            min_time = max_time = None

        summaries.append(
            DailyWindSummary(
                buoy_id=buoy_id,
                observation_date=observation_date,
                wind_speed_min_kts=min_value,
                wind_speed_min_time=min_time,
                wind_speed_median_kts=med_value,
                wind_speed_max_kts=max_value,
                wind_speed_max_time=max_time,
                sample_count=sample_count,
                valid_count=valid_count,
                quality_status=quality_status,
                ingested_at=datetime.now(tz=UTC),
            )
        )

    return summaries


def _time_for_value(observations: List[BuoyObservation], target: float | None) -> datetime | None:
    if target is None:
        return None
    for obs in observations:
        if obs.wind_speed_kts == target:
            return obs.observation_time
    return None
