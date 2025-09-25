#!/usr/bin/env python3
"""
Verify and Update Liberty Boat September 2025 Data
"""

from supabase import create_client
import json

class LibertyVerifier:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )

        # Expected Liberty data based on user input
        self.expected_liberty_data = {
            '2025-09-23': {
                'trip_duration': 'Full Day',
                'anglers': 37,
                'catches': [{'species': 'Bluefin Tuna', 'count': 4}],
                'total_fish': 4
            },
            '2025-09-22': {
                'trip_duration': 'Full Day',
                'anglers': 20,
                'catches': [{'species': 'Bluefin Tuna', 'count': 21}],
                'total_fish': 21
            },
            '2025-09-21': {
                'trip_duration': '2 Day',
                'anglers': 27,
                'catches': [{'species': 'Bluefin Tuna', 'count': 91}],
                'total_fish': 91
            },
            '2025-09-19': {
                'trip_duration': '1.5 Day',
                'anglers': 24,
                'catches': [{'species': 'Bluefin Tuna', 'count': 48}],
                'total_fish': 48
            },
            '2025-09-17': {
                'trip_duration': '2 Day',
                'anglers': 11,
                'catches': [{'species': 'Bluefin Tuna', 'count': 44}],
                'total_fish': 44
            },
            '2025-09-14': {
                'trip_duration': '2 Day',
                'anglers': 17,
                'catches': [{'species': 'Bluefin Tuna', 'count': 68}],
                'total_fish': 68
            },
            '2025-09-10': {
                'trip_duration': '2 Day',
                'anglers': 21,
                'catches': [
                    {'species': 'Bluefin Tuna', 'count': 3},
                    {'species': 'California Yellowtail', 'count': 2},
                    {'species': 'Dolphinfish', 'count': 1}
                ],
                'total_fish': 6
            },
            '2025-09-07': {
                'trip_duration': '2.5 Day',
                'anglers': 23,
                'catches': [
                    {'species': 'Bluefin Tuna', 'count': 25},
                    {'species': 'Pacific Bonito', 'count': 42}
                ],
                'total_fish': 67
            },
            '2025-09-03': {
                'trip_duration': 'Full Day',
                'anglers': 25,
                'catches': [
                    {'species': 'Bluefin Tuna', 'count': 1},
                    {'species': 'Yellowfin Tuna', 'count': 8}
                ],
                'total_fish': 9
            },
            '2025-09-02': {
                'trip_duration': 'Full Day',
                'anglers': 25,
                'catches': [
                    {'species': 'Bluefin Tuna', 'count': 2},
                    {'species': 'Yellowfin Tuna', 'count': 2},
                    {'species': 'California Yellowtail', 'count': 2}
                ],
                'total_fish': 6
            }
        }

        self.corrections_needed = []

    def get_liberty_trips_from_db(self):
        """Get all Liberty trips from September 2025"""
        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
            ).eq('trip_date', '2025-09-01').gte('trip_date', '2025-09-01').lte('trip_date', '2025-09-30').execute()

            liberty_trips = {}
            for trip in response.data:
                if trip['boats']['name'] == 'Liberty':
                    date = trip['trip_date']
                    liberty_trips[date] = {
                        'id': trip['id'],
                        'anglers': trip['anglers'],
                        'total_fish': trip['total_fish'],
                        'trip_duration': trip['trip_duration'],
                        'catches': trip.get('catches', [])
                    }

            return liberty_trips

        except Exception as e:
            print(f"❌ Error fetching Liberty trips: {e}")
            return {}

    def compare_and_identify_corrections(self, db_trips):
        """Compare database data with expected data and identify needed corrections"""
        print("🔍 COMPARING LIBERTY DATA")
        print("=" * 60)

        for date, expected in self.expected_liberty_data.items():
            print(f"\n📅 {date}:")

            if date in db_trips:
                db_trip = db_trips[date]
                trip_id = db_trip['id']

                # Compare each field
                issues = []

                # Check anglers
                if db_trip['anglers'] != expected['anglers']:
                    issues.append(f"Anglers: DB={db_trip['anglers']} vs Expected={expected['anglers']}")

                # Check total fish
                if db_trip['total_fish'] != expected['total_fish']:
                    issues.append(f"Total Fish: DB={db_trip['total_fish']} vs Expected={expected['total_fish']}")

                # Check trip duration
                if db_trip['trip_duration'] != expected['trip_duration']:
                    issues.append(f"Duration: DB={db_trip['trip_duration']} vs Expected={expected['trip_duration']}")

                # Check catches
                db_catches = db_trip['catches']
                expected_catches = expected['catches']

                # Create catch summaries for comparison
                db_catch_summary = {}
                for catch in db_catches:
                    species = catch['species']
                    count = catch['count']
                    db_catch_summary[species] = db_catch_summary.get(species, 0) + count

                expected_catch_summary = {}
                for catch in expected_catches:
                    species = catch['species']
                    count = catch['count']
                    expected_catch_summary[species] = expected_catch_summary.get(species, 0) + count

                if db_catch_summary != expected_catch_summary:
                    issues.append(f"Catches: DB={db_catch_summary} vs Expected={expected_catch_summary}")

                if issues:
                    print(f"  ❌ ISSUES FOUND:")
                    for issue in issues:
                        print(f"    - {issue}")

                    self.corrections_needed.append({
                        'date': date,
                        'trip_id': trip_id,
                        'issues': issues,
                        'expected': expected,
                        'current': {
                            'anglers': db_trip['anglers'],
                            'total_fish': db_trip['total_fish'],
                            'trip_duration': db_trip['trip_duration'],
                            'catches': db_catch_summary
                        }
                    })
                else:
                    print(f"  ✅ CORRECT: Matches expected data")

            else:
                print(f"  ❌ MISSING: No Liberty trip found in database")
                self.corrections_needed.append({
                    'date': date,
                    'trip_id': None,
                    'issues': ['MISSING TRIP'],
                    'expected': expected,
                    'current': None
                })

    def apply_corrections(self):
        """Apply the needed corrections to Supabase"""
        if not self.corrections_needed:
            print("\n✅ No corrections needed - Liberty data is accurate!")
            return

        print(f"\n🔧 APPLYING {len(self.corrections_needed)} CORRECTIONS")
        print("=" * 60)

        for correction in self.corrections_needed:
            date = correction['date']
            trip_id = correction['trip_id']
            expected = correction['expected']

            print(f"\n📅 Correcting {date}:")

            if trip_id is None:
                # Need to create missing trip
                print("  ➕ Creating missing Liberty trip")

                # First get boat_id for Liberty
                boat_response = self.supabase.table('boats').select('id').eq('name', 'Liberty').execute()
                if not boat_response.data:
                    print("  ❌ Cannot find Liberty boat in database")
                    continue

                boat_id = boat_response.data[0]['id']

                # Create the trip
                trip_data = {
                    'trip_date': date,
                    'boat_id': boat_id,
                    'anglers': expected['anglers'],
                    'total_fish': expected['total_fish'],
                    'trip_duration': expected['trip_duration']
                }

                try:
                    trip_insert = self.supabase.table('trips').insert(trip_data).execute()
                    if trip_insert.data:
                        new_trip_id = trip_insert.data[0]['id']
                        print(f"  ✅ Created trip ID {new_trip_id}")

                        # Add catches
                        for catch_data in expected['catches']:
                            catch_insert = self.supabase.table('catches').insert({
                                'trip_id': new_trip_id,
                                'species': catch_data['species'],
                                'count': catch_data['count']
                            }).execute()

                        print(f"  ✅ Added {len(expected['catches'])} catch records")
                    else:
                        print(f"  ❌ Failed to create trip")

                except Exception as e:
                    print(f"  ❌ Error creating trip: {e}")

            else:
                # Update existing trip
                print(f"  🔧 Updating trip ID {trip_id}")

                try:
                    # Update trip basics
                    trip_update = self.supabase.table('trips').update({
                        'anglers': expected['anglers'],
                        'total_fish': expected['total_fish'],
                        'trip_duration': expected['trip_duration']
                    }).eq('id', trip_id).execute()

                    if trip_update.data:
                        print(f"  ✅ Updated trip basics")

                        # Delete existing catches and recreate
                        catch_delete = self.supabase.table('catches').delete().eq('trip_id', trip_id).execute()
                        print(f"  🗑️ Cleared old catch records")

                        # Add correct catches
                        for catch_data in expected['catches']:
                            catch_insert = self.supabase.table('catches').insert({
                                'trip_id': trip_id,
                                'species': catch_data['species'],
                                'count': catch_data['count']
                            }).execute()

                        print(f"  ✅ Added {len(expected['catches'])} new catch records")
                    else:
                        print(f"  ❌ Failed to update trip")

                except Exception as e:
                    print(f"  ❌ Error updating trip: {e}")

    def verify_final_state(self):
        """Verify all corrections were applied successfully"""
        print(f"\n🔍 FINAL VERIFICATION")
        print("=" * 50)

        db_trips = self.get_liberty_trips_from_db()
        all_correct = True

        for date, expected in self.expected_liberty_data.items():
            if date in db_trips:
                db_trip = db_trips[date]

                # Quick verification
                correct = (
                    db_trip['anglers'] == expected['anglers'] and
                    db_trip['total_fish'] == expected['total_fish'] and
                    db_trip['trip_duration'] == expected['trip_duration']
                )

                if correct:
                    print(f"  ✅ {date}: {expected['total_fish']} fish, {expected['anglers']} anglers")
                else:
                    print(f"  ❌ {date}: Still incorrect")
                    all_correct = False
            else:
                print(f"  ❌ {date}: Still missing")
                all_correct = False

        print(f"\n🎯 FINAL STATUS:")
        if all_correct:
            print("✅ ALL LIBERTY DATA VERIFIED CORRECT IN SUPABASE")
        else:
            print("❌ SOME LIBERTY DATA STILL NEEDS ATTENTION")

        return all_correct

    def run_verification(self):
        """Run complete Liberty data verification and correction"""
        print("🎣 LIBERTY SEPTEMBER 2025 DATA VERIFICATION")
        print("=" * 70)

        # Get current database state
        db_trips = self.get_liberty_trips_from_db()
        print(f"Found {len(db_trips)} Liberty trips in database")

        # Compare and identify corrections needed
        self.compare_and_identify_corrections(db_trips)

        # Apply corrections if needed
        if self.corrections_needed:
            print(f"\n⚠️  Found {len(self.corrections_needed)} issues that need correction")

            proceed = input("Apply corrections? (yes/no): ")
            if proceed.lower() == 'yes':
                self.apply_corrections()
                self.verify_final_state()
            else:
                print("❌ Corrections cancelled")
        else:
            print("\n✅ No corrections needed!")

def main():
    verifier = LibertyVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()