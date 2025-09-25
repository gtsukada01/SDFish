"""Supabase helper functions for marine conditions ingestion."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List

from dateutil import parser
from supabase import Client, create_client

from .models import BuoyObservation, DailyWindSummary
from ..config import UTC


RAW_TABLE = "marine_conditions"
DAILY_TABLE = "marine_conditions_daily"


class MarineSupabase:
    def __init__(self, url: str, key: str) -> None:
        self._client: Client = create_client(url, key)

    def insert_observations(self, observations: Iterable[BuoyObservation]) -> None:
        rows: List[dict] = []
        for obs in observations:
            rows.append(
                {
                    "buoy_id": obs.buoy_id,
                    "observation_time": obs.observation_time.isoformat(),
                    "wind_speed_kts": obs.wind_speed_kts,
                    "wind_gust_kts": obs.wind_gust_kts,
                    "wind_direction_deg": obs.wind_direction_deg,
                    "wave_height_m": obs.wave_height_m,
                    "water_temp_c": obs.water_temp_c,
                    "air_temp_c": obs.air_temp_c,
                    "pressure_hpa": obs.pressure_hpa,
                    "fetched_at": obs.fetched_at.isoformat(),
                }
            )
        if not rows:
            return
        self._client.table(RAW_TABLE).upsert(rows, on_conflict="buoy_id,observation_time").execute()

    def upsert_daily_summary(self, summary: DailyWindSummary) -> None:
        payload = {
            "buoy_id": summary.buoy_id,
            "observation_date": summary.observation_date.isoformat(),
            "wind_speed_min_kts": summary.wind_speed_min_kts,
            "wind_speed_min_time": summary.wind_speed_min_time.isoformat() if summary.wind_speed_min_time else None,
            "wind_speed_median_kts": summary.wind_speed_median_kts,
            "wind_speed_max_kts": summary.wind_speed_max_kts,
            "wind_speed_max_time": summary.wind_speed_max_time.isoformat() if summary.wind_speed_max_time else None,
            "sample_count": summary.sample_count,
            "valid_count": summary.valid_count,
            "quality_status": summary.quality_status,
            # Note: ingested_at removed as it's not in the fixed table schema
        }
        self._client.table(DAILY_TABLE).upsert(payload, on_conflict="buoy_id,observation_date").execute()

    def fetch_observations_for_date(self, buoy_id: str, observation_date: datetime.date) -> List[BuoyObservation]:
        start = datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC)
        end = start + timedelta(days=1)
        response = (
            self._client.table(RAW_TABLE)
            .select("*")
            .eq("buoy_id", buoy_id)
            .gte("observation_time", start.isoformat())
            .lt("observation_time", end.isoformat())
            .order("observation_time")
            .execute()
        )
        observations: List[BuoyObservation] = []
        for row in response.data or []:
            observations.append(
                BuoyObservation(
                    buoy_id=row["buoy_id"],
                    observation_time=parser.parse(row["observation_time"]).astimezone(UTC),
                    wind_speed_kts=row.get("wind_speed_kts"),
                    wind_gust_kts=row.get("wind_gust_kts"),
                    wind_direction_deg=row.get("wind_direction_deg"),
                    wave_height_m=row.get("wave_height_m"),
                    water_temp_c=row.get("water_temp_c"),
                    air_temp_c=row.get("air_temp_c"),
                    pressure_hpa=row.get("pressure_hpa"),
                    fetched_at=parser.parse(row.get("fetched_at")) if row.get("fetched_at") else start,
                )
            )
        return observations
