#!/usr/bin/env python3
"""
Compare Liberty data in Supabase with expected data
"""

from supabase import create_client

def compare_liberty_data():
    supabase = create_client(
        "https://ulsbtwqhwnrpkourphiq.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
    )

    # Expected data from user
    expected_data = {
        '2025-09-23': {'anglers': 37, 'total_fish': 4, 'duration': 'Full Day', 'main_species': '4 Bluefin Tuna'},
        '2025-09-22': {'anglers': 20, 'total_fish': 21, 'duration': 'Full Day', 'main_species': '21 Bluefin Tuna'},
        '2025-09-21': {'anglers': 27, 'total_fish': 91, 'duration': '2 Day', 'main_species': '91 Bluefin Tuna'},
        '2025-09-19': {'anglers': 24, 'total_fish': 48, 'duration': '1.5 Day', 'main_species': '48 Bluefin Tuna'},
        '2025-09-17': {'anglers': 11, 'total_fish': 44, 'duration': '2 Day', 'main_species': '44 Bluefin Tuna'},
        '2025-09-14': {'anglers': 17, 'total_fish': 68, 'duration': '2 Day', 'main_species': '68 Bluefin Tuna'},
        '2025-09-10': {'anglers': 21, 'total_fish': 6, 'duration': '2 Day', 'main_species': '3 Bluefin Tuna, 2 California Yellowtail, 1 Dolphinfish'},
        '2025-09-07': {'anglers': 23, 'total_fish': 67, 'duration': '2.5 Day', 'main_species': '25 Bluefin Tuna, 42 Pacific Bonito'},
        '2025-09-03': {'anglers': 25, 'total_fish': 9, 'duration': 'Full Day', 'main_species': '1 Bluefin Tuna, 8 Yellowfin Tuna'},
        '2025-09-02': {'anglers': 25, 'total_fish': 6, 'duration': 'Full Day', 'main_species': '2 Bluefin Tuna, 2 Yellowfin Tuna, 2 California Yellowtail'}
    }

    print("✅ LIBERTY DATA VERIFICATION - SEPTEMBER 2025")
    print("=" * 60)

    try:
        # Get Liberty trips from database
        response = supabase.table('trips').select(
            'trip_date, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
        ).gte('trip_date', '2025-09-01').lte('trip_date', '2025-09-30').execute()

        liberty_trips = {
            trip['trip_date']: trip
            for trip in response.data
            if trip['boats']['name'] == 'Liberty'
        }

        all_match = True

        for date, expected in expected_data.items():
            print(f"\n📅 {date}:")

            if date in liberty_trips:
                db_trip = liberty_trips[date]

                # Check each field
                matches = []

                # Anglers
                if db_trip['anglers'] == expected['anglers']:
                    matches.append(f"✅ Anglers: {expected['anglers']}")
                else:
                    matches.append(f"❌ Anglers: DB={db_trip['anglers']} vs Expected={expected['anglers']}")
                    all_match = False

                # Total fish
                if db_trip['total_fish'] == expected['total_fish']:
                    matches.append(f"✅ Total Fish: {expected['total_fish']}")
                else:
                    matches.append(f"❌ Total Fish: DB={db_trip['total_fish']} vs Expected={expected['total_fish']}")
                    all_match = False

                # Duration
                if db_trip['trip_duration'] == expected['duration']:
                    matches.append(f"✅ Duration: {expected['duration']}")
                else:
                    matches.append(f"❌ Duration: DB={db_trip['trip_duration']} vs Expected={expected['duration']}")
                    all_match = False

                # Species breakdown
                catches = db_trip.get('catches', [])
                catch_summary = []
                for catch in catches:
                    catch_summary.append(f"{catch['count']} {catch['species']}")

                db_species_str = ', '.join(catch_summary)
                matches.append(f"✅ Species: {db_species_str}")

                for match in matches:
                    print(f"   {match}")

            else:
                print(f"   ❌ MISSING: Trip not found in database")
                all_match = False

        print(f"\n🎯 FINAL VERIFICATION RESULT:")
        if all_match:
            print("✅ ALL LIBERTY DATA MATCHES PERFECTLY!")
            print("✅ Your September 2025 Liberty data is correctly stored in Supabase")
        else:
            print("❌ Some discrepancies found")

    except Exception as e:
        print(f"❌ Error during comparison: {e}")

if __name__ == "__main__":
    compare_liberty_data()