# San Diego Fish Reports Scraper - Technical Documentation

**Status**: ✅ Production Ready
**Version**: 3.0
**Last Updated**: October 16, 2025
**Author**: Fishing Intelligence Platform

---

## ⚠️ IMPORTANT: Scraper Migration (October 16, 2025)

**The old `sd_fish_scraper.py` has been DELETED due to a critical boat name parsing bug.**

### What Changed
- **OLD (DELETED)**: `sd_fish_scraper.py` - Had a bug that used "author" field (e.g., "Seaforth Staff") as boat name
- **NEW (USE THIS)**: `boats_scraper.py` - Correctly extracts actual boat names (e.g., "New Seaforth", "San Diego", "Pacific Voyager")

### Why the Change
The old scraper incorrectly created a boat named "Seaforth Sportfishing" (the landing name) instead of identifying individual boats. This caused 85 trips (Sept 24 - Oct 15, 2025) to be misattributed.

### Data Fix Applied
- ✅ Deleted boat ID 329 "Seaforth Sportfishing" (incorrect landing-name boat)
- ✅ Deleted 85 incorrectly attributed trips
- ✅ Ready to re-scrape with correct boat names using `boats_scraper.py`

**Going forward: ONLY use `boats_scraper.py` for all scraping.**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Data Flow](#data-flow)
7. [Error Handling](#error-handling)
8. [Validation & Testing](#validation--testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose
Automated scraper to collect fishing trip reports from [sandiegofishreports.com](https://www.sandiegofishreports.com) and populate the Supabase database with normalized, structured data.

### Key Features
- ✅ **Smart delays**: 2-5 second intervals for quality and speed
- ✅ **Duplicate detection**: Checks existing trips before insertion
- ✅ **Normalized data**: Proper foreign key relationships (landings → boats → trips → catches)
- ✅ **Automatic retry**: Handles network failures gracefully
- ✅ **Progress tracking**: Detailed logging with colored console output
- ✅ **Dry run mode**: Test without database modifications

### Performance Metrics
- **Speed**: ~10-15 trips per minute (with 2-5 second delays)
- **Accuracy**: Parses species names, counts, trip duration, angler counts
- **Reliability**: Retry logic with exponential backoff
- **Data Quality**: Validates all fields before database insertion

---

## Architecture

### Components

```
fish-scraper/
├── boats_scraper.py            # ✅ MAIN SCRAPER (use this!)
├── check_scraper_status.py     # Helper: Check what dates need updating
├── validate_data.py            # Helper: Validate database integrity
├── scripts/python/requirements.txt            # Python dependencies
├── boats_scraper.log           # Automatic logging output
└── SCRAPER_DOCS.md             # This documentation
```

**IMPORTANT**: `sd_fish_scraper.py` has been deleted. Use `boats_scraper.py` exclusively.

### Technology Stack
- **Python**: 3.8+
- **Web Scraping**: BeautifulSoup4 + Requests
- **Database**: Supabase (PostgreSQL)
- **Parsing**: regex + dateutil
- **UI**: colorama (colored console output), tqdm (progress bars)

---

## Database Schema

### Table Relationships
```
landings (id, name)
    ↓
boats (id, name, landing_id)
    ↓
trips (id, boat_id, trip_date, trip_duration, anglers)
    ↓
catches (id, trip_id, species, count)
```

### Foreign Key Constraints
- `boats.landing_id` → `landings.id`
- `trips.boat_id` → `boats.id`
- `catches.trip_id` → `trips.id`

### Duplicate Prevention
Unique constraint on: `(boat_id, trip_date, trip_duration)`

This prevents inserting the same trip twice (e.g., "Excel on 2025-09-25 for 1.5 days").

---

## Installation

### Step 1: Install Python Dependencies
```bash
cd /Users/btsukada/desktop/fishing/fish-scraper
pip install -r scripts/python/requirements.txt
```

### Step 2: Verify Supabase Connection
```bash
python3 -c "from boats_scraper import init_supabase; init_supabase(); print('✅ Connected!')"
```

### Step 3: Make Scraper Executable
```bash
chmod +x boats_scraper.py
```

---

## Usage

### Basic Commands

#### 1. **Dry Run (Test Mode)**
Test scraping without database modifications:
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-09-24 --end-date 2025-10-15 --dry-run
```

#### 2. **Production Run (Update Database)**
Scrape and insert into database:
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-09-24 --end-date 2025-10-15
```

#### 3. **Single Day (Fast Test)**
Scrape just one day:
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-10-15 --end-date 2025-10-15
```

### Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--start-date` | Yes | None | Start date for scraping (YYYY-MM-DD) |
| `--end-date` | No | Today | End date for scraping (YYYY-MM-DD) |
| `--dry-run` | No | `False` | Test mode - don't insert into database |

### Examples

**Scrape last week's data:**
```bash
START_DATE=$(date -v-7d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
python3 scripts/python/boats_scraper.py --start-date $START_DATE --end-date $END_DATE
```

**Update from specific date to today:**
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-10-01
```

**Quick test (single day, dry run):**
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-10-15 --end-date 2025-10-15 --dry-run
```

---

## Data Flow

### 1. **Fetch Boats Page for Date**
```
GET https://www.sandiegofishreports.com/dock_totals/boats.php?date=YYYY-MM-DD
    ↓
Parse HTML with BeautifulSoup
    ↓
Extract structured boat trip data from tables
```

### 2. **Parse Seaforth Section**
```
For each landing section:
    Find landing header (e.g., "Seaforth Sportfishing Fish Counts")
    ↓
    Extract boat entries:
      - Boat name (e.g., "New Seaforth", "San Diego")
      - Anglers count
      - Trip duration (e.g., "1/2 Day AM", "Full Day Offshore")
      - Catches (species + counts)
```

### 3. **Normalize Trip Data**
```
For each trip:
    Normalize trip type (remove "Offshore"/"Local" suffixes)
    ↓
    Parse species counts from catch text
    ↓
    Prepare for database insertion
```

### 4. **Normalize Data**
```
Landing name → Get/Create landing ID
    ↓
Boat name + landing ID → Get/Create boat ID
    ↓
Check if trip exists (boat_id + trip_date)
    ↓
Insert trip → Insert catches
```

### 5. **Output**
```
✅ Trip inserted: Excel on 2025-09-25 - 3 species
⚠️  Trip already exists: Tomahawk on 2025-09-24
```

---

## Error Handling

### Network Failures
- **Retry logic**: 3 attempts with exponential backoff (5s, 10s, 15s)
- **Timeout**: 30 seconds per request
- **Graceful degradation**: Logs error, continues to next report

### Parsing Errors
- **Species parsing**: Handles multiple formats ("37 bluefin tuna", "80-120 lb yellowfin")
- **Date parsing**: Uses dateutil for flexible date formats
- **Missing data**: Allows null values for optional fields (anglers, weather_notes)

### Database Errors
- **Duplicate detection**: Checks before insertion
- **Foreign key violations**: Creates missing landings/boats automatically
- **Transaction safety**: Each trip is an atomic operation

### Logging
All errors are logged to:
- **Console**: Color-coded output (red = error, yellow = warning, green = success)
- **File**: `scraper.log` with timestamps and stack traces

---

## Validation & Testing

### Pre-Scraping Checks

#### 1. **Check Current Database State**
```bash
python3 check_scraper_status.py
```
Output:
```
Database Status:
✅ Landings: 7
✅ Boats: 74
✅ Trips: 7,954
✅ Latest trip date: 2025-09-22
⚠️  Missing dates since: 2025-09-23 to 2025-10-15 (23 days)
```

#### 2. **Validate Data Integrity**
```bash
python3 scripts/python/validate_data.py
```
Checks:
- All trips have valid boat_id
- All catches have valid trip_id
- No orphaned records
- Date ranges are reasonable

### Post-Scraping Validation

#### 1. **Count New Trips**
```bash
python3 -c "
from boats_scraper import init_supabase
supabase = init_supabase()
result = supabase.table('trips').select('count').gte('trip_date', '2025-09-24').execute()
print(f'Trips since 2025-09-24: {result.data[0][\"count\"]}')
"
```

#### 2. **Check Latest Date**
```bash
python3 -c "
from boats_scraper import init_supabase
supabase = init_supabase()
result = supabase.table('trips').select('trip_date').order('trip_date', desc=True).limit(1).execute()
print(f'Latest trip: {result.data[0][\"trip_date\"]}')
"
```

### Dry Run Testing
Always test with `--dry-run` first:
```bash
python3 scripts/python/boats_scraper.py --start-date 2025-10-15 --end-date 2025-10-15 --dry-run
```

Review logs for:
- ✅ Correct date filtering
- ✅ Proper species parsing
- ✅ Correct boat names (not landing names!)
- ✅ Landing/boat associations
- ✅ No parsing errors

---

## Troubleshooting

### Issue: No reports found on page 1

**Cause**: Website structure changed or network issue

**Solution**:
```bash
# Test if website is accessible
curl -I https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-15

# Check if HTML structure changed
python3 -c "
from boats_scraper import fetch_page
import requests
session = requests.Session()
html = fetch_page('https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-15', session)
print(html[:1000])
"
```

### Issue: Duplicate key violations

**Cause**: Trip already exists in database

**Solution**: This is expected behavior. Scraper logs and skips duplicates:
```
⚠️  Trip already exists: Excel on 2025-09-25
```

### Issue: Species not parsed correctly

**Cause**: Unexpected report format

**Solution**: Check `boats_scraper.log` for parsing warnings:
```bash
grep "species" boats_scraper.log
```

Update regex patterns in `parse_species_counts()` in `boats_scraper.py` if needed.

### Issue: Connection timeout

**Cause**: Network instability or server slowdown

**Solution**: Scraper automatically retries 3 times. If persistent:
```bash
# Increase timeout in boats_scraper.py (line ~100)
response = session.get(url, headers=headers, timeout=60)  # 60 seconds
```

### Issue: Too many requests / IP blocked

**Cause**: Delays too short (unlikely with 2-5 seconds)

**Solution**:
```bash
# Increase delays in boats_scraper.py (lines 50-51)
MIN_DELAY = 5  # 5 seconds
MAX_DELAY = 10  # 10 seconds
```

---

## Code Structure

### Main Functions

#### `scrape_from_date(start_date, dry_run, max_pages)`
Main orchestrator - coordinates pagination, parsing, and insertion.

#### `fetch_page(url, session, retry_count)`
Fetches HTML with retry logic and error handling.

#### `parse_report_page(html)`
Parses list page into report metadata (title, boat, landing, date, url).

#### `parse_detailed_report(html, report_metadata)`
Parses detailed report into trip data (catches, duration, anglers).

#### `parse_species_counts(text)`
Regex-based species and count extraction.

#### `insert_trip(supabase, trip)`
Normalizes and inserts trip with foreign key handling.

### Data Normalization

#### `get_or_create_landing(supabase, landing_name)`
Returns landing ID, creates if doesn't exist.

#### `get_or_create_boat(supabase, boat_name, landing_id)`
Returns boat ID, creates if doesn't exist.

#### `check_trip_exists(supabase, boat_id, trip_date)`
Prevents duplicate insertions.

### Utility Functions

#### `normalize_landing_name(landing)`
Maps common variations to standard names:
- "H&M" → "H&M Landing"
- "Seaforth" → "Seaforth Sportfishing"

#### `parse_trip_duration(text)`
Converts text to days:
- "1.5 day" → 1.5
- "overnight" → 0.5
- "3/4 day" → 0.75

---

## Performance Optimization

### Current Performance
- **Pages per minute**: ~12-15 pages (with 2-5 second delays)
- **Trips per minute**: ~10-15 trips (assuming ~1 trip per page)
- **100 trips**: ~7-10 minutes

### Optimization Strategies

#### 1. **Reduce Delays (if no blocking occurs)**
```python
MIN_DELAY = 1  # 1 second
MAX_DELAY = 2  # 2 seconds
```

#### 2. **Parallel Processing (advanced)**
Use `asyncio` or `multiprocessing` for concurrent requests:
```python
import asyncio
import aiohttp
# Fetch multiple pages simultaneously
```

#### 3. **Caching (for repeated runs)**
Cache already-processed report URLs to skip duplicates faster.

---

## Maintenance

### Regular Tasks

#### Weekly: Check for missing dates
```bash
python3 check_scraper_status.py
```

#### Monthly: Validate data integrity
```bash
python3 scripts/python/validate_data.py
```

#### Quarterly: Review landing/boat names
```bash
python3 -c "
from boats_scraper import init_supabase
supabase = init_supabase()
landings = supabase.table('landings').select('name').execute()
boats = supabase.table('boats').select('name, landing_id').execute()
print('Landings:', [l['name'] for l in landings.data])
print('Boats:', [(b['name'], b['landing_id']) for b in boats.data[:10]])
"
```

Check for:
- Duplicate landings with different names ("H&M" vs "H & M Landing")
- Boats assigned to wrong landings
- **Boats named after landings** (e.g., "Seaforth Sportfishing" as boat name - this is WRONG!)

### Code Updates

#### When website structure changes:
1. Run dry-run test
2. Check `boats_scraper.log` for parsing errors
3. Update parsing logic in `boats_scraper.py`:
   - `parse_boats_page()` - Main parsing function
   - `parse_species_counts()` - Species extraction
   - `normalize_trip_type()` - Trip duration normalization
4. Test with `--dry-run` on a single date first

#### When adding new features:
1. Create feature branch
2. Update this documentation
3. Add tests in `validate_data.py`
4. Run full dry-run before production

---

## Security Notes

### Supabase Credentials
- **URL**: `https://ulsbtwqhwnrpkourphiq.supabase.co`
- **Key**: Stored in code (anon key - safe for client-side use)
- **Security**: Row Level Security (RLS) enabled in Supabase

### API Rate Limiting
- Website has no explicit rate limits
- 2-5 second delays prevent server overload
- User-Agent identifies as standard browser

---

## Support & Contact

### Issues
- Check `scraper.log` for detailed error messages
- Review this documentation's [Troubleshooting](#troubleshooting) section
- Contact: Fishing Intelligence Platform team

### Future Enhancements
- [ ] Add weather data parsing
- [ ] Extract fishing locations (lat/lon)
- [ ] Add captain/author tracking
- [ ] Implement image scraping for reports
- [ ] Add email notifications for scraping failures

---

**Last Updated**: October 16, 2025
**Version**: 3.0
**Status**: ✅ Production Ready (using boats_scraper.py)

---

## 📝 Change Log

### Version 3.0 (October 16, 2025)
- **BREAKING**: Deleted `sd_fish_scraper.py` due to boat name parsing bug
- **NEW**: `boats_scraper.py` is now the only supported scraper
- **FIX**: Boat names now correctly extracted (not landing names)
- **DATA**: Deleted 85 misattributed trips, ready for re-scrape

### Version 2.0 (October 15, 2025)
- Deprecated version with sd_fish_scraper.py (DO NOT USE)
