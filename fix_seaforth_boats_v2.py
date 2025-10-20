#!/usr/bin/env python3
"""
Fix Seaforth Sportfishing Boat Misattribution - Version 2
==========================================================

Uses Bright Data scraper to bypass 403 blocks

Author: Fishing Intelligence Platform
Date: October 16, 2025
"""

import json
import subprocess
from supabase import create_client
from colorama import Fore, init
import re

init(autoreset=True)

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_boats_from_markdown(markdown: str, date: str) -> list:
    """Parse boat data from markdown text"""
    trips = []
    lines = markdown.split('\n')

    current_landing = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check for Seaforth landing header
        if 'Seaforth Sportfishing Fish Counts' in line:
            current_landing = 'Seaforth Sportfishing'
            i += 1
            continue

        # Stop if we hit another landing
        if 'Fish Counts' in line and current_landing == 'Seaforth Sportfishing' and 'Seaforth' not in line:
            break

        # Look for boat name, landing, location pattern
        if current_landing == 'Seaforth Sportfishing':
            # Pattern: Boat name followed by "Seaforth Sportfishing" then location
            if i + 4 < len(lines):
                potential_boat = line
                next_line = lines[i + 1].strip()

                if next_line == 'Seaforth Sportfishing':
                    # This is a boat entry
                    boat_name = potential_boat

                    # Skip landing and location lines
                    i += 3

                    # Next line should have anglers and trip type
                    if i < len(lines):
                        angler_line = lines[i].strip()
                        match = re.search(r'(\d+)\s+Anglers', angler_line)
                        if match:
                            anglers = int(match.group(1))

                            # Trip type is after "Anglers"
                            trip_type = angler_line.split('Anglers', 1)[1].strip() if 'Anglers' in angler_line else ''

                            # Next line is catches
                            i += 1
                            if i < len(lines):
                                catches = lines[i].strip()

                                trips.append({
                                    'boat_name': boat_name,
                                    'trip_duration': trip_type,
                                    'anglers': anglers,
                                    'catches_text': catches,
                                    'trip_date': date
                                })

        i += 1

    return trips

def main():
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔧 FIXING SEAFORTH BOAT MISATTRIBUTIONS (Manual Mode)")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    # Get unique dates that need fixing
    trips_329 = supabase.table('trips').select('trip_date').eq('boat_id', 329).execute()
    unique_dates = sorted(set(t['trip_date'] for t in trips_329.data))

    print(f"Found {len(unique_dates)} unique dates to process:")
    for date in unique_dates:
        count = len([t for t in trips_329.data if t['trip_date'] == date])
        print(f"  {date}: {count} trips")

    print(f"\n{Fore.YELLOW}Next steps:")
    print(f"1. For each date above, manually visit:")
    print(f"   https://www.sandiegofishreports.com/dock_totals/boats.php?date=YYYY-MM-DD")
    print(f"2. Copy the Seaforth Sportfishing section")
    print(f"3. Or use Claude MCP Bright Data scraper to fetch the data")

    print(f"\n{Fore.CYAN}Sample command to get data for a date:")
    print(f"  Use: mcp__Bright_Data__scrape_as_markdown")
    print(f"  URL: https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-15")

if __name__ == '__main__':
    main()
