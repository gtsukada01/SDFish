#!/usr/bin/env python3
"""
Southern California Fish Boats Scraper
========================================

Scrapes socalfishreports.com for fishing trip data from multiple regions:
- Avila Beach
- Santa Barbara
- Oxnard/Channel Islands
- Marina Del Rey
- Newport Beach

URL: https://www.socalfishreports.com/dock_totals/boats.php?date=YYYY-MM-DD

CRITICAL DIFFERENCES FROM SAN DIEGO SCRAPER:
- Regional headers (not landing headers) - e.g., "Avila Beach Fish Counts"
- Landing name comes AFTER boat name in entry data
- "Audio" elements that must be skipped
- Different HTML table structure

Key Lessons from Seaforth Fix Applied:
1. Case-insensitive matching for headers
2. Whitespace normalization
3. Continue statement to prevent double increment
4. Comprehensive logging

Speed: 2-5 second delays for ethical scraping
Database: Supabase with duplicate detection

Author: Fishing Intelligence Platform
Created: October 16, 2025
"""

import os
import sys
import time
import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from colorama import Fore, Style, init

# Date calculation logic REMOVED (Spec 006 - store dates AS-IS from boats.php)

# Initialize colorama
init(autoreset=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

# CRITICAL: SoCal data source
BASE_URL = "https://www.socalfishreports.com"
BOATS_URL_TEMPLATE = f"{BASE_URL}/dock_totals/boats.php?date={{date}}"

# REGIONAL FILTERING: Only scrape these regions (excludes Northern California)
# These correspond to the "Channel Islands", "Los Angeles", and "Orange County" regions
ALLOWED_REGIONS = [
    'Oxnard',              # Channel Islands
    'Marina Del Rey',      # Los Angeles
    'Long Beach',          # Los Angeles
    'San Pedro',           # Los Angeles
    'Newport Beach',       # Orange County
    'Dana Point'           # Orange County
]

# EXCLUDED REGIONS (Northern California - not in scope)
# These will be skipped during parsing:
# - 'Morro Bay' (Morro Bay Landing)
# - 'Avila Beach' (Patriot Sportfishing)
# - 'Santa Barbara' (Santa Barbara Landing)

# Ethical delays (2-5 seconds)
MIN_DELAY = 2
MAX_DELAY = 5

# Logging
LOG_FILE = "socal_scraper.log"
LOG_LEVEL = logging.INFO

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def init_supabase() -> Client:
    """Initialize Supabase client"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"{Fore.GREEN}✅ Supabase connected")
        return supabase
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Supabase connection failed: {e}")
        raise

# ============================================================================
# UTILITIES
# ============================================================================

def smart_delay():
    """2-5 second delay for speed and quality"""
    delay = random.randint(MIN_DELAY, MAX_DELAY)
    logger.info(f"{Fore.YELLOW}⏳ Delay: {delay}s")
    time.sleep(delay)

def fetch_page(url: str, session: requests.Session) -> Optional[str]:
    """Fetch page with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for attempt in range(3):
        try:
            logger.info(f"{Fore.CYAN}🌐 Fetching: {url}")
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            logger.info(f"{Fore.GREEN}✅ Fetched {len(response.text)} bytes")
            return response.text
        except Exception as e:
            logger.warning(f"{Fore.YELLOW}⚠️  Attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    logger.error(f"{Fore.RED}❌ Failed to fetch {url}")
    return None

def normalize_trip_type(trip_type: str) -> str:
    """
    Normalize trip type text for consistency

    Examples:
        "OvernightOffshore" -> "Overnight"
        "FullDayOffshore" -> "Full Day Offshore"
        "1/2DayAM" -> "1/2 Day AM"
    """
    # Simplify: OvernightOffshore/OvernightLocal -> just "Overnight"
    trip_type = re.sub(r'Overnight(Offshore|Local)', r'Overnight', trip_type)

    # Fix other concatenated patterns
    trip_type = re.sub(r'Full(Day|Night)', r'Full \1', trip_type)
    trip_type = re.sub(r'Half(Day|Night)', r'Half \1', trip_type)
    trip_type = re.sub(r'(\d+/\d+)Day', r'\1 Day', trip_type)
    trip_type = re.sub(r'(\d+\.?\d*)Day', r'\1 Day', trip_type)
    trip_type = re.sub(r'Day(AM|PM|Twilight|Offshore|Local)', r'Day \1', trip_type)

    # Remove trailing 'Local' or 'Offshore' after time modifiers
    trip_type = re.sub(r'(AM|PM)(Local|Offshore)$', r'\1', trip_type)

    return trip_type.strip()

def parse_species_counts(text: str) -> List[Dict]:
    """
    Parse species and counts from text

    Example:
        "28 Spiny Lobster, 9 Rock Crab, 49 Spiny Lobster Released"
        -> [{"species": "Spiny Lobster", "count": 28}, ...]

    Note: Ignores "Released" fish
    """
    catches = []

    # Pattern: number + species name (ignore if followed by "Released")
    pattern = r'(\d+)\s+([^,]+?)(?=\s*(?:,|$))'

    matches = re.findall(pattern, text)

    for count_str, species_raw in matches:
        # Skip if this is a "Released" entry
        if 'released' in species_raw.lower():
            continue

        count = int(count_str)
        species = species_raw.strip().title()

        catches.append({
            'species': species,
            'count': count
        })

    return catches

# ============================================================================
# SOCAL-SPECIFIC PARSING
# ============================================================================

def parse_socal_page(html: str, date: str) -> List[Dict]:
    """
    Parse socalfishreports.com boats.php page to extract trip data

    CRITICAL: SoCal structure is different from San Diego:

    SoCal Structure:
        Avila Beach Fish Counts  ← Regional header (NOT landing name)
        Boat    Dock Totals      ← Table headers
        Audio                    ← SKIP THIS (misidentified element)
        Flying Fish              ← ACTUAL boat name
        Patriot Sportfishing     ← ACTUAL landing name (line AFTER boat)
        Avila Beach, CA
        8 Anglers
        1/2 Day AM
        28 Spiny Lobster, 9 Rock Crab

    Key Lessons Applied from Seaforth Fix:
    1. Case-insensitive header matching
    2. Whitespace normalization
    3. Continue after parsing to prevent double increment

    Returns:
        List of trip dictionaries
    """
    soup = BeautifulSoup(html, 'lxml')
    trips = []

    # Get text content
    page_text = soup.get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]

    current_region = None  # Track region for context (not used as landing)
    i = 0

    while i < len(lines):
        line = lines[i]

        # LESSON FROM SEAFORTH FIX: Case-insensitive matching with whitespace normalization
        if 'fish counts' in line.lower():
            # Normalize whitespace (remove extra spaces, tabs, etc.)
            normalized = ' '.join(line.split())

            # Extract region name (for logging/context, NOT as landing name)
            if 'fish counts' in normalized.lower() and 'boat' not in normalized.lower():
                # Remove "Fish Counts" from line to get region name
                region_name = re.sub(r'\s*fish counts\s*', '', normalized, flags=re.IGNORECASE).strip()

                # REGIONAL FILTERING: Check if this region is in our allowed list
                is_allowed = any(allowed in region_name for allowed in ALLOWED_REGIONS)

                if is_allowed:
                    current_region = region_name
                    logger.info(f"{Fore.GREEN}✅ Processing region: {current_region}")
                else:
                    current_region = None  # Skip this region
                    logger.info(f"{Fore.YELLOW}⚠️  Skipping region (not in scope): {region_name}")

                i += 1
                continue
            else:
                logger.debug(f"Skipped line (contains 'Boat'): {normalized}")

        # Skip table headers
        if line.startswith('Boat') or 'Dock Totals' in line or 'Trip Details' in line:
            i += 1
            continue

        # CRITICAL: Skip "Audio" elements (SoCal-specific bug)
        if line.lower() == 'audio':
            logger.debug(f"{Fore.YELLOW}⚠️  Skipping 'Audio' element at line {i}")
            i += 1
            continue

        # Parse boat entry (if we have region context and enough lines ahead)
        if current_region and i + 5 < len(lines):
            # Check if this looks like a boat name (single word or two/three words, capitalized)
            # More flexible pattern for SoCal boats
            if re.match(r'^[A-Z][a-zA-Z0-9\s\-]+$', line) and len(line.split()) <= 3:
                boat_name = line
                logger.info(f"{Fore.YELLOW}🔍 Found boat: {boat_name} at line {i}")

                # CRITICAL DIFFERENCE: Next line is the LANDING NAME (not redundant landing)
                i += 1
                if i >= len(lines):
                    break

                landing_name = lines[i]
                logger.info(f"{Fore.CYAN}   Landing: {landing_name}")

                # Next line should be location (e.g., "Avila Beach, CA")
                i += 1
                if i >= len(lines):
                    break

                location_line = lines[i]
                logger.info(f"{Fore.YELLOW}   Location: {location_line}")

                # Log next few lines for debugging
                logger.debug(f"{Fore.YELLOW}   Next lines:")
                for offset in range(4):
                    if i + offset < len(lines):
                        logger.debug(f"{Fore.YELLOW}     +{offset}: '{lines[i + offset]}'")

                # Look for combined "X Anglers + Trip Type" line
                anglers = 0
                trip_type = None
                catches_text = None
                anglers_offset = 0

                for offset in range(5):
                    if i + offset >= len(lines):
                        break

                    line_check = lines[i + offset]

                    # Check for combined format: "16 Anglers1/2 Day AM" or "16 Anglers1/2 Day AMOut Front"
                    combined_match = re.match(r'(\d+)\s+Anglers(.+)', line_check, re.IGNORECASE)
                    if combined_match:
                        anglers = int(combined_match.group(1))
                        # Extract trip type (everything after "Anglers" but before "Out Front" or similar notes)
                        trip_raw = combined_match.group(2).strip()
                        # Remove notes like "Out Front", "Limits", etc.
                        trip_type = re.sub(r'(Out Front|Limits|Private)', '', trip_raw).strip()
                        anglers_offset = offset
                        logger.info(f"{Fore.YELLOW}   Found {anglers} anglers, trip: '{trip_type}' at offset +{offset}")

                        # Catches should be on NEXT line (NOT +2)
                        if i + offset + 1 < len(lines):
                            catches_text = lines[i + offset + 1]
                            logger.info(f"{Fore.YELLOW}   Catches: '{catches_text}'")

                        break

                # Validate we have all required data
                if anglers == 0 or not trip_type or not catches_text:
                    logger.info(f"{Fore.YELLOW}   Incomplete data, skipping")
                    i += 1
                    continue

                # Move past the catches line (anglers_offset + 2: skip to catches, then +1 to go past it)
                i += anglers_offset + 2

                # Parse catches
                catches = parse_species_counts(catches_text)

                # Normalize trip type (fix spacing issues)
                normalized_trip_type = normalize_trip_type(trip_type)

                # SPEC 006: Store dates EXACTLY as shown on boats.php
                # boats.php?date = RETURN/REPORT DATE (when boat came back)
                # NO date calculations - source of truth principle

                # Build trip object
                trip = {
                    'boat_name': boat_name,
                    'landing_name': landing_name,  # CRITICAL: From line after boat, NOT from header
                    'trip_date': date,  # SPEC 006: Store boats.php date AS-IS (return/report date)
                    'trip_duration': normalized_trip_type,
                    'trip_type': normalized_trip_type,
                    'anglers': anglers,
                    'catches': catches,
                    'region': current_region  # Additional context
                }

                trips.append(trip)
                logger.info(f"{Fore.GREEN}✅ Parsed: {boat_name} ({landing_name}) - {len(catches)} species, {anglers} anglers")

                # LESSON FROM SEAFORTH FIX: Continue to prevent double increment
                continue

        i += 1

    logger.info(f"{Fore.GREEN}✅ Total trips parsed: {len(trips)}")
    return trips

# ============================================================================
# DATABASE OPERATIONS (IDENTICAL TO SD SCRAPER)
# ============================================================================

def get_or_create_landing(supabase: Client, landing_name: str) -> int:
    """Get or create landing"""
    result = supabase.table('landings').select('id').eq('name', landing_name).execute()
    if result.data:
        return result.data[0]['id']

    result = supabase.table('landings').insert({'name': landing_name}).execute()
    logger.info(f"{Fore.GREEN}✅ Created landing: {landing_name}")
    return result.data[0]['id']

def get_or_create_boat(supabase: Client, boat_name: str, landing_id: int) -> int:
    """Get or create boat"""
    result = supabase.table('boats').select('id').eq('name', boat_name).execute()
    if result.data:
        return result.data[0]['id']

    result = supabase.table('boats').insert({
        'name': boat_name,
        'landing_id': landing_id
    }).execute()
    logger.info(f"{Fore.GREEN}✅ Created boat: {boat_name}")
    return result.data[0]['id']

def check_trip_exists(supabase: Client, boat_id: int, trip_date: str, trip_duration: str) -> bool:
    """Check if trip exists"""
    result = supabase.table('trips').select('id') \
        .eq('boat_id', boat_id) \
        .eq('trip_date', trip_date) \
        .eq('trip_duration', trip_duration) \
        .execute()
    return bool(result.data)

def insert_trip(supabase: Client, trip: Dict) -> bool:
    """Insert trip into database"""
    try:
        # Get/create landing
        landing_id = get_or_create_landing(supabase, trip['landing_name'])

        # Get/create boat
        boat_id = get_or_create_boat(supabase, trip['boat_name'], landing_id)

        # Check duplicate
        if check_trip_exists(supabase, boat_id, trip['trip_date'], trip['trip_duration']):
            logger.info(f"{Fore.YELLOW}⚠️  Duplicate: {trip['boat_name']} on {trip['trip_date']}")
            return False

        # Insert trip
        trip_data = {
            'boat_id': boat_id,
            'trip_date': trip['trip_date'],
            'trip_duration': trip['trip_duration'],
            'anglers': trip['anglers']
        }

        trip_result = supabase.table('trips').insert(trip_data).execute()
        trip_id = trip_result.data[0]['id']

        # Insert catches
        if trip['catches']:
            catch_data = [
                {
                    'trip_id': trip_id,
                    'species': c['species'],
                    'count': c['count']
                }
                for c in trip['catches']
            ]
            supabase.table('catches').insert(catch_data).execute()

        logger.info(f"{Fore.GREEN}✅ Inserted: {trip['boat_name']} ({len(trip['catches'])} species)")
        return True

    except Exception as e:
        logger.error(f"{Fore.RED}❌ Insert failed: {e}")
        return False

# ============================================================================
# MAIN SCRAPING LOGIC
# ============================================================================

def scrape_date_range(start_date: str, end_date: str, dry_run: bool = False):
    """
    Scrape SoCal boats data for a date range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dry_run: If True, don't insert into database
    """
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.MAGENTA}🚀 Starting SoCal Boats Scraper")
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.CYAN}📅 Date range: {start_date} to {end_date}")
    logger.info(f"{Fore.CYAN}🔧 Dry run: {dry_run}")

    # Initialize
    supabase = init_supabase() if not dry_run else None
    session = requests.Session()

    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    total_trips = 0
    inserted_trips = 0
    skipped_trips = 0

    # Iterate through dates
    current = start
    date_count = 0

    while current <= end:
        date_count += 1
        date_str = current.strftime('%Y-%m-%d')

        logger.info(f"{Fore.MAGENTA}\n{'='*80}")
        logger.info(f"{Fore.MAGENTA}📅 Processing: {date_str} ({date_count} of {(end - start).days + 1})")
        logger.info(f"{Fore.MAGENTA}{'='*80}")

        # Smart delay (skip for first date)
        if date_count > 1:
            smart_delay()

        # Fetch page
        url = BOATS_URL_TEMPLATE.format(date=date_str)
        html = fetch_page(url, session)

        if not html:
            logger.warning(f"{Fore.YELLOW}⚠️  Skipping {date_str}")
            current += timedelta(days=1)
            continue

        # Parse trips with SoCal-specific parser
        trips = parse_socal_page(html, date_str)
        total_trips += len(trips)

        # Insert trips
        if not dry_run:
            for trip in trips:
                if insert_trip(supabase, trip):
                    inserted_trips += 1
                else:
                    skipped_trips += 1
        else:
            logger.info(f"{Fore.YELLOW}🔧 DRY RUN - Would insert {len(trips)} trips")

        # Next date
        current += timedelta(days=1)

    # Summary
    logger.info(f"{Fore.MAGENTA}\n{'='*80}")
    logger.info(f"{Fore.MAGENTA}📊 SCRAPING SUMMARY")
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.GREEN}✅ Dates processed: {date_count}")
    logger.info(f"{Fore.GREEN}✅ Trips found: {total_trips}")
    logger.info(f"{Fore.GREEN}✅ Trips inserted: {inserted_trips}")
    logger.info(f"{Fore.YELLOW}⚠️  Trips skipped: {skipped_trips}")
    logger.info(f"{Fore.MAGENTA}{'='*80}\n")

# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='SoCal Fish Boats Scraper')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - no database insertions')

    args = parser.parse_args()

    end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')

    try:
        scrape_date_range(args.start_date, end_date, args.dry_run)
    except KeyboardInterrupt:
        logger.info(f"\n{Fore.YELLOW}⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
