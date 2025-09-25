#!/usr/bin/env python3
"""
Enhanced Scraper Execution Script
Comprehensive solution to prevent Pacific Dawn-type data loss

This script integrates:
- Enhanced parsing for weight qualifiers
- Real-time data integrity validation
- Comprehensive monitoring and alerting
- Bulletproof error handling and recovery

Usage:
    python run_enhanced_scraper.py                    # Scrape today
    python run_enhanced_scraper.py --date 2025-09-24  # Scrape specific date
    python run_enhanced_scraper.py --health-check     # Check system health
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Ensure we can import our modules
sys.path.append(str(Path(__file__).parent))

from enhanced_scraper import EnhancedFishingScraper
from data_integrity_validator import DataIntegrityValidator
from scraper_monitor import ScraperMonitor

def setup_logging():
    """Configure comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_scraper.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Enhanced Fishing Data Scraper')
    parser.add_argument('--date', type=str, help='Date to scrape (YYYY-MM-DD), defaults to today')
    parser.add_argument('--health-check', action='store_true', help='Run system health check only')
    parser.add_argument('--validate-only', action='store_true', help='Run data validation without scraping')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🎣 Enhanced Fishing Scraper Starting")
    logger.info("=" * 60)

    # Initialize components
    monitor = ScraperMonitor()
    validator = DataIntegrityValidator()

    try:
        if args.health_check:
            # Health check mode
            logger.info("Running system health check...")
            health_report = monitor.generate_health_report()

            print("\n📊 SYSTEM HEALTH REPORT")
            print("=" * 40)
            print(f"Status: {health_report['status'].upper()}")
            print(f"Message: {health_report['message']}")
            print(f"Average Success Rate: {health_report['metrics']['avg_success_rate']}%")
            print(f"Active Critical Alerts: {health_report['metrics']['active_critical_alerts']}")

            if health_report['active_alerts']:
                print("\n🚨 ACTIVE ALERTS:")
                for alert in health_report['active_alerts']:
                    print(f"  - {alert['severity']}: {alert['message']}")

            return 0 if health_report['status'] == 'healthy' else 1

        elif args.validate_only:
            # Validation-only mode
            target_date = args.date or datetime.now().strftime('%Y-%m-%d')
            logger.info(f"Running data validation for {target_date}...")

            audit_report = validator.audit_daily_data_quality(target_date)

            print(f"\n📋 DATA QUALITY AUDIT - {target_date}")
            print("=" * 50)
            print(f"Status: {audit_report['status'].upper()}")
            print(f"Total Trips: {audit_report['total_trips']}")
            print(f"Problematic Trips: {len(audit_report.get('problematic_trips', []))}")
            print(f"Zero Fish (High Anglers): {audit_report['zero_fish_high_anglers']}")

            if audit_report.get('problematic_trips'):
                print("\n⚠️  PROBLEMATIC TRIPS:")
                for trip in audit_report['problematic_trips']:
                    print(f"  - {trip['boat_name']}: {trip['anglers']} anglers, {trip['total_fish']} fish - {', '.join(trip['issues'])}")

            return 0 if audit_report['status'] in ['healthy', 'warning'] else 1

        else:
            # Full scraping mode
            target_date = args.date or datetime.now().strftime('%Y-%m-%d')
            logger.info(f"Starting enhanced scraping for {target_date}")

            # Initialize scraper
            scraper = EnhancedFishingScraper()

            # Run scraping with comprehensive monitoring
            logger.info("🔄 Executing scraping process...")
            stats = scraper.run_daily_scrape(target_date)

            # Record metrics and process alerts
            logger.info("📊 Recording metrics and processing alerts...")
            metric = monitor.record_scraping_session({
                'trips_attempted': stats.trips_attempted,
                'trips_successful': stats.trips_successful,
                'trips_failed': stats.trips_failed,
                'zero_fish_high_anglers': stats.zero_fish_high_anglers,
                'weight_qualifiers_found': stats.weight_qualifiers_found,
                'success_rate': stats.get_success_rate()
            }, target_date)

            # Run post-scraping validation
            logger.info("🔍 Running post-scraping data quality audit...")
            audit_report = validator.audit_daily_data_quality(target_date)

            # Generate summary
            print("\n" + "=" * 60)
            print("🎣 ENHANCED SCRAPING COMPLETE")
            print("=" * 60)
            print(f"Date: {target_date}")
            print(f"Trips Attempted: {stats.trips_attempted}")
            print(f"Trips Successful: {stats.trips_successful}")
            print(f"Success Rate: {stats.get_success_rate():.1f}%")
            print(f"Weight Qualifiers Found: {stats.weight_qualifiers_found}")
            print(f"Data Quality Score: {metric.data_quality_score:.1f}/100")

            if metric.alerts_triggered:
                print("\n🚨 ALERTS TRIGGERED:")
                for alert in metric.alerts_triggered:
                    print(f"  - {alert}")

            if audit_report['status'] == 'critical':
                print(f"\n⚠️  CRITICAL DATA QUALITY ISSUES DETECTED")
                print(f"Zero Fish (High Anglers): {audit_report['zero_fish_high_anglers']}")
                logger.critical("CRITICAL DATA QUALITY ISSUES - MANUAL REVIEW REQUIRED")
                return 1

            elif audit_report['status'] == 'warning':
                print(f"\n⚠️  Data quality concerns detected - review recommended")
                return 2

            else:
                print(f"\n✅ Scraping completed successfully with good data quality")
                return 0

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Critical error during scraping: {e}")
        logger.exception("Full error details:")
        return 1
    finally:
        logger.info("Enhanced scraper session ended")

if __name__ == "__main__":
    sys.exit(main())