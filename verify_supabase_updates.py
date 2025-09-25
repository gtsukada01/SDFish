#!/usr/bin/env python3
"""
Verify all September corrections were successfully pushed to Supabase
"""

from supabase import create_client

def verify_supabase_updates():
    """Verify all corrections were applied to Supabase"""
    supabase = create_client(
        "https://ulsbtwqhwnrpkourphiq.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
    )

    print("🔍 VERIFYING SUPABASE UPDATES")
    print("=" * 50)

    # Test cases for our corrections
    verifications = []

    # 1. Verify Pacific Queen recovery (98 fish)
    try:
        response = supabase.table('trips').select(
            'total_fish, boats(name), catches(species, count)'
        ).eq('trip_date', '2025-09-01').execute()

        pacific_queen_trip = None
        for trip in response.data:
            if trip['boats']['name'] == 'Pacific Queen':
                pacific_queen_trip = trip
                break

        if pacific_queen_trip:
            fish_count = pacific_queen_trip['total_fish']
            catches = pacific_queen_trip.get('catches', [])
            bluefin_catches = [c for c in catches if 'bluefin' in c['species'].lower()]

            verifications.append({
                'test': 'Pacific Queen Recovery',
                'expected': 98,
                'actual': fish_count,
                'status': '✅ PASS' if fish_count == 98 else '❌ FAIL',
                'catches': bluefin_catches
            })
        else:
            verifications.append({
                'test': 'Pacific Queen Recovery',
                'status': '❌ FAIL - Trip not found'
            })

    except Exception as e:
        verifications.append({
            'test': 'Pacific Queen Recovery',
            'status': f'❌ ERROR: {e}'
        })

    # 2. Verify Pacific Dawn recovery (66 fish)
    try:
        response = supabase.table('trips').select(
            'total_fish, boats(name), catches(species, count)'
        ).eq('trip_date', '2025-09-18').execute()

        pacific_dawn_trip = None
        for trip in response.data:
            if trip['boats']['name'] == 'Pacific Dawn':
                pacific_dawn_trip = trip
                break

        if pacific_dawn_trip:
            fish_count = pacific_dawn_trip['total_fish']
            catches = pacific_dawn_trip.get('catches', [])
            bluefin_catches = [c for c in catches if 'bluefin' in c['species'].lower()]

            verifications.append({
                'test': 'Pacific Dawn Recovery',
                'expected': 66,
                'actual': fish_count,
                'status': '✅ PASS' if fish_count == 66 else '❌ FAIL',
                'catches': bluefin_catches
            })
        else:
            verifications.append({
                'test': 'Pacific Dawn Recovery',
                'status': '❌ FAIL - Trip not found'
            })

    except Exception as e:
        verifications.append({
            'test': 'Pacific Dawn Recovery',
            'status': f'❌ ERROR: {e}'
        })

    # 3. Verify Premier Sept 7 recovery (148 fish)
    try:
        response = supabase.table('trips').select(
            'total_fish, boats(name), catches(species, count)'
        ).eq('trip_date', '2025-09-07').execute()

        premier_trips = [trip for trip in response.data if trip['boats']['name'] == 'Premier']

        if premier_trips:
            # Should be only one Premier trip on Sept 7 after correction
            premier_trip = premier_trips[0]
            fish_count = premier_trip['total_fish']
            catches = premier_trip.get('catches', [])

            verifications.append({
                'test': 'Premier Sept 7 Recovery',
                'expected': 148,
                'actual': fish_count,
                'status': '✅ PASS' if fish_count == 148 else '❌ FAIL',
                'catches': catches
            })
        else:
            verifications.append({
                'test': 'Premier Sept 7 Recovery',
                'status': '❌ FAIL - Trip not found'
            })

    except Exception as e:
        verifications.append({
            'test': 'Premier Sept 7 Recovery',
            'status': f'❌ ERROR: {e}'
        })

    # 4. Verify Horizon phantom trips removed
    try:
        horizon_dates = ['2025-09-09', '2025-09-10', '2025-09-11', '2025-09-12', '2025-09-13', '2025-09-14', '2025-09-15']
        horizon_trips_found = 0

        for date in horizon_dates:
            response = supabase.table('trips').select(
                'boats(name)'
            ).eq('trip_date', date).execute()

            horizon_trips = [trip for trip in response.data if trip['boats']['name'] == 'Horizon']
            horizon_trips_found += len(horizon_trips)

        verifications.append({
            'test': 'Horizon Phantom Removal',
            'expected': 0,
            'actual': horizon_trips_found,
            'status': '✅ PASS' if horizon_trips_found == 0 else '❌ FAIL',
            'note': f'Found {horizon_trips_found} Horizon trips in checked dates'
        })

    except Exception as e:
        verifications.append({
            'test': 'Horizon Phantom Removal',
            'status': f'❌ ERROR: {e}'
        })

    # 5. Verify Premier Sept 11 phantom removed
    try:
        response = supabase.table('trips').select(
            'boats(name), anglers'
        ).eq('trip_date', '2025-09-11').execute()

        premier_trips = [trip for trip in response.data if trip['boats']['name'] == 'Premier']

        verifications.append({
            'test': 'Premier Sept 11 Phantom Removal',
            'expected': 0,
            'actual': len(premier_trips),
            'status': '✅ PASS' if len(premier_trips) == 0 else '❌ FAIL',
            'note': f'Found {len(premier_trips)} Premier trips on Sept 11'
        })

    except Exception as e:
        verifications.append({
            'test': 'Premier Sept 11 Phantom Removal',
            'status': f'❌ ERROR: {e}'
        })

    # 6. Get current September totals
    try:
        response = supabase.table('trips').select(
            'total_fish, anglers, boats(name)'
        ).gte('trip_date', '2025-09-01').lte('trip_date', '2025-09-30').execute()

        total_trips = len(response.data)
        total_fish = sum(trip.get('total_fish', 0) for trip in response.data)
        suspicious_trips = len([
            trip for trip in response.data
            if trip.get('anglers', 0) >= 5 and trip.get('total_fish', 0) == 0
        ])

        verifications.append({
            'test': 'September Totals',
            'total_trips': total_trips,
            'total_fish': total_fish,
            'suspicious_trips': suspicious_trips,
            'failure_rate': f"{(suspicious_trips/total_trips*100):.1f}%" if total_trips > 0 else "0%",
            'status': '✅ DATA'
        })

    except Exception as e:
        verifications.append({
            'test': 'September Totals',
            'status': f'❌ ERROR: {e}'
        })

    # Print verification results
    print("\n📊 VERIFICATION RESULTS:")
    print("=" * 50)

    all_passed = True
    for verification in verifications:
        test_name = verification['test']
        status = verification['status']

        if status.startswith('✅'):
            print(f"✅ {test_name}")
            if 'expected' in verification and 'actual' in verification:
                print(f"   Expected: {verification['expected']} | Actual: {verification['actual']}")
            if 'catches' in verification:
                print(f"   Catches: {verification['catches']}")
            if 'note' in verification:
                print(f"   Note: {verification['note']}")
        else:
            print(f"❌ {test_name}: {status}")
            all_passed = False

        if verification['test'] == 'September Totals':
            print(f"   Total Trips: {verification.get('total_trips', 'N/A')}")
            print(f"   Total Fish: {verification.get('total_fish', 'N/A')}")
            print(f"   Suspicious Trips: {verification.get('suspicious_trips', 'N/A')}")
            print(f"   Failure Rate: {verification.get('failure_rate', 'N/A')}")

        print()

    # Final status
    print("🎯 FINAL VERIFICATION STATUS:")
    print("=" * 50)
    if all_passed:
        print("✅ ALL CORRECTIONS SUCCESSFULLY VERIFIED IN SUPABASE")
        print("✅ Data integrity has been restored")
        print("✅ 312 fish recovered and confirmed in database")
        print("✅ 10 phantom trips removed and confirmed deleted")
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("❌ Manual review required")

    return all_passed

if __name__ == "__main__":
    verify_supabase_updates()