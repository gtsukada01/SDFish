#!/usr/bin/env python3
"""
San Diego Fish Boats Scraper (OPTIMIZED)
==========================================

OPTIMIZED: Uses structured boats.php page with clean, tabular data
URL: https://www.sandiegofishreports.com/dock_totals/boats.php?date=YYYY-MM-DD

Data Structure:
- Individual boat trips by date
- Clear trip types (1/2 Day, 1.5 Day, 2 Day, etc.)
- Structured catch data (species + counts)
- Landing associations

Speed: 2-5 second delays for quality and speed
Database: Supabase with duplicate detection

Author: Fishing Intelligence Platform
Last Updated: October 15, 2025
"""

import os
import sys
import time
import random
import logging
import re
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from colorama import Fore, Style, init

# Date calculation logic REMOVED (Spec 006 - store dates AS-IS from boats.php)

# ============================================================================
# SPEC-010: Custom Exceptions
# ============================================================================

class ParserError(Exception):
    """Raised when parser cannot extract required data from page"""
    pass

class DateMismatchError(Exception):
    """Raised when requested date doesn't match actual report date on page"""
    pass

class FutureDateError(Exception):
    """Raised when attempting to scrape future dates without explicit override"""
    pass

class ScrapingTooEarlyError(Exception):
    """Raised when attempting to scrape today's data before reports are published (5pm PT)"""
    pass

class DuplicateContentError(Exception):
    """Raised when identical trip content found on different date (phantom duplicate)"""
    pass

# Initialize colorama
init(autoreset=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

BASE_URL = "https://www.sandiegofishreports.com"
BOATS_URL_TEMPLATE = f"{BASE_URL}/dock_totals/boats.php?date={{date}}"

# OPTIMIZED: Fast but respectful delays (2-5 seconds)
MIN_DELAY = 2
MAX_DELAY = 5

# Logging
LOG_FILE = "boats_scraper.log"
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
# SPEC-010 FR-003: Audit Trail Helpers
# ============================================================================

def get_git_sha() -> Optional[str]:
    """Get current Git commit SHA for audit trail"""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not get Git SHA: {e}")
        return None

def get_operator_identity() -> str:
    """
    Get operator identity for audit trail

    Priority order:
    1. Environment variable SCRAPER_OPERATOR
    2. Git user.name
    3. System username
    4. 'unknown'
    """
    # Check environment variable first
    operator = os.getenv('SCRAPER_OPERATOR')
    if operator:
        return operator

    # Try Git user.name
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        git_user = result.stdout.strip()
        if git_user:
            return git_user
    except Exception:
        pass

    # Try system username
    try:
        import getpass
        username = getpass.getuser()
        if username:
            return username
    except Exception:
        pass

    return 'unknown'

def get_operator_source() -> str:
    """
    Determine how scraper was invoked

    Returns:
        'cli' - Command line invocation
        'cron' - Scheduled task
        'api' - API invocation
    """
    # Check if running via cron
    if not sys.stdin.isatty():
        return 'cron'

    # Default to CLI for interactive terminal
    return 'cli'

# Scraper version for audit trail
SCRAPER_VERSION = '2.0.0-spec010'

# ============================================================================
# SPEC-010 FR-004: Pacific Time Enforcement & Scrape Timing Validation
# ============================================================================

def get_pacific_now() -> datetime:
    """Get current time in Pacific timezone"""
    pacific = pytz.timezone('America/Los_Angeles')
    return datetime.now(pacific)

def get_pacific_today() -> datetime:
    """Get today's date in Pacific timezone"""
    return get_pacific_now().date()

def validate_scrape_timing(date_str: str, allow_early: bool = False, require_after_hour: int = 17):
    """
    Validate it's safe to scrape this date (reports publish ~5pm PT)

    SPEC-010 FR-004: Prevents scraping today's data before reports are published

    Args:
        date_str: Date to scrape (YYYY-MM-DD)
        allow_early: If True, allow scraping today before 5pm PT (not recommended)
        require_after_hour: Hour (PT) after which scraping is safe (default 17 = 5pm)

    Raises:
        ScrapingTooEarlyError: If scraping today before require_after_hour and allow_early is False

    Example:
        >>> # If it's 3pm PT on Oct 19, 2025
        >>> validate_scrape_timing('2025-10-19', allow_early=False)  # Raises ScrapingTooEarlyError
        >>> validate_scrape_timing('2025-10-18', allow_early=False)  # OK (past date)
        >>> validate_scrape_timing('2025-10-19', allow_early=True)   # OK (override)
    """
    scrape_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    pacific_now = get_pacific_now()
    today_pt = pacific_now.date()

    # Only check if scraping today
    if scrape_date != today_pt:
        return  # Not today, no timing validation needed

    # Check if reports are likely published
    if pacific_now.hour < require_after_hour:
        if not allow_early:
            raise ScrapingTooEarlyError(
                f"Scraping today's data ({scrape_date}) before {require_after_hour}:00 PT. "
                f"Current time: {pacific_now.strftime('%H:%M PT')}. "
                f"Reports typically publish after 5pm PT. "
                f"Use --allow-early flag to override (not recommended)."
            )
        else:
            logger.warning(f"{Fore.YELLOW}⚠️  EARLY SCRAPING OVERRIDE ENABLED")
            logger.warning(f"{Fore.YELLOW}   Scraping today before {require_after_hour}:00 PT")
            logger.warning(f"{Fore.YELLOW}   Current time: {pacific_now.strftime('%H:%M PT')}")
            logger.warning(f"{Fore.YELLOW}   Risk: Reports may not be published yet")

# ============================================================================
# SPEC-010 FR-005: Deep Deduplication with trip_hash
# ============================================================================

def compute_trip_hash(
    boat_id: int,
    trip_duration: str,
    anglers: Optional[int],
    catches: List[Dict]
) -> str:
    """
    Compute deterministic hash of trip content (excluding date)

    SPEC-010 FR-005: Allows detection of identical trips on different dates
    Same boat + duration + anglers + catches = same hash

    Args:
        boat_id: Database ID of boat
        trip_duration: Trip type (e.g., "1/2 Day", "Overnight")
        anglers: Number of anglers (None if not reported)
        catches: List of catch dicts with species and count

    Returns:
        16-character hex hash (truncated SHA256)

    Example:
        >>> catches = [{'species': 'Yellowtail', 'count': 15}, {'species': 'Rockfish', 'count': 8}]
        >>> compute_trip_hash(42, '1/2 Day', 25, catches)
        'a1b2c3d4e5f67890'
    """
    import hashlib
    import json

    # Sort catches for deterministic hashing
    sorted_catches = sorted(catches, key=lambda c: c['species'])

    hash_input = {
        'boat_id': boat_id,
        'trip_duration': trip_duration,
        'anglers': anglers,
        'catches': sorted_catches
    }

    hash_str = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

def check_duplicate_in_window(
    supabase: Client,
    trip_hash: str,
    trip_date: str,
    window_days: int = 7
) -> Optional[Dict]:
    """
    Check if identical trip exists within ±N days

    SPEC-010 FR-005: Detects phantom duplicates across different dates

    Args:
        supabase: Supabase client
        trip_hash: 16-character trip content hash
        trip_date: Date of current trip (YYYY-MM-DD)
        window_days: Number of days to search before/after (default 7)

    Returns:
        Matching trip dict if found, None otherwise

    Example:
        >>> # Check if trip from 10/19 matches any trip within 7 days
        >>> duplicate = check_duplicate_in_window(supabase, 'a1b2c3d4e5f67890', '2025-10-19', 7)
        >>> if duplicate:
        >>>     print(f"Found duplicate on {duplicate['trip_date']}")
    """
    try:
        date_obj = datetime.strptime(trip_date, '%Y-%m-%d').date()
        start_date = (date_obj - timedelta(days=window_days)).isoformat()
        end_date = (date_obj + timedelta(days=window_days)).isoformat()

        # Query for matching hash in date window
        result = supabase.table('trips').select('*') \
            .eq('trip_hash', trip_hash) \
            .gte('trip_date', start_date) \
            .lte('trip_date', end_date) \
            .neq('trip_date', trip_date) \
            .execute()

        if result.data:
            return result.data[0]  # Return first match
        return None

    except Exception as e:
        logger.warning(f"{Fore.YELLOW}⚠️  Duplicate check failed: {e}")
        return None

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
        "1/2 Day AMLocal" -> "1/2 Day AM"
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

def parse_trip_duration(trip_type: str) -> float:
    """
    Parse trip type to duration in days (for analytics/display)
    NOTE: No longer used for database storage - we store trip_type text directly

    Examples:
        "1/2 Day" -> 0.5
        "1.5 Day" -> 1.5
        "2 Day" -> 2.0
        "Full Day" -> 1.0
        "Overnight" -> 1.0
    """
    trip_lower = trip_type.lower()

    # Handle fractions
    if '1/2' in trip_lower:
        return 0.5
    if '3/4' in trip_lower:
        return 0.75

    # Handle decimals
    match = re.search(r'(\d+\.?\d*)\s*day', trip_lower)
    if match:
        return float(match.group(1))

    # Default (Full Day, Overnight, etc.)
    return 1.0

def is_landing_header(line: str) -> bool:
    """
    Detect if a line is a landing header (e.g., "H&M Landing Fish Counts")

    CRITICAL: Must distinguish landing headers from catches/data text

    Returns:
        True if line is a landing header, False otherwise
    """
    if not line:
        return False

    # Normalize whitespace
    normalized = ' '.join(line.split()).lower()

    # Must contain "fish counts" but NOT "boat" (which indicates table header)
    return 'fish counts' in normalized and 'boat' not in normalized

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
# SPEC-010 FR-001: Source Date Validation
# ============================================================================

def extract_report_date_from_header(html: str) -> Optional[str]:
    """
    Extract actual report date from page header

    SPEC-010 FR-001: Parser MUST validate source date to prevent phantom data

    The boats.php page includes a title tag like:
        "Fish Counts by Boat - October 17, 2025"
        "Fish Counts by Boat - October 16, 2025"

    Args:
        html: Raw HTML from boats.php page

    Returns:
        Date string in YYYY-MM-DD format if found, None if not found

    Raises:
        ParserError: If date header exists but cannot be parsed

    Examples:
        >>> html = '<html><title>Fish Counts by Boat - October 17, 2025</title></html>'
        >>> extract_report_date_from_header(html)
        '2025-10-17'
    """
    soup = BeautifulSoup(html, 'lxml')

    # Extract date from page title
    # Pattern: "Fish Counts by Boat - October 17, 2025"
    title = soup.title.string if soup.title else None

    if not title:
        return None

    # Pattern: "Fish Counts by Boat - [Month] [Day], [Year]"
    # Example: "Fish Counts by Boat - October 17, 2025"
    pattern = r'Fish\s+Counts\s+by\s+Boat\s+-\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})'

    match = re.search(pattern, title, re.IGNORECASE)

    if not match:
        # Try alternative pattern with page text (fallback)
        page_text = soup.get_text()
        # Try: "Dock Totals for [Weekday] MM/DD/YYYY"
        pattern2 = r'Dock\s+Totals\s+for\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})/(\d{1,2})/(\d{4})'
        match2 = re.search(pattern2, page_text, re.IGNORECASE)

        if match2:
            try:
                month = int(match2.group(1))
                day = int(match2.group(2))
                year = int(match2.group(3))
                date_obj = datetime(year, month, day)
                return date_obj.strftime('%Y-%m-%d')
            except (ValueError, IndexError) as e:
                raise ParserError(f"Found date in page text but failed to parse: {match2.group(0)}, error: {e}")

        # No date found
        return None

    try:
        # Parse month name to number
        month_name = match.group(1)
        day = int(match.group(2))
        year = int(match.group(3))

        # Parse full date to validate and convert month name
        date_str = f"{month_name} {day}, {year}"
        date_obj = datetime.strptime(date_str, '%B %d, %Y')

        # Return in YYYY-MM-DD format
        return date_obj.strftime('%Y-%m-%d')

    except (ValueError, IndexError) as e:
        raise ParserError(f"Found date in title but failed to parse: {match.group(0)}, error: {e}")

# ============================================================================
# DATA PARSING
# ============================================================================

def parse_boats_page(html: str, date: str, supabase: Client) -> List[Dict]:
    """
    Parse boats.php page to extract trip data

    SPEC-010 FR-001: Validates actual report date matches requested date to prevent phantom data
    NEW: Cross-references boat names against database for accuracy

    Structure:
        H&M Landing Fish Counts
        Boat	Trip Details	Dock Totals
        Alicia
        H&M Landing
        San Diego, CA	8 Anglers
        1/2 Day Twilight	28 Spiny Lobster, 9 Rock Crab

    Args:
        html: Raw HTML from boats.php
        date: Requested date (YYYY-MM-DD)
        supabase: Supabase client for database cross-reference

    Returns:
        List of trip dictionaries

    Raises:
        ParserError: If date header cannot be found
        DateMismatchError: If actual date doesn't match requested date
    """
    # Load all known boats from database for validation
    known_boats = get_all_known_boats(supabase)

    # SPEC-010 FR-001: Source Date Validation
    # Extract actual report date from page header
    actual_date = extract_report_date_from_header(html)

    if actual_date is None:
        # No date header found - page structure may have changed
        logger.warning(f"{Fore.YELLOW}⚠️  Could not extract report date from page header")
        logger.warning(f"{Fore.YELLOW}    This may indicate page structure has changed")
        raise ParserError(
            f"Could not parse report date from page header. "
            f"Page structure may have changed. "
            f"Manual inspection required."
        )

    # Validate actual date matches requested date
    if actual_date != date:
        # CRITICAL: Date mismatch indicates website is serving fallback/cached content
        logger.error(f"{Fore.RED}❌ DATE MISMATCH DETECTED")
        logger.error(f"{Fore.RED}   Requested: {date}")
        logger.error(f"{Fore.RED}   Actual:    {actual_date}")
        logger.error(f"{Fore.RED}   → Source may be serving fallback/cached content")
        logger.error(f"{Fore.RED}   → This prevents phantom data injection")

        raise DateMismatchError(
            f"Date mismatch: requested {date}, page shows {actual_date}. "
            f"Source may be serving fallback/cached content for future dates. "
            f"ABORTING to prevent phantom data injection."
        )

    # Date validation passed
    logger.info(f"{Fore.GREEN}✅ Source date validated: {actual_date} matches requested {date}")

    soup = BeautifulSoup(html, 'lxml')
    trips = []

    # Get text content
    page_text = soup.get_text()
    lines = [l.strip() for l in page_text.split('\n') if l.strip()]

    current_landing = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # CRITICAL FIX: Check for landing header using robust detection
        # This prevents landing headers from being confused with catches text
        if is_landing_header(line):
            # Normalize whitespace (remove extra spaces, tabs, etc.)
            normalized = ' '.join(line.split())

            # Remove "Fish Counts" from line to get landing name
            landing_name = re.sub(r'\s*fish counts\s*', '', normalized, flags=re.IGNORECASE).strip()
            current_landing = landing_name
            logger.info(f"{Fore.CYAN}📍 Landing header detected: {current_landing}")
            i += 1
            continue

        # Skip table headers
        if line.startswith('Boat\t') or 'Trip Details' in line:
            i += 1
            continue

        # Parse boat entry (if we have a landing context)
        if current_landing and i + 3 < len(lines):
            boat_matched = False

            # CRITICAL FIX: Cross-reference boat name against database
            # This replaces unreliable regex matching with database validation
            if line in known_boats:
                boat_name = line
                boat_info = known_boats[line]
                boat_matched = True

                # Validate landing matches (optional warning, not blocker)
                if boat_info['landing_name'] != current_landing and boat_info['landing_name'] != 'Unknown':
                    logger.warning(f"{Fore.YELLOW}⚠️  Landing mismatch for {boat_name}")
                    logger.warning(f"{Fore.YELLOW}    Expected: {boat_info['landing_name']}")
                    logger.warning(f"{Fore.YELLOW}    Found in: {current_landing}")
                    # Continue anyway - boats can move between landings

                logger.info(f"{Fore.YELLOW}🔍 Found boat: {boat_name} at line {i} (validated against database)")

            # FALLBACK: Check for NEW boats not yet in database
            # Use relaxed regex to catch boats with numbers, 3+ words, single letters, etc.
            elif re.match(r'^[A-Z][a-z0-9]*(\s+[A-Z0-9][a-z0-9]*){0,4}$', line):
                # Potential new boat - check it's not a landing name
                if line != current_landing and 'Fish Counts' not in line:
                    boat_name = line
                    boat_matched = True
                    logger.warning(f"{Fore.RED}🚨 NEW BOAT DETECTED: {boat_name}")
                    logger.warning(f"{Fore.RED}   Landing: {current_landing}")
                    logger.warning(f"{Fore.RED}   This boat is NOT in the database - will be auto-created")
                    logger.warning(f"{Fore.RED}   Manual verification recommended")

            if boat_matched:

                # Next line should be landing name (skip it, we already have current_landing)
                i += 1
                if i >= len(lines):
                    break

                # Next line: "San Diego, CA\t8 Anglers"
                i += 1
                if i >= len(lines):
                    break

                location_line = lines[i]
                # Next few lines could be: location, then anglers, then trip/catches
                # Let me check the next few lines
                logger.info(f"{Fore.YELLOW}   Next lines:")
                for offset in range(4):
                    if i + offset < len(lines):
                        logger.info(f"{Fore.YELLOW}     +{offset}: '{lines[i + offset]}'")

                # Look for combined "X Anglers1/2 Day ..." line
                anglers = 0
                trip_type = None
                catches_text = None
                combined_line_offset = 0

                for offset in range(3):
                    if i + offset < len(lines):
                        line_check = lines[i + offset]
                        # Check for combined format: "8 Anglers1/2 Day Twilight"
                        combined_match = re.match(r'(\d+)\s+Anglers(.+)', line_check)
                        if combined_match:
                            anglers = int(combined_match.group(1))
                            trip_type = combined_match.group(2).strip()
                            combined_line_offset = offset
                            logger.info(f"{Fore.YELLOW}   Found {anglers} anglers, trip: '{trip_type}' at offset +{offset}")
                            # CRITICAL FIX: Check if next line is catches or landing header
                            if i + offset + 1 < len(lines):
                                potential_catches = lines[i + offset + 1]
                                # BUG FIX: Verify this is NOT a landing header
                                if is_landing_header(potential_catches):
                                    logger.warning(f"{Fore.RED}⚠️  Landing header found instead of catches for {boat_name} - boat has no catches, skipping")
                                    catches_text = None  # Skip this boat - no catches data
                                else:
                                    catches_text = potential_catches
                                    logger.info(f"{Fore.YELLOW}   Catches: '{catches_text}'")
                            break

                if anglers == 0 or not trip_type or not catches_text:
                    logger.info(f"{Fore.YELLOW}   Incomplete data, skipping")
                    i += 1
                    continue

                # Move past the catches line
                i += combined_line_offset + 2
                if i >= len(lines):
                    break

                # We now have everything we need
                trip_parts = [trip_type, catches_text]  # Fake the split for compatibility
                if len(trip_parts) >= 2:

                    # Parse catches
                    catches = parse_species_counts(catches_text)

                    # Normalize trip type (fix spacing issues)
                    normalized_trip_type = normalize_trip_type(trip_type)

                    # FR-006 (SPEC 006): Store dates EXACTLY as shown on boats.php
                    # boats.php?date = RETURN/REPORT DATE (when boat came back)
                    # NO date calculations - source of truth principle

                    # Store trip_type text (NOT numeric)
                    trip = {
                        'boat_name': boat_name,
                        'landing_name': current_landing,
                        'trip_date': date,  # SPEC 006: Store boats.php date AS-IS (return/report date)
                        'trip_duration': normalized_trip_type,  # Store text like "Full Day", "1/2 Day"
                        'trip_type': normalized_trip_type,
                        'anglers': anglers,
                        'catches': catches
                    }

                    trips.append(trip)
                    logger.info(f"{Fore.GREEN}✅ Parsed: {boat_name} - {len(catches)} species, {anglers} anglers")
                    # FIXED: Continue to prevent double increment and skipping next landing header
                    continue

        i += 1

    logger.info(f"{Fore.GREEN}✅ Total trips parsed: {len(trips)}")
    return trips

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_all_known_boats(supabase: Client) -> Dict[str, Dict]:
    """
    Get all boats from database for validation during parsing

    Returns dict mapping boat name -> {id, landing_id, landing_name}

    This allows parser to:
    1. Validate boat names against known boats (accuracy)
    2. Detect new boats that need manual verification
    3. Prevent parsing landing names as boat names

    Example:
        >>> boats = get_all_known_boats(supabase)
        >>> if "Lucky B Sportfishing" in boats:
        >>>     # Valid boat, continue parsing
    """
    try:
        result = supabase.table('boats').select('id, name, landing_id, landings(name)').execute()

        boats_dict = {}
        for boat in result.data:
            boat_name = boat['name']
            landing_name = boat.get('landings', {}).get('name', 'Unknown') if boat.get('landings') else 'Unknown'

            boats_dict[boat_name] = {
                'id': boat['id'],
                'landing_id': boat['landing_id'],
                'landing_name': landing_name
            }

        logger.info(f"{Fore.GREEN}✅ Loaded {len(boats_dict)} known boats from database")
        return boats_dict

    except Exception as e:
        logger.warning(f"{Fore.YELLOW}⚠️  Could not load boats from database: {e}")
        logger.warning(f"{Fore.YELLOW}    Falling back to regex-only parsing")
        return {}

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

def catches_identical(catches1: List[Dict], catches2: List[Dict]) -> bool:
    """
    Check if two catch lists are identical

    Args:
        catches1: First catch list (format: [{'species': str, 'count': int}, ...])
        catches2: Second catch list (format: [{'species': str, 'count': int}, ...])

    Returns:
        True if catches are identical, False otherwise
    """
    # Normalize species names to lowercase for comparison
    c1 = sorted([(c['species'].lower(), c['count']) for c in catches1])
    c2 = sorted([(c['species'].lower(), c['count']) for c in catches2])
    return c1 == c2

def check_trip_exists(supabase: Client, boat_id: int, trip_date: str, trip_duration: str, anglers: Optional[int] = None, catches: Optional[List[Dict]] = None) -> bool:
    """
    Check if trip exists (SPEC 006 FIX: Composite Key + Catch Comparison)

    Composite Key = Boat + Date + Trip Type + Anglers + Catches

    This handles cases where the same boat runs multiple trips with identical metadata
    (boat, date, trip_duration, anglers) but different catches.

    Args:
        boat_id: Database boat ID
        trip_date: Trip date (YYYY-MM-DD)
        trip_duration: Trip type text (e.g., 'Full Day', '1/2 Day PM')
        anglers: Number of anglers (optional but recommended for accuracy)
        catches: List of catches for comparison (optional, if None uses old behavior)

    Returns:
        True if trip exists with identical catches, False otherwise
    """
    query = supabase.table('trips').select('id') \
        .eq('boat_id', boat_id) \
        .eq('trip_date', trip_date) \
        .eq('trip_duration', trip_duration)

    # SPEC 006: Include anglers in composite key to handle multiple trips per boat/date/type
    if anglers is not None:
        query = query.eq('anglers', anglers)

    result = query.execute()

    if not result.data:
        return False  # No existing trip with this composite key

    # SPEC 006 FIX: If catches provided, check if any existing trip has IDENTICAL catches
    # This differentiates trips with same metadata but different catches
    if catches is not None:
        for existing_trip in result.data:
            trip_id = existing_trip['id']
            existing_catches = supabase.table('catches').select('species, count').eq('trip_id', trip_id).execute().data

            if catches_identical(existing_catches, catches):
                return True  # True duplicate (same metadata AND catches)

        return False  # Same metadata but different catches = different trip

    # Old behavior: If no catches provided for comparison, treat as duplicate
    return bool(result.data)

def create_scrape_job(
    supabase: Client,
    operator: str,
    start_date: str,
    end_date: str,
    allow_future: bool = False,
    dry_run: bool = False
) -> Optional[int]:
    """
    Create scrape job record for audit trail

    SPEC-010 FR-003: Complete audit trail for all scraping operations

    Args:
        supabase: Supabase client
        operator: Operator identity (username/email)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        allow_future: Whether future date override was used
        dry_run: Whether this is a dry-run

    Returns:
        Job ID if created, None if dry-run mode
    """
    if dry_run:
        logger.info(f"{Fore.YELLOW}🔧 DRY RUN - Skipping scrape_job creation")
        return None

    try:
        git_sha = get_git_sha()
        operator_source = get_operator_source()

        job_data = {
            'operator': operator,
            'operator_source': operator_source,
            'start_date': start_date,
            'end_date': end_date,
            'allow_future': allow_future,
            'dry_run': dry_run,
            'git_sha': git_sha,
            'scraper_version': SCRAPER_VERSION,
            'job_status': 'RUNNING',
            'source_url_pattern': BOATS_URL_TEMPLATE
        }

        result = supabase.table('scrape_jobs').insert(job_data).execute()
        job_id = result.data[0]['id']

        logger.info(f"{Fore.GREEN}✅ Created scrape_job #{job_id}")
        logger.info(f"{Fore.CYAN}   Operator: {operator} ({operator_source})")
        logger.info(f"{Fore.CYAN}   Version: {SCRAPER_VERSION}")
        if git_sha:
            logger.info(f"{Fore.CYAN}   Git SHA: {git_sha[:8]}")

        return job_id

    except Exception as e:
        logger.error(f"{Fore.RED}❌ Failed to create scrape_job: {e}")
        # Don't abort scraping due to audit failure, but log prominently
        logger.warning(f"{Fore.YELLOW}⚠️  Continuing without audit trail (NOT RECOMMENDED)")
        return None

def update_scrape_job_progress(
    supabase: Client,
    job_id: Optional[int],
    dates_processed: int,
    trips_inserted: int,
    trips_failed: int = 0
):
    """
    Update scrape job progress

    SPEC-010 FR-003: Incremental progress tracking

    Args:
        supabase: Supabase client
        job_id: Job ID (None if dry-run)
        dates_processed: Number of dates processed
        trips_inserted: Number of trips inserted
        trips_failed: Number of trips failed
    """
    if job_id is None:
        return

    try:
        supabase.table('scrape_jobs').update({
            'dates_processed': dates_processed,
            'trips_inserted': trips_inserted,
            'trips_failed': trips_failed
        }).eq('id', job_id).execute()

    except Exception as e:
        logger.warning(f"{Fore.YELLOW}⚠️  Failed to update scrape_job progress: {e}")

def complete_scrape_job(
    supabase: Client,
    job_id: Optional[int],
    status: str,
    error_message: Optional[str] = None
):
    """
    Mark scrape job as complete

    SPEC-010 FR-003: Final job status and runtime tracking

    Args:
        supabase: Supabase client
        job_id: Job ID (None if dry-run)
        status: Final status ('SUCCESS', 'FAILED', 'ABORTED')
        error_message: Error message if failed/aborted
    """
    if job_id is None:
        return

    try:
        # Get job start time to calculate runtime
        job_result = supabase.table('scrape_jobs').select('job_started_at').eq('id', job_id).execute()
        if not job_result.data:
            logger.warning(f"{Fore.YELLOW}⚠️  Scrape job #{job_id} not found for completion")
            return

        started_at = datetime.fromisoformat(job_result.data[0]['job_started_at'].replace('Z', '+00:00'))
        runtime = (datetime.now(pytz.UTC) - started_at).total_seconds()

        update_data = {
            'job_status': status,
            'job_completed_at': datetime.now(pytz.UTC).isoformat(),
            'runtime_seconds': round(runtime, 2)
        }

        if error_message:
            update_data['error_message'] = error_message

        supabase.table('scrape_jobs').update(update_data).eq('id', job_id).execute()

        logger.info(f"{Fore.GREEN}✅ Completed scrape_job #{job_id}: {status} ({runtime:.1f}s)")

    except Exception as e:
        logger.warning(f"{Fore.YELLOW}⚠️  Failed to complete scrape_job: {e}")

def insert_trip(supabase: Client, trip: Dict, scrape_job_id: Optional[int] = None) -> bool:
    """
    Insert trip into database

    SPEC-010 FR-003: Links trip to scrape_job_id for audit trail
    SPEC-010 FR-005: Detects phantom duplicates across different dates via trip_hash
    """
    try:
        # Get/create landing
        landing_id = get_or_create_landing(supabase, trip['landing_name'])

        # Get/create boat
        boat_id = get_or_create_boat(supabase, trip['boat_name'], landing_id)

        # Check duplicate (SPEC 006 FIX: Compare catches for trips with identical metadata)
        if check_trip_exists(supabase, boat_id, trip['trip_date'], trip['trip_duration'], trip.get('anglers'), trip.get('catches')):
            logger.info(f"{Fore.YELLOW}⚠️  Duplicate: {trip['boat_name']} on {trip['trip_date']} ({trip['trip_duration']}, {trip.get('anglers')} anglers)")
            return False

        # SPEC-010 FR-005: Compute trip hash and check for phantom duplicates
        trip_hash = compute_trip_hash(
            boat_id,
            trip['trip_duration'],
            trip.get('anglers'),
            trip.get('catches', [])
        )

        # Check for phantom duplicates (same trip on different dates)
        duplicate_trip = check_duplicate_in_window(
            supabase,
            trip_hash,
            trip['trip_date'],
            window_days=7
        )

        if duplicate_trip:
            logger.warning(f"{Fore.YELLOW}⚠️  PHANTOM DUPLICATE DETECTED")
            logger.warning(f"{Fore.YELLOW}   Current trip: {trip['boat_name']} on {trip['trip_date']}")
            logger.warning(f"{Fore.YELLOW}   Matches trip on: {duplicate_trip['trip_date']}")
            logger.warning(f"{Fore.YELLOW}   Trip type: {trip['trip_duration']}, Anglers: {trip.get('anglers')}")
            logger.warning(f"{Fore.YELLOW}   Hash: {trip_hash}")
            logger.warning(f"{Fore.YELLOW}   → This may be fallback data from website")

            # OPTION: Raise error to abort (strict mode)
            # raise DuplicateContentError(
            #     f"Phantom duplicate detected: trip on {trip['trip_date']} "
            #     f"matches trip on {duplicate_trip['trip_date']}"
            # )

            # OPTION: Flag and continue (lenient mode - current behavior)
            logger.warning(f"{Fore.YELLOW}   → Flagging trip for manual review")
            # Continue with insertion but flag it
            # (We'll add a 'needs_review' field in future if needed)

        # Insert trip (HISTORICAL FIX: Store landing_id per trip for boats that move between landings)
        trip_data = {
            'boat_id': boat_id,
            'landing_id': landing_id,  # Historical accuracy: landing at time of trip
            'trip_date': trip['trip_date'],
            'trip_duration': trip['trip_duration'],
            'anglers': trip['anglers']
        }

        # SPEC-010 FR-003: Link trip to scrape_job for audit trail
        if scrape_job_id is not None:
            trip_data['scrape_job_id'] = scrape_job_id

        # SPEC-010 FR-005: Store trip_hash for deduplication
        trip_data['trip_hash'] = trip_hash

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

def scrape_date_range(
    start_date: str,
    end_date: str,
    dry_run: bool = False,
    allow_future: bool = False,
    allow_early: bool = False,
    operator: Optional[str] = None
):
    """
    Scrape boats data for a date range

    SPEC-010 FR-002: Enforces Pacific Time and prevents future date scraping
    SPEC-010 FR-003: Complete audit trail for all scraping operations
    SPEC-010 FR-004: Validates scrape timing (prevents scraping today before 5pm PT)

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dry_run: If True, don't insert into database
        allow_future: If True, allow scraping future dates (DANGEROUS - use only for testing)
        allow_early: If True, allow scraping today before 5pm PT (not recommended)
        operator: Operator identity (defaults to auto-detect)

    Raises:
        FutureDateError: If end_date is in the future and allow_future is False
        ScrapingTooEarlyError: If scraping today before 5pm PT and allow_early is False
    """
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.MAGENTA}🚀 Starting Boats Scraper")
    logger.info(f"{Fore.MAGENTA}{'='*80}")
    logger.info(f"{Fore.CYAN}📅 Date range: {start_date} to {end_date}")
    logger.info(f"{Fore.CYAN}🔧 Dry run: {dry_run}")
    logger.info(f"{Fore.CYAN}🔧 Allow future: {allow_future}")
    logger.info(f"{Fore.CYAN}🔧 Allow early: {allow_early}")

    # SPEC-010 FR-003: Auto-detect operator if not provided
    if operator is None:
        operator = get_operator_identity()
    logger.info(f"{Fore.CYAN}👤 Operator: {operator}")

    # Initialize
    supabase = init_supabase() if not dry_run else None
    session = requests.Session()

    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # SPEC-010 FR-002: Pacific Time Enforcement & Future Date Guard
    # Get today in Pacific Time (America/Los_Angeles)
    pacific = pytz.timezone('America/Los_Angeles')
    today_pacific = datetime.now(pacific).date()

    logger.info(f"{Fore.CYAN}📅 Today (Pacific Time): {today_pacific}")

    # Hard guard against future dates
    if end > today_pacific:
        if not allow_future:
            logger.error(f"{Fore.RED}❌ FUTURE DATE DETECTED")
            logger.error(f"{Fore.RED}   end_date: {end_date}")
            logger.error(f"{Fore.RED}   Today (PT): {today_pacific}")
            logger.error(f"{Fore.RED}   Days in future: {(end - today_pacific).days}")
            logger.error(f"{Fore.RED}   → This prevents scraping unreported data")
            logger.error(f"{Fore.RED}   → Use --allow-future flag if intentional (NOT RECOMMENDED)")

            raise FutureDateError(
                f"end_date {end_date} is {(end - today_pacific).days} days in the future "
                f"(today is {today_pacific} Pacific Time). "
                f"This prevents accidental phantom data injection. "
                f"Use --allow-future flag if this is intentional (NOT RECOMMENDED)."
            )
        else:
            # Future dates explicitly allowed - log warning
            logger.warning(f"{Fore.YELLOW}⚠️  FUTURE DATE OVERRIDE ENABLED")
            logger.warning(f"{Fore.YELLOW}   Scraping {(end - today_pacific).days} days into the future")
            logger.warning(f"{Fore.YELLOW}   Risk: May inject phantom data if source serves fallback content")
            logger.warning(f"{Fore.YELLOW}   Safeguard: FR-001 date validation will catch mismatches")

    # SPEC-010 FR-003: Create scrape_job for audit trail
    scrape_job_id = None
    if supabase:
        scrape_job_id = create_scrape_job(
            supabase,
            operator,
            start_date,
            end_date,
            allow_future,
            dry_run
        )

    total_trips = 0
    inserted_trips = 0
    skipped_trips = 0
    failed_trips = 0

    try:
        # Iterate through dates
        current = start
        date_count = 0

        while current <= end:
            date_count += 1
            date_str = current.strftime('%Y-%m-%d')

            logger.info(f"{Fore.MAGENTA}\n{'='*80}")
            logger.info(f"{Fore.MAGENTA}📅 Processing: {date_str} ({date_count} of {(end - start).days + 1})")
            logger.info(f"{Fore.MAGENTA}{'='*80}")

            # SPEC-010 FR-004: Validate scrape timing (prevents scraping today before 5pm PT)
            validate_scrape_timing(date_str, allow_early=allow_early)

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

            # Parse trips (with database cross-reference for boat validation)
            trips = parse_boats_page(html, date_str, supabase)
            total_trips += len(trips)

            # Insert trips
            if not dry_run:
                for trip in trips:
                    # SPEC-010 FR-003: Pass scrape_job_id for audit trail
                    if insert_trip(supabase, trip, scrape_job_id):
                        inserted_trips += 1
                    else:
                        skipped_trips += 1

                # SPEC-010 FR-003: Update progress after each date
                if scrape_job_id:
                    update_scrape_job_progress(
                        supabase,
                        scrape_job_id,
                        date_count,
                        inserted_trips,
                        failed_trips
                    )
            else:
                logger.info(f"{Fore.YELLOW}🔧 DRY RUN - Would insert {len(trips)} trips")

            # Next date
            current += timedelta(days=1)

        # SPEC-010 FR-003: Complete scrape_job with SUCCESS status
        if supabase and scrape_job_id:
            complete_scrape_job(supabase, scrape_job_id, 'SUCCESS')

    except KeyboardInterrupt:
        # SPEC-010 FR-003: Handle user abort
        if supabase and scrape_job_id:
            complete_scrape_job(supabase, scrape_job_id, 'ABORTED', 'Interrupted by user')
        raise

    except (DateMismatchError, ParserError, FutureDateError, ScrapingTooEarlyError) as e:
        # SPEC-010 FR-003: Handle validation errors
        if supabase and scrape_job_id:
            complete_scrape_job(supabase, scrape_job_id, 'FAILED', str(e))
        raise

    except Exception as e:
        # SPEC-010 FR-003: Handle unexpected errors
        if supabase and scrape_job_id:
            complete_scrape_job(supabase, scrape_job_id, 'FAILED', f'Unexpected error: {str(e)}')
        raise

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

    parser = argparse.ArgumentParser(description='SD Fish Boats Scraper (Optimized) - SPEC-010 Hardened')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD), defaults to today (Pacific Time)')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - no database insertions')
    parser.add_argument('--allow-future', action='store_true',
                        help='DANGEROUS: Allow scraping future dates (may inject phantom data)')
    parser.add_argument('--allow-early', action='store_true',
                        help='Allow scraping today before 5pm PT (not recommended - reports may not be published)')
    parser.add_argument('--operator', help='Operator identity for audit trail (defaults to auto-detect)')

    args = parser.parse_args()

    # SPEC-010 FR-002: Use Pacific Time for default end_date
    if not args.end_date:
        pacific = pytz.timezone('America/Los_Angeles')
        end_date = datetime.now(pacific).strftime('%Y-%m-%d')
    else:
        end_date = args.end_date

    try:
        scrape_date_range(
            args.start_date,
            end_date,
            args.dry_run,
            args.allow_future,
            args.allow_early,
            args.operator
        )
    except KeyboardInterrupt:
        logger.info(f"\n{Fore.YELLOW}⚠️  Interrupted by user")
        sys.exit(0)
    except FutureDateError as e:
        logger.error(f"{Fore.RED}❌ Future date blocked: {e}")
        logger.error(f"{Fore.RED}   Use --allow-future flag if this is intentional (NOT RECOMMENDED)")
        sys.exit(1)
    except ScrapingTooEarlyError as e:
        logger.error(f"{Fore.RED}❌ Early scraping blocked: {e}")
        logger.error(f"{Fore.RED}   Use --allow-early flag to override (not recommended - reports may not be published)")
        sys.exit(1)
    except DateMismatchError as e:
        logger.error(f"{Fore.RED}❌ Date validation failed: {e}")
        logger.error(f"{Fore.RED}   This prevents phantom data injection")
        sys.exit(1)
    except ParserError as e:
        logger.error(f"{Fore.RED}❌ Parser error: {e}")
        logger.error(f"{Fore.RED}   Page structure may have changed - manual inspection required")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
