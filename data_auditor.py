#!/usr/bin/env python3
"""
Data Auditor Agent - Continuous Quality Monitoring
===================================================

SPEC 009: Random spot-checking of trip data to detect phantom/misattributed entries

Features:
- Random sampling with stratification (by landing, boat, date)
- Multi-level validation (existence, field accuracy, anomaly detection)
- Evidence capture with source snapshots
- Automated reporting with remediation recommendations
- Alert system for quality degradation

Author: Fishing Intelligence Platform
Date: October 18, 2025
"""

import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import statistics

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from colorama import Fore, Style, init
import argparse

# Import utilities from existing infrastructure
sys.path.insert(0, str(Path(__file__).parent))
from boats_scraper import (
    parse_boats_page,
    normalize_trip_type,
    parse_species_counts,
    init_supabase,
    BOATS_URL_TEMPLATE
)

from qc_validator import (
    get_database_trips,
    fetch_source_page,
    validate_date,
    setup_logging as qc_setup_logging
)

# Initialize colorama
init(autoreset=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

# Directories
SPEC_DIR = Path(__file__).parent / "specs" / "009-continuous-data-audit"
REPORT_DIR = SPEC_DIR / "audit_reports"
EVIDENCE_DIR = SPEC_DIR / "evidence"
AUDIT_HISTORY_FILE = SPEC_DIR / "audit_history.json"

# Ensure directories exist
SPEC_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Logging
LOG_FILE = "data_auditor.log"
LOG_LEVEL = logging.INFO

# Default configuration
DEFAULT_CONFIG = {
    "sampling": {
        "date_range_days": 30,
        "sample_size": 50,
        "stratified": True,
        "min_boats_per_landing": 2
    },
    "validation": {
        "anglers_tolerance": 1,
        "catch_count_tolerance_pct": 5,
        "enable_statistical_outlier_detection": True,
        "z_score_threshold": 3.0
    },
    "reporting": {
        "output_dir": str(REPORT_DIR),
        "evidence_dir": str(EVIDENCE_DIR),
        "generate_screenshots": False,
        "alert_on_qc_below": 99.5
    }
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging for data auditor"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - [AUDIT] %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# AUDIT HISTORY MANAGEMENT
# ============================================================================

def load_audit_history() -> Dict:
    """Load audit history from file"""
    if AUDIT_HISTORY_FILE.exists():
        with open(AUDIT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"audits": [], "trip_audit_count": {}}

def save_audit_history(history: Dict):
    """Save audit history to file"""
    with open(AUDIT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def update_audit_history(trip_ids: List[int], audit_date: str):
    """Update audit history with newly audited trips"""
    history = load_audit_history()

    # Add audit record
    history["audits"].append({
        "date": audit_date,
        "trip_count": len(trip_ids),
        "trip_ids": trip_ids
    })

    # Update trip audit counts
    for trip_id in trip_ids:
        trip_id_str = str(trip_id)
        if trip_id_str not in history["trip_audit_count"]:
            history["trip_audit_count"][trip_id_str] = 0
        history["trip_audit_count"][trip_id_str] += 1

    save_audit_history(history)
    logger.info(f"Updated audit history: {len(trip_ids)} trips audited")

# ============================================================================
# RANDOM SAMPLING
# ============================================================================

def get_recent_trips(supabase: Client, days_back: int) -> List[Dict]:
    """
    Get all trips from last N days

    Returns:
        List of trips with id, date, boat, landing
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    logger.info(f"Fetching trips from {start_date} to {end_date}")

    result = supabase.table('trips') \
        .select('id, trip_date, trip_duration, anglers, boat_id, landing_id, boats(name), landings(name)') \
        .gte('trip_date', str(start_date)) \
        .lte('trip_date', str(end_date)) \
        .execute()

    trips = []
    for row in result.data:
        trips.append({
            'id': row['id'],
            'trip_date': row['trip_date'],
            'trip_duration': row['trip_duration'],
            'anglers': row['anglers'],
            'boat_id': row['boat_id'],
            'boat_name': row['boats']['name'],
            'landing_id': row['landing_id'],
            'landing_name': row['landings']['name']
        })

    logger.info(f"Found {len(trips)} trips in date range")
    return trips

def stratified_sample(
    trips: List[Dict],
    sample_size: int,
    min_boats_per_landing: int = 2
) -> List[Dict]:
    """
    Select stratified random sample ensuring landing/boat diversity

    Strategy:
    1. Group trips by landing
    2. For each landing, select trips ensuring boat diversity
    3. Return balanced sample
    """
    # Group by landing
    by_landing = defaultdict(list)
    for trip in trips:
        by_landing[trip['landing_name']].append(trip)

    logger.info(f"Stratifying across {len(by_landing)} landings")

    # Calculate trips per landing
    trips_per_landing = max(1, sample_size // len(by_landing))

    sample = []
    audit_history = load_audit_history()
    trip_audit_counts = audit_history.get("trip_audit_count", {})

    for landing_name, landing_trips in by_landing.items():
        # Group by boat within this landing
        by_boat = defaultdict(list)
        for trip in landing_trips:
            by_boat[trip['boat_name']].append(trip)

        # Ensure boat diversity: select from multiple boats
        boats_to_sample = list(by_boat.keys())
        random.shuffle(boats_to_sample)

        landing_sample = []
        boat_index = 0

        # Prioritize trips that haven't been audited recently
        for _ in range(min(trips_per_landing, len(landing_trips))):
            # Get trips from next boat (round-robin)
            boat = boats_to_sample[boat_index % len(boats_to_sample)]
            boat_trips = by_boat[boat]

            if boat_trips:
                # Sort by audit frequency (least audited first)
                boat_trips.sort(key=lambda t: trip_audit_counts.get(str(t['id']), 0))
                selected_trip = boat_trips.pop(0)
                landing_sample.append(selected_trip)

            boat_index += 1

        logger.info(f"  {landing_name}: {len(landing_sample)} trips from {min(len(boats_to_sample), len(landing_sample))} boats")
        sample.extend(landing_sample)

    # If we haven't reached sample_size, randomly add more
    remaining = sample_size - len(sample)
    if remaining > 0:
        available = [t for t in trips if t not in sample]
        if available:
            sample.extend(random.sample(available, min(remaining, len(available))))

    logger.info(f"Selected {len(sample)} trips for audit")
    return sample[:sample_size]

# ============================================================================
# VALIDATION
# ============================================================================

def validate_trip(
    trip: Dict,
    supabase: Client,
    config: Dict
) -> Dict:
    """
    Validate a single trip against source

    Returns:
        Validation result with category, evidence, recommendation
    """
    trip_id = trip['id']
    trip_date = trip['trip_date']

    logger.info(f"Validating trip {trip_id} from {trip_date}")

    # Get full trip details from database
    db_trips = get_database_trips(supabase, trip_date)

    # Match trip using composite key (boat_name, trip_duration, anglers)
    # since get_database_trips doesn't return trip ID
    db_trip = next((
        t for t in db_trips
        if t.get('boat_name') == trip['boat_name']
        and t.get('trip_duration') == trip['trip_duration']
        and t.get('anglers') == trip['anglers']
    ), None)

    if not db_trip:
        logger.warning(f"Trip {trip_id} not found in db_trips (using composite key match)")
        return {
            "trip_id": trip_id,
            "category": "DATABASE_ERROR",
            "severity": "CRITICAL",
            "reasoning": f"Trip not found in database query for {trip_date} (boat: {trip['boat_name']}, duration: {trip['trip_duration']}, anglers: {trip['anglers']})"
        }

    # Add trip_id to db_trip for tracking
    db_trip['trip_id'] = trip_id

    # Use qc_validator's validate_date function to get comparison results
    try:
        validation_result = validate_date(trip_date, supabase)
        time.sleep(2)  # Rate limiting
    except Exception as e:
        logger.warning(f"Failed to validate {trip_date}: {e}")
        return {
            "trip_id": trip_id,
            "category": "VALIDATION_FAILED",
            "severity": "UNKNOWN",
            "reasoning": f"Source unavailable: {e}",
            "requires_manual_review": True
        }

    # Parse source page to get boat names
    # (validate_date structure: {status, matches, mismatches, missing_boats, extra_boats, ...})
    url = BOATS_URL_TEMPLATE.format(date=trip_date)
    html = fetch_source_page(url)
    source_boats = []
    if html:
        source_trips = parse_boats_page(html, trip_date)
        source_boats = [t['boat_name'] for t in source_trips]

    # Categorize based on validation results
    result = {
        "trip_id": trip_id,
        "audit_date": datetime.now().isoformat(),
        "database_record": db_trip,
        "source_verification": {
            "source_url": url,
            "boats_found_on_date": source_boats,
            "validation_status": validation_result.get('status')
        }
    }

    # Check if this trip is in the extra_boats list (phantom)
    extra_boats = validation_result.get('extra_boats', [])
    is_extra = any(
        eb.get('boat') == db_trip['boat_name']
        and eb.get('landing') == db_trip['landing_name']
        for eb in extra_boats
    )

    # Check if this trip is in the mismatches list (field errors)
    mismatches = validation_result.get('mismatches', [])
    is_mismatch = any(mm.get('boat') == db_trip['boat_name'] for mm in mismatches)

    # Check if this trip is in missing_boats (exists in source but not DB)
    missing_boats = validation_result.get('missing_boats', [])

    if is_extra:
        # Trip is in database but NOT on source page = PHANTOM
        result.update({
            "category": "PHANTOM",
            "severity": "CRITICAL",
            "validation_results": {
                "level_1_exists": False,
                "in_extra_boats": True
            },
            "recommendation": {
                "action": "DELETE",
                "confidence": "HIGH",
                "reasoning": "Trip exists in database but not found on source page (extra boat)"
            }
        })
    elif is_mismatch:
        # Trip found but has field mismatches = PARTIAL
        mismatch_details = next(mm for mm in mismatches if mm.get('boat') == db_trip['boat_name'])
        result.update({
            "category": "PARTIAL",
            "severity": "MEDIUM",
            "validation_results": {
                "level_1_exists": True,
                "field_errors": mismatch_details.get('errors', [])
            },
            "recommendation": {
                "action": "MANUAL_REVIEW",
                "confidence": "MEDIUM",
                "reasoning": f"Field mismatches: {', '.join(mismatch_details.get('errors', []))}",
                "requires_manual_review": True
            }
        })
    elif len(missing_boats) > 0:
        # Some boats on source but not in DB - might be misattributed
        result.update({
            "category": "MISATTRIBUTED",
            "severity": "HIGH",
            "validation_results": {
                "level_1_exists": True,
                "missing_boats_count": len(missing_boats)
            },
            "recommendation": {
                "action": "INVESTIGATE",
                "confidence": "MEDIUM",
                "reasoning": f"{len(missing_boats)} boats on source not in database - possible misattribution",
                "requires_manual_review": True
            }
        })
    else:
        # No issues found = VALID
        result.update({
            "category": "VALID",
            "severity": "NONE",
            "validation_results": {
                "level_1_exists": True,
                "level_2_fields": "EXACT_MATCH"
            },
            "recommendation": {
                "action": "NONE",
                "confidence": "HIGH",
                "reasoning": "Trip matches source exactly (no errors reported by QC validator)"
            }
        })

    # Level 3: Statistical anomaly detection (if VALID)
    if result['category'] == 'VALID' and config['validation']['enable_statistical_outlier_detection']:
        # Simple outlier check for unusually high anglers
        anglers = db_trip.get('anglers', 0)
        if anglers and anglers > 100:
            result['category'] = 'STATISTICAL_OUTLIER'
            result['severity'] = 'LOW'
            result['recommendation']['requires_manual_review'] = True

    return result

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(
    audit_results: List[Dict],
    sample_metadata: Dict,
    config: Dict
) -> str:
    """
    Generate markdown audit report

    Returns:
        Report content as string
    """
    audit_date = datetime.now().strftime("%Y-%m-%d")

    # Count categories
    category_counts = defaultdict(int)
    for result in audit_results:
        category_counts[result['category']] += 1

    total = len(audit_results)
    valid_count = category_counts.get('VALID', 0)
    qc_confidence = (valid_count / total * 100) if total > 0 else 0

    # Build report
    report_lines = [
        f"# Data Auditor Report – {audit_date}",
        "",
        "## Executive Summary",
        f"- **Sample Size**: {total} trips",
        f"- **Date Range**: {sample_metadata['start_date']} to {sample_metadata['end_date']} (last {sample_metadata['days_back']} days)",
        f"- **Landings Covered**: {sample_metadata['landings_count']} landings",
        f"- **Boats Covered**: {sample_metadata['boats_count']} boats",
        "",
        "## Findings Summary",
        "",
        "| Category | Count | % of Sample | Severity |",
        "|----------|-------|-------------|----------|"
    ]

    # Add category rows
    category_emojis = {
        'VALID': '✅',
        'PHANTOM': '🔴',
        'MISATTRIBUTED': '🟡',
        'PARTIAL': '🟠',
        'DUPLICATE': '🔵',
        'STATISTICAL_OUTLIER': '⚪',
        'VALIDATION_FAILED': '⚫',
        'DATABASE_ERROR': '🔴'
    }

    for category in ['VALID', 'PHANTOM', 'MISATTRIBUTED', 'PARTIAL', 'DUPLICATE', 'STATISTICAL_OUTLIER', 'VALIDATION_FAILED']:
        count = category_counts.get(category, 0)
        pct = (count / total * 100) if total > 0 else 0
        emoji = category_emojis.get(category, '⚪')

        severity = 'NONE' if category == 'VALID' else 'CRITICAL' if category in ['PHANTOM', 'DATABASE_ERROR'] else 'HIGH' if category in ['MISATTRIBUTED', 'DUPLICATE'] else 'MEDIUM' if category == 'PARTIAL' else 'LOW'

        report_lines.append(f"| {emoji} {category} | {count} | {pct:.1f}% | {severity} |")

    report_lines.extend([
        "",
        f"## QC Confidence Score: {qc_confidence:.1f}%"
    ])

    # Alert if below threshold
    alert_threshold = config['reporting']['alert_on_qc_below']
    if qc_confidence < alert_threshold:
        report_lines.append(f"⚠️ **ALERT**: QC confidence below {alert_threshold}% target. Immediate investigation required.")
    else:
        report_lines.append(f"✅ **HEALTHY**: QC confidence above {alert_threshold}% target.")

    report_lines.extend([
        "",
        "## Critical Findings Requiring Immediate Action",
        ""
    ])

    # List critical findings
    critical_findings = [r for r in audit_results if r.get('severity') == 'CRITICAL' and r['category'] != 'VALID']

    if critical_findings:
        for finding in critical_findings[:10]:  # Show first 10
            trip_id = finding['trip_id']
            db_record = finding.get('database_record', {})
            category = finding['category']
            reasoning = finding.get('recommendation', {}).get('reasoning', 'No reasoning provided')

            report_lines.extend([
                f"### {category} Trip Detected",
                f"**Trip ID {trip_id}** - {db_record.get('trip_date', 'Unknown date')}, {db_record.get('boat_name', 'Unknown boat')}, {db_record.get('trip_duration', 'Unknown duration')}, {db_record.get('anglers', '?')} anglers",
                f"- **Issue**: {reasoning}",
                f"- **Evidence**: `evidence/trip_{trip_id}_evidence.json`",
                f"- **Recommendation**: {finding.get('recommendation', {}).get('action', 'INVESTIGATE')}",
                f"- **Confidence**: {finding.get('recommendation', {}).get('confidence', 'UNKNOWN')}",
                ""
            ])
    else:
        report_lines.append("✅ **No critical findings detected**")
        report_lines.append("")

    # Remediation action plan
    report_lines.extend([
        "## Remediation Action Plan",
        "",
        "### Immediate Actions (Require Approval)",
        ""
    ])

    phantom_ids = [r['trip_id'] for r in audit_results if r['category'] == 'PHANTOM']
    misattributed = [r for r in audit_results if r['category'] == 'MISATTRIBUTED']

    if phantom_ids:
        report_lines.extend([
            f"**PHANTOM Trips** ({len(phantom_ids)} trips):",
            "```sql",
            "-- Delete phantom trips after approval",
            "BEGIN TRANSACTION;",
            f"DELETE FROM catches WHERE trip_id IN ({', '.join(map(str, phantom_ids[:20]))});",
            f"DELETE FROM trips WHERE id IN ({', '.join(map(str, phantom_ids[:20]))});",
            "COMMIT;",
            "```",
            ""
        ])

    if misattributed:
        report_lines.extend([
            f"**MISATTRIBUTED Trips** ({len(misattributed)} trips):",
            "```sql",
            "-- Manual investigation required to identify correct boats",
            "```",
            ""
        ])

    # Manual review queue
    manual_review = [r for r in audit_results if r.get('recommendation', {}).get('requires_manual_review', False)]
    report_lines.extend([
        f"### Manual Review Queue ({len(manual_review)} trips)",
        ""
    ])

    if manual_review:
        for item in manual_review[:5]:
            report_lines.append(f"- Trip {item['trip_id']}: {item['category']} - {item.get('recommendation', {}).get('reasoning', 'No details')}")
    else:
        report_lines.append("None")

    report_lines.extend([
        "",
        "## Audit Coverage",
        f"- Trips audited this run: {total}",
        f"- Unique dates covered: {sample_metadata['unique_dates']}",
        f"- Next audit recommended: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
        f"**Audit completed at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Generated by**: Data Auditor Agent v1.0.0 (SPEC-009)",
        ""
    ])

    return "\n".join(report_lines)

def save_evidence(result: Dict, evidence_dir: Path):
    """Save evidence file for a validation result"""
    trip_id = result['trip_id']
    evidence_file = evidence_dir / f"trip_{trip_id}_evidence.json"

    with open(evidence_file, 'w') as f:
        json.dump(result, f, indent=2)

# ============================================================================
# MAIN AUDIT LOGIC
# ============================================================================

def run_audit(
    sample_size: int = 50,
    date_range_days: int = 30,
    config: Optional[Dict] = None
):
    """
    Run a complete audit cycle

    Returns:
        Audit results and report path
    """
    if config is None:
        config = DEFAULT_CONFIG

    logger.info("=" * 80)
    logger.info("STARTING DATA QUALITY AUDIT")
    logger.info("=" * 80)

    # Initialize Supabase
    supabase = init_supabase()

    # Step 1: Get recent trips
    logger.info(f"Step 1: Fetching trips from last {date_range_days} days")
    all_trips = get_recent_trips(supabase, date_range_days)

    if not all_trips:
        logger.error("No trips found in date range")
        return None, None

    # Step 2: Select stratified sample
    logger.info(f"Step 2: Selecting stratified sample of {sample_size} trips")
    sample = stratified_sample(all_trips, sample_size, config['sampling']['min_boats_per_landing'])

    # Gather sample metadata
    unique_dates = len(set(t['trip_date'] for t in sample))
    landings = set(t['landing_name'] for t in sample)
    boats = set(t['boat_name'] for t in sample)

    sample_metadata = {
        "start_date": min(t['trip_date'] for t in sample),
        "end_date": max(t['trip_date'] for t in sample),
        "days_back": date_range_days,
        "unique_dates": unique_dates,
        "landings_count": len(landings),
        "boats_count": len(boats)
    }

    logger.info(f"Sample: {len(sample)} trips, {unique_dates} dates, {len(landings)} landings, {len(boats)} boats")

    # Step 3: Validate each trip
    logger.info(f"Step 3: Validating {len(sample)} trips against source")
    audit_results = []

    for i, trip in enumerate(sample, 1):
        logger.info(f"[{i}/{len(sample)}] Validating trip {trip['id']} ({trip['trip_date']})")
        result = validate_trip(trip, supabase, config)
        audit_results.append(result)

        # Save evidence for non-VALID trips
        if result['category'] != 'VALID':
            save_evidence(result, EVIDENCE_DIR)

    # Step 4: Generate report
    logger.info("Step 4: Generating audit report")
    report_content = generate_report(audit_results, sample_metadata, config)

    # Save report
    audit_date = datetime.now().strftime("%Y-%m-%d")
    report_path = REPORT_DIR / f"{audit_date}_audit_report.md"
    with open(report_path, 'w') as f:
        f.write(report_content)

    logger.info(f"Report saved to: {report_path}")

    # Save audit results JSON
    results_path = REPORT_DIR / f"{audit_date}_audit_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "audit_date": audit_date,
            "sample_metadata": sample_metadata,
            "results": audit_results,
            "config": config
        }, f, indent=2)

    logger.info(f"Results saved to: {results_path}")

    # Update audit history
    trip_ids = [t['id'] for t in sample]
    update_audit_history(trip_ids, audit_date)

    # Print summary
    valid_count = sum(1 for r in audit_results if r['category'] == 'VALID')
    qc_confidence = (valid_count / len(audit_results) * 100) if audit_results else 0

    logger.info("=" * 80)
    logger.info("AUDIT COMPLETE")
    logger.info(f"QC Confidence: {qc_confidence:.1f}%")
    logger.info(f"VALID: {valid_count}/{len(audit_results)}")
    logger.info(f"Report: {report_path}")
    logger.info("=" * 80)

    return audit_results, report_path

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Data Auditor Agent - Continuous Quality Monitoring (SPEC-009)"
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=50,
        help="Number of trips to audit (default: 50)"
    )
    parser.add_argument(
        '--date-range',
        type=int,
        default=30,
        help="Days back to sample from (default: 30)"
    )
    parser.add_argument(
        '--report-dir',
        type=str,
        default=str(REPORT_DIR),
        help="Directory to save reports"
    )

    args = parser.parse_args()

    # Run audit
    results, report_path = run_audit(
        sample_size=args.sample_size,
        date_range_days=args.date_range
    )

    if results and report_path:
        print(f"\n{Fore.GREEN}✅ Audit complete!{Style.RESET_ALL}")
        print(f"Report: {report_path}")

        # Print quick summary
        valid = sum(1 for r in results if r['category'] == 'VALID')
        phantom = sum(1 for r in results if r['category'] == 'PHANTOM')
        misattributed = sum(1 for r in results if r['category'] == 'MISATTRIBUTED')

        print(f"\nQuick Summary:")
        print(f"  ✅ VALID: {valid}")
        if phantom > 0:
            print(f"  🔴 PHANTOM: {phantom}")
        if misattributed > 0:
            print(f"  🟡 MISATTRIBUTED: {misattributed}")
    else:
        print(f"\n{Fore.RED}❌ Audit failed{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == '__main__':
    main()
