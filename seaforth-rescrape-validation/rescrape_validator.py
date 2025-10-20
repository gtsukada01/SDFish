#!/usr/bin/env python3
"""
Seaforth Boat Attribution Fix - Validation & Re-scraping Script
================================================================

Purpose: Correct 85 misattributed trips from boat ID 329 "Seaforth Sportfishing"
         to actual boat names (New Seaforth, San Diego, Pacific Voyager, etc.)

Constitution: v1.0.0 - Authentic Data Only, Validation-First, Safe Rollback
Specification: 003-seaforth-boat-fix

Author: Fishing Intelligence Platform
Date: October 15, 2025
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from colorama import Fore, Style, init

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from boats_scraper import (
    fetch_page,
    parse_boats_page,
    normalize_trip_type,
    get_or_create_boat,
    get_or_create_landing,
    check_trip_exists,
    init_supabase
)
import requests

init(autoreset=True)

# Constants
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

BOAT_ID_329 = 329
SEAFORTH_LANDING_ID = 14
START_DATE = "2025-09-24"
END_DATE = "2025-10-15"
BACKUP_DIR = Path(__file__).parent / "backups"
REPORTS_DIR = Path(__file__).parent / "reports"

# Valid boat name pattern (proper nouns, not landing names)
INVALID_BOAT_NAMES = ["Seaforth Sportfishing", "Seaforth Staff", "H&M Landing", "H & M Landing"]


class ValidationReport:
    """Track validation metrics throughout the process"""
    def __init__(self):
        self.start_time = datetime.now()
        self.backup_file: Optional[str] = None
        self.original_trip_count = 0
        self.trips_deleted = 0
        self.trips_inserted = 0
        self.trips_skipped = 0
        self.dates_processed = 0
        self.validation_errors: List[str] = []
        self.boat_names_found: List[str] = []
        self.species_comparison: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.start_time.isoformat(),
            "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "backup_file": self.backup_file,
            "original_trip_count": self.original_trip_count,
            "trips_deleted": self.trips_deleted,
            "trips_inserted": self.trips_inserted,
            "trips_skipped": self.trips_skipped,
            "dates_processed": self.dates_processed,
            "validation_errors": self.validation_errors,
            "boat_names_found": sorted(set(self.boat_names_found)),
            "species_comparison": self.species_comparison
        }


def print_header(text: str, color=Fore.CYAN):
    """Print formatted header"""
    print(f"\n{color}{'='*80}")
    print(f"{color}{text}")
    print(f"{color}{'='*80}{Style.RESET_ALL}\n")


def print_step(step: int, total: int, text: str):
    """Print formatted step"""
    print(f"{Fore.YELLOW}[{step}/{total}]{Style.RESET_ALL} {text}")


def backup_boat_329_trips(supabase) -> Dict[str, Any]:
    """
    FR-001: Backup all trips from boat ID 329 before deletion

    Returns: Dict with backup info and trip data
    """
    print_header("PHASE 1: BACKUP BOAT ID 329 DATA", Fore.MAGENTA)

    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)

    print_step(1, 3, "Fetching trips from boat ID 329...")

    # Get all trips
    trips_result = supabase.table('trips').select(
        'id, boat_id, trip_date, trip_duration, anglers'
    ).eq('boat_id', BOAT_ID_329).order('trip_date').execute()

    trips = trips_result.data
    print(f"{Fore.GREEN}✅ Found {len(trips)} trips{Style.RESET_ALL}")

    if len(trips) == 0:
        print(f"{Fore.YELLOW}⚠️  No trips found on boat ID 329{Style.RESET_ALL}")
        return {"trip_count": 0, "backup_file": None}

    print_step(2, 3, "Fetching associated catches...")

    # Get catches for each trip
    trip_ids = [t['id'] for t in trips]
    catches_result = supabase.table('catches').select('*').in_('trip_id', trip_ids).execute()
    catches = catches_result.data

    print(f"{Fore.GREEN}✅ Found {len(catches)} catches across {len(trips)} trips{Style.RESET_ALL}")

    # Organize catches by trip
    catches_by_trip = {}
    for catch in catches:
        trip_id = catch['trip_id']
        if trip_id not in catches_by_trip:
            catches_by_trip[trip_id] = []
        catches_by_trip[trip_id].append(catch)

    # Build backup data structure
    backup_data = {
        "backup_timestamp": datetime.now().isoformat(),
        "boat_id": BOAT_ID_329,
        "boat_name": "Seaforth Sportfishing",
        "trip_count": len(trips),
        "catch_count": len(catches),
        "date_range": {
            "start": trips[0]['trip_date'] if trips else None,
            "end": trips[-1]['trip_date'] if trips else None
        },
        "trips": []
    }

    for trip in trips:
        trip_data = {
            **trip,
            "catches": catches_by_trip.get(trip['id'], [])
        }
        backup_data["trips"].append(trip_data)

    print_step(3, 3, "Writing backup to file...")

    # Write backup file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"boat_329_backup_{timestamp}.json"

    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"{Fore.GREEN}✅ Backup saved: {backup_file}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Trips: {len(trips)} | Catches: {len(catches)}{Style.RESET_ALL}")

    return {
        "trip_count": len(trips),
        "catch_count": len(catches),
        "backup_file": str(backup_file),
        "date_range": backup_data["date_range"]
    }


def validate_backup(backup_info: Dict[str, Any]) -> bool:
    """
    Validate that backup was created successfully

    Returns: True if valid, False otherwise
    """
    if backup_info["trip_count"] == 0:
        print(f"{Fore.YELLOW}⚠️  No trips to backup{Style.RESET_ALL}")
        return True

    if not backup_info["backup_file"]:
        print(f"{Fore.RED}❌ Backup file not created{Style.RESET_ALL}")
        return False

    backup_path = Path(backup_info["backup_file"])
    if not backup_path.exists():
        print(f"{Fore.RED}❌ Backup file does not exist{Style.RESET_ALL}")
        return False

    # Verify backup can be loaded
    try:
        with open(backup_path, 'r') as f:
            data = json.load(f)

        if data["trip_count"] != backup_info["trip_count"]:
            print(f"{Fore.RED}❌ Backup trip count mismatch{Style.RESET_ALL}")
            return False

        print(f"{Fore.GREEN}✅ Backup validated successfully{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Backup validation failed: {e}{Style.RESET_ALL}")
        return False


def delete_boat_329_trips(supabase) -> int:
    """
    FR-007: Delete all trips from boat ID 329

    Returns: Number of trips deleted
    """
    print_header("PHASE 2: DELETE BOAT ID 329 TRIPS", Fore.MAGENTA)

    print_step(1, 2, "Counting trips to delete...")
    count_result = supabase.table('trips').select('id', count='exact').eq('boat_id', BOAT_ID_329).execute()
    trip_count = count_result.count

    print(f"{Fore.CYAN}Found {trip_count} trips to delete{Style.RESET_ALL}")

    if trip_count == 0:
        print(f"{Fore.YELLOW}⚠️  No trips to delete{Style.RESET_ALL}")
        return 0

    print_step(2, 2, f"Deleting {trip_count} trips (cascade deletes catches)...")

    # Delete trips (catches will cascade delete)
    delete_result = supabase.table('trips').delete().eq('boat_id', BOAT_ID_329).execute()

    print(f"{Fore.GREEN}✅ Deleted {trip_count} trips{Style.RESET_ALL}")

    return trip_count


def validate_boat_name(boat_name: str) -> bool:
    """
    FR-002: Validate boat name matches expected format

    Returns: True if valid, False if invalid
    """
    # Check against invalid names (landing names, author names)
    if boat_name in INVALID_BOAT_NAMES:
        return False

    # Check for proper noun format (at least one capital letter)
    if not any(c.isupper() for c in boat_name):
        return False

    # Check for minimum length
    if len(boat_name) < 3:
        return False

    return True


def test_single_date_dry_run(supabase, test_date: str = "2025-10-15") -> bool:
    """
    FR-013: Test on single date before batch processing

    Returns: True if test passes, False otherwise
    """
    print_header(f"PHASE 3: DRY-RUN TEST ({test_date})", Fore.MAGENTA)

    print_step(1, 3, f"Fetching boats.php page for {test_date}...")

    session = requests.Session()
    url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={test_date}"

    try:
        html = fetch_page(url, session)
        if not html:
            print(f"{Fore.RED}❌ Failed to fetch page{Style.RESET_ALL}")
            return False

        print(f"{Fore.GREEN}✅ Page fetched successfully{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Fetch error: {e}{Style.RESET_ALL}")
        return False

    print_step(2, 3, "Parsing Seaforth trips...")

    try:
        all_trips = parse_boats_page(html, test_date)
        print(f"{Fore.CYAN}Total trips parsed: {len(all_trips)}{Style.RESET_ALL}")

        # Debug: Show all landing names
        landing_names = set(t.get('landing_name', 'UNKNOWN') for t in all_trips)
        print(f"{Fore.CYAN}Landing names found: {landing_names}{Style.RESET_ALL}")

        # Filter for Seaforth Sportfishing only
        trips = [t for t in all_trips if t.get('landing_name') == 'Seaforth Sportfishing']
        print(f"{Fore.GREEN}✅ Parsed {len(trips)} Seaforth trips{Style.RESET_ALL}")

        if len(trips) == 0:
            print(f"{Fore.YELLOW}⚠️  No Seaforth trips found on {test_date}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Available landings: {landing_names}{Style.RESET_ALL}")
            # Show all trips for debugging
            for trip in all_trips:
                print(f"  - {trip['boat_name']:30s} @ {trip['landing_name']}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Parse error: {e}{Style.RESET_ALL}")
        return False

    print_step(3, 3, "Validating boat names...")

    validation_passed = True
    for trip in trips:
        boat_name = trip['boat_name']
        is_valid = validate_boat_name(boat_name)

        status = f"{Fore.GREEN}✅" if is_valid else f"{Fore.RED}❌"
        print(f"  {status} {boat_name:30s} | {trip['trip_duration']:20s} | {trip['anglers']} anglers{Style.RESET_ALL}")

        if not is_valid:
            validation_passed = False
            print(f"{Fore.RED}    ⚠️  INVALID: Boat name is a landing name or invalid format{Style.RESET_ALL}")

    if validation_passed:
        print(f"\n{Fore.GREEN}✅ DRY-RUN PASSED: All boat names valid{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ DRY-RUN FAILED: Some boat names invalid{Style.RESET_ALL}")

    return validation_passed


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """Generate list of dates between start and end (inclusive)"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def rescrape_date_range(supabase, start_date: str, end_date: str, report: ValidationReport) -> bool:
    """
    FR-005: Re-scrape date range with validation

    Returns: True if successful, False otherwise
    """
    print_header(f"PHASE 4: RE-SCRAPE {start_date} TO {end_date}", Fore.MAGENTA)

    dates = generate_date_range(start_date, end_date)
    print(f"{Fore.CYAN}Processing {len(dates)} dates...{Style.RESET_ALL}\n")

    session = requests.Session()

    for i, date in enumerate(dates, 1):
        print(f"{Fore.YELLOW}[{i}/{len(dates)}] {date}{Style.RESET_ALL}")

        try:
            # Fetch and parse
            url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={date}"
            html = fetch_page(url, session)
            if not html:
                print(f"  {Fore.YELLOW}⚠️  Failed to fetch{Style.RESET_ALL}")
                report.validation_errors.append(f"{date}: Failed to fetch page")
                continue

            all_trips = parse_boats_page(html, date)
            # Filter for Seaforth Sportfishing only
            trips = [t for t in all_trips if t.get('landing_name') == 'Seaforth Sportfishing']
            print(f"  {Fore.CYAN}Found {len(trips)} Seaforth trips{Style.RESET_ALL}")

            if len(trips) == 0:
                print(f"  {Fore.YELLOW}⚠️  No Seaforth trips found{Style.RESET_ALL}")
                continue

            # Validate and insert each trip
            for trip in trips:
                boat_name = trip['boat_name']

                # FR-002: Validate boat name
                if not validate_boat_name(boat_name):
                    print(f"  {Fore.RED}❌ Invalid boat name: {boat_name}{Style.RESET_ALL}")
                    report.validation_errors.append(f"{date}: Invalid boat name '{boat_name}'")
                    report.trips_skipped += 1
                    continue

                # Track boat names found
                report.boat_names_found.append(boat_name)

                # Get or create landing
                landing_id = get_or_create_landing(supabase, 'Seaforth Sportfishing')

                # Get or create boat
                boat_id = get_or_create_boat(supabase, boat_name, landing_id)

                # Check if trip already exists
                if check_trip_exists(supabase, boat_id, date, trip['trip_duration']):
                    print(f"  {Fore.YELLOW}⚠️  Duplicate: {boat_name}{Style.RESET_ALL}")
                    report.trips_skipped += 1
                    continue

                # Insert trip
                try:
                    trip_data = {
                        'boat_id': boat_id,
                        'trip_date': date,
                        'trip_duration': trip['trip_duration'],
                        'anglers': trip.get('anglers')
                    }

                    trip_result = supabase.table('trips').insert(trip_data).execute()
                    trip_id = trip_result.data[0]['id']

                    # Insert catches
                    if trip.get('catches'):
                        catch_data = [
                            {
                                'trip_id': trip_id,
                                'species': c['species'],
                                'count': c['count']
                            }
                            for c in trip['catches']
                        ]
                        supabase.table('catches').insert(catch_data).execute()

                    print(f"  {Fore.GREEN}✅ {boat_name}{Style.RESET_ALL}")
                    report.trips_inserted += 1

                except Exception as e:
                    print(f"  {Fore.RED}❌ Insert failed: {e}{Style.RESET_ALL}")
                    report.validation_errors.append(f"{date} - {boat_name}: {str(e)}")
                    report.trips_skipped += 1

            report.dates_processed += 1

            # Smart delay between dates (2-5 seconds)
            if i < len(dates):
                import time, random
                delay = random.randint(2, 5)
                print(f"  {Fore.YELLOW}⏳ Delay: {delay}s{Style.RESET_ALL}")
                time.sleep(delay)

        except Exception as e:
            print(f"  {Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
            report.validation_errors.append(f"{date}: {str(e)}")

    print(f"\n{Fore.GREEN}✅ Re-scraping complete{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  Dates processed: {report.dates_processed}/{len(dates)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  Trips inserted: {report.trips_inserted}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  Trips skipped: {report.trips_skipped}{Style.RESET_ALL}")

    return True


def verify_boat_329_empty(supabase) -> bool:
    """
    Verify boat ID 329 has zero trips

    Returns: True if empty, False otherwise
    """
    result = supabase.table('trips').select('id', count='exact').eq('boat_id', BOAT_ID_329).execute()
    count = result.count

    if count == 0:
        print(f"{Fore.GREEN}✅ Boat ID 329 has zero trips{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.YELLOW}⚠️  Boat ID 329 still has {count} trips{Style.RESET_ALL}")
        return False


def delete_boat_329(supabase) -> bool:
    """
    FR-008: Delete boat ID 329 after all trips reassigned

    Returns: True if deleted, False otherwise
    """
    print_header("PHASE 5: DELETE BOAT ID 329", Fore.MAGENTA)

    if not verify_boat_329_empty(supabase):
        print(f"{Fore.RED}❌ Cannot delete boat 329: Still has trips{Style.RESET_ALL}")
        return False

    try:
        supabase.table('boats').delete().eq('id', BOAT_ID_329).execute()
        print(f"{Fore.GREEN}✅ Deleted boat ID 329 'Seaforth Sportfishing'{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to delete boat: {e}{Style.RESET_ALL}")
        return False


def generate_validation_report(report: ValidationReport, backup_info: Dict[str, Any]):
    """
    FR-010: Generate comprehensive validation report
    """
    print_header("PHASE 6: VALIDATION REPORT", Fore.MAGENTA)

    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"validation_report_{timestamp}.json"

    # Build comprehensive report
    full_report = {
        **report.to_dict(),
        "backup_info": backup_info,
        "constitution_version": "1.0.0",
        "specification": "003-seaforth-boat-fix"
    }

    # Write report
    with open(report_file, 'w') as f:
        json.dump(full_report, f, indent=2, default=str)

    print(f"{Fore.GREEN}✅ Report saved: {report_file}{Style.RESET_ALL}\n")

    # Print summary
    print(f"{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  Original trips (boat 329): {backup_info['trip_count']}")
    print(f"  Trips deleted: {report.trips_deleted}")
    print(f"  Trips inserted: {report.trips_inserted}")
    print(f"  Trips skipped: {report.trips_skipped}")
    print(f"  Dates processed: {report.dates_processed}")
    print(f"  Unique boats found: {len(set(report.boat_names_found))}")

    if report.validation_errors:
        print(f"\n{Fore.YELLOW}Validation Errors: {len(report.validation_errors)}{Style.RESET_ALL}")
        for error in report.validation_errors[:10]:
            print(f"  - {error}")
        if len(report.validation_errors) > 10:
            print(f"  ... and {len(report.validation_errors) - 10} more")

    print(f"\n{Fore.CYAN}Boat Names Found:{Style.RESET_ALL}")
    for boat_name in sorted(set(report.boat_names_found)):
        count = report.boat_names_found.count(boat_name)
        print(f"  - {boat_name}: {count} trips")


def main():
    """Main execution flow"""
    print_header("SEAFORTH BOAT ATTRIBUTION FIX", Fore.MAGENTA)
    print(f"{Fore.CYAN}Constitution: v1.0.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Specification: 003-seaforth-boat-fix{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Date Range: {START_DATE} to {END_DATE} (22 dates){Style.RESET_ALL}\n")

    # Initialize
    supabase = init_supabase()
    report = ValidationReport()

    # Phase 1: Backup
    backup_info = backup_boat_329_trips(supabase)
    report.original_trip_count = backup_info["trip_count"]
    report.backup_file = backup_info.get("backup_file")

    if not validate_backup(backup_info):
        print(f"{Fore.RED}❌ ABORT: Backup validation failed{Style.RESET_ALL}")
        return 1

    # Phase 2: Delete existing trips
    report.trips_deleted = delete_boat_329_trips(supabase)

    # Phase 3: Test single date
    if not test_single_date_dry_run(supabase):
        print(f"{Fore.RED}❌ ABORT: Dry-run test failed{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Manual review required before proceeding{Style.RESET_ALL}")
        return 1

    # Confirmation before full re-scrape
    print(f"\n{Fore.YELLOW}{'='*80}")
    print(f"{Fore.YELLOW}Ready to re-scrape 22 dates with validated parser")
    print(f"{Fore.YELLOW}Continue? (y/n): {Style.RESET_ALL}", end='')

    response = input().strip().lower()
    if response != 'y':
        print(f"{Fore.YELLOW}Aborted by user{Style.RESET_ALL}")
        return 1

    # Phase 4: Full re-scrape
    rescrape_date_range(supabase, START_DATE, END_DATE, report)

    # Phase 5: Delete boat 329
    delete_boat_329(supabase)

    # Phase 6: Generate report
    generate_validation_report(report, backup_info)

    print(f"\n{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}✅ VALIDATION COMPLETE")
    print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
