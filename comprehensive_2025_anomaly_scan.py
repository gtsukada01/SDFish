#!/usr/bin/env python3
"""
Comprehensive 2025 Anomaly Detection
Check for remaining anomalies across all of 2025 beyond weight qualifier failures
"""

from supabase import create_client
import json
from collections import defaultdict

class Comprehensive2025AnomalyScanner:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

    def get_all_2025_trips(self):
        """Get ALL 2025 trips for comprehensive analysis"""
        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, boat_id, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
            ).gte('trip_date', '2025-01-01').lte('trip_date', '2025-12-31').execute()

            return response.data
        except Exception as e:
            print(f"❌ Error fetching 2025 trips: {e}")
            return []

    def analyze_remaining_months(self, trips):
        """Analyze Oct-Dec 2025 for issues we haven't covered yet"""
        print("📊 REMAINING MONTHS ANALYSIS (Oct-Dec 2025)")
        print("=" * 60)

        remaining_months = ['10', '11', '12']
        month_names = ['October', 'November', 'December']

        remaining_data = {}

        for i, month in enumerate(remaining_months):
            month_trips = [trip for trip in trips if trip['trip_date'].startswith(f'2025-{month}')]

            if not month_trips:
                print(f"{month_names[i]:>9}: No trips found")
                continue

            total_trips = len(month_trips)
            suspicious = [trip for trip in month_trips
                         if trip.get('anglers', 0) >= 5 and trip.get('total_fish', 0) == 0]

            suspicious_count = len(suspicious)
            failure_rate = (suspicious_count / total_trips * 100) if total_trips > 0 else 0

            remaining_data[month] = {
                'name': month_names[i],
                'total_trips': total_trips,
                'suspicious_trips': suspicious_count,
                'failure_rate': failure_rate,
                'suspicious_details': suspicious
            }

            print(f"{month_names[i]:>9}: {total_trips:>3} trips, {suspicious_count:>3} suspicious ({failure_rate:>5.1f}%)")

        return remaining_data

    def detect_data_inconsistencies(self, trips):
        """Look for various data inconsistencies beyond weight qualifiers"""
        print(f"\n🔍 DATA INCONSISTENCY ANALYSIS")
        print("=" * 50)

        inconsistencies = {
            'negative_fish': [],
            'extreme_angler_counts': [],
            'missing_catches_with_fish': [],
            'catches_exceed_total': [],
            'impossible_dates': [],
            'duplicate_trips': []
        }

        # Track for duplicate detection
        trip_signatures = defaultdict(list)

        for trip in trips:
            trip_date = trip['trip_date']
            boat_name = trip['boats']['name'] if trip.get('boats') else 'Unknown'
            anglers = trip.get('anglers', 0)
            total_fish = trip.get('total_fish', 0)
            duration = trip.get('trip_duration', '')
            catches = trip.get('catches', [])

            # 1. Negative fish counts
            if total_fish < 0:
                inconsistencies['negative_fish'].append({
                    'trip_id': trip['id'],
                    'date': trip_date,
                    'boat': boat_name,
                    'fish_count': total_fish
                })

            # 2. Extreme angler counts (over 50 or negative)
            if anglers < 0 or anglers > 50:
                inconsistencies['extreme_angler_counts'].append({
                    'trip_id': trip['id'],
                    'date': trip_date,
                    'boat': boat_name,
                    'anglers': anglers
                })

            # 3. Trips with fish but no catch records
            if total_fish > 0 and len(catches) == 0:
                inconsistencies['missing_catches_with_fish'].append({
                    'trip_id': trip['id'],
                    'date': trip_date,
                    'boat': boat_name,
                    'total_fish': total_fish,
                    'catches': len(catches)
                })

            # 4. Catch counts exceed total fish
            if catches:
                catch_sum = sum(catch.get('count', 0) for catch in catches)
                if catch_sum > total_fish:
                    inconsistencies['catches_exceed_total'].append({
                        'trip_id': trip['id'],
                        'date': trip_date,
                        'boat': boat_name,
                        'total_fish': total_fish,
                        'catch_sum': catch_sum,
                        'difference': catch_sum - total_fish
                    })

            # 5. Duplicate trip detection
            signature = f"{boat_name}_{trip_date}_{duration}_{anglers}"
            trip_signatures[signature].append({
                'trip_id': trip['id'],
                'date': trip_date,
                'boat': boat_name,
                'anglers': anglers,
                'duration': duration,
                'total_fish': total_fish
            })

        # Process duplicates
        for signature, trips_with_sig in trip_signatures.items():
            if len(trips_with_sig) > 1:
                inconsistencies['duplicate_trips'].append({
                    'signature': signature,
                    'count': len(trips_with_sig),
                    'trips': trips_with_sig
                })

        return inconsistencies

    def analyze_boat_performance_anomalies(self, trips):
        """Look for boats with unusual performance patterns"""
        print(f"\n🚤 BOAT PERFORMANCE ANOMALY ANALYSIS")
        print("=" * 50)

        boat_stats = defaultdict(lambda: {
            'trips': 0,
            'total_fish': 0,
            'total_anglers': 0,
            'zero_fish_trips': 0,
            'dates': []
        })

        # Collect boat statistics
        for trip in trips:
            boat_name = trip['boats']['name'] if trip.get('boats') else 'Unknown'
            anglers = trip.get('anglers', 0)
            total_fish = trip.get('total_fish', 0)

            boat_stats[boat_name]['trips'] += 1
            boat_stats[boat_name]['total_fish'] += total_fish
            boat_stats[boat_name]['total_anglers'] += anglers
            boat_stats[boat_name]['dates'].append(trip['trip_date'])

            if total_fish == 0 and anglers >= 5:
                boat_stats[boat_name]['zero_fish_trips'] += 1

        # Analyze for anomalies
        anomalous_boats = []

        for boat_name, stats in boat_stats.items():
            if stats['trips'] < 3:  # Skip boats with too few trips
                continue

            zero_fish_rate = (stats['zero_fish_trips'] / stats['trips']) * 100
            avg_fish_per_trip = stats['total_fish'] / stats['trips'] if stats['trips'] > 0 else 0
            avg_anglers_per_trip = stats['total_anglers'] / stats['trips'] if stats['trips'] > 0 else 0

            # Flag boats with high zero-fish rates
            if zero_fish_rate > 20:  # More than 20% zero-fish trips
                anomalous_boats.append({
                    'boat': boat_name,
                    'trips': stats['trips'],
                    'zero_fish_rate': zero_fish_rate,
                    'avg_fish_per_trip': avg_fish_per_trip,
                    'avg_anglers_per_trip': avg_anglers_per_trip,
                    'issue': 'High zero-fish rate'
                })

        # Sort by zero-fish rate
        anomalous_boats.sort(key=lambda x: x['zero_fish_rate'], reverse=True)

        return anomalous_boats

    def check_temporal_anomalies(self, trips):
        """Look for temporal patterns and anomalies"""
        print(f"\n📅 TEMPORAL ANOMALY ANALYSIS")
        print("=" * 50)

        # Group by month for trend analysis
        monthly_stats = defaultdict(lambda: {
            'trips': 0,
            'total_fish': 0,
            'suspicious_trips': 0
        })

        for trip in trips:
            month = trip['trip_date'][:7]  # YYYY-MM
            anglers = trip.get('anglers', 0)
            total_fish = trip.get('total_fish', 0)

            monthly_stats[month]['trips'] += 1
            monthly_stats[month]['total_fish'] += total_fish

            if anglers >= 5 and total_fish == 0:
                monthly_stats[month]['suspicious_trips'] += 1

        # Calculate failure rates and identify anomalous months
        anomalous_months = []

        for month, stats in monthly_stats.items():
            if stats['trips'] == 0:
                continue

            failure_rate = (stats['suspicious_trips'] / stats['trips']) * 100
            avg_fish_per_trip = stats['total_fish'] / stats['trips']

            if failure_rate > 10:  # More than 10% failure rate
                anomalous_months.append({
                    'month': month,
                    'failure_rate': failure_rate,
                    'trips': stats['trips'],
                    'suspicious_trips': stats['suspicious_trips'],
                    'avg_fish_per_trip': avg_fish_per_trip
                })

        # Sort by failure rate
        anomalous_months.sort(key=lambda x: x['failure_rate'], reverse=True)

        return anomalous_months, monthly_stats

    def run_comprehensive_anomaly_scan(self):
        """Run complete 2025 anomaly detection"""
        print("🚨 COMPREHENSIVE 2025 ANOMALY SCAN")
        print("=" * 80)

        # Get all 2025 data
        trips = self.get_all_2025_trips()

        if not trips:
            print("❌ No 2025 trips found")
            return

        total_trips = len(trips)
        print(f"Total 2025 Trips Analyzed: {total_trips}")

        # Analyze remaining months (Oct-Dec)
        remaining_months_data = self.analyze_remaining_months(trips)

        # Check data inconsistencies
        inconsistencies = self.detect_data_inconsistencies(trips)

        # Analyze boat performance anomalies
        anomalous_boats = self.analyze_boat_performance_anomalies(trips)

        # Check temporal anomalies
        anomalous_months, monthly_stats = self.check_temporal_anomalies(trips)

        # Generate comprehensive summary
        print(f"\n📋 COMPREHENSIVE 2025 ANOMALY SUMMARY")
        print("=" * 60)

        print(f"🗓️  REMAINING MONTHS STATUS:")
        if remaining_months_data:
            for month_data in remaining_months_data.values():
                if month_data['total_trips'] > 0:
                    print(f"   {month_data['name']}: {month_data['failure_rate']:.1f}% failure rate ({month_data['suspicious_trips']}/{month_data['total_trips']} trips)")
        else:
            print("   October-December: No trips found (data collection ended)")

        print(f"\n🔍 DATA INCONSISTENCIES:")
        for issue_type, issues in inconsistencies.items():
            if issues:
                print(f"   {issue_type.replace('_', ' ').title()}: {len(issues)} cases")

        print(f"\n🚤 BOAT PERFORMANCE ANOMALIES:")
        if anomalous_boats:
            print(f"   Boats with high failure rates: {len(anomalous_boats)}")
            for boat in anomalous_boats[:5]:
                print(f"      {boat['boat']}: {boat['zero_fish_rate']:.1f}% zero-fish rate")
        else:
            print("   No significant boat performance anomalies detected")

        print(f"\n📅 TEMPORAL ANOMALIES:")
        if anomalous_months:
            print(f"   Months with high failure rates: {len(anomalous_months)}")
            for month in anomalous_months[:5]:
                print(f"      {month['month']}: {month['failure_rate']:.1f}% failure rate")
        else:
            print("   No significant temporal anomalies beyond known issues")

        # Save comprehensive results
        results = {
            'total_2025_trips': total_trips,
            'remaining_months': remaining_months_data,
            'data_inconsistencies': inconsistencies,
            'anomalous_boats': anomalous_boats,
            'temporal_anomalies': anomalous_months,
            'monthly_statistics': dict(monthly_stats),
            'analysis_date': '2025-09-24'
        }

        with open('comprehensive_2025_anomaly_scan.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✅ Comprehensive anomaly scan saved to: comprehensive_2025_anomaly_scan.json")

        # Final assessment
        critical_issues = 0
        if remaining_months_data:
            critical_issues += sum(1 for data in remaining_months_data.values()
                                 if data.get('failure_rate', 0) > 10)

        critical_issues += len([issues for issues in inconsistencies.values() if issues])
        critical_issues += len(anomalous_boats)
        critical_issues += len(anomalous_months)

        print(f"\n🚨 FINAL ASSESSMENT:")
        if critical_issues > 5:
            print("❌ CRITICAL: Multiple anomaly types detected")
            print("   - Immediate investigation required")
        elif critical_issues > 0:
            print("⚠️  WARNING: Some anomalies detected")
            print("   - Selective investigation recommended")
        else:
            print("✅ GOOD: No significant new anomalies beyond known weight qualifier issues")

        return results

def main():
    scanner = Comprehensive2025AnomalyScanner()
    scanner.run_comprehensive_anomaly_scan()

if __name__ == "__main__":
    main()