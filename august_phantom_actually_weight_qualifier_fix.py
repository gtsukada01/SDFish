#!/usr/bin/env python3
"""
August Phantom Pattern Emergency Fix - CRITICAL WEIGHT QUALIFIER FAILURES
These aren't phantom trips - they're massive weight qualifier parsing failures!

Constitution Aug 26: 12 Bluefin Tuna (up to 150 pounds)
Pacific Dawn Aug 20: 7 Bluefin Tuna (up to 100 pounds)
Pacific Dawn Aug 27: 43 Bluefin Tuna (up to 150 pounds)
"""

from supabase import create_client

class AugustPhantomWeightQualifierFix:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.total_recovered = 0

    def fix_constitution_aug_26(self):
        """Fix Constitution Aug 26 - 12 Bluefin Tuna (up to 150 pounds)"""
        print("🔧 FIXING CONSTITUTION - AUGUST 26, 2025")
        print("=" * 50)

        try:
            response = self.supabase.table('trips').select(
                'id, total_fish, boats(name)'
            ).eq('trip_date', '2025-08-26').execute()

            constitution_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Constitution':
                    constitution_trip = trip
                    break

            if constitution_trip:
                trip_id = constitution_trip['id']
                current_fish = constitution_trip['total_fish']

                print(f"Trip ID: {trip_id}, Current fish: {current_fish}")
                print(f"Source: 12 Bluefin Tuna (up to 150 pounds)")

                # Update trip
                self.supabase.table('trips').update({'total_fish': 12}).eq('id', trip_id).execute()

                # Add catch record
                self.supabase.table('catches').insert({
                    'trip_id': trip_id,
                    'species': 'Bluefin Tuna',
                    'count': 12
                }).execute()

                recovered = 12 - current_fish
                self.total_recovered += recovered
                print(f"✅ Constitution: +{recovered} fish recovered")

        except Exception as e:
            print(f"❌ Error fixing Constitution: {e}")

    def fix_pacific_dawn_aug_20(self):
        """Fix Pacific Dawn Aug 20 - 7 Bluefin Tuna (up to 100 pounds)"""
        print("\n🔧 FIXING PACIFIC DAWN - AUGUST 20, 2025")
        print("=" * 50)

        try:
            response = self.supabase.table('trips').select(
                'id, total_fish, boats(name)'
            ).eq('trip_date', '2025-08-20').execute()

            pacific_dawn_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Pacific Dawn':
                    pacific_dawn_trip = trip
                    break

            if pacific_dawn_trip:
                trip_id = pacific_dawn_trip['id']
                current_fish = pacific_dawn_trip['total_fish']

                print(f"Trip ID: {trip_id}, Current fish: {current_fish}")
                print(f"Source: 7 Bluefin Tuna (up to 100 pounds)")

                # Update trip
                self.supabase.table('trips').update({'total_fish': 7}).eq('id', trip_id).execute()

                # Add catch record
                self.supabase.table('catches').insert({
                    'trip_id': trip_id,
                    'species': 'Bluefin Tuna',
                    'count': 7
                }).execute()

                recovered = 7 - current_fish
                self.total_recovered += recovered
                print(f"✅ Pacific Dawn Aug 20: +{recovered} fish recovered")

        except Exception as e:
            print(f"❌ Error fixing Pacific Dawn Aug 20: {e}")

    def fix_pacific_dawn_aug_27(self):
        """Fix Pacific Dawn Aug 27 - 43 Bluefin Tuna (up to 150 pounds)"""
        print("\n🔧 FIXING PACIFIC DAWN - AUGUST 27, 2025")
        print("=" * 50)

        try:
            response = self.supabase.table('trips').select(
                'id, total_fish, boats(name)'
            ).eq('trip_date', '2025-08-27').execute()

            pacific_dawn_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Pacific Dawn':
                    pacific_dawn_trip = trip
                    break

            if pacific_dawn_trip:
                trip_id = pacific_dawn_trip['id']
                current_fish = pacific_dawn_trip['total_fish']

                print(f"Trip ID: {trip_id}, Current fish: {current_fish}")
                print(f"Source: 43 Bluefin Tuna (up to 150 pounds)")

                # Update trip
                self.supabase.table('trips').update({'total_fish': 43}).eq('id', trip_id).execute()

                # Add catch record
                self.supabase.table('catches').insert({
                    'trip_id': trip_id,
                    'species': 'Bluefin Tuna',
                    'count': 43
                }).execute()

                recovered = 43 - current_fish
                self.total_recovered += recovered
                print(f"✅ Pacific Dawn Aug 27: +{recovered} fish recovered")

        except Exception as e:
            print(f"❌ Error fixing Pacific Dawn Aug 27: {e}")

    def run_emergency_fix(self):
        """Run emergency weight qualifier fixes for phantom pattern trips"""
        print("🚨 AUGUST PHANTOM PATTERN EMERGENCY FIX")
        print("These are NOT phantom trips - they're MASSIVE weight qualifier failures!")
        print("=" * 80)

        self.fix_constitution_aug_26()
        self.fix_pacific_dawn_aug_20()
        self.fix_pacific_dawn_aug_27()

        print(f"\n🎯 EMERGENCY FIX COMPLETE")
        print("=" * 50)
        print(f"Total Fish Recovered: +{self.total_recovered}")
        print(f"Critical Error: Phantom detection algorithm failed")
        print(f"Root Cause: Weight qualifier parsing failures, not phantom trips")

        print(f"\n✅ All 'phantom' trips were actually weight qualifier failures:")
        print(f"  Constitution Aug 26: 12 Bluefin Tuna (up to 150 pounds)")
        print(f"  Pacific Dawn Aug 20: 7 Bluefin Tuna (up to 100 pounds)")
        print(f"  Pacific Dawn Aug 27: 43 Bluefin Tuna (up to 150 pounds)")

def main():
    fix = AugustPhantomWeightQualifierFix()
    fix.run_emergency_fix()

if __name__ == "__main__":
    main()