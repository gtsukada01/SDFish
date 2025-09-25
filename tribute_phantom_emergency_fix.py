#!/usr/bin/env python3
"""
Tribute Phantom Pattern Emergency Fix - CATASTROPHIC WEIGHT QUALIFIER FAILURES
These aren't phantom trips - they're massive weight qualifier parsing failures!
"""

from supabase import create_client

class TributePhantomEmergencyFix:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.total_recovered = 0

    def fix_tribute_trip(self, date, fish_count, weight_info):
        """Fix individual Tribute weight qualifier failure"""
        print(f"\n🔧 FIXING TRIBUTE - {date}")
        print("=" * 50)

        try:
            response = self.supabase.table('trips').select(
                'id, total_fish, boats(name)'
            ).eq('trip_date', date).execute()

            tribute_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Tribute':
                    tribute_trip = trip
                    break

            if tribute_trip:
                trip_id = tribute_trip['id']
                current_fish = tribute_trip['total_fish']

                print(f"Trip ID: {trip_id}, Current fish: {current_fish}")
                print(f"Source: {fish_count} Bluefin Tuna {weight_info}")

                # Update trip
                self.supabase.table('trips').update({'total_fish': fish_count}).eq('id', trip_id).execute()

                # Add catch record
                self.supabase.table('catches').insert({
                    'trip_id': trip_id,
                    'species': 'Bluefin Tuna',
                    'count': fish_count
                }).execute()

                recovered = fish_count - current_fish
                self.total_recovered += recovered
                print(f"✅ Tribute {date}: +{recovered} fish recovered")

        except Exception as e:
            print(f"❌ Error fixing Tribute {date}: {e}")

    def run_tribute_emergency_fix(self):
        """Fix all Tribute phantom pattern weight qualifier failures"""
        print("🚨 TRIBUTE PHANTOM PATTERN EMERGENCY FIX")
        print("These are NOT phantom trips - they're CATASTROPHIC weight qualifier failures!")
        print("=" * 80)

        # All Tribute "phantom" trips are actually massive weight qualifier failures
        tribute_fixes = [
            # June 29: No catch data confirmed - legitimate 0 fish
            {'date': '2025-07-14', 'fish_count': 47, 'weight_info': '(up to 220 pounds)'},
            {'date': '2025-07-21', 'fish_count': 76, 'weight_info': '(up to 240 pounds)'},
            {'date': '2025-07-27', 'fish_count': 18, 'weight_info': '(up to 160 pounds)'},
            {'date': '2025-07-28', 'fish_count': 21, 'weight_info': '(up to 200 pounds)'}
        ]

        for fix in tribute_fixes:
            self.fix_tribute_trip(fix['date'], fix['fish_count'], fix['weight_info'])

        print(f"\n🎯 TRIBUTE EMERGENCY FIX COMPLETE")
        print("=" * 50)
        print(f"Total Fish Recovered from 'Phantom' Pattern: +{self.total_recovered}")
        print(f"Largest Single Failure: 76 Bluefin Tuna (July 21)")
        print(f"Premium Fish Sizes: Up to 240 pounds")

        print(f"\n💡 CRITICAL INSIGHT:")
        print(f"'Phantom trip' detection algorithm completely failed")
        print(f"Missed {self.total_recovered} fish in 4 trips due to false phantom classification")
        print(f"Weight qualifier parsing failures created identical 0-fish signatures")

        return self.total_recovered

def main():
    fix = TributePhantomEmergencyFix()
    recovered = fix.run_tribute_emergency_fix()

    print(f"\n📊 TRIBUTE PATTERN RESOLUTION:")
    print(f"Pattern Classification: PHANTOM → WEIGHT QUALIFIER FAILURES")
    print(f"Fish Recovered: {recovered}")
    print(f"Algorithm Error: CRITICAL - Nearly lost massive catch data")

if __name__ == "__main__":
    main()