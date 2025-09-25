"""Typed domain models for marine conditions ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class BuoyObservation:
    buoy_id: str
    observation_time: datetime
    wind_speed_kts: Optional[float]
    wind_gust_kts: Optional[float]
    wind_direction_deg: Optional[int]
    wave_height_m: Optional[float]
    water_temp_c: Optional[float]
    air_temp_c: Optional[float]
    pressure_hpa: Optional[float]
    fetched_at: datetime


@dataclass
class DailyWindSummary:
    buoy_id: str
    observation_date: date
    wind_speed_min_kts: Optional[float]
    wind_speed_min_time: Optional[datetime]
    wind_speed_median_kts: Optional[float]
    wind_speed_max_kts: Optional[float]
    wind_speed_max_time: Optional[datetime]
    sample_count: int
    valid_count: int
    quality_status: str
    ingested_at: datetime
