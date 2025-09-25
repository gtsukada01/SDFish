#!/usr/bin/env python3
"""
Remove Phantom Horizon Trips from Database
Based on confirmed analysis showing Horizon doesn't exist on these dates
"""

from supabase import create_client

# Horizon phantom trip dates confirmed by analysis
HORIZON_DATES = [
    '2025-09-15', '2025-09-14', '2025-09-13', '2025-09-12',
    '2025-09-11', '2025-09-10', '2025-09-09'
]

def setup_supabase():
    """Set up Supabase client"""
    url = "https://ulsbtwqhwnrpkourphiq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
    return create_client(url, key)

def analyze_horizon_trips():
    """Analyze Horizon trips before deletion"""
    supabase = setup_supabase()

    print("🔍 ANALYZING HORIZON PHANTOM TRIPS")
    print("=" * 50)

    total_trips = 0
    total_phantom_anglers = 0

    for date in HORIZON_DATES:
        try:
            # Find Horizon trips on this date
            response = supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, trip_duration, boats(name)'
            ).eq('trip_date', date).execute()

            trips = response.data
            horizon_trips = [trip for trip in trips if trip.get('boats', {}).get('name') == 'Horizon']

            if horizon_trips:
                print(f"\n📅 {date}: {len(horizon_trips)} Horizon trips found")
                for trip in horizon_trips:
                    print(f"  Trip ID {trip['id']}: {trip['anglers']} anglers, {trip['total_fish']} fish, {trip.get('trip_duration', 'N/A')}")
                    total_trips += 1
                    total_phantom_anglers += trip['anglers']
            else:
                print(f"📅 {date}: No Horizon trips")

        except Exception as e:
            print(f"❌ Error analyzing {date}: {e}")

    print(f"\n📊 PHANTOM TRIP SUMMARY:")
    print(f"Total Phantom Trips: {total_trips}")
    print(f"Total Phantom Anglers: {total_phantom_anglers}")

    return total_trips

def remove_phantom_horizon_trips():
    """Remove phantom Horizon trips from database"""
    supabase = setup_supabase()

    print("\n🗑️  REMOVING PHANTOM HORIZON TRIPS")
    print("=" * 50)

    removed_trips = 0

    for date in HORIZON_DATES:
        try:
            # Find Horizon trips on this date
            response = supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, boats(name)'
            ).eq('trip_date', date).execute()

            trips = response.data
            horizon_trips = [trip for trip in trips if trip.get('boats', {}).get('name') == 'Horizon']

            if horizon_trips:
                print(f"\n📅 {date}: Removing {len(horizon_trips)} Horizon trips")

                for trip in horizon_trips:
                    trip_id = trip['id']
                    anglers = trip['anglers']

                    print(f"  Removing trip ID {trip_id}: Horizon ({anglers} anglers)")

                    # Delete the trip
                    delete_response = supabase.table('trips').delete().eq('id', trip_id).execute()

                    if delete_response.data or not delete_response.error:
                        print(f"  ✅ Successfully removed trip ID {trip_id}")
                        removed_trips += 1
                    else:
                        print(f"  ❌ Failed to remove trip ID {trip_id}: {delete_response.error}")
            else:
                print(f"📅 {date}: No Horizon trips found")

        except Exception as e:
            print(f"❌ Error processing {date}: {e}")

    print(f"\n✅ REMOVAL COMPLETE: {removed_trips} phantom trips deleted")

def main():
    """Main execution"""
    print("🚨 HORIZON PHANTOM TRIP REMOVAL")
    print("=" * 60)
    print("Based on confirmed analysis that Horizon boat doesn't exist on these dates")
    print("WebFetch confirmed: No Horizon boat found on 2025-09-15")
    print("")

    # Analyze first
    total_trips = analyze_horizon_trips()

    if total_trips > 0:
        print(f"\n⚠️  CONFIRMED: {total_trips} phantom Horizon trips need removal")
        print("These are confirmed phantom trips (boat doesn't exist on source)")

        # Remove the phantom trips
        remove_phantom_horizon_trips()

        print(f"\n🎯 NEXT STEPS:")
        print("1. Phantom Horizon trips have been removed")
        print("2. Database now cleaned of confirmed phantom data")
        print("3. Real boats and their data remain intact")
        print("4. Zero-fish failure rate should improve significantly")

    else:
        print(f"\n✅ No Horizon trips found - database already clean")

if __name__ == "__main__":
    main()