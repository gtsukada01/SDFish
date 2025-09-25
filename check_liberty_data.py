#!/usr/bin/env python3
"""
Check what Liberty data actually exists in Supabase
"""

from supabase import create_client

def check_liberty_data():
    supabase = create_client(
        "https://ulsbtwqhwnrpkourphiq.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
    )

    print("🔍 CHECKING CURRENT LIBERTY DATA IN SUPABASE")
    print("=" * 60)

    try:
        # Get all September trips first
        response = supabase.table('trips').select(
            'id, trip_date, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
        ).gte('trip_date', '2025-09-01').lte('trip_date', '2025-09-30').execute()

        all_trips = response.data
        liberty_trips = [trip for trip in all_trips if trip['boats']['name'] == 'Liberty']

        print(f"Found {len(liberty_trips)} Liberty trips in September 2025:")
        print()

        if liberty_trips:
            for trip in sorted(liberty_trips, key=lambda x: x['trip_date']):
                date = trip['trip_date']
                anglers = trip['anglers']
                total_fish = trip['total_fish']
                duration = trip['trip_duration']
                catches = trip.get('catches', [])

                print(f"📅 {date}:")
                print(f"   Trip Duration: {duration}")
                print(f"   Anglers: {anglers}")
                print(f"   Total Fish: {total_fish}")

                if catches:
                    print(f"   Catches:")
                    for catch in catches:
                        print(f"     - {catch['count']} {catch['species']}")
                else:
                    print(f"   Catches: None")
                print()

            # Compare with expected data
            expected_dates = [
                '2025-09-02', '2025-09-03', '2025-09-07', '2025-09-10',
                '2025-09-14', '2025-09-17', '2025-09-19', '2025-09-21',
                '2025-09-22', '2025-09-23'
            ]

            existing_dates = [trip['trip_date'] for trip in liberty_trips]
            missing_dates = [date for date in expected_dates if date not in existing_dates]

            print(f"📊 SUMMARY:")
            print(f"Expected dates: {len(expected_dates)}")
            print(f"Found in database: {len(existing_dates)}")
            print(f"Missing: {len(missing_dates)}")

            if missing_dates:
                print(f"\n❌ MISSING DATES:")
                for date in missing_dates:
                    print(f"   - {date}")

        else:
            print("❌ No Liberty trips found in September 2025")

    except Exception as e:
        print(f"❌ Error checking Liberty data: {e}")

if __name__ == "__main__":
    check_liberty_data()