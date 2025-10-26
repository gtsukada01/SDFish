#!/usr/bin/env python3
"""
Collision Recovery Utility
--------------------------

Backs up trips for a set of dates, deletes them from production, triggers a re-scrape,
and stores JSON snapshots for audit purposes.

Usage:
    python scripts/data/recover_collisions.py --dates 2025-06-03,2025-06-04 --dry-run

Environment:
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (write access required)
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from supabase import create_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely re-scrape collision dates.")
    parser.add_argument(
        "--dates",
        required=True,
        help="Comma-separated list of YYYY-MM-DD dates to re-scrape.",
    )
    parser.add_argument(
        "--output-dir",
        default="backups/phase2",
        help="Directory to store JSON backups (default: backups/phase2).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print planned operations without mutating data.",
    )
    return parser.parse_args()


def ensure_env() -> None:
    if "SUPABASE_URL" not in os.environ or "SUPABASE_SERVICE_ROLE_KEY" not in os.environ:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")


def backup_date(supabase, trip_date: str, dest_dir: Path, dry_run: bool) -> Tuple[List[dict], List[int]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = dest_dir / f"trips_{trip_date}.json"
    quarantine_reason = f"phase2_rescrape_{trip_date}"

    if dry_run:
        print(f"[DRY RUN] Would backup trips for {trip_date} to {filename}")
        return [], []

    trips = supabase.table("trips").select("*").eq("trip_date", trip_date).execute().data
    if not trips:
        print(f"[WARN] No trips to backup for {trip_date}")
        return [], []

    # Persist JSON snapshot
    with filename.open("w", encoding="utf-8") as fh:
        json.dump(trips, fh, indent=2, sort_keys=True)

    # Copy into quarantine table
    supabase.table("trips_quarantine").insert(
        [
            {
                **trip,
                "quarantined_at": datetime.utcnow().isoformat(),
                "reason": quarantine_reason,
            }
            for trip in trips
        ]
    ).execute()

    print(f"[INFO] Backed up {len(trips)} trips for {trip_date}")
    trip_ids = [trip["id"] for trip in trips]
    return trips, trip_ids


def delete_date(supabase, trip_date: str, trip_ids: List[int], dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] Would delete {len(trip_ids)} trips for {trip_date}")
        return
    if trip_ids:
        supabase.table("catches").delete().in_("trip_id", trip_ids).execute()
    supabase.table("trips").delete().eq("trip_date", trip_date).execute()
    print(f"[INFO] Deleted trips + catches for {trip_date}")


def trigger_rescrape(trip_date: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] Would run socal_scraper.py --start-date {trip_date} --end-date {trip_date}")
        return
    exit_code = os.system(
        f"python3 scripts/python/socal_scraper.py --start-date {trip_date} --end-date {trip_date}"
    )
    if exit_code != 0:
        raise RuntimeError(f"socal_scraper.py failed for {trip_date} with exit code {exit_code}")


def main() -> None:
    args = parse_args()
    ensure_env()

    dates: List[str] = [d.strip() for d in args.dates.split(",") if d.strip()]
    if not dates:
        raise ValueError("No valid dates supplied.")

    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    output_dir = Path(args.output_dir)

    for date in dates:
        print(f"=== Processing {date} ===")
        _, trip_ids = backup_date(supabase, date, output_dir, args.dry_run)
        delete_date(supabase, date, trip_ids, args.dry_run)
        trigger_rescrape(date, args.dry_run)
        print()


if __name__ == "__main__":
    main()
