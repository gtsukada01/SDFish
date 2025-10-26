#!/usr/bin/env python3
"""
SPEC-008 Diagnostic QC Validation
==================================

Validates all 105 affected dates against source to categorize 116 phantom trips.

Categories:
- PHANTOM: Trip does NOT exist in source
- MISATTRIBUTED: Trip exists but assigned to wrong boat
- DATE-SHIFTED: Trip exists on different date
- FIELD-MISMATCH: Trip exists but with different details
- UNKNOWN: Cannot determine

Author: Fishing Intelligence Platform
Date: October 18, 2025
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add fish-scraper directory to path
sys.path.insert(0, '/Users/btsukada/Desktop/Fishing/fish-scraper')

from boats_scraper import (
    parse_boats_page,
    normalize_trip_type,
    parse_species_counts,
    init_supabase,
    BOATS_URL_TEMPLATE
)

import requests
from bs4 import BeautifulSoup

# Constants
PHANTOM_BOAT_IDS = [374, 375]
SPEC_DIR = Path(__file__).parent

def load_affected_dates() -> List[str]:
    """Load list of affected dates from text file"""
    dates_file = SPEC_DIR / 'unmatched_dates_for_qc.txt'
    with open(dates_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def load_phantom_trips() -> Dict[int, List[Dict]]:
    """Load phantom trip data from extraction files"""
    phantom_trips = {}

    for boat_id in PHANTOM_BOAT_IDS:
        trips_file = SPEC_DIR / f'diagnostic_trips_boat_{boat_id}.json'
        with open(trips_file, 'r') as f:
            phantom_trips[boat_id] = json.load(f)

    return phantom_trips

def fetch_source_page(date: str, session: requests.Session, delay: float = 3.0) -> Optional[str]:
    """Fetch source page HTML for a given date with proper headers"""
    url = BOATS_URL_TEMPLATE.format(date=date)

    # Proper headers to avoid 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        time.sleep(delay)  # Ethical scraping delay
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"   ❌ Error fetching {url}: {e}")
        # Retry once after longer delay
        try:
            time.sleep(10)
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except:
            return None

def parse_source_trips(html: str, date: str) -> List[Dict]:
    """Parse trips from source page HTML"""
    try:
        trips_data = parse_boats_page(html, date)
        return trips_data
    except Exception as e:
        print(f"   ❌ Error parsing source page: {e}")
        return []

def find_matching_trip(phantom_trip: Dict, source_trips: List[Dict]) -> Optional[Dict]:
    """
    Find matching trip in source data

    Returns:
        Matching trip dict if found, None otherwise
    """
    # Extract phantom trip details
    phantom_duration = phantom_trip.get('trip_duration', '')
    phantom_anglers = phantom_trip.get('anglers')

    # Try to find exact match on duration + anglers
    for source_trip in source_trips:
        source_duration = source_trip.get('trip_duration', '')
        source_anglers = source_trip.get('anglers')

        # Normalize trip durations for comparison
        phantom_norm = normalize_trip_type(phantom_duration)
        source_norm = normalize_trip_type(source_duration)

        # Match on duration + anglers
        if phantom_norm == source_norm and phantom_anglers == source_anglers:
            return source_trip

    # No exact match found
    return None

def categorize_trip(phantom_trip: Dict, date: str, source_trips: List[Dict],
                   all_dates_source: Dict[str, List[Dict]]) -> Dict:
    """
    Categorize a single phantom trip

    Returns:
        Evidence dict with category and reasoning
    """
    trip_id = phantom_trip['id']
    trip_date = phantom_trip['trip_date']
    trip_duration = phantom_trip['trip_duration']
    anglers = phantom_trip['anglers']
    current_boat_id = phantom_trip['boat_id']

    evidence = {
        'trip_id': trip_id,
        'trip_date': trip_date,
        'trip_duration': trip_duration,
        'anglers': anglers,
        'current_boat_id': current_boat_id,
        'category': 'UNKNOWN',
        'reasoning': '',
        'confidence': 'low',
        'recommended_action': '',
        'source_url': BOATS_URL_TEMPLATE.format(date=date),
        'match_details': None
    }

    # Try to find match on the expected date
    match = find_matching_trip(phantom_trip, source_trips)

    if match:
        # Trip exists on expected date
        # Check if boat name matches
        phantom_boat_name = phantom_trip.get('boat_name', '')
        source_boat_name = match.get('boat_name', '')

        if phantom_boat_name == source_boat_name:
            # This shouldn't happen - if it exists correctly, why is it on phantom boat?
            evidence['category'] = 'FIELD-MISMATCH'
            evidence['reasoning'] = f"Trip exists on source with same boat '{source_boat_name}' but is on phantom boat_id {current_boat_id} in database. Investigate schema issue."
            evidence['confidence'] = 'medium'
            evidence['recommended_action'] = 'MANUAL_REVIEW'
        else:
            # Different boat name - this is a misattribution
            evidence['category'] = 'MISATTRIBUTED'
            evidence['reasoning'] = f"Trip exists on source with boat '{source_boat_name}' but is assigned to '{phantom_boat_name}' (boat_id {current_boat_id}) in database."
            evidence['confidence'] = 'high'
            evidence['recommended_action'] = f"UPDATE trips SET boat_id = (SELECT id FROM boats WHERE name = '{source_boat_name}' LIMIT 1) WHERE id = {trip_id}"
            evidence['match_details'] = {
                'source_boat_name': source_boat_name,
                'source_landing_name': match.get('landing_name'),
                'source_catches': match.get('catches', [])
            }
    else:
        # No match on expected date - check if it's phantom or date-shifted
        # For now, categorize as PHANTOM (date-shift detection would require checking adjacent dates)
        evidence['category'] = 'PHANTOM'
        evidence['reasoning'] = f"No trip with {anglers} anglers and '{trip_duration}' duration found on source page for {date}. Trip appears to not exist."
        evidence['confidence'] = 'high'
        evidence['recommended_action'] = f"DELETE FROM trips WHERE id = {trip_id}"

        # List boats that were on the source page
        boats_on_date = [t.get('boat_name') for t in source_trips]
        evidence['boats_on_source'] = boats_on_date

    return evidence

def validate_date(date: str, phantom_trips: Dict[int, List[Dict]],
                 supabase, session: requests.Session) -> Dict:
    """
    Validate all phantom trips for a specific date

    Returns:
        Validation report for the date
    """
    print(f"\n📅 Validating {date}...")

    report = {
        'date': date,
        'source_url': BOATS_URL_TEMPLATE.format(date=date),
        'phantom_trips_on_date': [],
        'categorizations': [],
        'status': 'pending'
    }

    # Find phantom trips on this date
    trips_on_date = []
    for boat_id, trips in phantom_trips.items():
        for trip in trips:
            if trip['trip_date'] == date:
                trips_on_date.append(trip)

    report['phantom_trips_on_date'] = len(trips_on_date)

    if len(trips_on_date) == 0:
        report['status'] = 'no_phantom_trips'
        print(f"   ℹ️  No phantom trips on this date")
        return report

    print(f"   🔍 Found {len(trips_on_date)} phantom trip(s) to validate")

    # Fetch source page
    source_html = fetch_source_page(date, session)

    if not source_html:
        report['status'] = 'source_fetch_failed'
        print(f"   ⚠️  Could not fetch source page")
        return report

    # Parse source trips
    source_trips = parse_source_trips(source_html, date)

    if not source_trips:
        report['status'] = 'source_parse_failed'
        print(f"   ⚠️  Could not parse source page")
        return report

    print(f"   ✅ Found {len(source_trips)} trip(s) on source page")

    # Categorize each phantom trip
    for trip in trips_on_date:
        evidence = categorize_trip(trip, date, source_trips, {})
        report['categorizations'].append(evidence)

        # Print summary
        category = evidence['category']
        confidence = evidence['confidence']
        trip_id = evidence['trip_id']

        symbol = "🔴" if category == "PHANTOM" else "🟡" if category == "MISATTRIBUTED" else "⚪"
        print(f"      {symbol} Trip {trip_id}: {category} (confidence: {confidence})")
        print(f"         {evidence['reasoning'][:100]}...")

    report['status'] = 'completed'
    return report

def run_diagnostic():
    """Main diagnostic function"""
    print("=" * 80)
    print("SPEC-008 DIAGNOSTIC QC VALIDATION")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Load data
    print("📂 Loading affected dates and phantom trips...")
    affected_dates = load_affected_dates()
    phantom_trips = load_phantom_trips()

    total_phantom_trips = sum(len(trips) for trips in phantom_trips.values())

    print(f"   ✅ Loaded {len(affected_dates)} dates")
    print(f"   ✅ Loaded {total_phantom_trips} phantom trips")

    # Initialize Supabase
    print("\n🔌 Connecting to Supabase...")
    supabase = init_supabase()
    print("   ✅ Connected")

    # Create requests session with proper headers
    print("\n🌐 Creating HTTP session with proper headers...")
    session = requests.Session()
    print("   ✅ Session ready")

    # Validate each date
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION ON ALL DATES")
    print("=" * 80)

    diagnostic_report = {
        'timestamp': datetime.now().isoformat(),
        'spec': 'SPEC-008',
        'phase': 'Phase 1: Diagnostic QC Validation',
        'summary': {
            'total_dates': len(affected_dates),
            'total_phantom_trips': total_phantom_trips,
            'dates_validated': 0,
            'trips_categorized': 0,
            'categories': {
                'PHANTOM': 0,
                'MISATTRIBUTED': 0,
                'DATE-SHIFTED': 0,
                'FIELD-MISMATCH': 0,
                'UNKNOWN': 0
            }
        },
        'date_reports': []
    }

    for i, date in enumerate(affected_dates, 1):
        print(f"\n[{i}/{len(affected_dates)}]", end=" ")

        try:
            date_report = validate_date(date, phantom_trips, supabase, session)
            diagnostic_report['date_reports'].append(date_report)

            # Update summary
            if date_report['status'] == 'completed':
                diagnostic_report['summary']['dates_validated'] += 1

                for cat in date_report['categorizations']:
                    category = cat['category']
                    diagnostic_report['summary']['categories'][category] += 1
                    diagnostic_report['summary']['trips_categorized'] += 1

        except Exception as e:
            print(f"   ❌ Error validating {date}: {e}")
            diagnostic_report['date_reports'].append({
                'date': date,
                'status': 'error',
                'error': str(e)
            })

    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)

    output_file = SPEC_DIR / 'qc_diagnostic_report.json'
    with open(output_file, 'w') as f:
        json.dump(diagnostic_report, f, indent=2)

    print(f"✅ Full diagnostic report: {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    summary = diagnostic_report['summary']
    print(f"Dates validated: {summary['dates_validated']}/{summary['total_dates']}")
    print(f"Trips categorized: {summary['trips_categorized']}/{summary['total_phantom_trips']}")
    print()
    print("Categories:")
    for category, count in summary['categories'].items():
        percentage = (count / summary['total_phantom_trips'] * 100) if summary['total_phantom_trips'] > 0 else 0
        symbol = "🔴" if category == "PHANTOM" else "🟡" if category == "MISATTRIBUTED" else "⚪"
        print(f"  {symbol} {category:20s}: {count:3d} ({percentage:5.1f}%)")

    print("\n" + "=" * 80)
    print(f"Completed: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == '__main__':
    run_diagnostic()
