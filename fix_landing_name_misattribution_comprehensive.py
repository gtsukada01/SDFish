#!/usr/bin/env python3
"""
Comprehensive Landing Name Misattribution Fix
==============================================

Problem: Multiple landings have phantom boat records with the landing name
instead of actual boat names.

Affected:
- Boat ID 374: Seaforth Sportfishing (132 trips, 2024-05-25 to 2025-10-31)
- Boat ID 375: Helgrens Sportfishing (50 trips, 2024-01-19 to 2025-02-16)

Solution: Re-scrape affected dates, match trips by duration + anglers,
update boat_id to correct boats.

Author: Fishing Intelligence Platform
Date: October 17, 2025
Governed By: SPEC 007
"""

import time
import re
import json
import requests
from bs4 import BeautifulSoup
from boats_scraper import init_supabase
from colorama import Fore, init
from datetime import datetime

init(autoreset=True)

BASE_URL = "https://www.sandiegofishreports.com"
BOATS_URL_TEMPLATE = f"{BASE_URL}/dock_totals/boats.php?date={{date}}"

supabase = init_supabase()

# Landing configurations
LANDING_CONFIG = {
    374: {
        'boat_id': 374,
        'boat_name': 'Seaforth Sportfishing',
        'landing_name': 'Seaforth Sportfishing',
        'landing_id': 14
    },
    375: {
        'boat_id': 375,
        'boat_name': 'Helgrens Sportfishing',
        'landing_name': 'Helgrens Sportfishing',
        'landing_id': 29
    }
}

def fetch_boats_page(date: str) -> str:
    """Fetch boats.php page for a specific date"""
    url = BOATS_URL_TEMPLATE.format(date=date)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to fetch {date}: {e}")
        return None

def parse_landing_section(html: str, landing_name: str, date: str) -> list:
    """Parse boats page and extract trips for a specific landing"""
    soup = BeautifulSoup(html, 'lxml')
    page_text = soup.get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]

    trips = []
    current_landing = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for our target landing header
        if f'{landing_name} Fish Counts' in line:
            current_landing = landing_name
            i += 1
            continue

        # Stop if we hit another landing
        if current_landing == landing_name and 'Fish Counts' in line and i > 5:
            break

        # Skip headers
        if line.startswith('Boat\t') or 'Trip Details' in line:
            i += 1
            continue

        # Parse boat entry (only if we're in target landing section)
        if current_landing == landing_name and i + 3 < len(lines):
            # Check for boat name pattern
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', line):
                boat_name = line

                # CRITICAL: Skip if this is the landing name itself
                if boat_name == landing_name:
                    i += 1
                    continue

                # Next line should be landing name - consume it
                i += 1
                if i >= len(lines):
                    break
                # Verify it's actually the landing name
                if lines[i] != landing_name:
                    # Not the expected structure, skip this entry
                    i += 1
                    continue

                # Next line should be location
                i += 1
                if i >= len(lines):
                    break

                # Look for anglers/trip line
                anglers = 0
                trip_duration = None
                catches_text = None

                for offset in range(3):
                    if i + offset < len(lines):
                        line_check = lines[i + offset]
                        combined_match = re.match(r'(\d+)\s+Anglers(.+)', line_check)
                        if combined_match:
                            anglers = int(combined_match.group(1))
                            trip_duration = combined_match.group(2).strip()

                            # Get catches from next line (if exists)
                            if i + offset + 1 < len(lines):
                                catches_text = lines[i + offset + 1]

                            i += offset + 2
                            break

                if anglers > 0 and trip_duration:
                    trips.append({
                        'boat_name': boat_name,
                        'trip_duration': trip_duration,
                        'anglers': anglers,
                        'catches_text': catches_text,
                        'trip_date': date
                    })
                    continue

        i += 1

    return trips

def normalize_trip_duration(duration: str) -> str:
    """Normalize trip duration for matching"""
    return ' '.join(duration.split()).strip()

def find_matching_trip(db_trip, scraped_trips):
    """Find which scraped trip matches the database trip"""
    db_duration = normalize_trip_duration(db_trip['trip_duration'])
    db_anglers = db_trip['anglers']

    # Try exact match first (duration + anglers)
    for scraped in scraped_trips:
        scraped_duration = normalize_trip_duration(scraped['trip_duration'])
        if scraped_duration == db_duration and scraped['anglers'] == db_anglers:
            return scraped

    # Try looser match (just anglers + similar duration)
    for scraped in scraped_trips:
        scraped_duration = normalize_trip_duration(scraped['trip_duration'])
        if scraped['anglers'] == db_anglers and (scraped_duration in db_duration or db_duration in scraped_duration):
            return scraped

    return None

def get_or_create_boat(boat_name: str, landing_id: int) -> int:
    """Get boat ID, create if doesn't exist"""
    result = supabase.table('boats').select('id').eq('name', boat_name).execute()

    if result.data:
        return result.data[0]['id']

    # Create new boat
    result = supabase.table('boats').insert({
        'name': boat_name,
        'landing_id': landing_id
    }).execute()

    print(f"{Fore.GREEN}✅ Created boat: {boat_name} (ID: {result.data[0]['id']})")
    return result.data[0]['id']

def process_landing(boat_id: int):
    """Process all trips for a specific phantom boat ID"""
    config = LANDING_CONFIG[boat_id]

    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔧 PROCESSING {config['boat_name']} (BOAT ID {boat_id})")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    # Get all trips from this phantom boat
    trips_query = supabase.table('trips').select('id, trip_date, trip_duration, anglers').eq('boat_id', boat_id).order('trip_date').execute()

    print(f"Found {len(trips_query.data)} trips to fix\n")

    # Group by date
    dates = {}
    for trip in trips_query.data:
        date = trip['trip_date']
        if date not in dates:
            dates[date] = []
        dates[date].append(trip)

    print(f"Covering {len(dates)} unique dates\n")

    # Track results
    fixed_count = 0
    error_count = 0
    unmatched_trips = []

    for date in sorted(dates.keys()):
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📅 Processing {date} ({len(dates[date])} trips)")
        print(f"{Fore.CYAN}{'='*80}")

        # Fetch boats page for this date
        html = fetch_boats_page(date)
        if not html:
            print(f"{Fore.RED}❌ Couldn't fetch data for {date}, skipping")
            error_count += len(dates[date])
            time.sleep(2)
            continue

        # Parse landing section from page
        scraped_trips = parse_landing_section(html, config['landing_name'], date)
        print(f"{Fore.GREEN}Found {len(scraped_trips)} trips on page")

        if scraped_trips:
            boat_names = set(t['boat_name'] for t in scraped_trips)
            print(f"{Fore.YELLOW}  Boats found: {', '.join(boat_names)}")

        # Match each database trip to scraped data
        for db_trip in dates[date]:
            print(f"\n{Fore.YELLOW}  DB Trip ID {db_trip['id']}: {db_trip['trip_duration']:25s} | {db_trip['anglers']} anglers")

            match = find_matching_trip(db_trip, scraped_trips)

            if match:
                correct_boat = match['boat_name']
                print(f"{Fore.GREEN}  ✅ Match: {correct_boat}")

                # Get/create correct boat ID
                correct_boat_id = get_or_create_boat(correct_boat, config['landing_id'])

                # Update trip
                try:
                    supabase.table('trips').update({'boat_id': correct_boat_id}).eq('id', db_trip['id']).execute()
                    print(f"{Fore.GREEN}  ✅ Updated trip {db_trip['id']} to boat '{correct_boat}' (ID {correct_boat_id})")
                    fixed_count += 1
                except Exception as e:
                    print(f"{Fore.RED}  ❌ Failed to update: {e}")
                    error_count += 1
            else:
                print(f"{Fore.RED}  ❌ No match found")
                unmatched_trips.append({
                    'trip_id': db_trip['id'],
                    'date': date,
                    'duration': db_trip['trip_duration'],
                    'anglers': db_trip['anglers']
                })
                error_count += 1

        # Delay between requests
        time.sleep(3)

    # Summary for this landing
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}📊 SUMMARY FOR {config['boat_name']}")
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.GREEN}✅ Fixed: {fixed_count}")
    print(f"{Fore.RED}❌ Errors: {error_count}")

    if unmatched_trips:
        print(f"\n{Fore.YELLOW}⚠️  Unmatched trips requiring manual review:")
        for trip in unmatched_trips[:10]:  # Show first 10
            print(f"  Trip ID {trip['trip_id']}: {trip['date']} | {trip['duration']} | {trip['anglers']} anglers")
        if len(unmatched_trips) > 10:
            print(f"  ... and {len(unmatched_trips) - 10} more")

    # Save unmatched trips for review
    if unmatched_trips:
        unmatched_file = f'unmatched_trips_boat_{boat_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(unmatched_file, 'w') as f:
            json.dump(unmatched_trips, f, indent=2)
        print(f"\n{Fore.YELLOW}📝 Unmatched trips saved to: {unmatched_file}")

    return {
        'boat_id': boat_id,
        'fixed': fixed_count,
        'errors': error_count,
        'unmatched': unmatched_trips
    }

def main():
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔧 COMPREHENSIVE LANDING NAME MISATTRIBUTION FIX")
    print(f"{Fore.MAGENTA}{'='*80}\n")
    print(f"Processing {len(LANDING_CONFIG)} phantom boats:")
    for boat_id, config in LANDING_CONFIG.items():
        print(f"  - Boat ID {boat_id}: {config['boat_name']}")
    print()

    # Process each landing
    results = []
    for boat_id in LANDING_CONFIG.keys():
        result = process_landing(boat_id)
        results.append(result)
        print("\n")

    # Overall summary
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🎯 OVERALL SUMMARY")
    print(f"{Fore.MAGENTA}{'='*80}")

    total_fixed = sum(r['fixed'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_unmatched = sum(len(r['unmatched']) for r in results)

    print(f"{Fore.GREEN}✅ Total Fixed: {total_fixed}")
    print(f"{Fore.RED}❌ Total Errors: {total_errors}")
    print(f"{Fore.YELLOW}⚠️  Total Unmatched: {total_unmatched}")

    # Check remaining trips on phantom boats
    print(f"\n{Fore.CYAN}Checking remaining trips on phantom boats:")
    for boat_id in LANDING_CONFIG.keys():
        remaining = supabase.table('trips').select('id', count='exact').eq('boat_id', boat_id).execute()
        config = LANDING_CONFIG[boat_id]
        if remaining.count == 0:
            print(f"{Fore.GREEN}✅ Boat ID {boat_id} ({config['boat_name']}): 0 trips - READY FOR DELETION")
        else:
            print(f"{Fore.YELLOW}⚠️  Boat ID {boat_id} ({config['boat_name']}): {remaining.count} trips remaining")

    # Save final summary
    summary_file = f'fix_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'total_fixed': total_fixed,
            'total_errors': total_errors,
            'total_unmatched': total_unmatched
        }, f, indent=2)

    print(f"\n{Fore.GREEN}📝 Summary saved to: {summary_file}")

if __name__ == '__main__':
    main()
