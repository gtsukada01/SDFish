#!/usr/bin/env python3
"""
Automated 2024 Full Year Scraper with Progressive QC Validation

SPEC 006 Compliant: 100% Accuracy Mandate
- Scrapes all of 2024 in batches of 5 dates
- QC validates after each batch
- Stops immediately if any batch fails QC
- Generates comprehensive validation report

Usage:
    python3 scrape_2024_full.py [--resume-from BATCH_NUM]
"""

import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_2024_full.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_date_batches(year=2024, batch_size=5):
    """Generate date batches for the entire year."""
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)

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

    logger.info(f"🚀 Scraping: {start_date} to {end_date}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"❌ Scraper failed: {result.stderr}")
        return False

    logger.info(f"✅ Scraper completed: {start_date} to {end_date}")
    return True

def run_qc_validation(start_date, end_date, output_file):
    """Run QC validation for a date range."""
    cmd = [
        'python3', 'qc_validator.py',
        '--start-date', start_date,
        '--end-date', end_date,
        '--output', output_file
    ]

    logger.info(f"🔍 QC Validating: {start_date} to {end_date}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"❌ QC validation failed: {result.stderr}")
        return False, None

    # Load validation results
    try:
        with open(output_file, 'r') as f:
            qc_data = json.load(f)

        pass_rate = qc_data['summary']['pass_rate']
        logger.info(f"✅ QC Pass Rate: {pass_rate}%")

        return pass_rate == 100.0, qc_data
    except Exception as e:
        logger.error(f"❌ Failed to parse QC results: {e}")
        return False, None

def main():
    """Main automation workflow."""
    logger.info("=" * 80)
    logger.info("🚀 AUTOMATED 2024 FULL YEAR SCRAPER")
    logger.info("=" * 80)
    logger.info("SPEC 006 Compliant: 100% Accuracy Mandate")
    logger.info("Workflow: Scrape → QC Validate → Verify 100% Pass")
    logger.info("=" * 80)

    # Check for resume flag
    resume_from = 1
    if len(sys.argv) > 2 and sys.argv[1] == '--resume-from':
        resume_from = int(sys.argv[2])
        logger.info(f"📍 Resuming from batch {resume_from}")

    # Generate all batches
    batches = generate_date_batches(year=2024, batch_size=5)
    total_batches = len(batches)

    logger.info(f"📊 Total batches: {total_batches} (366 days, 5-day batches)")
    logger.info("")

    # Track overall progress
    progress = {
        'total_batches': total_batches,
        'completed_batches': 0,
        'failed_batches': 0,
        'total_dates': 0,
        'total_trips': 0,
        'batch_results': []
    }

    # Process each batch
    for batch in batches:
        if batch['batch_num'] < resume_from:
            logger.info(f"⏭️  Skipping batch {batch['batch_num']} (resume from {resume_from})")
            continue

        batch_num = batch['batch_num']
        start_date = batch['start_date']
        end_date = batch['end_date']

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📦 BATCH {batch_num}/{total_batches}")
        logger.info(f"📅 Date range: {start_date} to {end_date} ({batch['days']} days)")
        logger.info("=" * 80)

        # Step 1: Scrape
        if not run_scraper(start_date, end_date):
            logger.error(f"❌ BATCH {batch_num} FAILED: Scraper error")
            progress['failed_batches'] += 1
            break

        # Step 2: QC Validate
        qc_output = f"qc_batch{batch_num:03d}_2024.json"
        passed, qc_data = run_qc_validation(start_date, end_date, qc_output)

        if not passed:
            logger.error(f"❌ BATCH {batch_num} FAILED: QC validation did not pass 100%")
            progress['failed_batches'] += 1

            # Save failure report
            with open(f'FAILED_BATCH_{batch_num}.json', 'w') as f:
                json.dump({
                    'batch_num': batch_num,
                    'start_date': start_date,
                    'end_date': end_date,
                    'qc_data': qc_data
                }, f, indent=2)

            logger.error(f"📄 Failure details saved to FAILED_BATCH_{batch_num}.json")
            logger.error("🛑 STOPPING AUTOMATION - REQUIRES INVESTIGATION")
            break

        # Step 3: Update progress
        progress['completed_batches'] += 1
        progress['total_dates'] += qc_data['summary']['total_dates']

        batch_result = {
            'batch_num': batch_num,
            'start_date': start_date,
            'end_date': end_date,
            'days': batch['days'],
            'pass_rate': qc_data['summary']['pass_rate'],
            'dates_validated': qc_data['summary']['total_dates'],
            'qc_file': qc_output
        }
        progress['batch_results'].append(batch_result)

        logger.info(f"✅ BATCH {batch_num} COMPLETE: 100% pass rate")
        logger.info(f"📊 Overall progress: {progress['completed_batches']}/{total_batches} batches ({progress['completed_batches']/total_batches*100:.1f}%)")

    # Generate final report
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 FINAL SUMMARY")
    logger.info("=" * 80)

    if progress['failed_batches'] == 0 and progress['completed_batches'] == total_batches:
        logger.info("🎉 100% SUCCESS - ALL 2024 DATA SCRAPED AND VALIDATED!")
        logger.info(f"✅ Total batches: {progress['completed_batches']}/{total_batches}")
        logger.info(f"✅ Total dates validated: {progress['total_dates']}")
        logger.info(f"✅ QC pass rate: 100%")

        # Save comprehensive report
        report_file = 'SCRAPE_2024_FINAL_REPORT.json'
        with open(report_file, 'w') as f:
            json.dump(progress, f, indent=2)

        logger.info(f"📄 Comprehensive report saved: {report_file}")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("❌ SCRAPING INCOMPLETE OR FAILED")
        logger.error(f"⚠️  Completed batches: {progress['completed_batches']}/{total_batches}")
        logger.error(f"⚠️  Failed batches: {progress['failed_batches']}")

        # Save partial progress report
        report_file = f'SCRAPE_2024_PARTIAL_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(progress, f, indent=2)

        logger.error(f"📄 Partial progress saved: {report_file}")
        logger.error("=" * 80)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
