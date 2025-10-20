#!/usr/bin/env python3
"""
Test date extraction from boats.php page
"""

import requests
from bs4 import BeautifulSoup
import re

# Fetch page with proper User-Agent
url = "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-17"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

print("Fetching page...")
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Size: {len(response.text)} bytes\n")

soup = BeautifulSoup(response.text, 'lxml')

# Try to find the date in page title
print("=== PAGE TITLE ===")
if soup.title:
    print(soup.title.string)
print()

# Find all text content
page_text = soup.get_text()
lines = [l.strip() for l in page_text.split('\n') if l.strip()]

# Look for any line containing date-related text
print("=== LINES CONTAINING 'DOCK' OR 'TOTAL' ===")
for i, line in enumerate(lines[:100]):  # First 100 lines
    if 'dock' in line.lower() or 'total' in line.lower():
        if 'cookie' not in line.lower() and len(line) < 100:
            print(f"{i:3d}: {line}")

print("\n=== LOOKING FOR DATE PATTERNS ===")
# Pattern 1: "Dock Totals for Tuesday 10/15/2025"
pattern1 = r'Dock\s+Totals\s+for\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})/(\d{1,2})/(\d{4})'
match = re.search(pattern1, page_text, re.IGNORECASE)
if match:
    print(f"Pattern 1 matched: {match.group(0)}")
else:
    print("Pattern 1 not found")

# Pattern 2: Just "10/17/2025" or similar
pattern2 = r'(\d{1,2})/(\d{1,2})/(\d{4})'
matches = re.findall(pattern2, page_text)
if matches:
    print(f"Pattern 2 found {len(matches)} dates:")
    for m in matches[:5]:  # Show first 5
        print(f"  {m[0]}/{m[1]}/{m[2]}")
else:
    print("Pattern 2 not found")

# Pattern 3: Look for the specific boat page structure
print("\n=== LOOKING FOR BOAT PAGE IDENTIFIERS ===")
if 'H&M Landing' in page_text:
    print("✅ H&M Landing found")
if 'Fish Counts' in page_text:
    print("✅ Fish Counts found")
if 'Boat\tTrip Details' in page_text or 'Boat' in page_text and 'Trip Details' in page_text:
    print("✅ Boat/Trip Details table headers found")
