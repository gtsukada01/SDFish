"""Configuration helpers for the marine conditions ingestion MVP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import tzinfo, timezone
from typing import Dict, List

DEFAULT_PRIORITY_BUOYS = ["46047", "46086"]
DEFAULT_FALLBACKS = {
    "46047": "46086",
    "46086": "46047",
}


@dataclass(frozen=True)
class MarineConfig:
    """Runtime configuration derived from environment variables."""

    supabase_url: str
    supabase_key: str
    priority_buoys: List[str]
    polling_interval_minutes: int
    off_season_interval_minutes: int
    fallback_buoys: Dict[str, str]

    @staticmethod
    def from_env() -> "MarineConfig":
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("Supabase credentials missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

        buoys_raw = os.environ.get("MARINE_PRIORITY_BUOYS")
        if buoys_raw:
            priority_buoys = [b.strip() for b in buoys_raw.split(",") if b.strip()]
        else:
            priority_buoys = DEFAULT_PRIORITY_BUOYS

        polling_interval = int(os.environ.get("MARINE_IN_SEASON_INTERVAL_MIN", "30"))
        off_season_interval = int(os.environ.get("MARINE_OFF_SEASON_INTERVAL_MIN", "60"))

        fallback_map = _parse_fallback_map(os.environ.get("MARINE_FALLBACK_BUOYS"))

        return MarineConfig(
            supabase_url=url,
            supabase_key=key,
            priority_buoys=priority_buoys,
            polling_interval_minutes=polling_interval,
            off_season_interval_minutes=off_season_interval,
            fallback_buoys=fallback_map,
        )


def current_season_interval(config: MarineConfig, month: int) -> int:
    """Return the polling interval appropriate for the given month (1-12)."""
    # Tuna season June-November inclusive uses in-season interval
    if 6 <= month <= 11:
        return config.polling_interval_minutes
    return config.off_season_interval_minutes


UTC: tzinfo = timezone.utc


def _parse_fallback_map(raw: str | None) -> Dict[str, str]:
    """Parse fallback buoy mapping from env (e.g., "46047:46086;46086:46047")."""
    if not raw:
        return DEFAULT_FALLBACKS.copy()

    mapping: Dict[str, str] = {}
    pairs = [p.strip() for p in raw.split(";") if p.strip()]
    for pair in pairs:
        if ":" not in pair:
            continue
        primary, fallback = [x.strip() for x in pair.split(":", 1)]
        if primary and fallback:
            mapping[primary] = fallback
    if not mapping:
        return DEFAULT_FALLBACKS.copy()
    return mapping
