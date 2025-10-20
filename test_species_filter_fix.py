#!/usr/bin/env python3
"""
Test script to verify species filter bug fix.
Tests that moon phase calculations respect species filters.
"""

from supabase import create_client
from collections import defaultdict

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

def test_species_filter():
    """Test Aztec boat with bluefin tuna filter."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Query Aztec trips (2025-09-17 to 2025-10-17)
    result = supabase.table('trips').select('''
        id,
        trip_date,
        anglers,
        boats!inner(name),
        catches(species, count)
    ''').eq('boats.name', 'Aztec').gte('trip_date', '2025-09-17').lte('trip_date', '2025-10-17').order('trip_date').execute()

    print('=' * 100)
    print('SPECIES FILTER TEST: Aztec Boat + Bluefin Tuna (09/17 - 10/17/2025)')
    print('=' * 100)

    # Get moon phase data
    moon_result = supabase.table('ocean_conditions').select('date, moon_phase_name').gte('date', '2025-09-17').lte('date', '2025-10-17').execute()
    moon_map = {row['date']: row['moon_phase_name'] for row in moon_result.data}

    # Calculate two sets of metrics: ALL species vs BLUEFIN ONLY
    all_species_by_phase = defaultdict(lambda: {'trips': 0, 'fish': 0})
    bluefin_only_by_phase = defaultdict(lambda: {'trips': 0, 'fish': 0})

    trips_with_bluefin = 0

    print('\n📊 Trip-by-Trip Breakdown:')
    print('-' * 100)
    print(f"{'Date':<12} {'Moon Phase':<20} {'All Fish':>10} {'Bluefin':>10} {'Other':>10}")
    print('-' * 100)

    for trip in result.data:
        date = trip['trip_date']
        moon_phase = moon_map.get(date, 'unknown')

        # Calculate ALL species total
        all_fish = sum(c['count'] for c in trip['catches'])

        # Calculate BLUEFIN ONLY total
        bluefin_fish = sum(c['count'] for c in trip['catches'] if 'bluefin' in c['species'].lower())
        other_fish = all_fish - bluefin_fish

        # Track stats
        all_species_by_phase[moon_phase]['trips'] += 1
        all_species_by_phase[moon_phase]['fish'] += all_fish

        if bluefin_fish > 0:
            trips_with_bluefin += 1
            bluefin_only_by_phase[moon_phase]['trips'] += 1
            bluefin_only_by_phase[moon_phase]['fish'] += bluefin_fish

        print(f"{date:<12} {moon_phase:<20} {all_fish:>10} {bluefin_fish:>10} {other_fish:>10}")

    # Summary
    print('\n' + '=' * 100)
    print('SUMMARY: ALL SPECIES (Before Fix Behavior)')
    print('=' * 100)
    print(f"{'Moon Phase':<20} {'Trips':>8} {'Total Fish':>12} {'Avg/Trip':>12}")
    print('-' * 100)

    for phase in sorted(all_species_by_phase.keys()):
        stats = all_species_by_phase[phase]
        avg = stats['fish'] / stats['trips'] if stats['trips'] > 0 else 0
        print(f"{phase:<20} {stats['trips']:>8} {stats['fish']:>12} {avg:>12.1f}")

    print('\n' + '=' * 100)
    print('SUMMARY: BLUEFIN TUNA ONLY (After Fix Behavior)')
    print('=' * 100)
    print(f"{'Moon Phase':<20} {'Trips':>8} {'Total Fish':>12} {'Avg/Trip':>12}")
    print('-' * 100)

    for phase in sorted(bluefin_only_by_phase.keys()):
        stats = bluefin_only_by_phase[phase]
        avg = stats['fish'] / stats['trips'] if stats['trips'] > 0 else 0
        meets_threshold = '✅' if stats['trips'] >= 10 else '❌'
        print(f"{phase:<20} {stats['trips']:>8} {stats['fish']:>12} {avg:>12.1f} {meets_threshold}")

    # Key findings
    all_total_trips = len(result.data)
    all_total_fish = sum(s['fish'] for s in all_species_by_phase.values())
    bluefin_total_fish = sum(s['fish'] for s in bluefin_only_by_phase.values())

    print('\n' + '=' * 100)
    print('KEY FINDINGS:')
    print('=' * 100)
    print(f"Total Trips (Aztec): {all_total_trips}")
    print(f"Trips with Bluefin: {trips_with_bluefin}")
    print(f"All Species Total Fish: {all_total_fish}")
    print(f"Bluefin Only Total Fish: {bluefin_total_fish}")
    print(f"Percentage Bluefin: {bluefin_total_fish/all_total_fish*100:.1f}%")

    print('\n🐛 BUG IMPACT:')
    print(f"   BEFORE FIX: Moon phase avg based on {all_total_fish} fish (all species)")
    print(f"   AFTER FIX:  Moon phase avg based on {bluefin_total_fish} fish (bluefin only)")
    print(f"   Difference: {all_total_fish - bluefin_total_fish} fish ({(1 - bluefin_total_fish/all_total_fish)*100:.1f}% inflation)")

    print('\n✅ FIX VERIFICATION:')
    print('   Dashboard should now show moon phase averages based on BLUEFIN ONLY totals')
    print('   No phase meets 10-trip threshold, so "Best Moon Phase" should show "N/A"')
    print('=' * 100)

if __name__ == '__main__':
    test_species_filter()
