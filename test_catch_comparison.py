#!/usr/bin/env python3
"""Test catch comparison logic to debug why Trip 2 isn't being inserted."""

import os
from boats_scraper import catches_identical

# Trip 1 catches (what's in database)
trip1_catches = [
    {'species': 'Cabezon', 'count': 1},
    {'species': 'Calico Bass', 'count': 51},
    {'species': 'Rockfish', 'count': 21},
    {'species': 'Sculpin', 'count': 3},
    {'species': 'Sheephead', 'count': 1}
]

# Trip 2 catches (what should be inserted)
trip2_catches = [
    {'species': 'Barracuda', 'count': 2},
    {'species': 'Cabezon', 'count': 3},
    {'species': 'Calico Bass', 'count': 48},
    {'species': 'Rockfish', 'count': 28},
    {'species': 'Sculpin', 'count': 3}
]

print("Trip 1 catches:", trip1_catches)
print("Trip 2 catches:", trip2_catches)
print()

result = catches_identical(trip1_catches, trip2_catches)
print(f"catches_identical result: {result}")
print()

if result:
    print("❌ BUG: Catches are being marked as identical when they're clearly different!")
else:
    print("✅ CORRECT: Catches are correctly identified as different")
    print()
    print("This means the scraper should be inserting Trip 2...")
    print("Let me check if the issue is with how the scraper is calling check_trip_exists")
