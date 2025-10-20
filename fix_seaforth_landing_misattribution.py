#!/usr/bin/env python3
"""
Fix Seaforth Landing Name Misattribution (Boat ID 374)
=======================================================

Problem: Boat ID 374 "Seaforth Sportfishing" contains 196 trips that were
incorrectly scraped with the landing name instead of actual boat names.

This happened because the parser didn't check if the "boat name" was actually
the landing name repeated in each boat entry.

Solution: Re-scrape each affected date and match trips to correct boats based on:
- Trip date
- Trip duration
- Number of anglers
- Species caught (if needed for disambiguation)

Author: Fishing Intelligence Platform
Date: October 17, 2025
"""

import time
import re
import requests
from bs4 import BeautifulSoup
from boats_scraper import init_supabase
from colorama import Fore, init

init(autoreset=True)

BASE_URL = "https://www.sandiegofishreports.com"
BOATS_URL_TEMPLATE = f"{BASE_URL}/dock_totals/boats.php?date={{date}}"

supabase = init_supabase()

def fetch_boats_page(date: str) -> str:
    """Fetch boats.php page for a specific date"""
    url = BOATS_URL_TEMPLATE.format(date=date)
    print(f"{Fore.CYAN}🌐 Fetching: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"{Fore.RED}❌ Failed: {e}")
        return None

def parse_seaforth_section(html: str, date: str) -> list:
    """Parse boats page and extract only Seaforth Sportfishing trips"""
    soup = BeautifulSoup(html, 'lxml')
    page_text = soup.get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]

    trips = []
    current_landing = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for Seaforth landing header
        if 'Seaforth Sportfishing Fish Counts' in line:
            current_landing = 'Seaforth Sportfishing'
            i += 1
            continue

        # Stop if we hit another landing
        if current_landing == 'Seaforth Sportfishing' and 'Fish Counts' in line and i > 5:
            break

        # Skip headers
        if line.startswith('Boat\t') or 'Trip Details' in line:
            i += 1
            continue

        # Parse boat entry (only if we're in Seaforth section)
        if current_landing == 'Seaforth Sportfishing' and i + 3 < len(lines):
            # Check for boat name pattern
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', line):
                boat_name = line

                # Skip if this is the landing name itself
                if boat_name == 'Seaforth Sportfishing':
                    i += 1
                    continue

                # Next line should be landing name
                i += 1
                if i >= len(lines):
                    break

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

                            # Get catches from next line
                            if i + offset + 1 < len(lines):
                                catches_text = lines[i + offset + 1]

                            i += offset + 2
                            break

                if anglers > 0 and trip_duration and catches_text:
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
    # Remove extra spaces
    duration = ' '.join(duration.split())
    return duration.strip()

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
        if scraped['anglers'] == db_anglers and scraped_duration in db_duration or db_duration in scraped_duration:
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

def main():
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔧 FIXING SEAFORTH LANDING NAME MISATTRIBUTIONS (BOAT ID 374)")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    # Get all trips from boat ID 374
    trips_374 = supabase.table('trips').select('id, trip_date, trip_duration, anglers').eq('boat_id', 374).order('trip_date').execute()

    print(f"Found {len(trips_374.data)} trips to fix\n")

    # Group by date
    dates = {}
    for trip in trips_374.data:
        date = trip['trip_date']
        if date not in dates:
            dates[date] = []
        dates[date].append(trip)

    print(f"Covering {len(dates)} unique dates\n")

    fixed_count = 0
    error_count = 0
    seaforth_landing_id = 14

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

        # Parse Seaforth trips from page
        scraped_trips = parse_seaforth_section(html, date)
        print(f"{Fore.GREEN}Found {len(scraped_trips)} Seaforth trips on page")

        if scraped_trips:
            print(f"{Fore.YELLOW}  Boats found: {', '.join(set(t['boat_name'] for t in scraped_trips))}")

        # Match each database trip to scraped data
        for db_trip in dates[date]:
            print(f"\n{Fore.YELLOW}  DB Trip: {db_trip['trip_duration']:25s} | {db_trip['anglers']} anglers")

            match = find_matching_trip(db_trip, scraped_trips)

            if match:
                correct_boat = match['boat_name']
                print(f"{Fore.GREEN}  ✅ Match: {correct_boat}")

                # Get/create correct boat ID
                correct_boat_id = get_or_create_boat(correct_boat, seaforth_landing_id)

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
                error_count += 1

        # Delay between requests
        time.sleep(3)

    # Summary
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}📊 SUMMARY")
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.GREEN}✅ Fixed: {fixed_count}")
    print(f"{Fore.RED}❌ Errors: {error_count}")

    # Check if boat 374 has any remaining trips
    remaining = supabase.table('trips').select('id', count='exact').eq('boat_id', 374).execute()

    if remaining.count == 0:
        print(f"\n{Fore.GREEN}✅ All trips reassigned! Boat ID 374 can now be deleted.")

        # Ask for confirmation before deleting
        response = input(f"\n{Fore.YELLOW}Delete boat ID 374 'Seaforth Sportfishing'? (y/n): ")
        if response.lower() == 'y':
            try:
                supabase.table('boats').delete().eq('id', 374).execute()
                print(f"{Fore.GREEN}✅ Deleted boat ID 374 'Seaforth Sportfishing'")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Couldn't delete boat: {e}")
        else:
            print(f"{Fore.YELLOW}⚠️  Boat ID 374 not deleted (manual deletion required)")
    else:
        print(f"\n{Fore.YELLOW}⚠️  {remaining.count} trips still on boat 374")

if __name__ == '__main__':
    main()
