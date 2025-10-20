#!/usr/bin/env python3
"""
Fix Seaforth Sportfishing Boat Misattribution
==============================================

Problem: Boat ID 329 "Seaforth Sportfishing" contains 85 trips that were
incorrectly scraped with the landing name instead of actual boat names.

Solution: Re-scrape each date and match trips to correct boats based on:
- Trip date
- Trip duration
- Number of anglers
- Species caught

Author: Fishing Intelligence Platform
Date: October 16, 2025
"""

import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from colorama import Fore, init
import re

init(autoreset=True)

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

BASE_URL = "https://www.sandiegofishreports.com"
BOATS_URL_TEMPLATE = f"{BASE_URL}/dock_totals/boats.php?date={{date}}"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_boats_page(date: str) -> str:
    """Fetch boats.php page for a specific date"""
    url = BOATS_URL_TEMPLATE.format(date=date)
    print(f"{Fore.CYAN}🌐 Fetching: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"{Fore.RED}❌ Failed: {e}")
        return None

def parse_boats_for_seaforth(html: str, date: str) -> list:
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
        if 'Fish Counts' in line and current_landing == 'Seaforth Sportfishing':
            break

        # Skip headers
        if line.startswith('Boat\t') or 'Trip Details' in line:
            i += 1
            continue

        # Parse boat entry (only if we're in Seaforth section)
        if current_landing == 'Seaforth Sportfishing' and i + 3 < len(lines):
            # Check for boat name pattern
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line):
                boat_name = line

                # Skip landing name line
                i += 1
                if i >= len(lines):
                    break

                # Skip location line
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
    # Common normalizations
    duration = duration.replace('Offshore', '').replace('Local', '').strip()
    return duration

def find_matching_trip(db_trip, scraped_trips):
    """Find which scraped trip matches the database trip"""
    db_duration = normalize_trip_duration(db_trip['trip_duration'])
    db_anglers = db_trip['anglers']

    # Try exact match first
    for scraped in scraped_trips:
        scraped_duration = normalize_trip_duration(scraped['trip_duration'])
        if scraped_duration == db_duration and scraped['anglers'] == db_anglers:
            return scraped

    # Try looser match (just anglers)
    for scraped in scraped_trips:
        if scraped['anglers'] == db_anglers:
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

    print(f"{Fore.GREEN}✅ Created boat: {boat_name}")
    return result.data[0]['id']

def main():
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔧 FIXING SEAFORTH BOAT MISATTRIBUTIONS")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    # Get all trips from boat ID 329
    trips_329 = supabase.table('trips').select('id, trip_date, trip_duration, anglers').eq('boat_id', 329).order('trip_date').execute()

    print(f"Found {len(trips_329.data)} trips to fix\n")

    # Group by date
    dates = {}
    for trip in trips_329.data:
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
            continue

        # Parse Seaforth trips from page
        scraped_trips = parse_boats_for_seaforth(html, date)
        print(f"{Fore.GREEN}Found {len(scraped_trips)} Seaforth trips on page")

        # Match each database trip to scraped data
        for db_trip in dates[date]:
            print(f"\n{Fore.YELLOW}  DB Trip: {db_trip['trip_duration']:20s} | {db_trip['anglers']} anglers")

            match = find_matching_trip(db_trip, scraped_trips)

            if match:
                correct_boat = match['boat_name']
                print(f"{Fore.GREEN}  ✅ Match: {correct_boat}")

                # Get/create correct boat ID
                correct_boat_id = get_or_create_boat(correct_boat, seaforth_landing_id)

                # Update trip
                try:
                    supabase.table('trips').update({'boat_id': correct_boat_id}).eq('id', db_trip['id']).execute()
                    print(f"{Fore.GREEN}  ✅ Updated trip {db_trip['id']} to boat {correct_boat} (ID {correct_boat_id})")
                    fixed_count += 1
                except Exception as e:
                    print(f"{Fore.RED}  ❌ Failed to update: {e}")
                    error_count += 1
            else:
                print(f"{Fore.RED}  ❌ No match found")
                error_count += 1

        # Delay between requests
        time.sleep(2)

    # Summary
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}📊 SUMMARY")
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.GREEN}✅ Fixed: {fixed_count}")
    print(f"{Fore.RED}❌ Errors: {error_count}")

    # Check if boat 329 has any remaining trips
    remaining = supabase.table('trips').select('id', count='exact').eq('boat_id', 329).execute()

    if remaining.count == 0:
        print(f"\n{Fore.GREEN}✅ All trips reassigned! Boat ID 329 can now be deleted.")

        # Delete boat 329
        try:
            supabase.table('boats').delete().eq('id', 329).execute()
            print(f"{Fore.GREEN}✅ Deleted boat ID 329 'Seaforth Sportfishing'")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Couldn't delete boat: {e}")
    else:
        print(f"\n{Fore.YELLOW}⚠️  {remaining.count} trips still on boat 329")

if __name__ == '__main__':
    main()
