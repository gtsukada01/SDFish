#!/usr/bin/env python3
"""
Automated 2024 Monthly Scraper with Progressive QC Validation

SPEC 006 Compliant: 100% Accuracy Mandate
- Scrapes 2024 month-by-month in batches of 5 dates
- QC validates after each batch
- Stops immediately if any batch fails QC
- Generates monthly and comprehensive validation reports

Usage:
    python3 scrape_2024_by_month.py [--start-month JAN|FEB|...|DEC]
"""

import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_2024_by_month.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MONTHS = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
}

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

def generate_month_batches(year, month, batch_size=5):
    """Generate date batches for a specific month."""
    _, last_day = calendar.monthrange(year, month)
    start = datetime(year, month, 1)
    end = datetime(year, month, last_day)

    batches = []
    current = start
    batch_num = 1

    while current <= end:
        batch_end = min(current + timedelta(days=batch_size - 1), end)
        batches.append({
            'batch_num': batch_num,
            'start_date': current.strftime('%Y-%m-%d'),
            'end_date': batch_end.strftime('%Y-%m-%d'),
            'days': (batch_end - current).days + 1
        })
        current = batch_end + timedelta(days=1)
        batch_num += 1

    return batches

def run_scraper(start_date, end_date):
    """Run the boats_scraper.py for a date range."""
    cmd = [
        'python3', 'boats_scraper.py',
        '--start-date', start_date,
        '--end-date', end_date
    ]

    logger.info(f"  🚀 Scraping: {start_date} to {end_date}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"  ❌ Scraper failed: {result.stderr}")
        return False

    logger.info(f"  ✅ Scraper completed")
    return True

def run_qc_validation(start_date, end_date, output_file):
    """Run QC validation for a date range."""
    cmd = [
        'python3', 'qc_validator.py',
        '--start-date', start_date,
        '--end-date', end_date,
        '--output', output_file
    ]

    logger.info(f"  🔍 QC Validating: {start_date} to {end_date}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"  ❌ QC validation failed: {result.stderr}")
        return False, None

    # Load validation results
    try:
        with open(output_file, 'r') as f:
            qc_data = json.load(f)

        pass_rate = qc_data['summary']['pass_rate']
        logger.info(f"  ✅ QC Pass Rate: {pass_rate}%")

        return pass_rate == 100.0, qc_data
    except Exception as e:
        logger.error(f"  ❌ Failed to parse QC results: {e}")
        return False, None

def process_month(year, month_num, month_name):
    """Process all batches for a specific month."""
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"📅 MONTH: {month_name.upper()} 2024")
    logger.info("=" * 80)

    # Generate batches for this month
    batches = generate_month_batches(year, month_num)
    logger.info(f"📊 Total batches for {month_name}: {len(batches)}")

    month_progress = {
        'month': month_name,
        'month_num': month_num,
        'total_batches': len(batches),
        'completed_batches': 0,
        'failed_batches': 0,
        'total_dates': 0,
        'batch_results': []
    }

    # Process each batch in this month
    for batch in batches:
        batch_num = batch['batch_num']
        start_date = batch['start_date']
        end_date = batch['end_date']

        logger.info("")
        logger.info(f"  📦 Batch {batch_num}/{len(batches)} | {start_date} to {end_date} ({batch['days']} days)")

        # Step 1: Scrape
        if not run_scraper(start_date, end_date):
            logger.error(f"  ❌ BATCH {batch_num} FAILED: Scraper error")
            month_progress['failed_batches'] += 1
            return False, month_progress

        # Step 2: QC Validate
        qc_output = f"qc_{month_name.lower()}_batch{batch_num:02d}_2024.json"
        passed, qc_data = run_qc_validation(start_date, end_date, qc_output)

        if not passed:
            logger.error(f"  ❌ BATCH {batch_num} FAILED: QC validation did not pass 100%")
            month_progress['failed_batches'] += 1

            # Save failure report
            failure_file = f'FAILED_{month_name.upper()}_BATCH_{batch_num}.json'
            with open(failure_file, 'w') as f:
                json.dump({
                    'month': month_name,
                    'batch_num': batch_num,
                    'start_date': start_date,
                    'end_date': end_date,
                    'qc_data': qc_data
                }, f, indent=2)

            logger.error(f"  📄 Failure details saved to {failure_file}")
            logger.error("  🛑 STOPPING MONTH PROCESSING")
            return False, month_progress

        # Step 3: Update progress
        month_progress['completed_batches'] += 1
        month_progress['total_dates'] += qc_data['summary']['total_dates']

        batch_result = {
            'batch_num': batch_num,
            'start_date': start_date,
            'end_date': end_date,
            'days': batch['days'],
            'pass_rate': qc_data['summary']['pass_rate'],
            'dates_validated': qc_data['summary']['total_dates'],
            'qc_file': qc_output
        }
        month_progress['batch_results'].append(batch_result)

        logger.info(f"  ✅ Batch {batch_num} complete: 100% pass rate")

    # Month complete
    logger.info("")
    logger.info(f"✅ {month_name.upper()} COMPLETE!")
    logger.info(f"   📊 Batches: {month_progress['completed_batches']}/{len(batches)}")
    logger.info(f"   📅 Dates validated: {month_progress['total_dates']}")
    logger.info(f"   ✅ Pass rate: 100%")

    # Save monthly report
    monthly_report = f'SCRAPE_2024_{month_name.upper()}_REPORT.json'
    with open(monthly_report, 'w') as f:
        json.dump(month_progress, f, indent=2)
    logger.info(f"   📄 Monthly report: {monthly_report}")

    return True, month_progress

def main():
    """Main automation workflow."""
    logger.info("=" * 80)
    logger.info("🚀 AUTOMATED 2024 MONTHLY SCRAPER")
    logger.info("=" * 80)
    logger.info("SPEC 006 Compliant: 100% Accuracy Mandate")
    logger.info("Workflow: Month → Batches → QC Validate → Verify 100% Pass")
    logger.info("=" * 80)

    # Check for start month flag
    start_month = 1
    if len(sys.argv) > 2 and sys.argv[1] == '--start-month':
        month_abbr = sys.argv[2].upper()
        if month_abbr in MONTHS:
            start_month = MONTHS[month_abbr]
            logger.info(f"📍 Starting from: {MONTH_NAMES[start_month]}")
        else:
            logger.error(f"❌ Invalid month: {month_abbr}")
            logger.error(f"   Valid: {', '.join(MONTHS.keys())}")
            return 1

    # Track overall progress
    overall_progress = {
        'year': 2024,
        'months_completed': 0,
        'months_failed': 0,
        'total_dates': 0,
        'total_batches': 0,
        'month_results': []
    }

    # Process each month
    for month_num in range(start_month, 13):
        month_name = MONTH_NAMES[month_num]

        success, month_progress = process_month(2024, month_num, month_name)

        if success:
            overall_progress['months_completed'] += 1
            overall_progress['total_dates'] += month_progress['total_dates']
            overall_progress['total_batches'] += month_progress['completed_batches']
            overall_progress['month_results'].append(month_progress)

            logger.info(f"📊 OVERALL PROGRESS: {overall_progress['months_completed']}/12 months complete ({overall_progress['months_completed']/12*100:.1f}%)")
        else:
            overall_progress['months_failed'] += 1
            overall_progress['month_results'].append(month_progress)

            logger.error("")
            logger.error("=" * 80)
            logger.error(f"❌ {month_name.upper()} FAILED")
            logger.error("=" * 80)
            logger.error("🛑 STOPPING AUTOMATION - REQUIRES INVESTIGATION")

            # Save partial progress
            partial_report = f'SCRAPE_2024_PARTIAL_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(partial_report, 'w') as f:
                json.dump(overall_progress, f, indent=2)
            logger.error(f"📄 Partial progress saved: {partial_report}")
            return 1

    # All months complete
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 100% SUCCESS - ALL 2024 DATA SCRAPED AND VALIDATED!")
    logger.info("=" * 80)
    logger.info(f"✅ Months completed: {overall_progress['months_completed']}/12")
    logger.info(f"✅ Total batches: {overall_progress['total_batches']}")
    logger.info(f"✅ Total dates validated: {overall_progress['total_dates']}")
    logger.info(f"✅ QC pass rate: 100%")

    # Save comprehensive report
    final_report = 'SCRAPE_2024_FINAL_REPORT.json'
    with open(final_report, 'w') as f:
        json.dump(overall_progress, f, indent=2)

    logger.info(f"📄 Final report: {final_report}")
    logger.info("=" * 80)
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
