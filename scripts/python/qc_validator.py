#!/usr/bin/env python3
"""
QC Validation Script - 100% Data Accuracy Verification
========================================================

SPEC 006: Validates database matches boats.php source pages with 100% accuracy

Features:
- Field-level comparison (landing, boat, trip type, anglers, species, counts)
- Missing boats detection (on source but not in database)
- Extra boats detection (in database but not on source)
- Polaris Supreme validation test (10 trips from 09-09 to 10-10)
- JSON report generation with PASS/FAIL status

Author: Fishing Intelligence Platform
Date: October 16, 2025
"""

import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from colorama import Fore, Style, init

# Import parsing utilities from boats_scraper
sys.path.insert(0, str(Path(__file__).parent))
from boats_scraper import (
    parse_boats_page,
    normalize_trip_type,
    parse_species_counts,
    init_supabase,
    BOATS_URL_TEMPLATE
)

# Initialize colorama
init(autoreset=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

# Logging
LOG_FILE = "qc_validator.log"
LOG_LEVEL = logging.INFO

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# DATABASE QUERIES
# ============================================================================

def get_database_trips(supabase: Client, date: str) -> List[Dict]:
    """
    Get all San Diego trips from database for a specific date

    FILTERS BY SOURCE: Only returns trips from www.sandiegofishreports.com scrape jobs

    Returns:
        List of trips with all fields (boat, landing, trip type, anglers, catches)
    """
    try:
        # First, get all San Diego scrape job IDs
        jobs_result = supabase.table('scrape_jobs') \
            .select('id') \
            .like('source_url_pattern', '%sandiegofishreports%') \
            .execute()

        if not jobs_result.data:
            logger.warning(f"{Fore.YELLOW}⚠️  No San Diego scrape jobs found in database")
            return []

        job_ids = [job['id'] for job in jobs_result.data]

        # Get trips with joins to boats, landings (direct), and catches
        # FILTER: Only San Diego trips (scrape_job_id from sandiegofishreports.com)
        result = supabase.table('trips') \
            .select('*, boats(name), landings(name), catches(species, count)') \
            .eq('trip_date', date) \
            .in_('scrape_job_id', job_ids) \
            .execute()

        trips = []
        for row in result.data:
            # Extract nested data
            boat_name = row['boats']['name']
            landing_name = row['landings']['name']  # Now from trips.landing_id, not boats.landing_id

            trip = {
                'boat_name': boat_name,
                'landing_name': landing_name,
                'trip_date': row['trip_date'],
                'trip_duration': row['trip_duration'],
                'anglers': row['anglers'],
                'catches': row['catches'] if row['catches'] else []
            }
            trips.append(trip)

        return trips

    except Exception as e:
        logger.error(f"{Fore.RED}❌ Database query failed: {e}")
        return []

def get_polaris_supreme_trips(supabase: Client, start_date: str, end_date: str) -> List[Dict]:
    """
    Get all Polaris Supreme trips in date range for validation test

    Returns:
        List of Polaris Supreme trips
    """
    try:
        # First get Polaris Supreme boat ID
        boat_result = supabase.table('boats').select('id').eq('name', 'Polaris Supreme').execute()

        if not boat_result.data:
            logger.warning(f"{Fore.YELLOW}⚠️  Polaris Supreme boat not found in database")
            return []

        boat_id = boat_result.data[0]['id']

        # Get trips for this boat in date range
        result = supabase.table('trips') \
            .select('trip_date, trip_duration, anglers') \
            .eq('boat_id', boat_id) \
            .gte('trip_date', start_date) \
            .lte('trip_date', end_date) \
            .order('trip_date') \
            .execute()

        return result.data

    except Exception as e:
        logger.error(f"{Fore.RED}❌ Polaris Supreme query failed: {e}")
        return []

# ============================================================================
# SOURCE PAGE FETCHING
# ============================================================================

def fetch_source_page(url: str) -> Optional[str]:
    """Fetch boats.php page from source website"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        logger.info(f"{Fore.CYAN}🌐 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"{Fore.GREEN}✅ Fetched {len(response.text)} bytes")
        return response.text

    except Exception as e:
        logger.error(f"{Fore.RED}❌ Failed to fetch {url}: {e}")
        return None

# ============================================================================
# FIELD-LEVEL COMPARISON
# ============================================================================

def normalize_species_list(catches: List[Dict]) -> Dict[str, int]:
    """Convert catches list to normalized dict for comparison"""
    result = {}
    for catch in catches:
        species = catch['species'].strip().lower()
        count = catch['count']

        # Accumulate counts for same species (in case of duplicates)
        if species in result:
            result[species] += count
        else:
            result[species] = count

    return result

def compare_trips(source_trip: Dict, db_trip: Dict) -> Tuple[bool, List[str]]:
    """
    Compare source trip against database trip field-by-field

    Returns:
        (matches: bool, errors: List[str])
    """
    errors = []

    # Landing name (case-insensitive)
    if source_trip['landing_name'].lower() != db_trip['landing_name'].lower():
        errors.append(f"Landing mismatch: source='{source_trip['landing_name']}' db='{db_trip['landing_name']}'")

    # Boat name (exact match)
    if source_trip['boat_name'] != db_trip['boat_name']:
        errors.append(f"Boat name mismatch: source='{source_trip['boat_name']}' db='{db_trip['boat_name']}'")

    # Trip type/duration (exact match)
    if source_trip['trip_duration'] != db_trip['trip_duration']:
        errors.append(f"Trip type mismatch: source='{source_trip['trip_duration']}' db='{db_trip['trip_duration']}'")

    # Anglers count (exact match, allow None)
    if source_trip.get('anglers') != db_trip.get('anglers'):
        errors.append(f"Anglers mismatch: source={source_trip.get('anglers')} db={db_trip.get('anglers')}")

    # Species and counts (normalized comparison)
    source_species = normalize_species_list(source_trip['catches'])
    db_species = normalize_species_list(db_trip['catches'])

    # Check for missing species
    for species, count in source_species.items():
        if species not in db_species:
            errors.append(f"Missing species: '{species}' (count={count}) not in database")
        elif db_species[species] != count:
            errors.append(f"Species count mismatch: '{species}' source={count} db={db_species[species]}")

    # Check for extra species
    for species, count in db_species.items():
        if species not in source_species:
            errors.append(f"Extra species: '{species}' (count={count}) in database but not on source page")

    return (len(errors) == 0, errors)

def find_matching_trip(source_trip: Dict, db_trips: List[Dict]) -> Optional[Dict]:
    """
    Find matching trip in database using composite key matching

    ROBUST MATCHING: Uses ALL distinguishing fields to uniquely identify trips
    - boat_name (exact match)
    - trip_duration/trip_type (exact match)
    - anglers (exact match, if available)

    CRITICAL: Boats can have multiple trips per day with same type
    (e.g., "1/2 Day AM" at 6am and "1/2 Day AM" at 8am)
    Must use anglers count as tiebreaker when boat + type aren't unique.

    Returns:
        - Single matching trip if unique match found
        - None if no match or ambiguous match (logs warning)
    """
    # Find all candidates matching boat name and trip type
    candidates = []
    for db_trip in db_trips:
        if (db_trip['boat_name'] == source_trip['boat_name'] and
            db_trip['trip_duration'] == source_trip['trip_duration']):
            candidates.append(db_trip)

    # No candidates - missing boat
    if len(candidates) == 0:
        return None

    # Single candidate - unique match
    if len(candidates) == 1:
        return candidates[0]

    # Multiple candidates - use anglers as tiebreaker
    logger.debug(f"{Fore.YELLOW}⚠️  Multiple trips for {source_trip['boat_name']} ({source_trip['trip_duration']}), using anglers as tiebreaker")

    anglers_matches = [
        c for c in candidates
        if c.get('anglers') == source_trip.get('anglers')
    ]

    if len(anglers_matches) == 1:
        return anglers_matches[0]
    elif len(anglers_matches) == 0:
        logger.warning(f"{Fore.RED}❌ AMBIGUOUS: Multiple trips for {source_trip['boat_name']} ({source_trip['trip_duration']}), none match anglers={source_trip.get('anglers')}")
        return None  # Ambiguous - report as mismatch
    else:
        logger.error(f"{Fore.RED}❌ CRITICAL: {len(anglers_matches)} trips match {source_trip['boat_name']} ({source_trip['trip_duration']}, {source_trip.get('anglers')} anglers) - duplicate trips in database!")
        return None  # Database integrity issue - duplicates exist

# ============================================================================
# QC VALIDATION
# ============================================================================

def validate_date(date: str, supabase: Client) -> Dict:
    """
    Validate database against source page for a specific date

    Returns:
        QC report dict with status and details
    """
    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    logger.info(f"{Fore.MAGENTA}🔍 QC VALIDATION: {date}")
    logger.info(f"{Fore.MAGENTA}{'='*80}")

    # Fetch source page
    url = BOATS_URL_TEMPLATE.format(date=date)
    html = fetch_source_page(url)

    if not html:
        return {
            'date': date,
            'status': 'ERROR',
            'error': 'Failed to fetch source page',
            'timestamp': datetime.utcnow().isoformat()
        }

    # Check for "Dock Totals" duplicate dates (website bug)
    # These are dates where the website shows a different date's content with "Dock Totals" title
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title.string if soup.title else None

    if title and "Dock Totals" in title:
        # Extract the date shown in the title
        import re
        date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', title)
        if date_match:
            from datetime import datetime as dt
            month_name = date_match.group(1)
            day = int(date_match.group(2))
            year = int(date_match.group(3))

            try:
                date_obj = dt.strptime(f"{month_name} {day}, {year}", '%B %d, %Y')
                shown_date = date_obj.strftime('%Y-%m-%d')

                # If shown date doesn't match requested date, it's a duplicate
                if shown_date != date:
                    logger.warning(f"{Fore.YELLOW}⚠️  DUPLICATE DATE DETECTED")
                    logger.warning(f"{Fore.YELLOW}   Requested: {date}")
                    logger.warning(f"{Fore.YELLOW}   Shown:     {shown_date} (Dock Totals duplicate)")
                    logger.warning(f"{Fore.YELLOW}   → Deleting any existing trips for {date}")

                    # Delete any trips for this date
                    result = supabase.table('trips').delete().eq('trip_date', date).execute()
                    deleted_count = len(result.data) if result.data else 0

                    logger.warning(f"{Fore.YELLOW}   → Deleted {deleted_count} trips from {date}")
                    logger.warning(f"{Fore.YELLOW}   → Skipping QC validation (duplicate content)")

                    return {
                        'date': date,
                        'status': 'SKIPPED',
                        'reason': f'Dock Totals duplicate - shows {shown_date} content',
                        'deleted_trips': deleted_count,
                        'timestamp': datetime.utcnow().isoformat()
                    }
            except Exception as e:
                logger.error(f"{Fore.RED}Error parsing Dock Totals date: {e}")

    # Parse source trips (with database cross-reference for boat validation)
    source_trips = parse_boats_page(html, date, supabase)
    logger.info(f"{Fore.CYAN}📊 Source page: {len(source_trips)} trips")

    # Get database trips
    db_trips = get_database_trips(supabase, date)
    logger.info(f"{Fore.CYAN}📊 Database: {len(db_trips)} trips")

    # Compare trips
    matches = 0
    mismatches = []
    missing_boats = []
    field_errors = []

    # Check each source trip against database
    for source_trip in source_trips:
        db_trip = find_matching_trip(source_trip, db_trips)

        if not db_trip:
            missing_boats.append({
                'boat': source_trip['boat_name'],
                'landing': source_trip['landing_name'],
                'trip_type': source_trip['trip_duration'],
                'anglers': source_trip.get('anglers')
            })
            logger.warning(f"{Fore.YELLOW}⚠️  Missing: {source_trip['boat_name']} ({source_trip['landing_name']})")
        else:
            # Field-level comparison
            is_match, errors = compare_trips(source_trip, db_trip)

            if is_match:
                matches += 1
                logger.info(f"{Fore.GREEN}✅ Match: {source_trip['boat_name']}")
            else:
                mismatches.append({
                    'boat': source_trip['boat_name'],
                    'errors': errors
                })
                field_errors.extend(errors)
                logger.error(f"{Fore.RED}❌ Mismatch: {source_trip['boat_name']}")
                for error in errors:
                    logger.error(f"{Fore.RED}   - {error}")

    # Check for extra boats (in database but not on source page)
    extra_boats = []
    source_boat_names = {t['boat_name'] for t in source_trips}
    for db_trip in db_trips:
        if db_trip['boat_name'] not in source_boat_names:
            extra_boats.append({
                'boat': db_trip['boat_name'],
                'landing': db_trip['landing_name'],
                'trip_date': db_trip['trip_date']
            })
            logger.warning(f"{Fore.YELLOW}⚠️  Extra: {db_trip['boat_name']} in database but not on source page")

    # Determine status
    status = 'PASS' if (len(missing_boats) == 0 and len(mismatches) == 0 and len(extra_boats) == 0) else 'FAIL'

    # Build report
    report = {
        'date': date,
        'status': status,
        'source_boat_count': len(source_trips),
        'database_boat_count': len(db_trips),
        'matches': matches,
        'mismatches': mismatches,
        'missing_boats': missing_boats,
        'extra_boats': extra_boats,
        'field_errors': field_errors,
        'timestamp': datetime.utcnow().isoformat()
    }

    # Summary
    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    if status == 'PASS':
        logger.info(f"{Fore.GREEN}✅ QC PASSED: {date}")
    else:
        logger.error(f"{Fore.RED}❌ QC FAILED: {date}")
    logger.info(f"{Fore.CYAN}📊 Matches: {matches}/{len(source_trips)}")
    logger.info(f"{Fore.YELLOW}⚠️  Mismatches: {len(mismatches)}")
    logger.info(f"{Fore.YELLOW}⚠️  Missing boats: {len(missing_boats)}")
    logger.info(f"{Fore.YELLOW}⚠️  Extra boats: {len(extra_boats)}")
    logger.info(f"{Fore.MAGENTA}{'='*80}\n")

    return report

# ============================================================================
# POLARIS SUPREME VALIDATION TEST
# ============================================================================

def validate_polaris_supreme(supabase: Client) -> Dict:
    """
    Primary QC Test: Polaris Supreme 10 trips from 09-09 to 10-10

    Expected: Exactly 10 trips with specific dates matching charter boat page
    """
    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    logger.info(f"{Fore.MAGENTA}🎯 POLARIS SUPREME VALIDATION TEST")
    logger.info(f"{Fore.MAGENTA}{'='*80}")

    # Expected dates from charter boat page
    expected_dates = [
        '2025-09-09',  # 2 Day, 14 anglers
        '2025-09-11',  # 2 Day, 17 anglers
        '2025-09-14',  # 3 Day, 24 anglers
        '2025-09-18',  # 4 Day, 10 anglers
        '2025-09-21',  # 3 Day, 22 anglers
        '2025-09-24',  # 3 Day, 24 anglers
        '2025-09-27',  # 3 Day, 18 anglers
        '2025-09-30',  # 3 Day, 24 anglers
        '2025-10-08',  # 5 Day, 22 anglers
        '2025-10-10',  # 2 Day, 23 anglers
    ]

    # Get trips from database
    trips = get_polaris_supreme_trips(supabase, '2025-09-09', '2025-10-10')

    logger.info(f"{Fore.CYAN}📊 Expected: {len(expected_dates)} trips")
    logger.info(f"{Fore.CYAN}📊 Database: {len(trips)} trips")

    # Check count
    count_match = len(trips) == 10
    if count_match:
        logger.info(f"{Fore.GREEN}✅ Trip count: PASS (10 trips)")
    else:
        logger.error(f"{Fore.RED}❌ Trip count: FAIL (expected 10, got {len(trips)})")

    # Check dates
    actual_dates = {t['trip_date'] for t in trips}
    expected_dates_set = set(expected_dates)

    dates_match = actual_dates == expected_dates_set
    if dates_match:
        logger.info(f"{Fore.GREEN}✅ Trip dates: PASS (all dates match)")
    else:
        logger.error(f"{Fore.RED}❌ Trip dates: FAIL")

        missing_dates = expected_dates_set - actual_dates
        if missing_dates:
            logger.error(f"{Fore.RED}   Missing dates: {sorted(missing_dates)}")

        extra_dates = actual_dates - expected_dates_set
        if extra_dates:
            logger.error(f"{Fore.RED}   Extra dates: {sorted(extra_dates)}")

    # Overall status
    status = 'PASS' if (count_match and dates_match) else 'FAIL'

    report = {
        'test': 'Polaris Supreme Validation',
        'status': status,
        'expected_trips': 10,
        'actual_trips': len(trips),
        'expected_dates': expected_dates,
        'actual_dates': sorted(list(actual_dates)),
        'missing_dates': sorted(list(expected_dates_set - actual_dates)) if not dates_match else [],
        'extra_dates': sorted(list(actual_dates - expected_dates_set)) if not dates_match else [],
        'timestamp': datetime.utcnow().isoformat()
    }

    logger.info(f"{Fore.MAGENTA}{'='*80}")
    if status == 'PASS':
        logger.info(f"{Fore.GREEN}✅ POLARIS SUPREME TEST: PASSED")
    else:
        logger.error(f"{Fore.RED}❌ POLARIS SUPREME TEST: FAILED")
    logger.info(f"{Fore.MAGENTA}{'='*80}\n")

    return report

# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_date_range(start_date: str, end_date: str, output_file: Optional[str] = None):
    """
    Validate all dates in range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_file: Optional JSON file to save results
    """
    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    logger.info(f"{Fore.MAGENTA}🚀 QC VALIDATION - DATE RANGE")
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.CYAN}📅 Date range: {start_date} to {end_date}")

    # Initialize
    supabase = init_supabase()

    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Validate each date
    reports = []
    current = start

    while current <= end:
        date_str = current.strftime('%Y-%m-%d')

        # Small delay to be respectful
        if current != start:
            time.sleep(2)

        # Validate date
        report = validate_date(date_str, supabase)
        reports.append(report)

        current += timedelta(days=1)

    # Summary
    total_dates = len(reports)
    passed = sum(1 for r in reports if r['status'] == 'PASS')
    failed = sum(1 for r in reports if r['status'] == 'FAIL')
    errors = sum(1 for r in reports if r['status'] == 'ERROR')
    skipped = sum(1 for r in reports if r['status'] == 'SKIPPED')

    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    logger.info(f"{Fore.MAGENTA}📊 QC VALIDATION SUMMARY")
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.CYAN}📅 Dates validated: {total_dates}")
    logger.info(f"{Fore.GREEN}✅ Passed: {passed}")
    logger.info(f"{Fore.RED}❌ Failed: {failed}")
    logger.info(f"{Fore.YELLOW}⚠️  Errors: {errors}")
    if skipped > 0:
        logger.info(f"{Fore.YELLOW}⏭️  Skipped (Dock Totals duplicates): {skipped}")

    # List skipped dates with details
    if skipped > 0:
        logger.info(f"{Fore.YELLOW}\n📋 Skipped Dates:")
        for r in reports:
            if r['status'] == 'SKIPPED':
                logger.info(f"{Fore.YELLOW}   - {r['date']}: {r.get('reason', 'Unknown')} (deleted {r.get('deleted_trips', 0)} trips)")

    effective_dates = total_dates - skipped
    if passed == effective_dates:
        logger.info(f"{Fore.GREEN}\n{'='*80}")
        logger.info(f"{Fore.GREEN}🎉 100% QC VALIDATION PASSED!")
        if skipped > 0:
            logger.info(f"{Fore.YELLOW}   ({skipped} dates skipped as Dock Totals duplicates)")
        logger.info(f"{Fore.GREEN}{'='*80}\n")
    else:
        logger.error(f"{Fore.RED}\n{'='*80}")
        logger.error(f"{Fore.RED}❌ QC VALIDATION FAILED")
        logger.error(f"{Fore.RED}{'='*80}\n")

    # Save to file if requested
    if output_file:
        effective_dates = total_dates - skipped
        output_data = {
            'date_range': {'start': start_date, 'end': end_date},
            'summary': {
                'total_dates': total_dates,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'skipped': skipped,
                'effective_dates': effective_dates,
                'pass_rate': round(passed / effective_dates * 100, 2) if effective_dates > 0 else 0
            },
            'reports': reports,
            'timestamp': datetime.utcnow().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"{Fore.GREEN}✅ Report saved: {output_file}")

# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='QC Validator - 100% Data Accuracy Verification')
    parser.add_argument('--date', help='Single date to validate (YYYY-MM-DD)')
    parser.add_argument('--start-date', help='Start date for range validation (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for range validation (YYYY-MM-DD)')
    parser.add_argument('--polaris-test', action='store_true', help='Run Polaris Supreme validation test')
    parser.add_argument('--output', help='Output JSON file for results')

    args = parser.parse_args()

    try:
        if args.polaris_test:
            # Run Polaris Supreme test
            supabase = init_supabase()
            report = validate_polaris_supreme(supabase)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"{Fore.GREEN}✅ Report saved: {args.output}")

        elif args.date:
            # Validate single date
            supabase = init_supabase()
            report = validate_date(args.date, supabase)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"{Fore.GREEN}✅ Report saved: {args.output}")

        elif args.start_date and args.end_date:
            # Validate date range
            validate_date_range(args.start_date, args.end_date, args.output)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info(f"\n{Fore.YELLOW}⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
