#!/usr/bin/env python3
"""
Fix Critical September 2025 Issues
Target the confirmed data losses and make immediate corrections
"""

from supabase import create_client
import json

class CriticalSeptemberFixer:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.corrections = []

    def find_and_fix_pacific_queen(self):
        """Find and fix Pacific Queen Sept 1 - confirmed 98 Bluefin loss"""
        print("🔧 FIXING PACIFIC QUEEN - SEPT 1, 2025")
        print("=" * 50)

        try:
            # Find Pacific Queen trip on 2025-09-01
            response = self.supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, boats(name), catches(id, species, count)'
            ).eq('trip_date', '2025-09-01').execute()

            trips = response.data
            pacific_queen_trip = None

            for trip in trips:
                if trip['boats']['name'] == 'Pacific Queen':
                    pacific_queen_trip = trip
                    break

            if pacific_queen_trip:
                trip_id = pacific_queen_trip['id']
                current_fish = pacific_queen_trip['total_fish']
                current_catches = pacific_queen_trip.get('catches', [])

                print(f"Found Pacific Queen trip ID: {trip_id}")
                print(f"Current data: {current_fish} fish, {len(current_catches)} catch records")
                print(f"Source confirmed: 98 Bluefin Tuna (up to 140 pounds)")

                # Update the trip with correct fish count
                update_response = self.supabase.table('trips').update({
                    'total_fish': 98
                }).eq('id', trip_id).execute()

                if update_response.data:
                    print(f"✅ Updated trip total_fish: {current_fish} → 98")

                    # Add/update catch record for Bluefin Tuna
                    bluefin_catch = None
                    for catch in current_catches:
                        if 'bluefin' in catch['species'].lower():
                            bluefin_catch = catch
                            break

                    if bluefin_catch:
                        # Update existing catch
                        catch_update = self.supabase.table('catches').update({
                            'count': 98,
                            'species': 'Bluefin Tuna'
                        }).eq('id', bluefin_catch['id']).execute()

                        print(f"✅ Updated Bluefin catch: {bluefin_catch['count']} → 98")
                    else:
                        # Create new catch record
                        catch_insert = self.supabase.table('catches').insert({
                            'trip_id': trip_id,
                            'species': 'Bluefin Tuna',
                            'count': 98
                        }).execute()

                        print(f"✅ Created new Bluefin catch record: 98 fish")

                    self.corrections.append({
                        'date': '2025-09-01',
                        'boat': 'Pacific Queen',
                        'trip_id': trip_id,
                        'old_fish': current_fish,
                        'new_fish': 98,
                        'issue': 'Weight qualifier parsing failure',
                        'source': '98 Bluefin Tuna (up to 140 pounds)'
                    })

                else:
                    print(f"❌ Failed to update Pacific Queen trip")

            else:
                print(f"❌ Pacific Queen trip not found for 2025-09-01")

        except Exception as e:
            print(f"❌ Error fixing Pacific Queen: {e}")

    def find_and_fix_pacific_dawn(self):
        """Find and fix Pacific Dawn Sept 18 - confirmed 66 Bluefin loss"""
        print("\n🔧 FIXING PACIFIC DAWN - SEPT 18, 2025")
        print("=" * 50)

        try:
            # Find Pacific Dawn trip on 2025-09-18
            response = self.supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, boats(name), catches(id, species, count)'
            ).eq('trip_date', '2025-09-18').execute()

            trips = response.data
            pacific_dawn_trip = None

            for trip in trips:
                if trip['boats']['name'] == 'Pacific Dawn':
                    pacific_dawn_trip = trip
                    break

            if pacific_dawn_trip:
                trip_id = pacific_dawn_trip['id']
                current_fish = pacific_dawn_trip['total_fish']
                current_catches = pacific_dawn_trip.get('catches', [])

                print(f"Found Pacific Dawn trip ID: {trip_id}")
                print(f"Current data: {current_fish} fish, {len(current_catches)} catch records")
                print(f"Source confirmed: 66 Bluefin Tuna (up to 100 pounds)")

                # Update the trip with correct fish count
                update_response = self.supabase.table('trips').update({
                    'total_fish': 66
                }).eq('id', trip_id).execute()

                if update_response.data:
                    print(f"✅ Updated trip total_fish: {current_fish} → 66")

                    # Add/update catch record for Bluefin Tuna
                    bluefin_catch = None
                    for catch in current_catches:
                        if 'bluefin' in catch['species'].lower():
                            bluefin_catch = catch
                            break

                    if bluefin_catch:
                        # Update existing catch
                        catch_update = self.supabase.table('catches').update({
                            'count': 66,
                            'species': 'Bluefin Tuna'
                        }).eq('id', bluefin_catch['id']).execute()

                        print(f"✅ Updated Bluefin catch: {bluefin_catch['count']} → 66")
                    else:
                        # Create new catch record
                        catch_insert = self.supabase.table('catches').insert({
                            'trip_id': trip_id,
                            'species': 'Bluefin Tuna',
                            'count': 66
                        }).execute()

                        print(f"✅ Created new Bluefin catch record: 66 fish")

                    self.corrections.append({
                        'date': '2025-09-18',
                        'boat': 'Pacific Dawn',
                        'trip_id': trip_id,
                        'old_fish': current_fish,
                        'new_fish': 66,
                        'issue': 'Weight qualifier parsing failure',
                        'source': '66 Bluefin Tuna (up to 100 pounds)'
                    })

                else:
                    print(f"❌ Failed to update Pacific Dawn trip")

            else:
                print(f"❌ Pacific Dawn trip not found for 2025-09-18")

        except Exception as e:
            print(f"❌ Error fixing Pacific Dawn: {e}")

    def verify_corrections(self):
        """Verify the corrections were applied successfully"""
        print(f"\n🔍 VERIFYING CORRECTIONS")
        print("=" * 50)

        for correction in self.corrections:
            try:
                trip_id = correction['trip_id']
                expected_fish = correction['new_fish']

                # Check the trip
                response = self.supabase.table('trips').select(
                    'total_fish, boats(name)'
                ).eq('id', trip_id).execute()

                if response.data:
                    trip = response.data[0]
                    actual_fish = trip['total_fish']
                    boat_name = trip['boats']['name']

                    if actual_fish == expected_fish:
                        print(f"  ✅ {boat_name}: {actual_fish} fish (correct)")
                    else:
                        print(f"  ❌ {boat_name}: {actual_fish} fish (expected {expected_fish})")

            except Exception as e:
                print(f"  ❌ Error verifying trip {trip_id}: {e}")

    def run_critical_fixes(self):
        """Run all critical fixes"""
        print("🚨 CRITICAL SEPTEMBER 2025 DATA RECOVERY")
        print("=" * 70)
        print("Fixing confirmed weight qualifier parsing failures")
        print("")

        # Fix the two confirmed critical losses
        self.find_and_fix_pacific_queen()
        self.find_and_fix_pacific_dawn()

        # Verify corrections
        self.verify_corrections()

        # Generate summary
        print(f"\n🎯 CRITICAL FIXES COMPLETE")
        print("=" * 50)
        print(f"Total Critical Corrections: {len(self.corrections)}")

        if self.corrections:
            recovered_fish = sum(c['new_fish'] - c['old_fish'] for c in self.corrections)
            print(f"Total Fish Recovered: {recovered_fish}")

            print(f"\n📊 RECOVERY DETAILS:")
            for correction in self.corrections:
                fish_recovered = correction['new_fish'] - correction['old_fish']
                print(f"  {correction['date']} - {correction['boat']}: +{fish_recovered} fish recovered")
                print(f"    Issue: {correction['issue']}")
                print(f"    Source: {correction['source']}")

        # Save corrections log
        with open('critical_september_fixes.json', 'w') as f:
            json.dump(self.corrections, f, indent=2, default=str)

        print(f"\n✅ Critical fixes complete! Recovered fish from weight qualifier failures.")
        print(f"📄 Recovery log saved to: critical_september_fixes.json")

def main():
    fixer = CriticalSeptemberFixer()
    fixer.run_critical_fixes()

if __name__ == "__main__":
    main()