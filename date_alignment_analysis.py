#!/usr/bin/env python3
"""
Date Alignment Analysis for 2025
Investigate date mismatch issues where trips appear on wrong dates
"""

from supabase import create_client
from datetime import datetime, timedelta
from collections import defaultdict

class DateAlignmentAnalysis:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

    def analyze_multi_day_trip_dates(self):
        """Analyze multi-day trips for date alignment issues"""
        print("🗓️ DATE ALIGNMENT ANALYSIS - MULTI-DAY TRIPS")
        print("=" * 60)

        # Get all 2025 trips
        response = self.supabase.table('trips').select(
            'id, trip_date, trip_duration, anglers, total_fish, boats(name)'
        ).gte('trip_date', '2025-01-01').lte('trip_date', '2025-09-23').execute()

        trips = response.data

        # Categorize by trip duration
        multi_day_trips = defaultdict(list)

        for trip in trips:
            duration = trip.get('trip_duration', '')
            if 'Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day']:
                # Extract numeric duration (e.g., "2 Day" -> 2, "1.5 Day" -> 1.5)
                try:
                    if duration == 'Overnight':
                        days = 1
                    else:
                        days_str = duration.replace(' Day', '').strip()
                        days = float(days_str)

                    if days >= 1.5:  # Focus on trips 1.5 days or longer
                        multi_day_trips[duration].append({
                            'id': trip['id'],
                            'date': trip['trip_date'],
                            'boat': trip['boats']['name'],
                            'anglers': trip.get('anglers', 0),
                            'fish': trip.get('total_fish', 0),
                            'duration': duration
                        })
                except:
                    pass

        print(f"Multi-day trips found: {sum(len(trips) for trips in multi_day_trips.values())}")

        return multi_day_trips

    def check_date_patterns(self, multi_day_trips):
        """Check for suspicious date patterns in multi-day trips"""
        print(f"\n🔍 DATE PATTERN ANALYSIS")
        print("=" * 60)

        suspicious_patterns = []

        # Look for patterns where multi-day trips might be on wrong date
        # Pattern 1: Multi-day trip with 0 fish on departure date
        # Pattern 2: Multi-day trip appearing on what should be return date

        for duration, trips in multi_day_trips.items():
            for trip in trips:
                # Check if this looks like a return date (trip with catches)
                # but no corresponding departure date entry
                if trip['fish'] > 0:
                    # Try to find if there's a departure date entry
                    trip_date = datetime.strptime(trip['date'], '%Y-%m-%d')

                    # Calculate expected departure date
                    if '1.5' in duration:
                        expected_departure = trip_date - timedelta(days=1)
                    elif '2' in duration:
                        expected_departure = trip_date - timedelta(days=1)
                    elif '3' in duration:
                        expected_departure = trip_date - timedelta(days=2)
                    else:
                        continue

                    # Check if this might be a return-date recorded trip
                    # (High fish count suggests it's the return, not departure)
                    if trip['fish'] > 20:
                        suspicious_patterns.append({
                            'trip_id': trip['id'],
                            'recorded_date': trip['date'],
                            'boat': trip['boat'],
                            'duration': duration,
                            'fish': trip['fish'],
                            'issue': 'High fish count - possibly recorded on return date instead of departure'
                        })

        return suspicious_patterns

    def analyze_departure_return_mismatches(self):
        """Analyze trips that might be recorded on wrong dates"""
        print(f"\n📅 DEPARTURE/RETURN DATE MISMATCH ANALYSIS")
        print("=" * 60)

        # Get all trips ordered by date and boat
        response = self.supabase.table('trips').select(
            'id, trip_date, trip_duration, anglers, total_fish, boats(name)'
        ).gte('trip_date', '2025-01-01').lte('trip_date', '2025-09-23').order('trip_date').execute()

        trips = response.data

        # Group by boat to analyze patterns
        boat_trips = defaultdict(list)
        for trip in trips:
            boat_name = trip['boats']['name']
            boat_trips[boat_name].append(trip)

        mismatches = []

        for boat_name, trips in boat_trips.items():
            for i, trip in enumerate(trips):
                duration = trip.get('trip_duration', '')

                # Check for multi-day trips
                if 'Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day']:
                    trip_date = datetime.strptime(trip['trip_date'], '%Y-%m-%d')

                    # Look for impossible patterns
                    # E.g., Same boat on consecutive days with multi-day trips
                    if i > 0:
                        prev_trip = trips[i-1]
                        prev_date = datetime.strptime(prev_trip['trip_date'], '%Y-%m-%d')
                        prev_duration = prev_trip.get('trip_duration', '')

                        # Check if previous trip was multi-day
                        if 'Day' in prev_duration and prev_duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day']:
                            # Calculate expected return date of previous trip
                            if '1.5' in prev_duration:
                                prev_return = prev_date + timedelta(days=2)
                            elif '2' in prev_duration:
                                prev_return = prev_date + timedelta(days=2)
                            elif '3' in prev_duration:
                                prev_return = prev_date + timedelta(days=3)
                            else:
                                continue

                            # If current trip starts before previous trip returns
                            if trip_date < prev_return:
                                mismatches.append({
                                    'boat': boat_name,
                                    'trip1': {
                                        'id': prev_trip['id'],
                                        'date': prev_trip['trip_date'],
                                        'duration': prev_duration,
                                        'expected_return': prev_return.strftime('%Y-%m-%d')
                                    },
                                    'trip2': {
                                        'id': trip['id'],
                                        'date': trip['trip_date'],
                                        'duration': duration
                                    },
                                    'issue': 'Overlapping multi-day trips - impossible schedule'
                                })

        return mismatches

    def check_september_date_issues(self):
        """Specifically check September date alignment issues we discovered"""
        print(f"\n🚨 SEPTEMBER DATE ALIGNMENT ISSUES")
        print("=" * 60)

        # Check specific dates from September where we found misalignments
        problem_dates = [
            '2025-09-04',  # Electra appeared here but shouldn't have
            '2025-09-05',  # Multiple boats might be misaligned
            '2025-09-11',  # Potential date shift
            '2025-09-12',  # Potential date shift
        ]

        for date in problem_dates:
            print(f"\n📅 Checking {date}:")

            response = self.supabase.table('trips').select(
                'id, trip_date, trip_duration, anglers, total_fish, boats(name)'
            ).eq('trip_date', date).execute()

            if response.data:
                print(f"  Found {len(response.data)} trips:")
                for trip in response.data:
                    duration = trip.get('trip_duration', '')
                    if 'Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day']:
                        print(f"    ⚠️  {trip['boats']['name']}: {duration} trip with {trip.get('total_fish', 0)} fish")
                        print(f"       Trip ID: {trip['id']}, Anglers: {trip.get('anglers', 0)}")

    def run_comprehensive_date_analysis(self):
        """Run complete date alignment analysis"""
        print("🚨 COMPREHENSIVE DATE ALIGNMENT ANALYSIS FOR 2025")
        print("=" * 80)

        # Analyze multi-day trips
        multi_day_trips = self.analyze_multi_day_trip_dates()

        # Check date patterns
        suspicious_patterns = self.check_date_patterns(multi_day_trips)

        if suspicious_patterns:
            print(f"\n⚠️  SUSPICIOUS DATE PATTERNS FOUND: {len(suspicious_patterns)}")
            for i, pattern in enumerate(suspicious_patterns[:10], 1):
                print(f"{i}. {pattern['recorded_date']} - {pattern['boat']} ({pattern['duration']})")
                print(f"   Issue: {pattern['issue']}")
                print(f"   Fish: {pattern['fish']}")

        # Analyze departure/return mismatches
        mismatches = self.analyze_departure_return_mismatches()

        if mismatches:
            print(f"\n❌ IMPOSSIBLE SCHEDULES FOUND: {len(mismatches)}")
            for i, mismatch in enumerate(mismatches[:10], 1):
                print(f"{i}. {mismatch['boat']}:")
                print(f"   Trip 1: {mismatch['trip1']['date']} ({mismatch['trip1']['duration']}) → returns {mismatch['trip1']['expected_return']}")
                print(f"   Trip 2: {mismatch['trip2']['date']} ({mismatch['trip2']['duration']}) - CONFLICT!")

        # Check September specific issues
        self.check_september_date_issues()

        # Summary
        print(f"\n📋 DATE ALIGNMENT SUMMARY")
        print("=" * 60)
        print(f"Multi-day trips analyzed: {sum(len(trips) for trips in multi_day_trips.values())}")
        print(f"Suspicious return-date recordings: {len(suspicious_patterns)}")
        print(f"Impossible overlapping schedules: {len(mismatches)}")

        if suspicious_patterns or mismatches:
            print(f"\n🚨 CRITICAL FINDING:")
            print(f"Date alignment issues detected!")
            print(f"Multi-day trips may be recorded on return date instead of departure date")
            print(f"This could affect data accuracy for trip timing analysis")
        else:
            print(f"\n✅ No major date alignment issues detected")

        return {
            'multi_day_trips': sum(len(trips) for trips in multi_day_trips.values()),
            'suspicious_patterns': suspicious_patterns,
            'mismatches': mismatches
        }

def main():
    analyzer = DateAlignmentAnalysis()
    analyzer.run_comprehensive_date_analysis()

if __name__ == "__main__":
    main()