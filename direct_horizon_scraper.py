#!/usr/bin/env python3
"""
Direct scraper for Horizon phantom trip investigation
Get the exact data from the source and push to Supabase
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from supabase import create_client

# Horizon problem dates from our analysis
HORIZON_DATES = [
    '2025-09-15', '2025-09-14', '2025-09-13', '2025-09-12',
    '2025-09-11', '2025-09-10', '2025-09-09'
]

def setup_supabase():
    """Set up Supabase client"""
    url = "https://ulsbtwqhwnrpkourphiq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
    return create_client(url, key)

def scrape_date(date):
    """Scrape fishing data for a specific date"""
    url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={date}"
    print(f"\n🔍 Scraping {date} - {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for boat data in the HTML structure
        boats_found = []

        # Find the main content area
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])

                # Look for patterns that indicate boat names
                for cell in cells:
                    text = cell.get_text().strip()

                    # Skip headers and empty cells
                    if not text or text in ['Date', 'Boat', 'Landing', 'Fish', 'Anglers']:
                        continue

                    # Check if this looks like a boat name or fishing data
                    if any(word in text.lower() for word in ['bluefin', 'yellowtail', 'tuna', 'bass', 'rockfish']):
                        # This looks like catch data
                        print(f"  Found catch data: {text}")
                    elif len(text) > 3 and text.replace(' ', '').replace('-', '').replace('.', '').isalnum():
                        # This might be a boat name
                        print(f"  Potential boat: {text}")

        # Also look for any mention of "Horizon"
        page_text = soup.get_text()
        if 'horizon' in page_text.lower():
            print(f"  ⚠️  Found 'Horizon' in page text!")
        else:
            print(f"  ✅ Confirmed: No 'Horizon' boat on {date}")

        # Look for structured fishing data
        # Try different parsing approaches to find the actual data

        # Method 1: Look for common fishing report patterns
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('bluefin' in line.lower() or 'yellowtail' in line.lower() or 'bass' in line.lower()):
                print(f"  Fishing data: {line}")

        return boats_found

    except Exception as e:
        print(f"❌ Error scraping {date}: {e}")
        return []

def remove_phantom_horizon_trips():
    """Remove phantom Horizon trips from database"""
    supabase = setup_supabase()

    print("\n🗑️  REMOVING PHANTOM HORIZON TRIPS")
    print("=" * 50)

    for date in HORIZON_DATES:
        try:
            # Find Horizon trips on this date
            response = supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, boats(name)'
            ).eq('trip_date', date).execute()

            trips = response.data

            horizon_trips = [trip for trip in trips if trip.get('boats', {}).get('name') == 'Horizon']

            if horizon_trips:
                print(f"\n📅 {date}: Found {len(horizon_trips)} Horizon trips to remove")

                for trip in horizon_trips:
                    trip_id = trip['id']
                    anglers = trip['anglers']

                    print(f"  Removing trip ID {trip_id}: Horizon ({anglers} anglers)")

                    # Delete the trip
                    delete_response = supabase.table('trips').delete().eq('id', trip_id).execute()

                    if delete_response.data:
                        print(f"  ✅ Successfully removed trip ID {trip_id}")
                    else:
                        print(f"  ❌ Failed to remove trip ID {trip_id}")
            else:
                print(f"📅 {date}: No Horizon trips found")

        except Exception as e:
            print(f"❌ Error processing {date}: {e}")

def main():
    """Main execution"""
    print("🚨 HORIZON PHANTOM TRIP INVESTIGATION")
    print("=" * 60)

    # First, investigate what's actually on these dates
    for date in HORIZON_DATES:
        scrape_date(date)

    # Ask for confirmation before deleting
    print(f"\n⚠️  READY TO REMOVE PHANTOM HORIZON TRIPS")
    print(f"This will delete Horizon trips from {len(HORIZON_DATES)} dates")
    print(f"Dates: {', '.join(HORIZON_DATES)}")

    confirm = input("\nProceed with deletion? (yes/no): ")

    if confirm.lower() == 'yes':
        remove_phantom_horizon_trips()
        print(f"\n✅ Phantom Horizon trips removed!")
    else:
        print(f"\n❌ Deletion cancelled")

if __name__ == "__main__":
    main()