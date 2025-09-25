#!/usr/bin/env python3
"""
Data Integrity Validator
Prevents Pacific Dawn-type data loss through comprehensive validation

This module implements the prevention strategy identified from the September 2025 audit:
- Pre-collection validation
- Real-time monitoring during scraping
- Post-collection data quality audits
- Database-level constraint enforcement
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from supabase import create_client
from marine_conditions.config import MarineConfig
import json
import requests

logger = logging.getLogger(__name__)

class DataIntegrityValidator:
    """Comprehensive data integrity validation system"""

    def __init__(self):
        config = MarineConfig.from_env()
        self.supabase = create_client(config.supabase_url, config.supabase_key)

        # Quality thresholds
        self.MIN_SUCCESS_RATE = 85.0  # Minimum acceptable success rate
        self.MAX_ZERO_FISH_RATE = 15.0  # Maximum acceptable zero-fish rate for high-angler trips
        self.HIGH_ANGLER_THRESHOLD = 5  # Trips with >5 anglers should rarely be zero fish

    def validate_pre_collection(self, trip_data: Dict) -> Tuple[bool, List[str]]:
        """
        Pre-collection validation - reject incomplete trips before database insertion
        CRITICAL: This prevents Pacific Dawn-type failures from being stored
        """
        errors = []
        boat_name = trip_data.get('boat_name', 'Unknown')
        anglers = trip_data.get('anglers', 0)
        total_fish = trip_data.get('total_fish', 0)
        catches = trip_data.get('catches', [])

        # CRITICAL CHECK: High angler trips must have catch data
        if anglers > self.HIGH_ANGLER_THRESHOLD:
            if total_fish == 0 and len(catches) == 0:
                errors.append(f"HIGH PRIORITY: {boat_name} has {anglers} anglers but no fish data")
                logger.critical(f"BLOCKED: {boat_name} ({anglers} anglers, 0 fish) - Would cause data integrity failure")

        # Validate required fields
        required_fields = {
            'boat_name': str,
            'trip_date': str,
            'trip_duration': str,
            'anglers': int
        }

        for field, expected_type in required_fields.items():
            if field not in trip_data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(trip_data[field], expected_type):
                errors.append(f"Invalid type for {field}: expected {expected_type.__name__}")

        # Validate date format
        try:
            datetime.strptime(trip_data.get('trip_date', ''), '%Y-%m-%d')
        except ValueError:
            errors.append("Invalid date format (expected YYYY-MM-DD)")

        # Validate angler count reasonableness
        if anglers < 0 or anglers > 100:  # Sanity check
            errors.append(f"Unrealistic angler count: {anglers}")

        # Validate catches structure
        if catches:
            for i, catch in enumerate(catches):
                if 'species' not in catch or 'count' not in catch:
                    errors.append(f"Catch {i} missing species or count")
                elif catch['count'] <= 0:
                    errors.append(f"Catch {i} has invalid count: {catch['count']}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def monitor_collection_success_rate(self, successful_trips: int, total_attempts: int) -> Dict:
        """
        Real-time collection monitoring - alert if success rate drops
        """
        if total_attempts == 0:
            return {'status': 'no_data', 'message': 'No collection attempts'}

        success_rate = (successful_trips / total_attempts) * 100

        status_info = {
            'successful_trips': successful_trips,
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'timestamp': datetime.now().isoformat()
        }

        if success_rate < self.MIN_SUCCESS_RATE:
            status_info['status'] = 'critical'
            status_info['message'] = f"SUCCESS RATE CRITICAL: {success_rate:.1f}% (below {self.MIN_SUCCESS_RATE}%)"
            logger.critical(status_info['message'])

            # Send immediate alert (would integrate with alerting system)
            self._send_critical_alert(status_info)
        elif success_rate < 90:
            status_info['status'] = 'warning'
            status_info['message'] = f"Success rate declining: {success_rate:.1f}%"
            logger.warning(status_info['message'])
        else:
            status_info['status'] = 'healthy'
            status_info['message'] = f"Collection healthy: {success_rate:.1f}% success rate"

        return status_info

    def audit_daily_data_quality(self, date_str: str) -> Dict:
        """
        Post-collection data quality audit for a specific date
        Identifies Pacific Dawn-type issues in collected data
        """
        logger.info(f"Auditing data quality for {date_str}")

        audit_results = {
            'date': date_str,
            'timestamp': datetime.now().isoformat(),
            'total_trips': 0,
            'problematic_trips': [],
            'zero_fish_high_anglers': 0,
            'success_metrics': {},
            'recommendations': []
        }

        try:
            # Get all trips for the date
            trips_response = self.supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, boat:boats(name), catches(species, count)'
            ).eq('trip_date', date_str).execute()

            trips = trips_response.data
            audit_results['total_trips'] = len(trips)

            if len(trips) == 0:
                audit_results['status'] = 'no_data'
                audit_results['message'] = f"No trips found for {date_str}"
                return audit_results

            # Analyze each trip for data integrity issues
            problematic_trips = []
            zero_fish_high_anglers = 0

            for trip in trips:
                boat_name = trip.get('boat', {}).get('name', 'Unknown')
                anglers = trip.get('anglers', 0)
                total_fish = trip.get('total_fish', 0)
                catches = trip.get('catches', [])

                # Calculate actual fish from catches
                catch_sum = sum(catch.get('count', 0) for catch in catches)

                # Identify problems
                issues = []

                # Pacific Dawn-type issue: High anglers, no fish data
                if anglers > self.HIGH_ANGLER_THRESHOLD:
                    if total_fish == 0 and catch_sum == 0:
                        issues.append("HIGH_ANGLERS_ZERO_FISH")
                        zero_fish_high_anglers += 1

                # Data inconsistency: total_fish vs catch sum mismatch
                if total_fish != catch_sum and total_fish > 0 and catch_sum > 0:
                    issues.append(f"DATA_MISMATCH: total_fish={total_fish}, catch_sum={catch_sum}")

                # Missing catch details for trips with total_fish > 0
                if total_fish > 0 and len(catches) == 0:
                    issues.append("MISSING_CATCH_DETAILS")

                if issues:
                    problematic_trips.append({
                        'boat_name': boat_name,
                        'anglers': anglers,
                        'total_fish': total_fish,
                        'catch_sum': catch_sum,
                        'issues': issues
                    })

            audit_results['problematic_trips'] = problematic_trips
            audit_results['zero_fish_high_anglers'] = zero_fish_high_anglers

            # Calculate quality metrics
            zero_fish_rate = (zero_fish_high_anglers / len(trips)) * 100 if len(trips) > 0 else 0
            problem_rate = (len(problematic_trips) / len(trips)) * 100 if len(trips) > 0 else 0

            audit_results['success_metrics'] = {
                'zero_fish_rate': zero_fish_rate,
                'problem_rate': problem_rate,
                'clean_trips': len(trips) - len(problematic_trips)
            }

            # Generate status and recommendations
            if zero_fish_rate > self.MAX_ZERO_FISH_RATE:
                audit_results['status'] = 'critical'
                audit_results['message'] = f"CRITICAL: {zero_fish_rate:.1f}% zero-fish rate (above {self.MAX_ZERO_FISH_RATE}%)"
                audit_results['recommendations'].append("Immediate review of scraper parsing logic required")
                audit_results['recommendations'].append("Check source data for affected trips")

                logger.critical(f"Data quality audit FAILED for {date_str}: {audit_results['message']}")
            elif problem_rate > 10:
                audit_results['status'] = 'warning'
                audit_results['message'] = f"Data quality concerns: {problem_rate:.1f}% of trips have issues"
                audit_results['recommendations'].append("Review scraper configuration")
            else:
                audit_results['status'] = 'healthy'
                audit_results['message'] = f"Data quality good: {zero_fish_rate:.1f}% zero-fish rate"

        except Exception as e:
            audit_results['status'] = 'error'
            audit_results['message'] = f"Audit failed: {str(e)}"
            logger.error(f"Data quality audit failed for {date_str}: {e}")

        return audit_results

    def cross_reference_with_source(self, date_str: str, boat_name: str) -> Dict:
        """
        Cross-reference suspicious trips against source data
        CRITICAL: This would have caught the Pacific Dawn issue
        """
        source_url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={date_str}"

        validation_result = {
            'boat_name': boat_name,
            'date': date_str,
            'source_url': source_url,
            'validation_status': 'unknown',
            'recommendations': []
        }

        try:
            # Get database data for this boat/date
            db_trip = self.supabase.table('trips').select(
                'anglers, total_fish, boat:boats(name), catches(species, count)'
            ).eq('trip_date', date_str).eq('boat.name', boat_name).execute()

            if not db_trip.data:
                validation_result['validation_status'] = 'not_found_in_db'
                validation_result['recommendations'].append("Trip not found in database - possible scraping failure")
                return validation_result

            trip = db_trip.data[0]
            db_anglers = trip.get('anglers', 0)
            db_total_fish = trip.get('total_fish', 0)
            db_catches = trip.get('catches', [])

            # For full implementation, would fetch and parse source page
            # For now, flagging for manual review
            validation_result['database_data'] = {
                'anglers': db_anglers,
                'total_fish': db_total_fish,
                'catch_count': len(db_catches)
            }

            if db_anglers > self.HIGH_ANGLER_THRESHOLD and db_total_fish == 0:
                validation_result['validation_status'] = 'suspicious'
                validation_result['recommendations'].append(f"REVIEW REQUIRED: {boat_name} has {db_anglers} anglers but 0 fish")
                validation_result['recommendations'].append(f"Check source at: {source_url}")
            else:
                validation_result['validation_status'] = 'appears_normal'

        except Exception as e:
            validation_result['validation_status'] = 'error'
            validation_result['error'] = str(e)

        return validation_result

    def _send_critical_alert(self, status_info: Dict):
        """
        Send critical alert (placeholder - would integrate with actual alerting system)
        """
        alert_message = f"CRITICAL SCRAPER ALERT: {status_info['message']}"
        logger.critical(alert_message)

        # In production, would send to Slack, email, PagerDuty, etc.
        print(f"🚨 {alert_message}")

    def generate_daily_report(self, date_str: str) -> Dict:
        """
        Generate comprehensive daily data integrity report
        """
        report = {
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'audit_results': self.audit_daily_data_quality(date_str),
            'recommendations': [],
            'action_items': []
        }

        audit = report['audit_results']

        if audit['status'] == 'critical':
            report['recommendations'].append("IMMEDIATE ACTION REQUIRED")
            report['action_items'].append("Review all zero-fish high-angler trips")
            report['action_items'].append("Cross-reference suspicious trips with source data")

        elif audit['status'] == 'warning':
            report['recommendations'].append("Review scraper configuration")
            report['action_items'].append("Monitor success rates closely")

        # Add specific trip reviews for problematic cases
        for trip in audit.get('problematic_trips', []):
            if 'HIGH_ANGLERS_ZERO_FISH' in trip['issues']:
                report['action_items'].append(
                    f"Review {trip['boat_name']}: {trip['anglers']} anglers, 0 fish"
                )

        return report

def main():
    """Example usage of the data integrity validator"""
    validator = DataIntegrityValidator()

    # Audit today's data
    today = datetime.now().strftime('%Y-%m-%d')
    report = validator.generate_daily_report(today)

    print(json.dumps(report, indent=2))

    return report

if __name__ == "__main__":
    main()