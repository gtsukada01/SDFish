#!/usr/bin/env python3
"""
Comprehensive 2024 Data Analysis
Apply lessons learned from 2025 to identify and fix 2024 issues
"""

from supabase import create_client
from collections import defaultdict

class Comprehensive2024Analysis:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

    def get_all_2024_trips(self):
        """Get ALL 2024 trips for analysis"""
        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, boat_id, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

            return response.data
        except Exception as e:
            print(f"❌ Error fetching 2024 trips: {e}")
            return []

    def analyze_2024_weight_qualifier_suspects(self, trips):
        """Identify weight qualifier failure suspects using 2025 patterns"""
        print("🏋️  2024 WEIGHT QUALIFIER ANALYSIS")
        print("=" * 60)

        weight_qualifier_suspects = []

        for trip in trips:
            boat_name = trip['boats']['name']
            anglers = trip.get('anglers', 0)
            fish_count = trip.get('total_fish', 0)
            date = trip['trip_date']
            duration = trip.get('trip_duration', '')

            # Apply 2025 pattern: High-angler, multi-day trips with 0 fish
            if (anglers >= 10 and
                fish_count == 0 and
                ('Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day', '1/2 Day Twilight'])):

                priority = 'CRITICAL' if anglers >= 20 else 'HIGH' if anglers >= 15 else 'MEDIUM'

                weight_qualifier_suspects.append({
                    'date': date,
                    'boat': boat_name,
                    'anglers': anglers,
                    'duration': duration,
                    'trip_id': trip['id'],
                    'priority': priority
                })

        # Sort by priority and angler count
        weight_qualifier_suspects.sort(key=lambda x: (x['priority'] == 'CRITICAL', x['anglers']), reverse=True)

        print(f"2024 Weight Qualifier Suspects: {len(weight_qualifier_suspects)}")

        if weight_qualifier_suspects:
            print(f"\n🎯 TOP 20 2024 WEIGHT QUALIFIER SUSPECTS:")
            for i, suspect in enumerate(weight_qualifier_suspects[:20], 1):
                print(f"{i:2}. [{suspect['priority']:>8}] {suspect['date']} - {suspect['boat']} ({suspect['anglers']} anglers, {suspect['duration']})")

        return weight_qualifier_suspects

    def analyze_2024_date_alignment_issues(self, trips):
        """Identify date alignment issues in 2024"""
        print(f"\n📅 2024 DATE ALIGNMENT ANALYSIS")
        print("=" * 60)

        multi_day_trips = []
        duplicates = defaultdict(list)

        for trip in trips:
            duration = trip.get('trip_duration', '')

            # Check for multi-day trips
            multi_day_durations = ['Overnight', '1.5 Day', '2 Day', '2.5 Day', '3 Day', '3.5 Day', '4 Day', '5 Day']

            if any(d in duration for d in multi_day_durations):
                multi_day_trips.append({
                    'id': trip['id'],
                    'date': trip['trip_date'],
                    'boat': trip['boats']['name'],
                    'duration': duration,
                    'anglers': trip.get('anglers', 0),
                    'fish': trip.get('total_fish', 0)
                })

            # Check for duplicates
            signature = f"{trip['boats']['name']}_{trip.get('trip_duration', '')}_{trip.get('anglers', 0)}_{trip.get('total_fish', 0)}"
            duplicates[signature].append(trip)

        # Count duplicates
        duplicate_patterns = [sig for sig, trips in duplicates.items() if len(trips) > 1]

        print(f"Multi-day trips needing date correction: {len(multi_day_trips)}")
        print(f"Duplicate patterns detected: {len(duplicate_patterns)}")

        return multi_day_trips, duplicate_patterns

    def monthly_failure_rate_analysis(self, trips):
        """Analyze failure rates by month in 2024"""
        print(f"\n📊 2024 MONTHLY FAILURE RATE ANALYSIS")
        print("=" * 60)

        monthly_stats = defaultdict(lambda: {
            'trips': 0,
            'suspicious': 0,
            'total_fish': 0
        })

        for trip in trips:
            month = trip['trip_date'][:7]  # YYYY-MM
            anglers = trip.get('anglers', 0)
            total_fish = trip.get('total_fish', 0)

            monthly_stats[month]['trips'] += 1
            monthly_stats[month]['total_fish'] += total_fish

            if anglers >= 5 and total_fish == 0:
                monthly_stats[month]['suspicious'] += 1

        print("MONTH        TRIPS   SUSPICIOUS   RATE     AVG FISH")
        print("-" * 55)

        high_failure_months = []

        for month in sorted(monthly_stats.keys()):
            stats = monthly_stats[month]
            failure_rate = (stats['suspicious'] / stats['trips'] * 100) if stats['trips'] > 0 else 0
            avg_fish = stats['total_fish'] / stats['trips'] if stats['trips'] > 0 else 0

            print(f"{month}      {stats['trips']:>4}    {stats['suspicious']:>8}   {failure_rate:>5.1f}%   {avg_fish:>8.1f}")

            if failure_rate > 8.0:  # Flag months with high failure rates
                high_failure_months.append({
                    'month': month,
                    'failure_rate': failure_rate,
                    'trips': stats['trips'],
                    'suspicious': stats['suspicious']
                })

        return high_failure_months

    def compare_2024_vs_2025_patterns(self, trips_2024):
        """Compare 2024 patterns with known 2025 issues"""
        print(f"\n🔍 2024 vs 2025 PATTERN COMPARISON")
        print("=" * 60)

        # Analyze similar boats that had issues in 2025
        problem_boats_2025 = ['Tribute', 'Pacific Queen', 'Tomahawk', 'Dolphin', 'Constitution', 'Pacific Dawn']

        boat_analysis_2024 = {}

        for boat in problem_boats_2025:
            boat_trips = [trip for trip in trips_2024 if trip['boats']['name'] == boat]

            if boat_trips:
                zero_fish_trips = [trip for trip in boat_trips
                                 if trip.get('total_fish', 0) == 0 and trip.get('anglers', 0) >= 5]

                total_trips = len(boat_trips)
                zero_fish_count = len(zero_fish_trips)
                failure_rate = (zero_fish_count / total_trips * 100) if total_trips > 0 else 0

                boat_analysis_2024[boat] = {
                    'total_trips': total_trips,
                    'zero_fish_trips': zero_fish_count,
                    'failure_rate': failure_rate
                }

        print("2024 PROBLEM BOAT ANALYSIS:")
        for boat, stats in boat_analysis_2024.items():
            print(f"  {boat}: {stats['zero_fish_trips']}/{stats['total_trips']} trips ({stats['failure_rate']:.1f}% failure rate)")

        return boat_analysis_2024

    def run_comprehensive_2024_analysis(self):
        """Run complete 2024 analysis based on 2025 findings"""
        print("🚨 COMPREHENSIVE 2024 DATA ANALYSIS")
        print("=" * 80)
        print("Applying lessons learned from 2025 recovery to analyze 2024 data")
        print()

        # Get all 2024 data
        trips = self.get_all_2024_trips()

        if not trips:
            print("❌ No 2024 trips found")
            return

        total_trips = len(trips)
        print(f"Total 2024 Trips Analyzed: {total_trips}")

        # Weight qualifier analysis
        weight_qualifier_suspects = self.analyze_2024_weight_qualifier_suspects(trips)

        # Date alignment analysis
        multi_day_trips, duplicate_patterns = self.analyze_2024_date_alignment_issues(trips)

        # Monthly failure analysis
        high_failure_months = self.monthly_failure_rate_analysis(trips)

        # Pattern comparison with 2025
        boat_analysis = self.compare_2024_vs_2025_patterns(trips)

        # Generate comprehensive summary
        print(f"\n📋 2024 COMPREHENSIVE ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Total 2024 Trips: {total_trips}")
        print(f"Weight Qualifier Suspects: {len(weight_qualifier_suspects)}")
        print(f"Multi-day Trips Needing Date Correction: {len(multi_day_trips)}")
        print(f"Duplicate Patterns: {len(duplicate_patterns)}")
        print(f"High-Failure Months: {len(high_failure_months)}")

        # Show high failure months
        if high_failure_months:
            print(f"\n🚨 2024 HIGH-FAILURE MONTHS:")
            for month in high_failure_months[:5]:
                print(f"   {month['month']}: {month['failure_rate']:.1f}% failure rate ({month['suspicious']}/{month['trips']} trips)")

        # Risk assessment
        print(f"\n🚨 2024 RISK ASSESSMENT:")

        total_suspects = len(weight_qualifier_suspects) + len(multi_day_trips) + len(duplicate_patterns)

        if total_suspects > 500:
            print("❌ CRITICAL: 2024 shows same systematic issues as 2025")
            print("   - Immediate comprehensive recovery required")
            print("   - Estimated fish loss: 500-2000+ fish")
        elif total_suspects > 200:
            print("⚠️  HIGH RISK: Significant 2024 data quality issues detected")
            print("   - Systematic recovery recommended")
        else:
            print("✅ MODERATE: 2024 data quality better than 2025")

        # Recommendations
        print(f"\n🎯 2024 RECOVERY RECOMMENDATIONS:")
        print("1. Apply weight qualifier recovery methodology from 2025")
        print("2. Implement date correction system for multi-day trips")
        print("3. Remove duplicate entries using proven algorithms")
        print("4. Focus on high-failure months first")
        print("5. Prioritize boats with known 2025 patterns")

        return {
            'total_trips': total_trips,
            'weight_qualifier_suspects': weight_qualifier_suspects,
            'multi_day_trips': multi_day_trips,
            'duplicate_patterns': duplicate_patterns,
            'high_failure_months': high_failure_months,
            'boat_analysis': boat_analysis
        }

def main():
    analyzer = Comprehensive2024Analysis()
    analyzer.run_comprehensive_2024_analysis()

if __name__ == "__main__":
    main()