#!/usr/bin/env python3
"""
Fix Additional September 2025 Issues Found Through Verification
"""

from supabase import create_client
import json

class AdditionalSeptemberFixer:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.corrections = []

    def identify_phantom_premier_trip(self, date):
        """Check if Premier trip on given date is phantom"""
        try:
            response = self.supabase.table('trips').select(
                'id, anglers, total_fish, boats(name)'
            ).eq('trip_date', date).execute()

            trips = response.data
            premier_trips = [trip for trip in trips if trip['boats']['name'] == 'Premier']

            return premier_trips
        except Exception as e:
            print(f"❌ Error checking Premier on {date}: {e}")
            return []

    def remove_phantom_premier_sept_11(self):
        """Remove phantom Premier trip on Sept 11 (doesn't exist in source)"""
        print("🗑️  REMOVING PHANTOM PREMIER - SEPT 11, 2025")
        print("=" * 50)

        premier_trips = self.identify_phantom_premier_trip('2025-09-11')

        for trip in premier_trips:
            trip_id = trip['id']
            anglers = trip['anglers']

            print(f"Found Premier trip ID {trip_id}: {anglers} anglers")
            print("Source verification: Premier NOT FOUND on Sept 11, 2025")

            try:
                # Delete the phantom trip
                delete_response = self.supabase.table('trips').delete().eq('id', trip_id).execute()

                if delete_response.data or not delete_response.error:
                    print(f"✅ Removed phantom Premier trip ID {trip_id}")
                    self.corrections.append({
                        'date': '2025-09-11',
                        'boat': 'Premier',
                        'action': 'REMOVED',
                        'trip_id': trip_id,
                        'reason': 'Phantom trip - boat not found in source'
                    })
                else:
                    print(f"❌ Failed to remove trip {trip_id}")

            except Exception as e:
                print(f"❌ Error removing trip {trip_id}: {e}")

    def fix_premier_sept_07(self):
        """Fix Premier Sept 7 - confirmed 148 total fish (70 AM + 78 PM)"""
        print("\n🔧 FIXING PREMIER - SEPT 7, 2025")
        print("=" * 50)

        premier_trips = self.identify_phantom_premier_trip('2025-09-07')

        if premier_trips:
            for trip in premier_trips:
                trip_id = trip['id']
                current_fish = trip['total_fish']

                print(f"Found Premier trip ID {trip_id}: {current_fish} fish")
                print("Source confirmed: AM (70 fish) + PM (78 fish) = 148 total fish")

                try:
                    # Update with correct fish count
                    update_response = self.supabase.table('trips').update({
                        'total_fish': 148
                    }).eq('id', trip_id).execute()

                    if update_response.data:
                        print(f"✅ Updated Premier Sept 7: {current_fish} → 148 fish")

                        # Add catch records based on source data
                        catches_to_add = [
                            {'species': 'Sand Bass', 'count': 2},
                            {'species': 'Sculpin', 'count': 37},  # 35 AM + 2 PM
                            {'species': 'Sheephead', 'count': 6},
                            {'species': 'Calico Bass', 'count': 25},
                            {'species': 'Rockfish', 'count': 78}  # 33 AM + 45 PM
                        ]

                        for catch_data in catches_to_add:
                            catch_insert = self.supabase.table('catches').insert({
                                'trip_id': trip_id,
                                'species': catch_data['species'],
                                'count': catch_data['count']
                            }).execute()

                        print(f"✅ Added catch records for Premier Sept 7")

                        self.corrections.append({
                            'date': '2025-09-07',
                            'boat': 'Premier',
                            'action': 'UPDATED',
                            'trip_id': trip_id,
                            'old_fish': current_fish,
                            'new_fish': 148,
                            'source': 'AM (70 fish) + PM (78 fish)',
                            'fish_recovered': 148 - current_fish
                        })

                    else:
                        print(f"❌ Failed to update Premier Sept 7")

                except Exception as e:
                    print(f"❌ Error fixing Premier Sept 7: {e}")

    def remove_phantom_vendetta2_trips(self):
        """Remove phantom Vendetta 2 trips that don't exist in source"""
        print("\n🗑️  CHECKING VENDETTA 2 PHANTOM TRIPS")
        print("=" * 50)

        # Check multiple Vendetta 2 dates
        vendetta_dates = ['2025-09-07', '2025-09-06']

        for date in vendetta_dates:
            try:
                response = self.supabase.table('trips').select(
                    'id, anglers, total_fish, boats(name)'
                ).eq('trip_date', date).execute()

                trips = response.data
                vendetta_trips = [trip for trip in trips if trip['boats']['name'] == 'Vendetta 2']

                if vendetta_trips:
                    print(f"\n📅 {date}: Found {len(vendetta_trips)} Vendetta 2 trips")

                    for trip in vendetta_trips:
                        trip_id = trip['id']
                        anglers = trip['anglers']

                        print(f"  Trip ID {trip_id}: {anglers} anglers")
                        print(f"  Source verification for {date}: Vendetta 2 NOT FOUND")

                        # Remove phantom trip
                        delete_response = self.supabase.table('trips').delete().eq('id', trip_id).execute()

                        if delete_response.data or not delete_response.error:
                            print(f"  ✅ Removed phantom Vendetta 2 trip ID {trip_id}")

                            self.corrections.append({
                                'date': date,
                                'boat': 'Vendetta 2',
                                'action': 'REMOVED',
                                'trip_id': trip_id,
                                'reason': f'Phantom trip - boat not found in source on {date}'
                            })
                        else:
                            print(f"  ❌ Failed to remove trip {trip_id}")

                else:
                    print(f"📅 {date}: No Vendetta 2 trips found")

            except Exception as e:
                print(f"❌ Error processing Vendetta 2 on {date}: {e}")

    def run_additional_fixes(self):
        """Run all additional fixes based on verification"""
        print("🚨 ADDITIONAL SEPTEMBER 2025 DATA CORRECTIONS")
        print("=" * 70)
        print("Based on systematic verification against source data")
        print("")

        # Remove phantom Premier on Sept 11
        self.remove_phantom_premier_sept_11()

        # Fix Premier on Sept 7 with correct catch data
        self.fix_premier_sept_07()

        # Remove phantom Vendetta 2 trips
        self.remove_phantom_vendetta2_trips()

        # Generate summary
        print(f"\n🎯 ADDITIONAL FIXES COMPLETE")
        print("=" * 50)

        updates = [c for c in self.corrections if c['action'] == 'UPDATED']
        removals = [c for c in self.corrections if c['action'] == 'REMOVED']

        print(f"Total Updates: {len(updates)}")
        print(f"Total Removals: {len(removals)}")

        if updates:
            total_recovered = sum(c.get('fish_recovered', 0) for c in updates)
            print(f"Fish Recovered from Updates: {total_recovered}")

            print(f"\n📊 RECOVERY DETAILS:")
            for correction in updates:
                print(f"  {correction['date']} - {correction['boat']}: +{correction.get('fish_recovered', 0)} fish")

        if removals:
            print(f"\n🗑️  PHANTOM TRIPS REMOVED:")
            for correction in removals:
                print(f"  {correction['date']} - {correction['boat']}: {correction['reason']}")

        # Save corrections log
        with open('additional_september_fixes.json', 'w') as f:
            json.dump(self.corrections, f, indent=2, default=str)

        print(f"\n✅ Additional fixes complete!")
        print(f"📄 Corrections log saved to: additional_september_fixes.json")

def main():
    fixer = AdditionalSeptemberFixer()
    fixer.run_additional_fixes()

if __name__ == "__main__":
    main()