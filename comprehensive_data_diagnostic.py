#!/usr/bin/env python3
"""
Comprehensive Data Diagnostic: 2024 and 2025
Identify missing records, bad data, wrong dates, and other data quality issues
"""

from supabase import create_client
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class ComprehensiveDataDiagnostic:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

    def diagnose_missing_records(self):
        """Identify missing trip records and date gaps"""
        print("🔍 MISSING RECORDS DIAGNOSTIC")
        print("=" * 60)

        try:
            # Get all trips for 2024 and 2025
            response = self.supabase.table('trips').select(
                'trip_date, boats(name), total_fish, anglers, trip_duration'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2025-12-31').order('trip_date').execute()

            trips_by_date = defaultdict(list)
            for trip in response.data:
                trips_by_date[trip['trip_date']].append(trip)

            # Analyze by year
            for year in ['2024', '2025']:
                year_dates = [date for date in trips_by_date.keys() if date.startswith(year)]

                if not year_dates:
                    print(f"\n🚨 {year}: NO DATA FOUND")
                    continue

                start_date = min(year_dates)
                end_date = max(year_dates)
                print(f"\n📅 {year} DATE RANGE: {start_date} to {end_date}")

                # Check for missing dates
                current = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                missing_dates = []
                low_activity_dates = []

                while current <= end:
                    date_str = current.strftime('%Y-%m-%d')
                    if date_str not in trips_by_date:
                        missing_dates.append(date_str)
                    elif len(trips_by_date[date_str]) < 5:  # Suspiciously low activity
                        low_activity_dates.append((date_str, len(trips_by_date[date_str])))
                    current += timedelta(days=1)

                total_days = (end - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
                coverage = ((total_days - len(missing_dates)) / total_days) * 100

                print(f"Total dates with data: {len(year_dates)}")
                print(f"Missing dates: {len(missing_dates)}")
                print(f"Coverage: {coverage:.1f}%")

                if missing_dates:
                    print(f"Sample missing dates: {missing_dates[:10]}")

                if low_activity_dates:
                    print(f"Low activity dates (sample): {low_activity_dates[:5]}")

        except Exception as e:
            print(f"❌ Error diagnosing missing records: {e}")

    def diagnose_bad_data(self):
        """Identify bad data: null values, impossible values, inconsistencies"""
        print(f"\n🔍 BAD DATA DIAGNOSTIC")
        print("=" * 60)

        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, boats(name), total_fish, anglers, trip_duration'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2025-12-31').execute()

            bad_data_issues = {
                'negative_fish': [],
                'excessive_fish': [],
                'negative_anglers': [],
                'excessive_anglers': [],
                'null_boat_names': [],
                'invalid_dates': [],
                'null_fish': [],
                'null_anglers': [],
                'impossible_combinations': []
            }

            for trip in response.data:
                trip_id = trip['id']
                date = trip['trip_date']
                boat_name = trip['boats']['name'] if trip['boats'] else None
                total_fish = trip.get('total_fish', 0)
                anglers = trip.get('anglers', 0)
                duration = trip.get('trip_duration', '')

                # Check for bad data
                if total_fish is not None and total_fish < 0:
                    bad_data_issues['negative_fish'].append((trip_id, date, boat_name, total_fish))

                if total_fish is not None and total_fish > 2000:  # Excessive fish count
                    bad_data_issues['excessive_fish'].append((trip_id, date, boat_name, total_fish))

                if anglers is not None and anglers < 0:
                    bad_data_issues['negative_anglers'].append((trip_id, date, boat_name, anglers))

                if anglers is not None and anglers > 100:  # Excessive angler count
                    bad_data_issues['excessive_anglers'].append((trip_id, date, boat_name, anglers))

                if not boat_name or boat_name.strip() == '':
                    bad_data_issues['null_boat_names'].append((trip_id, date))

                if total_fish is None:
                    bad_data_issues['null_fish'].append((trip_id, date, boat_name))

                if anglers is None:
                    bad_data_issues['null_anglers'].append((trip_id, date, boat_name))

                # Check for impossible combinations
                if total_fish is not None and anglers is not None:
                    if total_fish > 0 and anglers == 0:  # Fish caught with no anglers
                        bad_data_issues['impossible_combinations'].append((trip_id, date, boat_name, f"{total_fish} fish, {anglers} anglers"))

            # Report bad data
            total_issues = sum(len(issues) for issues in bad_data_issues.values())
            print(f"Total bad data issues found: {total_issues}")

            for issue_type, issues in bad_data_issues.items():
                if issues:
                    print(f"\n🚨 {issue_type.upper().replace('_', ' ')}: {len(issues)} cases")
                    for issue in issues[:5]:  # Show first 5 examples
                        print(f"  {issue}")

        except Exception as e:
            print(f"❌ Error diagnosing bad data: {e}")

    def diagnose_wrong_dates(self):
        """Identify wrong dates: future dates, impossible date sequences"""
        print(f"\n🔍 WRONG DATES DIAGNOSTIC")
        print("=" * 60)

        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, boats(name), trip_duration, total_fish'
            ).gte('trip_date', '2024-01-01').order('trip_date').execute()

            today = datetime.now().strftime('%Y-%m-%d')
            wrong_date_issues = {
                'future_dates': [],
                'invalid_date_formats': [],
                'impossible_sequences': []
            }

            boat_last_seen = {}

            for trip in response.data:
                trip_id = trip['id']
                date = trip['trip_date']
                boat_name = trip['boats']['name'] if trip['boats'] else 'Unknown'
                duration = trip.get('trip_duration', '')

                # Check for future dates
                if date > today:
                    wrong_date_issues['future_dates'].append((trip_id, date, boat_name))

                # Check for impossible sequences (same boat on consecutive days with multi-day trips)
                if 'Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day']:
                    if boat_name in boat_last_seen:
                        last_date = boat_last_seen[boat_name]['date']
                        last_duration = boat_last_seen[boat_name]['duration']

                        # Calculate expected return date from last trip
                        if '1.5' in last_duration or '2 Day' in last_duration:
                            expected_days = 2
                        elif '3' in last_duration:
                            expected_days = 3
                        elif '4' in last_duration:
                            expected_days = 4
                        elif '5' in last_duration:
                            expected_days = 5
                        else:
                            expected_days = 1

                        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                        current_date_obj = datetime.strptime(date, '%Y-%m-%d')
                        expected_return = last_date_obj + timedelta(days=expected_days)

                        if current_date_obj < expected_return:
                            wrong_date_issues['impossible_sequences'].append({
                                'boat': boat_name,
                                'last_trip': f"{last_date} ({last_duration})",
                                'current_trip': f"{date} ({duration})",
                                'issue': f"Boat can't start new trip before {expected_return.strftime('%Y-%m-%d')}"
                            })

                boat_last_seen[boat_name] = {'date': date, 'duration': duration}

            # Report wrong dates
            total_issues = sum(len(issues) for issues in wrong_date_issues.values())
            print(f"Total wrong date issues found: {total_issues}")

            for issue_type, issues in wrong_date_issues.items():
                if issues:
                    print(f"\n🚨 {issue_type.upper().replace('_', ' ')}: {len(issues)} cases")
                    for issue in issues[:5]:  # Show first 5 examples
                        print(f"  {issue}")

        except Exception as e:
            print(f"❌ Error diagnosing wrong dates: {e}")

    def diagnose_data_consistency(self):
        """Identify data consistency issues"""
        print(f"\n🔍 DATA CONSISTENCY DIAGNOSTIC")
        print("=" * 60)

        try:
            # Get trips with catches
            trips_response = self.supabase.table('trips').select(
                'id, trip_date, boats(name), total_fish, catches(species, count)'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2025-12-31').execute()

            consistency_issues = {
                'fish_count_mismatch': [],
                'missing_catch_records': [],
                'orphan_catch_records': [],
                'species_inconsistencies': []
            }

            for trip in trips_response.data:
                trip_id = trip['id']
                total_fish = trip.get('total_fish', 0) or 0
                catches = trip.get('catches', []) or []

                # Calculate sum of catches
                catch_sum = sum(catch.get('count', 0) or 0 for catch in catches)

                # Check for mismatches
                if total_fish != catch_sum:
                    consistency_issues['fish_count_mismatch'].append({
                        'trip_id': trip_id,
                        'date': trip['trip_date'],
                        'boat': trip['boats']['name'] if trip['boats'] else 'Unknown',
                        'total_fish': total_fish,
                        'catch_sum': catch_sum,
                        'difference': total_fish - catch_sum
                    })

                # Check for missing catch records when fish > 0
                if total_fish > 0 and not catches:
                    consistency_issues['missing_catch_records'].append({
                        'trip_id': trip_id,
                        'date': trip['trip_date'],
                        'boat': trip['boats']['name'] if trip['boats'] else 'Unknown',
                        'total_fish': total_fish
                    })

            # Report consistency issues
            total_issues = sum(len(issues) for issues in consistency_issues.values())
            print(f"Total consistency issues found: {total_issues}")

            for issue_type, issues in consistency_issues.items():
                if issues:
                    print(f"\n🚨 {issue_type.upper().replace('_', ' ')}: {len(issues)} cases")
                    for issue in issues[:5]:  # Show first 5 examples
                        print(f"  {issue}")

        except Exception as e:
            print(f"❌ Error diagnosing data consistency: {e}")

    def diagnose_premium_boat_bias(self):
        """Diagnose premium boat vs day boat collection bias"""
        print(f"\n🔍 PREMIUM BOAT BIAS DIAGNOSTIC")
        print("=" * 60)

        premium_boats = [
            'Legend', 'Spirit of Adventure', 'Polaris Supreme', 'Apollo',
            'Highliner', 'Aztec', 'Islander', 'Pacific Dawn', 'Condor',
            'Top Gun 80', 'Pacific Queen', 'Pegasus', 'Tomahawk',
            'Fortune', 'Tribute', 'Excel', 'Oceanside 95'
        ]

        day_boats = [
            'New Seaforth', 'San Diego', 'Mission Belle', 'Daily Double',
            'Premier', 'Dolphin', 'Grande', 'Malihini', 'Southern Cal'
        ]

        try:
            for year in ['2024', '2025']:
                response = self.supabase.table('trips').select(
                    'boats(name), total_fish'
                ).gte('trip_date', f'{year}-01-01').lte('trip_date', f'{year}-12-31').execute()

                boat_stats = Counter()
                premium_stats = Counter()
                day_stats = Counter()

                for trip in response.data:
                    boat_name = trip['boats']['name'] if trip['boats'] else 'Unknown'
                    boat_stats[boat_name] += 1

                    if boat_name in premium_boats:
                        premium_stats[boat_name] += 1
                    elif boat_name in day_boats:
                        day_stats[boat_name] += 1

                premium_avg = sum(premium_stats.values()) / len(premium_boats) if premium_boats else 0
                day_avg = sum(day_stats.values()) / len(day_boats) if day_boats else 0
                bias_ratio = premium_avg / day_avg if day_avg > 0 else 0

                print(f"\n📊 {year} BOAT COLLECTION BIAS:")
                print(f"Premium boats average: {premium_avg:.1f} trips")
                print(f"Day boats average: {day_avg:.1f} trips")
                print(f"Bias ratio: {bias_ratio:.2f} (should be ~1.0)")

                if bias_ratio < 0.5:
                    print(f"🚨 SEVERE PREMIUM BOAT BIAS DETECTED in {year}")
                elif bias_ratio < 0.8:
                    print(f"⚠️  Moderate premium boat bias in {year}")
                else:
                    print(f"✅ No significant bias in {year}")

        except Exception as e:
            print(f"❌ Error diagnosing premium boat bias: {e}")

    def generate_summary_report(self):
        """Generate summary of all diagnostic findings"""
        print(f"\n📋 COMPREHENSIVE DIAGNOSTIC SUMMARY")
        print("=" * 60)

        try:
            # Get basic stats for both years
            for year in ['2024', '2025']:
                response = self.supabase.table('trips').select(
                    'id, trip_date, total_fish, anglers, boats(name)'
                ).gte('trip_date', f'{year}-01-01').lte('trip_date', f'{year}-12-31').execute()

                total_trips = len(response.data)
                total_fish = sum(trip.get('total_fish', 0) or 0 for trip in response.data)
                unique_boats = len(set(trip['boats']['name'] for trip in response.data if trip['boats']))

                # Get date range
                dates = [trip['trip_date'] for trip in response.data]
                date_range = f"{min(dates)} to {max(dates)}" if dates else "No data"

                print(f"\n📊 {year} SUMMARY:")
                print(f"Total trips: {total_trips:,}")
                print(f"Total fish: {total_fish:,}")
                print(f"Unique boats: {unique_boats}")
                print(f"Date range: {date_range}")
                print(f"Average fish per trip: {total_fish/total_trips:.1f}" if total_trips > 0 else "Average: N/A")

            print(f"\n🎯 DIAGNOSTIC RECOMMENDATIONS:")
            print("1. Address premium boat collection bias if found")
            print("2. Fix data consistency issues (fish count mismatches)")
            print("3. Fill missing date gaps where possible")
            print("4. Clean up bad data (negative values, nulls)")
            print("5. Verify impossible date sequences")

        except Exception as e:
            print(f"❌ Error generating summary: {e}")

    def run_comprehensive_diagnostic(self):
        """Run complete diagnostic of 2024 and 2025 data"""
        print("🔍 COMPREHENSIVE DATA DIAGNOSTIC: 2024 & 2025")
        print("=" * 80)
        print("Identifying missing records, bad data, wrong dates, and quality issues")
        print()

        self.diagnose_missing_records()
        self.diagnose_bad_data()
        self.diagnose_wrong_dates()
        self.diagnose_data_consistency()
        self.diagnose_premium_boat_bias()
        self.generate_summary_report()

        print(f"\n✅ COMPREHENSIVE DIAGNOSTIC COMPLETE")
        print("=" * 60)
        print("Review findings above and prioritize fixes based on impact")

def main():
    diagnostic = ComprehensiveDataDiagnostic()
    diagnostic.run_comprehensive_diagnostic()

if __name__ == "__main__":
    main()