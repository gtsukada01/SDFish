#!/usr/bin/env python3
"""
August Excalibur Weight Qualifier Emergency Fix
Fix Excalibur Aug 26 - confirmed 19 Bluefin Tuna weight qualifier failure
"""

from supabase import create_client

class AugustExcaliburFix:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

    def fix_excalibur_aug_26(self):
        """Fix Excalibur Aug 26 - confirmed 19 Bluefin Tuna weight qualifier failure"""
        print("🔧 FIXING EXCALIBUR - AUGUST 26, 2025")
        print("=" * 50)

        try:
            response = self.supabase.table('trips').select(
                'id, anglers, total_fish, boats(name), catches(id, species, count)'
            ).eq('trip_date', '2025-08-26').execute()

            excalibur_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Excalibur':
                    excalibur_trip = trip
                    break

            if excalibur_trip:
                trip_id = excalibur_trip['id']
                current_fish = excalibur_trip['total_fish']

                print(f"Found Excalibur trip ID: {trip_id}")
                print(f"Current data: {current_fish} fish")
                print(f"Source confirmed: 19 Bluefin Tuna (up to 130 pounds)")

                # Update the trip with correct fish count
                update_response = self.supabase.table('trips').update({
                    'total_fish': 19
                }).eq('id', trip_id).execute()

                if update_response.data:
                    print(f"✅ Updated trip total_fish: {current_fish} → 19")

                    # Create new catch record
                    catch_insert = self.supabase.table('catches').insert({
                        'trip_id': trip_id,
                        'species': 'Bluefin Tuna',
                        'count': 19
                    }).execute()

                    print(f"✅ Created new Bluefin catch record: 19 fish")

                    print(f"\n🎯 EXCALIBUR RECOVERY COMPLETE")
                    print(f"Fish Recovered: +{19 - current_fish}")
                    print(f"Issue: Weight qualifier parsing failure")
                    print(f"Source: 19 Bluefin Tuna (up to 130 pounds)")

            else:
                print(f"❌ Excalibur trip not found")

        except Exception as e:
            print(f"❌ Error fixing Excalibur: {e}")

def main():
    fix = AugustExcaliburFix()
    fix.fix_excalibur_aug_26()

if __name__ == "__main__":
    main()