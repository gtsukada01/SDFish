#!/usr/bin/env python3
"""Test the boats parser with real data"""

sample_text = """
H&M Landing Fish Counts
Boat	Trip Details	Dock Totals
Alicia
H&M Landing
San Diego, CA	8 Anglers
1/2 Day Twilight	28 Spiny Lobster, 9 Rock Crab, 49 Spiny Lobster Released
Excalibur
H&M Landing
San Diego, CA	19 Anglers
2 Day	16 Bluefin Tuna, 2 Yellowtail, 6 Yellowfin Tuna
Premier
H&M Landing
San Diego, CA	16 Anglers
1/2 Day AM	97 Rockfish
"""

lines = [l.strip() for l in sample_text.split('\n') if l.strip()]

import re

for i, line in enumerate(lines):
    boat_match = re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line)
    print(f"{i:2d}: '{line}' -> Match: {bool(boat_match)}")

print("\nBoat names found:")
for i, line in enumerate(lines):
    if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line):
        print(f"  {i}: {line}")
