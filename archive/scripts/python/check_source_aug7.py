#!/usr/bin/env python3
"""Check Aug 7 source page for Dolphin trips."""

import requests
from boats_scraper import parse_boats_page, BOATS_URL_TEMPLATE

# Fetch Aug 7 source page
url = BOATS_URL_TEMPLATE.format(date='2025-08-07')
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Fetching: {url}\n")
response = requests.get(url, headers=headers, timeout=30)
html = response.text

# Parse trips
trips = parse_boats_page(html, '2025-08-07')

# Find Dolphin trips
dolphin_trips = [t for t in trips if 'Dolphin' in t['boat_name']]

print(f"Found {len(dolphin_trips)} Dolphin trip(s) on 2025-08-07:\n")

for i, trip in enumerate(dolphin_trips, 1):
    print(f"Trip {i}:")
    print(f"  Boat: {trip['boat_name']}")
    print(f"  Landing: {trip['landing_name']}")
    print(f"  Duration: {trip['trip_duration']}")
    print(f"  Anglers: {trip['anglers']}")
    print(f"  Catches:")
    for catch in sorted(trip['catches'], key=lambda x: x['species']):
        print(f"    {catch['count']} {catch['species']}")
    print()
