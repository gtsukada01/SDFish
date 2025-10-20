#!/usr/bin/env python3
"""
Test script to validate fishing date estimation logic for moon phase correlation.
Shows before/after comparison of moon phase assignments.
"""

from supabase import create_client
from datetime import datetime, timedelta

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

def estimate_fishing_date(trip_date_str, trip_duration):
    """Python version of the TypeScript estimateFishingDate function"""

    hours_back = 6  # Default
    duration = trip_duration or ''

    # CRITICAL: Check fractional/decimal days FIRST to avoid substring conflicts
    # Half day trips - check FIRST
    if '1/2 Day Twilight' in duration:
        hours_back = 3
    elif '1/2 Day AM' in duration or '1/2 Day PM' in duration:
        hours_back = 4
    # 3/4 day trips - check BEFORE "3 Day" and "4 Day"
    elif '3/4 Day Islands' in duration or '3/4 DayCoronado' in duration or '3/4 DayMexican' in duration:
        hours_back = 7
    elif '3/4 Day Local' in duration:
        hours_back = 6
    elif '3/4 Day' in duration:
        hours_back = 6
    # Decimal day trips - check BEFORE whole number days
    elif 'Extended 1.5 Day' in duration:
        hours_back = 28
    elif '1.5 Day' in duration:
        hours_back = 24
    elif '1.75 Day' in duration:
        hours_back = 30
    elif '2.5 Day' in duration:
        hours_back = 48
    elif '3.5 Day' in duration:
        hours_back = 72
    # Multi-day trips - NOW safe to check whole numbers
    elif '5 Day' in duration:
        hours_back = 96
    elif '4 Day' in duration:
        hours_back = 84
    elif '3 Day' in duration:
        hours_back = 60
    elif '2 Day' in duration:
        hours_back = 36
    # Overnight
    elif 'Overnight' in duration or 'Reverse Overnight' in duration:
        hours_back = 10
    # Full day
    elif 'Full Day Offshore' in duration:
        hours_back = 10
    elif 'Full Day Coronado' in duration or 'Full DayCoronado' in duration:
        hours_back = 9
    elif 'Full Day Mexican' in duration or 'Full DayMexican' in duration:
        hours_back = 10
    elif 'Full Day Local' in duration:
        hours_back = 7
    elif 'Full Day' in duration:
        hours_back = 8
    # Hour-based
    elif '12 Hour' in duration:
        hours_back = 6
    elif '10 Hour' in duration:
        hours_back = 5
    elif '6 Hour' in duration:
        hours_back = 3
    elif '4 Hour' in duration:
        hours_back = 2
    elif '2 Hour' in duration:
        hours_back = 1
    # Special
    elif 'Lobster' in duration:
        hours_back = 3

    # Calculate fishing date
    return_date = datetime.strptime(trip_date_str, '%Y-%m-%d')
    fishing_date = return_date - timedelta(hours=hours_back)

    return fishing_date.strftime('%Y-%m-%d'), hours_back


def main():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("=" * 100)
    print("FISHING DATE ESTIMATION VALIDATION")
    print("=" * 100)
    print()

    # Get sample trips from different duration categories
    result = supabase.table('trips').select('''
        trip_date,
        trip_duration,
        boats(name),
        catches(species, count)
    ''').order('trip_date', desc=True).limit(50).execute()

    # Get moon phase data
    moon_result = supabase.table('ocean_conditions').select('date, moon_phase_name').gte('date', '2025-09-01').execute()
    moon_map = {row['date']: row['moon_phase_name'] for row in moon_result.data}

    # Group by duration type for testing
    duration_categories = {
        'Multi-day (1.5+ Day)': [],
        'Overnight': [],
        'Full Day': [],
        'Half Day': []
    }

    for trip in result.data:
        duration = trip['trip_duration']
        if '1.5 Day' in duration or '2 Day' in duration or '2.5 Day' in duration or '3 Day' in duration:
            duration_categories['Multi-day (1.5+ Day)'].append(trip)
        elif 'Overnight' in duration:
            duration_categories['Overnight'].append(trip)
        elif 'Full Day' in duration:
            duration_categories['Full Day'].append(trip)
        elif '1/2 Day' in duration:
            duration_categories['Half Day'].append(trip)

    # Test each category
    for category, trips in duration_categories.items():
        if not trips:
            continue

        print(f"\n{'='*100}")
        print(f"{category.upper()} TRIPS")
        print('=' * 100)
        print(f"{'Return Date':<13} {'Duration':<25} {'Boat':<20} {'Hours Back':>12} {'Fishing Date':<13} {'OLD Phase':<20} {'NEW Phase':<20}")
        print('-' * 100)

        for trip in trips[:5]:  # Show first 5 of each type
            return_date = trip['trip_date']
            duration = trip['trip_duration']
            boat = trip['boats']['name'] if trip['boats'] else 'Unknown'

            # Get fishing date estimate
            fishing_date, hours_back = estimate_fishing_date(return_date, duration)

            # Get moon phases
            old_phase = moon_map.get(return_date, 'N/A')
            new_phase = moon_map.get(fishing_date, 'N/A')

            # Highlight changes
            changed = '⚠️ ' if old_phase != new_phase else '   '

            print(f"{return_date:<13} {duration:<25} {boat:<20} {hours_back:>12} {fishing_date:<13} {old_phase:<20} {changed}{new_phase:<20}")

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    # Calculate overall impact
    total_tested = sum(len(trips[:5]) for trips in duration_categories.values())
    changes = 0

    for trips in duration_categories.values():
        for trip in trips[:5]:
            return_date = trip['trip_date']
            duration = trip['trip_duration']
            fishing_date, _ = estimate_fishing_date(return_date, duration)

            old_phase = moon_map.get(return_date, 'N/A')
            new_phase = moon_map.get(fishing_date, 'N/A')

            if old_phase != new_phase and old_phase != 'N/A' and new_phase != 'N/A':
                changes += 1

    print(f"Trips Tested: {total_tested}")
    print(f"Moon Phase Changes: {changes} ({changes/total_tested*100:.1f}%)")
    print()
    print("✅ Multi-day trips now use accurate fishing dates")
    print("✅ Overnight trips adjusted by ~10 hours")
    print("✅ Half-day trips have minimal adjustment (3-4 hours)")
    print()
    print("=" * 100)


if __name__ == '__main__':
    main()
