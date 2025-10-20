#!/usr/bin/env python3
"""
Validate Data Integrity
========================

Performs comprehensive validation checks on the Supabase database:
- Foreign key integrity (orphaned records)
- Data quality checks (null values, invalid dates)
- Duplicate detection
- Statistical anomalies

Usage:
    python3 validate_data.py
"""

import sys
from datetime import datetime
from supabase import create_client
from colorama import Fore, Style, init
from collections import Counter

# Initialize colorama
init(autoreset=True)

# Supabase configuration
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

def main():
    """Main validation"""
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔍 San Diego Fish Scraper - Data Validation")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    errors = []
    warnings = []

    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"{Fore.GREEN}✅ Connected to Supabase\n")

        # ===================================================================
        # TEST 1: Foreign Key Integrity - Boats → Landings
        # ===================================================================
        print(f"{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 1: Foreign Key Integrity - Boats → Landings")
        print(f"{Fore.CYAN}{'─'*80}")

        boats = supabase.table('boats').select('id, name, landing_id').execute()
        landings = supabase.table('landings').select('id').execute()
        landing_ids = {l['id'] for l in landings.data}

        orphaned_boats = [b for b in boats.data if b['landing_id'] not in landing_ids]
        if orphaned_boats:
            errors.append(f"Found {len(orphaned_boats)} boats with invalid landing_id")
            print(f"{Fore.RED}❌ Found {len(orphaned_boats)} orphaned boats:")
            for boat in orphaned_boats[:5]:  # Show first 5
                print(f"{Fore.RED}   - Boat ID {boat['id']} ({boat['name']}) → Invalid landing_id {boat['landing_id']}")
        else:
            print(f"{Fore.GREEN}✅ All boats have valid landing_id")

        # ===================================================================
        # TEST 2: Foreign Key Integrity - Trips → Boats
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 2: Foreign Key Integrity - Trips → Boats")
        print(f"{Fore.CYAN}{'─'*80}")

        trips = supabase.table('trips').select('id, trip_date, boat_id').execute()
        boat_ids = {b['id'] for b in boats.data}

        orphaned_trips = [t for t in trips.data if t['boat_id'] not in boat_ids]
        if orphaned_trips:
            errors.append(f"Found {len(orphaned_trips)} trips with invalid boat_id")
            print(f"{Fore.RED}❌ Found {len(orphaned_trips)} orphaned trips:")
            for trip in orphaned_trips[:5]:
                print(f"{Fore.RED}   - Trip ID {trip['id']} ({trip['trip_date']}) → Invalid boat_id {trip['boat_id']}")
        else:
            print(f"{Fore.GREEN}✅ All trips have valid boat_id")

        # ===================================================================
        # TEST 3: Foreign Key Integrity - Catches → Trips
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 3: Foreign Key Integrity - Catches → Trips")
        print(f"{Fore.CYAN}{'─'*80}")

        catches = supabase.table('catches').select('id, trip_id, species, count').execute()
        trip_ids = {t['id'] for t in trips.data}

        orphaned_catches = [c for c in catches.data if c['trip_id'] not in trip_ids]
        if orphaned_catches:
            errors.append(f"Found {len(orphaned_catches)} catches with invalid trip_id")
            print(f"{Fore.RED}❌ Found {len(orphaned_catches)} orphaned catches:")
            for catch in orphaned_catches[:5]:
                print(f"{Fore.RED}   - Catch ID {catch['id']} ({catch['species']}) → Invalid trip_id {catch['trip_id']}")
        else:
            print(f"{Fore.GREEN}✅ All catches have valid trip_id")

        # ===================================================================
        # TEST 4: Duplicate Trips
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 4: Duplicate Trip Detection")
        print(f"{Fore.CYAN}{'─'*80}")

        trip_keys = [(t['boat_id'], t['trip_date']) for t in trips.data]
        trip_counts = Counter(trip_keys)
        duplicates = {k: v for k, v in trip_counts.items() if v > 1}

        if duplicates:
            warnings.append(f"Found {len(duplicates)} potential duplicate trips")
            print(f"{Fore.YELLOW}⚠️  Found {len(duplicates)} potential duplicates:")
            for (boat_id, trip_date), count in list(duplicates.items())[:5]:
                print(f"{Fore.YELLOW}   - Boat {boat_id} on {trip_date}: {count} entries")
        else:
            print(f"{Fore.GREEN}✅ No duplicate trips found")

        # ===================================================================
        # TEST 5: Invalid Dates
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 5: Date Validation")
        print(f"{Fore.CYAN}{'─'*80}")

        today = datetime.now().date()
        min_date = datetime(2020, 1, 1).date()  # Reasonable minimum

        future_trips = []
        old_trips = []

        for trip in trips.data:
            trip_date = datetime.fromisoformat(trip['trip_date']).date()
            if trip_date > today:
                future_trips.append(trip)
            elif trip_date < min_date:
                old_trips.append(trip)

        if future_trips:
            warnings.append(f"Found {len(future_trips)} trips with future dates")
            print(f"{Fore.YELLOW}⚠️  Found {len(future_trips)} trips with future dates:")
            for trip in future_trips[:5]:
                print(f"{Fore.YELLOW}   - Trip ID {trip['id']} on {trip['trip_date']}")
        else:
            print(f"{Fore.GREEN}✅ No trips with future dates")

        if old_trips:
            warnings.append(f"Found {len(old_trips)} trips before {min_date}")
            print(f"{Fore.YELLOW}⚠️  Found {len(old_trips)} trips before {min_date}:")
            for trip in old_trips[:5]:
                print(f"{Fore.YELLOW}   - Trip ID {trip['id']} on {trip['trip_date']}")
        else:
            print(f"{Fore.GREEN}✅ All trips have reasonable dates")

        # ===================================================================
        # TEST 6: Invalid Catch Counts
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 6: Catch Count Validation")
        print(f"{Fore.CYAN}{'─'*80}")

        invalid_counts = [c for c in catches.data if c['count'] <= 0]
        if invalid_counts:
            errors.append(f"Found {len(invalid_counts)} catches with count <= 0")
            print(f"{Fore.RED}❌ Found {len(invalid_counts)} catches with invalid counts:")
            for catch in invalid_counts[:5]:
                print(f"{Fore.RED}   - Catch ID {catch['id']} ({catch['species']}): count = {catch['count']}")
        else:
            print(f"{Fore.GREEN}✅ All catches have valid counts (> 0)")

        # Check for unusually high counts (potential data entry errors)
        high_counts = [c for c in catches.data if c['count'] > 1000]
        if high_counts:
            warnings.append(f"Found {len(high_counts)} catches with count > 1000")
            print(f"{Fore.YELLOW}⚠️  Found {len(high_counts)} catches with unusually high counts:")
            for catch in high_counts[:5]:
                print(f"{Fore.YELLOW}   - Catch ID {catch['id']} ({catch['species']}): count = {catch['count']}")
        else:
            print(f"{Fore.GREEN}✅ No unusually high catch counts")

        # ===================================================================
        # TEST 7: Missing Species Names
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 7: Species Name Validation")
        print(f"{Fore.CYAN}{'─'*80}")

        empty_species = [c for c in catches.data if not c.get('species') or c['species'].strip() == '']
        if empty_species:
            errors.append(f"Found {len(empty_species)} catches with missing species names")
            print(f"{Fore.RED}❌ Found {len(empty_species)} catches with missing species:")
            for catch in empty_species[:5]:
                print(f"{Fore.RED}   - Catch ID {catch['id']}: species = '{catch.get('species', 'NULL')}'")
        else:
            print(f"{Fore.GREEN}✅ All catches have species names")

        # Check for species name quality
        species_list = [c['species'] for c in catches.data if c.get('species')]
        unique_species = set(species_list)
        print(f"{Fore.CYAN}📊 Total unique species: {len(unique_species)}")

        # Look for potential typos (species with very low counts)
        species_counts = Counter(species_list)
        rare_species = [s for s, c in species_counts.items() if c == 1]
        if rare_species:
            print(f"{Fore.YELLOW}⚠️  Found {len(rare_species)} species with only 1 record (potential typos):")
            for species in rare_species[:10]:
                print(f"{Fore.YELLOW}   - {species}")

        # ===================================================================
        # TEST 8: Trips Without Catches
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}TEST 8: Trips Without Catches")
        print(f"{Fore.CYAN}{'─'*80}")

        trip_ids_with_catches = {c['trip_id'] for c in catches.data}
        trips_without_catches = [t for t in trips.data if t['id'] not in trip_ids_with_catches]

        if trips_without_catches:
            warnings.append(f"Found {len(trips_without_catches)} trips without catches")
            print(f"{Fore.YELLOW}⚠️  Found {len(trips_without_catches)} trips without catches:")
            for trip in trips_without_catches[:5]:
                print(f"{Fore.YELLOW}   - Trip ID {trip['id']} on {trip['trip_date']}")
        else:
            print(f"{Fore.GREEN}✅ All trips have at least one catch")

        # ===================================================================
        # FINAL SUMMARY
        # ===================================================================
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}📋 Validation Summary")
        print(f"{Fore.MAGENTA}{'='*80}")

        if not errors and not warnings:
            print(f"{Fore.GREEN}✅ ALL TESTS PASSED - No data integrity issues found!")
        else:
            if errors:
                print(f"{Fore.RED}❌ ERRORS FOUND: {len(errors)}")
                for error in errors:
                    print(f"{Fore.RED}   - {error}")

            if warnings:
                print(f"{Fore.YELLOW}⚠️  WARNINGS: {len(warnings)}")
                for warning in warnings:
                    print(f"{Fore.YELLOW}   - {warning}")

        print(f"\n{Fore.CYAN}📊 Database Statistics:")
        print(f"{Fore.CYAN}   - Landings: {len(landings.data)}")
        print(f"{Fore.CYAN}   - Boats: {len(boats.data)}")
        print(f"{Fore.CYAN}   - Trips: {len(trips.data)}")
        print(f"{Fore.CYAN}   - Catches: {len(catches.data)}")
        print(f"{Fore.CYAN}   - Unique Species: {len(unique_species)}")

        print(f"{Fore.MAGENTA}{'='*80}\n")

        # Exit code based on results
        if errors:
            sys.exit(1)  # Fatal errors
        elif warnings:
            sys.exit(0)  # Warnings but no fatal errors
        else:
            sys.exit(0)  # All good

    except Exception as e:
        print(f"{Fore.RED}❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
