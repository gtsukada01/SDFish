import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts" / "python"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from socal_scraper import (
    check_trip_exists,
    compute_trip_hash_v1,
    compute_trip_hash_v2,
    derive_landing_slug,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTripsTable:
    def __init__(self, client: "FakeSupabase"):
        self.client = client
        self.filters: Dict[str, Any] = {}

    def select(self, _columns: str) -> "FakeTripsTable":
        return self

    def eq(self, field: str, value: Any) -> "FakeTripsTable":
        self.filters[field] = value
        return self

    def is_(self, field: str, value: Any) -> "FakeTripsTable":
        sentinel = "__IS_NULL__" if value is None else value
        self.filters[field] = sentinel
        return self

    def execute(self) -> FakeResponse:
        def matches(trip: Dict[str, Any]) -> bool:
            for field, expected in self.filters.items():
                if expected == "__IS_NULL__":
                    if trip.get(field) is not None:
                        return False
                    continue
                if trip.get(field) != expected:
                    return False
            return True

        data = [
            {"id": trip["id"]}
            for trip in self.client.trips
            if matches(trip)
        ]
        return FakeResponse(data)


class FakeCatchesTable:
    def __init__(self, client: "FakeSupabase"):
        self.client = client
        self.filters: Dict[str, Any] = {}

    def select(self, _columns: str) -> "FakeCatchesTable":
        return self

    def eq(self, field: str, value: Any) -> "FakeCatchesTable":
        self.filters[field] = value
        return self

    def execute(self) -> FakeResponse:
        trip_id = self.filters.get("trip_id")
        catches = self.client.catches_by_trip.get(trip_id, [])
        return FakeResponse(catches)


class FakeCollisionTable:
    def __init__(self, client: "FakeSupabase"):
        self.client = client
        self._pending: Optional[Dict[str, Any]] = None

    def insert(self, data: Dict[str, Any]) -> "FakeCollisionTable":
        # Clone to avoid downstream mutation
        self._pending = dict(data)
        return self

    def execute(self) -> FakeResponse:
        assert self._pending is not None, "insert must be called before execute"
        self.client.trip_collisions.append(self._pending)
        return FakeResponse([{"id": len(self.client.trip_collisions)}])


class FakeSupabase:
    def __init__(self):
        # Preload single trip identical to Thunderbird example
        self.trips: List[Dict[str, Any]] = [
            {
                "id": 101,
                "boat_id": 501,
                "trip_date": "2025-06-03",
                "trip_duration": "Overnight",
                "anglers": 25,
                "raw_landing_slug": "newport-landing",
            }
        ]
        self.catches_by_trip: Dict[int, List[Dict[str, Any]]] = {
            101: [
                {"species": "Halibut", "count": 29},
                {"species": "Sheephead", "count": 1},
            ]
        }
        self.trip_collisions: List[Dict[str, Any]] = []

    def table(self, name: str):
        if name == "trips":
            return FakeTripsTable(self)
        if name == "catches":
            return FakeCatchesTable(self)
        if name == "trip_collisions":
            return FakeCollisionTable(self)
        raise ValueError(f"Unsupported table requested: {name}")


class CollisionDetectionTests(unittest.TestCase):
    def test_collision_logged_when_catches_differ(self):
        supabase = FakeSupabase()

        # Incoming trip with same composite key but missing Sheephead
        incoming_catches = [
            {"species": "Halibut", "count": 29},
            {"species": "Red Snapper", "count": 50},
        ]

        landing_slug = derive_landing_slug("newport_landing", "Newport Landing")
        trip_hash_v2 = compute_trip_hash_v2(
            boat_name="Thunderbird",
            raw_landing_slug=landing_slug,
            trip_duration="Overnight",
            anglers=25,
            catches=incoming_catches,
        )
        trip_hash_v1 = compute_trip_hash_v1(
            boat_id=501,
            trip_duration="Overnight",
            anglers=25,
            catches=incoming_catches,
        )

        collision_context = {
            "boat_name": "Thunderbird",
            "raw_landing_slug": landing_slug,
            "normalized_landing": "Newport Landing",
            "trip_hash": trip_hash_v2,
            "scrape_job_id": 777,
        }

        exists = check_trip_exists(
            supabase=supabase,
            boat_id=501,
            trip_date="2025-06-03",
            trip_duration="Overnight",
            anglers=25,
            catches=incoming_catches,
            collision_context=collision_context,
            trip_hash_v2=trip_hash_v2,
            trip_hash_v1=trip_hash_v1,
        )

        self.assertFalse(exists, "Trips with different catches must be treated as distinct")
        self.assertEqual(len(supabase.trip_collisions), 1, "Collision should be logged exactly once")

        record = supabase.trip_collisions[0]
        self.assertEqual(record["boat_name"], "Thunderbird")
        self.assertEqual(record["scrape_job_id"], 777)
        self.assertEqual(record["normalized_landing"], "Newport Landing")
        self.assertIsInstance(record["existing_catches"], list)
        self.assertIsInstance(record["new_catches"], list)
        self.assertEqual(record["resolution"], "skipped")


if __name__ == "__main__":
    unittest.main()
