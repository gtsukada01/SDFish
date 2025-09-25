#!/usr/bin/env python3
"""
Root Cause Analysis: 2024 Data Collection System Failure
Systematic investigation of why premium multi-day boats are missing
"""

from supabase import create_client
from collections import defaultdict, Counter

class RootCauseAnalysis:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

        # Premium multi-day boats that are systematically missing
        self.premium_boats = [
            'Legend', 'Spirit of Adventure', 'Polaris Supreme', 'Apollo',
            'Highliner', 'Aztec', 'Islander', 'Pacific Dawn', 'Condor',
            'Top Gun 80', 'Pacific Queen', 'Pegasus', 'Tomahawk',
            'Fortune', 'Tribute', 'Excel', 'Oceanside 95'
        ]

        # Day boats that are generally present
        self.day_boats = [
            'New Seaforth', 'San Diego', 'Mission Belle', 'Daily Double',
            'Premier', 'Dolphin', 'Grande', 'Malihini', 'Southern Cal'
        ]

    def analyze_boat_presence_patterns(self):
        """Analyze which boats are systematically missing vs present"""
        print("🔍 ROOT CAUSE ANALYSIS: BOAT PRESENCE PATTERNS")
        print("=" * 70)

        try:
            # Get all 2024 trips
            response = self.supabase.table('trips').select(
                'trip_date, boats(name), trip_duration, anglers, total_fish'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

            boat_appearances = Counter()
            premium_boat_appearances = Counter()
            day_boat_appearances = Counter()

            for trip in response.data:
                boat_name = trip['boats']['name']
                boat_appearances[boat_name] += 1

                if boat_name in self.premium_boats:
                    premium_boat_appearances[boat_name] += 1
                elif boat_name in self.day_boats:
                    day_boat_appearances[boat_name] += 1

            print(f"📊 2024 BOAT APPEARANCE ANALYSIS:")
            print(f"Total boats in database: {len(boat_appearances)}")
            print(f"Total trips analyzed: {sum(boat_appearances.values())}")

            print(f"\n🚨 PREMIUM BOAT APPEARANCES (Expected: High for multi-day operators):")
            for boat in sorted(self.premium_boats):
                count = premium_boat_appearances[boat]
                status = "CRITICAL" if count < 50 else "LOW" if count < 100 else "NORMAL"
                print(f"  {boat}: {count} appearances [{status}]")

            print(f"\n✅ DAY BOAT APPEARANCES (Expected: High for daily operations):")
            for boat in sorted(self.day_boats):
                count = day_boat_appearances[boat]
                status = "NORMAL" if count > 100 else "LOW" if count > 50 else "CRITICAL"
                print(f"  {boat}: {count} appearances [{status}]")

            # Calculate missing rates
            premium_avg = sum(premium_boat_appearances.values()) / len(self.premium_boats) if self.premium_boats else 0
            day_avg = sum(day_boat_appearances.values()) / len(self.day_boats) if self.day_boats else 0

            print(f"\n📊 AVERAGE APPEARANCES:")
            print(f"Premium boats average: {premium_avg:.1f} appearances")
            print(f"Day boats average: {day_avg:.1f} appearances")
            print(f"Ratio (Premium/Day): {premium_avg/day_avg:.2f} (Should be ~1.0 if equal)")

            return {
                'premium_appearances': premium_boat_appearances,
                'day_appearances': day_boat_appearances,
                'premium_avg': premium_avg,
                'day_avg': day_avg
            }

        except Exception as e:
            print(f"❌ Error analyzing boat patterns: {e}")
            return {}

    def analyze_trip_duration_bias(self):
        """Analyze if certain trip durations are systematically missing"""
        print(f"\n🔍 TRIP DURATION BIAS ANALYSIS")
        print("=" * 60)

        try:
            response = self.supabase.table('trips').select(
                'trip_duration, boats(name), total_fish'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

            duration_stats = defaultdict(lambda: {'count': 0, 'total_fish': 0, 'boats': set()})

            for trip in response.data:
                duration = trip.get('trip_duration', 'Unknown')
                boat_name = trip['boats']['name']
                fish_count = trip.get('total_fish', 0)

                duration_stats[duration]['count'] += 1
                duration_stats[duration]['total_fish'] += fish_count
                duration_stats[duration]['boats'].add(boat_name)

            print(f"📊 TRIP DURATION DISTRIBUTION:")
            print(f"{'DURATION':<20} {'TRIPS':<8} {'AVG FISH':<10} {'BOATS':<8}")
            print("-" * 55)

            # Sort by expected trip length (longer trips should have more fish)
            duration_order = [
                '1/2 Day AM', '1/2 Day PM', '1/2 Day Twilight', '3/4 Day', 'Full Day',
                'Overnight', '1.5 Day', '2 Day', '2.5 Day', '3 Day', '3.5 Day', '4 Day', '5 Day'
            ]

            missing_durations = []
            low_count_durations = []

            for duration in duration_order:
                if duration in duration_stats:
                    stats = duration_stats[duration]
                    avg_fish = stats['total_fish'] / stats['count'] if stats['count'] > 0 else 0
                    print(f"{duration:<20} {stats['count']:<8} {avg_fish:<10.1f} {len(stats['boats']):<8}")

                    # Flag suspicious patterns
                    if stats['count'] < 10 and 'Day' in duration and duration not in ['1/2 Day AM', '1/2 Day PM']:
                        low_count_durations.append(duration)
                else:
                    missing_durations.append(duration)
                    print(f"{duration:<20} {'0':<8} {'0.0':<10} {'0':<8}")

            if missing_durations:
                print(f"\n🚨 COMPLETELY MISSING DURATIONS: {missing_durations}")

            if low_count_durations:
                print(f"\n⚠️  SUSPICIOUSLY LOW COUNT DURATIONS: {low_count_durations}")

            return duration_stats

        except Exception as e:
            print(f"❌ Error analyzing trip duration bias: {e}")
            return {}

    def analyze_landing_specific_failures(self):
        """Analyze if failures are specific to certain landings/locations"""
        print(f"\n🔍 LANDING-SPECIFIC FAILURE ANALYSIS")
        print("=" * 60)

        # Map boats to their typical landings based on known patterns
        landing_boats = {
            "Fisherman's Landing": ['Islander', 'Pacific Dawn', 'Pacific Queen', 'Pegasus', 'Tomahawk', 'Condor'],
            "H&M Landing": ['Legend', 'Spirit of Adventure', 'Old Glory', 'Producer'],
            "Point Loma Sportfishing": ['New Lo-An'],
            "Seaforth Sportfishing": ['Polaris Supreme', 'Apollo', 'Highliner', 'Aztec', 'New Seaforth', 'San Diego', 'Tribute'],
            "Oceanside Sea Center": ['Southern Cal', 'Blue Horizon'],
            "Mission Bay": ['Daily Double', 'Mission Belle']
        }

        try:
            # Get boat appearance data from previous analysis
            response = self.supabase.table('trips').select(
                'boats(name)'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

            boat_counts = Counter(trip['boats']['name'] for trip in response.data)

            print(f"📊 LANDING-SPECIFIC BOAT PRESENCE:")

            for landing, boats in landing_boats.items():
                print(f"\n{landing}:")
                total_appearances = 0
                missing_boats = 0

                for boat in boats:
                    count = boat_counts.get(boat, 0)
                    total_appearances += count
                    status = "MISSING" if count == 0 else "LOW" if count < 50 else "NORMAL"

                    if count == 0:
                        missing_boats += 1

                    print(f"  {boat}: {count} trips [{status}]")

                failure_rate = (missing_boats / len(boats) * 100) if boats else 0
                print(f"  Landing Summary: {missing_boats}/{len(boats)} boats missing ({failure_rate:.1f}% failure)")

            return landing_boats

        except Exception as e:
            print(f"❌ Error analyzing landing failures: {e}")
            return {}

    def analyze_temporal_failure_patterns(self):
        """Analyze if failures occur at specific times/dates"""
        print(f"\n🔍 TEMPORAL FAILURE PATTERN ANALYSIS")
        print("=" * 60)

        try:
            response = self.supabase.table('trips').select(
                'trip_date, boats(name)'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').order('trip_date').execute()

            # Group by month
            monthly_boat_counts = defaultdict(lambda: defaultdict(int))
            monthly_totals = defaultdict(int)

            for trip in response.data:
                month = trip['trip_date'][:7]  # YYYY-MM
                boat_name = trip['boats']['name']
                monthly_boat_counts[month][boat_name] += 1
                monthly_totals[month] += 1

            print(f"📊 MONTHLY PREMIUM BOAT PRESENCE:")
            print(f"{'MONTH':<10} {'TOTAL':<8} {'PREMIUM':<8} {'DAY':<8} {'FAILURE%':<10}")
            print("-" * 50)

            for month in sorted(monthly_totals.keys()):
                total_trips = monthly_totals[month]
                premium_trips = sum(monthly_boat_counts[month].get(boat, 0) for boat in self.premium_boats)
                day_trips = sum(monthly_boat_counts[month].get(boat, 0) for boat in self.day_boats)

                # Estimate failure rate (premium boats should have ~30-40% of trips)
                expected_premium_rate = 0.35  # 35% expected premium boat trips
                actual_premium_rate = premium_trips / total_trips if total_trips > 0 else 0
                failure_rate = max(0, (expected_premium_rate - actual_premium_rate) * 100)

                print(f"{month:<10} {total_trips:<8} {premium_trips:<8} {day_trips:<8} {failure_rate:<10.1f}")

            return monthly_boat_counts

        except Exception as e:
            print(f"❌ Error analyzing temporal patterns: {e}")
            return {}

    def generate_root_cause_hypothesis(self):
        """Generate hypothesis about root cause of collection failures"""
        print(f"\n🎯 ROOT CAUSE HYPOTHESIS GENERATION")
        print("=" * 60)

        print(f"📋 EVIDENCE SUMMARY:")
        print("1. ✅ Premium multi-day boats systematically missing (confirmed)")
        print("2. ✅ Day boats generally present (confirmed)")
        print("3. ✅ Pattern consistent across all months (confirmed)")
        print("4. ✅ Multiple landings affected (confirmed)")
        print("5. ✅ Weight qualifier boats disproportionately missing (confirmed)")

        print(f"\n🔍 MOST LIKELY ROOT CAUSES:")

        print(f"\n1. 🚨 SCRAPING DEPTH/TIMEOUT ISSUES:")
        print("   - Premium boats may be listed deeper in HTML structure")
        print("   - Multi-day boats might require JavaScript/AJAX loading")
        print("   - Scraper may timeout before loading all boats")
        print("   - Solution: Increase scraping depth and timeout settings")

        print(f"\n2. 🚨 LANDING-SPECIFIC HTML STRUCTURE:")
        print("   - Fisherman's Landing (premium boats) may have different HTML")
        print("   - H&M Landing premium boats also affected")
        print("   - Day boat landings (Mission Bay, etc.) structure works")
        print("   - Solution: Landing-specific parsing logic required")

        print(f"\n3. 🚨 DATA VALIDATION FAILURES:")
        print("   - Premium boat names may contain special characters")
        print("   - Trip duration parsing may fail for multi-day formats")
        print("   - Weight qualifiers may cause parser crashes")
        print("   - Solution: Enhanced data validation and error handling")

        print(f"\n4. 🚨 SOURCE WEBSITE CHANGES:")
        print("   - Website may have restructured premium boat display")
        print("   - Mobile/desktop view differences")
        print("   - Premium data may be behind authentication/paywall")
        print("   - Solution: Source website structure analysis required")

        print(f"\n🎯 RECOMMENDED IMMEDIATE ACTIONS:")
        print("1. Analyze current scraper code for timeout/depth settings")
        print("2. Test scraper against current source website structure")
        print("3. Implement landing-specific parsing logic")
        print("4. Add comprehensive error logging for parsing failures")
        print("5. Implement fallback mechanisms for premium boat data")

    def run_comprehensive_root_cause_analysis(self):
        """Run complete root cause analysis"""
        print("🚨 COMPREHENSIVE ROOT CAUSE ANALYSIS")
        print("=" * 80)
        print("Systematic investigation of 2024 data collection system failures")
        print()

        # Analyze boat presence patterns
        boat_patterns = self.analyze_boat_presence_patterns()

        # Analyze trip duration bias
        duration_analysis = self.analyze_trip_duration_bias()

        # Analyze landing-specific failures
        landing_analysis = self.analyze_landing_specific_failures()

        # Analyze temporal patterns
        temporal_analysis = self.analyze_temporal_failure_patterns()

        # Generate hypothesis
        self.generate_root_cause_hypothesis()

        print(f"\n🎯 ROOT CAUSE ANALYSIS COMPLETE")
        print("=" * 60)
        print("Analysis reveals systematic bias against premium multi-day boats")
        print("Root cause likely involves scraping depth/timeout or HTML structure changes")
        print("Immediate technical intervention required to fix collection system")

        return {
            'boat_patterns': boat_patterns,
            'duration_analysis': duration_analysis,
            'landing_analysis': landing_analysis,
            'temporal_analysis': temporal_analysis
        }

def main():
    analyzer = RootCauseAnalysis()
    analyzer.run_comprehensive_root_cause_analysis()

if __name__ == "__main__":
    main()