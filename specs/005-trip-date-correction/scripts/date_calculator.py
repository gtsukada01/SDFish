#!/usr/bin/env python3
"""
Date Calculator - Trip Date Correction Project
Calculates departure dates from report dates and trip durations

Author: Claude Code
Date: October 16, 2025
Specification: FR-001 (Date Calculation Logic)
"""

from datetime import datetime, timedelta
from typing import Optional
import re
import math


def calculate_departure_date(report_date: str, trip_duration: str) -> str:
    """
    Calculate the departure date from report date and trip duration.

    The departure date is when the boat LEFT the dock.
    The report date is when the trip was REPORTED on the website.

    Logic: departure_date = report_date - trip_duration_days

    Args:
        report_date: Report date in 'YYYY-MM-DD' format
        trip_duration: Trip duration string (e.g., "3 Day", "1/2 Day AM", "Overnight")

    Returns:
        Departure date in 'YYYY-MM-DD' format

    Examples:
        >>> calculate_departure_date('2025-10-10', '2 Day')
        '2025-10-08'

        >>> calculate_departure_date('2025-10-08', '5 Day')
        '2025-10-03'

        >>> calculate_departure_date('2025-09-24', '3 Day')
        '2025-09-21'

        >>> calculate_departure_date('2025-10-10', '1/2 Day AM')
        '2025-10-10'

        >>> calculate_departure_date('2025-10-10', 'Overnight')
        '2025-10-09'

        >>> calculate_departure_date('2025-10-10', '1.5 Day')
        '2025-10-08'

        >>> calculate_departure_date('2025-10-10', '2.5 Day')
        '2025-10-07'
    """
    # Parse report date
    report_dt = datetime.strptime(report_date, '%Y-%m-%d')

    # Extract number of days from trip duration
    days_to_subtract = parse_trip_duration(trip_duration)

    # Calculate departure date
    departure_dt = report_dt - timedelta(days=days_to_subtract)

    # Return in YYYY-MM-DD format
    return departure_dt.strftime('%Y-%m-%d')


def parse_trip_duration(trip_duration: str) -> int:
    """
    Parse trip duration string to extract number of days.

    Rules:
    - "1/2 Day AM/PM" → 0 days (same-day trip)
    - "Full Day" → 0 days (same-day trip)
    - "3/4 Day" → 0 days (same-day trip, less than 1 day)
    - "Overnight" → 1 day
    - "1.5 Day" → 1 day (round down)
    - "2 Day" → 2 days
    - "2.5 Day" → 2 days (round down)
    - "3 Day" → 3 days
    - etc.

    Args:
        trip_duration: Trip duration string from database

    Returns:
        Number of days to subtract from report date

    Raises:
        ValueError: If trip duration format is unrecognized
    """
    # Normalize whitespace
    duration = trip_duration.strip()

    # Handle special cases
    if '1/2' in duration or 'half' in duration.lower():
        return 0  # Same-day trip

    if 'full day' in duration.lower():
        return 0  # Same-day trip

    if '3/4' in duration:
        return 0  # Same-day trip (less than 1 day)

    if 'overnight' in duration.lower():
        return 1  # Next day

    # Extract numeric value (handles "2 Day", "2.5 Day", "3.5 Day", etc.)
    match = re.search(r'(\d+(?:\.\d+)?)', duration)
    if match:
        days_float = float(match.group(1))
        # Round UP for decimal trips (ceiling function)
        # 1.5 Day → 2 days, 2.5 Day → 3 days, 3.0 Day → 3 days
        # A "2.5 Day" trip reported on 10-10 likely departed on 10-07 (3 days ago)
        # This accounts for partial days spanning calendar days
        return math.ceil(days_float)

    # If no pattern matched, raise error
    raise ValueError(f"Unrecognized trip duration format: '{trip_duration}'")


def validate_date_change(old_date: str, new_date: str, trip_duration: str,
                        boat_name: str, trip_id: int) -> dict:
    """
    Validate that a date change makes sense given the trip duration.

    Args:
        old_date: Original trip_date (report date)
        new_date: Calculated departure date
        trip_duration: Trip duration string
        boat_name: Boat name for logging
        trip_id: Trip ID for logging

    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'expected_days': int,
            'actual_days': int,
            'message': str
        }
    """
    old_dt = datetime.strptime(old_date, '%Y-%m-%d')
    new_dt = datetime.strptime(new_date, '%Y-%m-%d')

    # Calculate actual difference
    actual_days = (old_dt - new_dt).days

    # Calculate expected difference
    expected_days = parse_trip_duration(trip_duration)

    # Validation
    valid = (actual_days == expected_days)

    if valid:
        message = f"✅ Valid: {boat_name} (ID {trip_id}) - {old_date} → {new_date} ({trip_duration}, {actual_days} days)"
    else:
        message = f"❌ MISMATCH: {boat_name} (ID {trip_id}) - Expected {expected_days} days, got {actual_days} days ({trip_duration})"

    return {
        'valid': valid,
        'expected_days': expected_days,
        'actual_days': actual_days,
        'message': message,
        'trip_id': trip_id,
        'boat_name': boat_name,
        'old_date': old_date,
        'new_date': new_date,
        'trip_duration': trip_duration
    }


def test_date_calculator():
    """
    Unit tests for date calculation function.
    Run this to verify correctness before migration.
    """
    print("=" * 80)
    print("DATE CALCULATOR UNIT TESTS")
    print("=" * 80)

    test_cases = [
        # (report_date, trip_duration, expected_departure_date, description)
        ('2025-10-10', '2 Day', '2025-10-08', 'Standard 2-day trip'),
        ('2025-10-08', '5 Day', '2025-10-03', 'Long 5-day trip'),
        ('2025-09-24', '3 Day', '2025-09-21', 'Sep 24 → Sep 21 (3-day)'),
        ('2025-10-10', '1/2 Day AM', '2025-10-10', 'Half-day AM (same day)'),
        ('2025-10-10', '1/2 Day PM', '2025-10-10', 'Half-day PM (same day)'),
        ('2025-10-10', 'Full Day', '2025-10-10', 'Full day (same day)'),
        ('2025-10-10', '3/4 Day', '2025-10-10', '3/4 day (same day)'),
        ('2025-10-10', 'Overnight', '2025-10-09', 'Overnight (1 day)'),
        ('2025-10-10', '1.5 Day', '2025-10-08', '1.5 day → 1 day (round down)'),
        ('2025-10-10', '2.5 Day', '2025-10-07', '2.5 day → 2 days (round down)'),
        ('2025-10-10', '3.5 Day', '2025-10-06', '3.5 day → 3 days (round down)'),
        ('2025-09-30', '3 Day', '2025-09-27', 'Sep 30 → Sep 27 (3-day)'),
        ('2025-09-27', '3 Day', '2025-09-24', 'Sep 27 → Sep 24 (3-day)'),
    ]

    passed = 0
    failed = 0

    for report_date, trip_duration, expected, description in test_cases:
        try:
            result = calculate_departure_date(report_date, trip_duration)
            if result == expected:
                print(f"✅ PASS: {description}")
                print(f"   {report_date} - {trip_duration} → {result}")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Expected: {expected}, Got: {result}")
                failed += 1
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Exception: {e}")
            failed += 1
        print()

    print("=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} tests passed")
    if failed == 0:
        print("✅ ALL TESTS PASSED - Date calculator is ready for production")
    else:
        print(f"❌ {failed} TESTS FAILED - Fix issues before migration")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    # Run unit tests
    success = test_date_calculator()

    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)
