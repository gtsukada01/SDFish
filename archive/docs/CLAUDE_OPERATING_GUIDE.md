# Fish Scraper - Claude Operating Guide

**For Claude Code Agents**: This guide provides explicit, step-by-step instructions for operating the fish scraper system with 100% data accuracy (SPEC 006 mandate).

**Last Updated**: October 20, 2025
**Status**: 🚨 **CRITICAL PARSER BUG FIXED - REMEDIATION IN PROGRESS**

---

## 🚨 CRITICAL: Parser Bug Fixed (Oct 20, 2025)

**ALL NEW TEAM MEMBERS READ THIS FIRST**

### What Happened

A regex bug in `parse_boats_page()` (boats_scraper.py line 655) silently dropped boats with:
- 3+ word names (Lucky B Sportfishing)
- Single letters (Little G)
- Numbers (Oceanside 95)
- Special characters (Patriot (SD))

**Impact**: 28+ trips missing from Oct 10-18 alone. Potentially hundreds missing from all historical data (Jan 2024 - Oct 2025).

### What Was Fixed

**OLD (BROKEN) CODE:**
```python
# Line 655 - FAULTY REGEX
if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line):
    boat_name = line
```

**NEW (FIXED) CODE:**
```python
# Database cross-reference validation (PRIMARY)
if line in known_boats:
    boat_name = line
    boat_info = known_boats[line]
    # Validated against 124 known boats in database

# Fallback regex for new boats (SECONDARY)
elif re.match(r'^[A-Z][a-z0-9]*(\s+[A-Z0-9][a-z0-9]*){0,4}$', line):
    boat_name = line
    logger.warning("NEW BOAT DETECTED")
```

### Files Modified

1. **boats_scraper.py**:
   - Added `get_all_known_boats(supabase)` - loads 124 boats from database
   - Modified `parse_boats_page(html, date, supabase)` - now takes supabase client
   - Replaced regex-only matching with database cross-reference

2. **qc_validator.py**:
   - Updated `validate_date()` to pass supabase client to parser

### Current Status

- ✅ **Parser fixed** (Oct 20, 2025)
- ✅ **Oct 19 scraped** with fixed parser (28/28 trips)
- ⚠️ **Oct 10-18 needs re-scraping** (28 known missing trips)
- ⚠️ **All historical data needs audit** (potentially hundreds of missing trips)

### Next Team: IMMEDIATE ACTIONS

See README.md "Remediation Commands" section for step-by-step instructions.

**DO NOT SKIP THE REMEDIATION STEPS** - The database is currently incomplete.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Required Tools & Dependencies](#required-tools--dependencies)
3. [System Architecture](#system-architecture)
4. [Progressive Scraping Workflow](#progressive-scraping-workflow)
5. [QC Validation Process](#qc-validation-process)
6. [Error Handling & Recovery](#error-handling--recovery)
7. [Database Operations](#database-operations)
8. [Parser Maintenance](#parser-maintenance)
9. [Troubleshooting Guide](#troubleshooting-guide)

---

## Directory Structure

### Working Directory
```bash
/Users/btsukada/Desktop/Fishing/fish-scraper/
```

### Critical Files
```
fish-scraper/
├── boats_scraper.py              # Main scraper (SPEC 006 validated)
├── qc_validator.py               # QC validation system
├── socal_scraper.py              # Regional scraper (uses same parser)
├── index.html                    # Dashboard entry point
├── package.json                  # Node dependencies
├── tsconfig.json                 # TypeScript config
├── tailwind.config.js            # Tailwind CSS config
│
├── src/                          # React dashboard source
│   ├── main.tsx                  # React entry
│   ├── App.tsx                   # Main app component
│   ├── components/               # shadcn/ui components
│   └── lib/                      # Utilities
│
├── assets/                       # Compiled dashboard assets
│   ├── main.js                   # React bundle
│   └── styles.css                # Tailwind output
│
├── specs/                        # Specification documents
│   └── 006-scraper-accuracy-validation/
│       ├── constitution.md       # Zero tolerance principles
│       ├── spec.md               # Functional requirements
│       ├── date-semantics-report.md
│       └── qc_validator_README.md
│
├── SPEC_006_SUMMARY.md           # High-level summary
├── FINAL_VALIDATION_REPORT.md    # Validation results
├── README.md                     # Project documentation
└── CLAUDE_OPERATING_GUIDE.md     # This file
```

---

## Required Tools & Dependencies

### Python Environment (3.9+)

**Required Packages**:
```bash
pip3 install requests beautifulsoup4 lxml supabase colorama
```

**Package Purposes**:
- `requests`: HTTP requests to fetch boat pages
- `beautifulsoup4`: HTML parsing
- `lxml`: Fast XML/HTML parser backend
- `supabase`: Database client (PostgreSQL)
- `colorama`: Colored terminal output

### Node.js Environment (16+)

**Install Dependencies**:
```bash
cd /Users/btsukada/Desktop/Fishing/fish-scraper
npm --prefix frontend install
```

**Key Packages**:
- `react@18.3.1`: UI framework
- `@radix-ui/*`: shadcn/ui components
- `tailwindcss`: CSS framework
- `esbuild`: Fast JavaScript bundler
- `@supabase/supabase-js`: Database client

### Database Access

**Supabase Connection**:
- URL: `https://ulsbtwqhwnrpkourphiq.supabase.co`
- Key: Embedded in `boats_scraper.py` line 47
- Tables: `landings`, `boats`, `trips`, `catches`

**Schema**:
```
landings (id, name)
    ↓
boats (id, name, landing_id)
    ↓
trips (id, boat_id, trip_date, trip_duration, anglers)
    ↓
catches (id, trip_id, species, count)
```

---

## System Architecture

### Data Flow (SPEC 006)
```
Source Page (boats.php)
    ↓
Parser (boats_scraper.py)
    ↓
Validation (field-level checks)
    ↓
Database (Supabase)
    ↓
QC Validator (qc_validator.py)
    ↓
Pass/Fail Report (JSON)
```

### Critical Components

**1. boats_scraper.py**
- **Purpose**: Scrapes boats.php pages and inserts into database
- **Key Function**: `parse_boats_page(html, date)` (line 212-352)
- **Landing Detection**: `is_landing_header(line)` (line 176-192)
- **Rate Limiting**: 2-5 second delays between requests

**2. qc_validator.py**
- **Purpose**: Validates database matches source pages 100%
- **Key Function**: `validate_date(date)` - field-level comparison
- **Composite Matching**: Boat + Trip Type + Anglers
- **Speed**: ~2-3 seconds per date

**3. Dashboard (index.html + React)**
- **Purpose**: Visualize validated fishing data
- **Port**: 3002
- **Data Source**: Direct Supabase queries
- **UI**: shadcn/ui components

---

## Progressive Scraping Workflow

### CRITICAL: Always Use Progressive Validation

**Rule**: Scrape in batches of 5 dates, QC validate after each batch. If any date fails, STOP, investigate, fix, delete bad data, re-scrape.

### Step-by-Step Process

#### Step 1: Plan Your Batch

```bash
# Example: Scraping Sept 1-5, 2025
START_DATE="2025-09-01"
END_DATE="2025-09-05"
BATCH_NAME="batch1_sept1-5"
```

#### Step 2: Run Scraper

```bash
cd /Users/btsukada/Desktop/Fishing/fish-scraper

# Execute scraper
python3 scripts/python/boats_scraper.py --start-date $START_DATE --end-date $END_DATE

# Expected output:
# ✅ Fetched [X] bytes
# ✅ Parsed [Y] trips
# ✅ Inserted [Y] trips
# ⚠️  Trips skipped: 0  # MUST be 0
```

**Monitor Output**:
- Look for `📍 Landing header detected:` - confirms landing recognition
- Look for `✅ Parsed: [boat] - [N] species, [M] anglers` - confirms trip parsing
- Look for `⚠️ Trips skipped: 0` - MUST be zero

#### Step 3: QC Validate Immediately

```bash
# Run QC validation
python3 scripts/python/qc_validator.py \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --output qc_$BATCH_NAME.json

# Expected output:
# ✅ QC PASSED: 2025-09-01
# ✅ QC PASSED: 2025-09-02
# ...
# ✅ QC PASSED: 2025-09-05
```

#### Step 4: Verify Results

```bash
# Check pass rate
cat qc_$BATCH_NAME.json | jq '.summary.pass_rate'

# Expected: 100

# Check for failures
cat qc_$BATCH_NAME.json | jq '.summary.failed'

# Expected: 0
```

**Decision Point**:
- **If pass_rate == 100**: ✅ Continue to next batch
- **If pass_rate < 100**: ❌ STOP, go to Error Handling section

#### Step 5: Continue to Next Batch

```bash
# Move to next batch
START_DATE="2025-09-06"
END_DATE="2025-09-10"
BATCH_NAME="batch2_sept6-10"

# Repeat Steps 2-4
```

---

## QC Validation Process

### Understanding QC Validation

**Purpose**: Verify database matches source pages field-by-field.

**What It Checks**:
1. ✅ **Boat Count Match**: Source page has X boats, database has X boats
2. ✅ **Field-Level Accuracy**: Landing, boat, trip type, anglers, species, counts
3. ✅ **No Missing Boats**: All boats on source page are in database
4. ✅ **No Extra Boats**: No boats in database that aren't on source page
5. ✅ **Composite Key Matching**: Uses boat + trip type + anglers to identify trips

### QC Validator Commands

#### Validate Single Date
```bash
python3 scripts/python/qc_validator.py --date 2025-09-30
```

**Use Case**: Quick check of a specific date.

**Output**:
```
================================================================================
🔍 QC VALIDATION: 2025-09-30
================================================================================
📊 Source page: 15 trips
📊 Database: 15 trips
✅ Match: Polaris Supreme
✅ Match: Liberty
...
================================================================================
✅ QC PASSED: 2025-09-30
📊 Matches: 15/15
⚠️  Mismatches: 0
⚠️  Missing boats: 0
⚠️  Extra boats: 0
================================================================================
```

#### Validate Date Range
```bash
python3 scripts/python/qc_validator.py \
  --start-date 2025-09-01 \
  --end-date 2025-09-30 \
  --output qc_september.json
```

**Use Case**: Validate entire batch or month.

**Output**: JSON report with per-date results.

#### Polaris Supreme Test
```bash
python3 scripts/python/qc_validator.py --polaris-test --output polaris_test.json
```

**Use Case**: Validate the 10 Polaris Supreme trips from Sept 9 - Oct 10.

**Expected**: 10/10 trips with exact dates.

### Interpreting QC Results

#### ✅ PASS Status
```json
{
  "date": "2025-09-30",
  "status": "PASS",
  "source_boat_count": 15,
  "database_boat_count": 15,
  "matches": 15,
  "mismatches": [],
  "missing_boats": [],
  "extra_boats": [],
  "field_errors": []
}
```

**Meaning**: 100% accuracy. Database matches source page perfectly.

**Action**: Continue to next batch.

#### ❌ FAIL Status - Mismatch
```json
{
  "date": "2025-09-03",
  "status": "FAIL",
  "mismatches": [
    {
      "boat": "Sea Star",
      "errors": [
        "Landing mismatch: source='Oceanside Sea Center' db='H&M Landing'"
      ]
    }
  ]
}
```

**Meaning**: Database has wrong data for this trip.

**Action**:
1. Go to Error Handling section
2. Investigate parser bug
3. Fix parser
4. Delete bad data
5. Re-scrape

#### ❌ FAIL Status - Missing Boat
```json
{
  "date": "2025-09-15",
  "status": "FAIL",
  "missing_boats": [
    {
      "boat": "Polaris Supreme",
      "landing": "Seaforth Sportfishing",
      "trip_type": "3 Day",
      "anglers": 22
    }
  ]
}
```

**Meaning**: Boat on source page but NOT in database.

**Action**:
1. Check if scraper ran for this date
2. Check scraper logs for parsing errors
3. Investigate landing header detection
4. Re-scrape this date

---

## Error Handling & Recovery

### When QC Validation Fails

#### Step 1: Identify Root Cause

**Check QC Report**:
```bash
cat qc_report.json | jq '.reports[] | select(.status == "FAIL")'
```

**Common Issues**:
1. **Landing Mismatch**: Wrong landing assigned (parser bug)
2. **Missing Boat**: Boat not parsed (parsing failed)
3. **Field Mismatch**: Wrong anglers/species/counts
4. **Extra Boat**: Duplicate in database

#### Step 2: Investigate Parser

**Test Parser on Failing Date**:
```bash
# Dry run to see what parser extracts
python3 scripts/python/boats_scraper.py --start-date 2025-09-03 --end-date 2025-09-03 --dry-run
```

**Check Logs**:
```bash
tail -100 boats_scraper.log | grep "2025-09-03"
```

**Look For**:
- `📍 Landing header detected:` - Are all landings detected?
- `🔍 Found boat:` - Are all boats found?
- `⚠️ Warning:` - Any parsing warnings?

#### Step 3: Fix Parser (If Needed)

**Common Parser Bugs**:

**Landing Detection Bug**:
```python
# File: boats_scraper.py
# Function: is_landing_header() (line 176-192)

# Symptom: Landing headers confused with data
# Fix: Ensure is_landing_header() checks for "fish counts" without "boat"
```

**Composite Key Matching**:
```python
# File: qc_validator.py
# Function: find_matching_trip() (line ~300)

# Symptom: Multiple trips per boat not distinguished
# Fix: Ensure matching uses boat + trip_type + anglers
```

#### Step 4: Delete Bad Data

**CRITICAL**: Always backup before deletion.

```bash
# Delete trips for specific date
python3 -c "
from boats_scraper import init_supabase

supabase = init_supabase()

# Delete date
date = '2025-09-03'
result = supabase.table('trips').delete().eq('trip_date', date).execute()
print(f'Deleted {len(result.data)} trips for {date}')
"
```

**For Date Range**:
```bash
# Delete Sept 1-5
python3 -c "
from boats_scraper import init_supabase
from datetime import datetime, timedelta

supabase = init_supabase()

start = datetime(2025, 9, 1).date()
for i in range(5):
    date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
    result = supabase.table('trips').delete().eq('trip_date', date).execute()
    print(f'{date}: {len(result.data)} trips deleted')
"
```

#### Step 5: Re-scrape with Fixed Parser

```bash
# Re-scrape the dates that failed
python3 scripts/python/boats_scraper.py --start-date 2025-09-03 --end-date 2025-09-03

# QC validate again
python3 scripts/python/qc_validator.py --date 2025-09-03

# Verify PASS
```

---

## Database Operations

### Connection Test

```bash
python3 -c "
from boats_scraper import init_supabase

supabase = init_supabase()

# Count trips
result = supabase.table('trips').select('id').execute()
print(f'✅ Database connected: {len(result.data)} trips')
"
```

### Query Trip Data

```bash
# Get trips for specific date
python3 -c "
from boats_scraper import init_supabase

supabase = init_supabase()

result = supabase.table('trips').select('*,boats(name,landings(name)),catches(species,count)').eq('trip_date', '2025-09-30').execute()

for trip in result.data:
    print(f'{trip[\"boats\"][\"name\"]} - {trip[\"boats\"][\"landings\"][\"name\"]}')
"
```

### Check for Duplicates

```bash
# Check for duplicate trips
python3 -c "
from boats_scraper import init_supabase

supabase = init_supabase()

result = supabase.rpc('find_duplicate_trips').execute()
if result.data:
    print(f'❌ Found {len(result.data)} duplicates')
else:
    print('✅ No duplicates')
"
```

### Database Schema Validation

**Tables**:
- `landings`: Landing names (H&M Landing, Seaforth, etc.)
- `boats`: Boat names with landing_id foreign key
- `trips`: Trip records with boat_id, date, duration, anglers
- `catches`: Species and counts with trip_id foreign key

**Foreign Keys** (CRITICAL):
```sql
boats.landing_id → landings.id
trips.boat_id → boats.id
catches.trip_id → trips.id
```

**Unique Constraint**:
```sql
UNIQUE (boat_id, trip_date, trip_duration)
```

This prevents duplicate trips for same boat/date/type.

**Trip Duration Normalization** (Oct 18, 2025):
- Database contains **20 standardized trip duration categories**
- Normalized from 43 original variants
- Geographic qualifiers removed (Local, Coronado Islands, Mexican Waters, Offshore)
- Duplicate types consolidated (e.g., "Reverse Overnight" → "Overnight")
- See [MOON_PHASE_DURATION_MAPPING.md](MOON_PHASE_DURATION_MAPPING.md) for complete mapping

**Standard Trip Duration Values** (Dashboard Display Order):
```
Half-Day: 2 Hour, 4 Hour, 6 Hour, 1/2 Day AM, 1/2 Day PM, 1/2 Day Twilight
Three-Quarter Day: 3/4 Day, 10 Hour
Full Day: Full Day, 12 Hour
Overnight: Overnight
Multi-Day: 1.5 Day, 1.75 Day, 2 Day, 2.5 Day, 3 Day, 3.5 Day, 4 Day, 5 Day
Special: Lobster
```

**Note**: Dashboard groups trips by actual duration. Short hourly trips (2-6 hours) are grouped with half-day trips. 10 Hour trips are grouped with 3/4 Day (~9-10 hours), and 12 Hour trips are grouped with Full Day (~12 hours).

---

## Parser Maintenance

### Critical Parser Functions

#### 1. parse_boats_page()
**Location**: `boats_scraper.py` line 212-352

**Purpose**: Extract trip data from HTML.

**Critical Sections**:
```python
# Line 260: Landing header detection
if is_landing_header(line):
    landing_name = re.sub(r'\s*fish counts\s*', '', normalized, flags=re.IGNORECASE).strip()
    current_landing = landing_name

# Line 279-308: Boat/anglers/trip parsing
# Line 321-327: Catches assignment with landing header check
```

**SPEC 006 Fix** (Line 321-327):
```python
# CRITICAL: Check if next line is landing header
if is_landing_header(potential_catches):
    logger.warning("Landing header found instead of catches")
    catches_text = None  # Skip boat
else:
    catches_text = potential_catches
```

#### 2. is_landing_header()
**Location**: `boats_scraper.py` line 176-192

**Purpose**: Distinguish landing headers from data.

**Implementation**:
```python
def is_landing_header(line: str) -> bool:
    if not line:
        return False
    normalized = ' '.join(line.split()).lower()
    return 'fish counts' in normalized and 'boat' not in normalized
```

**Why Critical**: Prevents "Oceanside Sea Center Fish Counts" from being treated as catches data.

#### 3. normalize_trip_type()
**Location**: `boats_scraper.py` line 123-146

**Purpose**: Clean trip type text for consistency.

**Examples**:
- `"OvernightOffshore"` → `"Overnight"`
- `"1/2DayAM"` → `"1/2 Day AM"`
- `"FullDayCoronado Islands"` → `"Full Day Coronado Islands"`

#### 4. parse_species_counts()
**Location**: `boats_scraper.py` line 194-224

**Purpose**: Extract species and counts from catches text.

**Example**:
```
Input: "28 Bluefin Tuna, 9 Yellowtail, 5 Bluefin Tuna Released"
Output: [
  {"species": "Bluefin Tuna", "count": 28},
  {"species": "Yellowtail", "count": 9}
]
Note: Ignores "Released" fish
```

### Parser Testing

**Dry Run Test**:
```bash
# Test parser without database insertion
python3 scripts/python/boats_scraper.py --start-date 2025-09-30 --end-date 2025-09-30 --dry-run
```

**Expected Output**:
- Landing detection messages
- Boat parsing messages
- Trip counts
- NO database insertions

**Landing Detection Test**:
```python
from boats_scraper import is_landing_header

# Test cases
assert is_landing_header("H&M Landing Fish Counts") == True
assert is_landing_header("Seaforth Sportfishing Fish Counts") == True
assert is_landing_header("Boat  Trip Details  Dock Totals") == False
assert is_landing_header("28 Bluefin Tuna, 9 Yellowtail") == False
```

---

## Troubleshooting Guide

### Issue: Scraper Fails to Fetch Page

**Symptoms**:
```
❌ Failed to fetch https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-09-30
```

**Causes**:
1. Network connection issue
2. Website down
3. Rate limiting (too many requests)

**Solutions**:
```bash
# Test URL directly
curl -I "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-09-30"

# Expected: HTTP/2 200

# If 403/429: Wait 5 minutes, then retry
# If 404: Check date format (must be YYYY-MM-DD)
# If connection error: Check internet connection
```

### Issue: QC Validation Shows Mismatches

**Symptoms**:
```json
{
  "status": "FAIL",
  "mismatches": [...]
}
```

**Solution Path**:
1. Read QC report to identify exact mismatch
2. Compare source page manually: `boats.php?date=YYYY-MM-DD`
3. Check parser logs for that date
4. Identify parser bug
5. Fix parser
6. Delete bad data
7. Re-scrape
8. QC validate again

### Issue: Multiple Trips Per Boat Not Distinguished

**Symptoms**:
```
❌ AMBIGUOUS: Multiple trips for New Seaforth (1/2 Day AM)
```

**Cause**: Composite key matching not using anglers.

**Solution**:
Check `qc_validator.py` function `find_matching_trip()` uses anglers as tiebreaker.

### Issue: Database Connection Fails

**Symptoms**:
```
❌ Supabase connection failed
```

**Solutions**:
```bash
# Test connection
python3 -c "from boats_scraper import init_supabase; init_supabase()"

# Expected: ✅ Supabase connected

# If fails:
# 1. Check internet connection
# 2. Check Supabase credentials (line 46-47 in boats_scraper.py)
# 3. Check Supabase service status
```

### Issue: Dashboard Not Loading

**Symptoms**: http://localhost:3002 shows blank page or errors.

**Solutions**:
```bash
# 1. Check if assets are built
ls -la assets/
# Expected: main.js, styles.css

# 2. Rebuild assets
npm run build

# 3. Start HTTP server
python3 -m http.server 3002

# 4. Check browser console for errors (F12)
```

---

## Quick Reference Commands

### Scraping
```bash
# Scrape single date
python3 scripts/python/boats_scraper.py --start-date 2025-09-30 --end-date 2025-09-30

# Scrape date range
python3 scripts/python/boats_scraper.py --start-date 2025-09-01 --end-date 2025-09-30

# Dry run (no database)
python3 scripts/python/boats_scraper.py --start-date 2025-09-30 --end-date 2025-09-30 --dry-run
```

### QC Validation
```bash
# Validate single date
python3 scripts/python/qc_validator.py --date 2025-09-30

# Validate date range
python3 scripts/python/qc_validator.py --start-date 2025-09-01 --end-date 2025-09-30 --output qc.json

# Polaris Supreme test
python3 scripts/python/qc_validator.py --polaris-test --output polaris.json

# Check pass rate
cat qc.json | jq '.summary.pass_rate'
```

### Dashboard
```bash
# Build assets (watch mode)
npm run dev &

# Start HTTP server
python3 -m http.server 3002

# Access dashboard
# → http://localhost:3002
```

### Database
```bash
# Count trips
python3 -c "from boats_scraper import init_supabase; s = init_supabase(); r = s.table('trips').select('id').execute(); print(f'{len(r.data)} trips')"

# Delete date
python3 -c "from boats_scraper import init_supabase; s = init_supabase(); s.table('trips').delete().eq('trip_date', '2025-09-30').execute()"
```

---

## Critical Success Factors

### Zero Tolerance Principles

1. **100% Accuracy Required**: No tolerance for data drift
2. **Progressive Validation**: Always scrape in batches, validate immediately
3. **Source of Truth**: boats.php pages are single source of truth
4. **Field-Level Validation**: Every field must match exactly
5. **Composite Key Matching**: Use boat + trip type + anglers

### Red Flags (STOP IMMEDIATELY)

❌ **QC pass rate < 100%**
❌ **"Trips skipped" > 0** during scraping
❌ **Parser warnings** about missing data
❌ **Multiple trips for same boat** without anglers tiebreaker
❌ **Landing headers** appearing in catches text

### Green Lights (CONTINUE)

✅ **QC pass rate = 100%**
✅ **Zero mismatches** in QC report
✅ **Zero missing boats**
✅ **Zero extra boats**
✅ **All landing headers detected**

---

## Final Checklist

Before considering a scraping session complete:

- [ ] All dates scraped successfully (no fetch errors)
- [ ] All dates QC validated (100% pass rate)
- [ ] Polaris Supreme test passed (if date range includes Sept 9 - Oct 10)
- [ ] No parser warnings in logs
- [ ] Database trip count matches expected
- [ ] Dashboard displays new data correctly
- [ ] QC reports saved for documentation

---

## Support Documents

- **SPEC 006 Summary**: `/Users/btsukada/Desktop/Fishing/fish-scraper/SPEC_006_SUMMARY.md`
- **Final Validation Report**: `/Users/btsukada/Desktop/Fishing/fish-scraper/FINAL_VALIDATION_REPORT.md`
- **QC Validator README**: `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/006-scraper-accuracy-validation/qc_validator_README.md`
- **Constitution**: `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/006-scraper-accuracy-validation/constitution.md`
- **Documentation Standards**: `/Users/btsukada/Desktop/Fishing/fish-scraper/DOCUMENTATION_STANDARDS.md`
- **Comprehensive QC Verification**: `/Users/btsukada/Desktop/Fishing/fish-scraper/COMPREHENSIVE_QC_VERIFICATION.md`

---

## Documentation Standards & Hygiene

### CRITICAL: Single Source of Truth

**README.md** is the ONLY entry point for project status. All other documents are linked from README, never duplicated.

### Documentation Rules

**❌ DO NOT:**
- Create new monthly/batch .md files
- Duplicate stats or status across multiple files
- Delete historical docs without archiving
- Create standalone completion reports

**✅ DO:**
- Update existing annual reports (2024_SCRAPING_REPORT.md, 2025_SCRAPING_REPORT.md)
- Append new months to master documents
- Archive superseded files to `archive/` folder
- Update DOC_CHANGELOG.md for every change
- Link all docs from README.md

### Master Documents Structure

```
README.md                           # Single source of truth
COMPREHENSIVE_QC_VERIFICATION.md    # Master QC validation report
2024_SCRAPING_REPORT.md            # 2024 consolidated annual report
2025_SCRAPING_REPORT.md            # 2025 consolidated annual report
DOC_CHANGELOG.md                    # Audit trail
DOCUMENTATION_STANDARDS.md          # Governance rules
```

### When Completing New Months

**Update Process** (Example: November 2025 completes):

1. **Update 2025_SCRAPING_REPORT.md**:
   - Add November to monthly breakdown
   - Update overall statistics
   - Document any QC issues in appendix

2. **Update README.md**:
   - Update total trip count
   - Update completion percentage
   - Update "Last Updated" timestamp

3. **Update COMPREHENSIVE_QC_VERIFICATION.md** (if QC issues):
   - Add to Known Issues appendix
   - Update pass rate if needed

4. **Update DOC_CHANGELOG.md**:
   - Add entry for November completion
   - List all files modified

**DO NOT** create `NOVEMBER_2025_COMPLETE.md` - this violates single source of truth.

### Known Issues / Accepted Exceptions

Track all accepted QC issues in COMPREHENSIVE_QC_VERIFICATION.md using this format:

```markdown
### [Date] - [Boat Name] ([Status])

**Issue**: Brief description
**Impact**: Percentage affected
**Decision**: Why accepted
**Tracked In**: QC file reference
```

Example:
```markdown
### August 7, 2025 - Dolphin Boat (✅ ACCEPTED)

**Issue**: Species count mismatches on 5 fields
**Impact**: 1 trip out of 7,958 total (0.013%)
**Decision**: Accepted as production-ready per stakeholder
**Tracked In**: qc_august_batch02_2025.json
```

### Pre-Commit Checklist

Before committing documentation changes:

- [ ] Verify changes follow documentation standards
- [ ] Update DOC_CHANGELOG.md
- [ ] Update README.md if needed
- [ ] Test all navigation links
- [ ] Confirm no duplicate information
- [ ] Verify single source of truth maintained

**See DOCUMENTATION_STANDARDS.md** for complete templates and guidelines.

---

**END OF GUIDE**

*For questions or issues not covered in this guide, refer to SPEC_006_SUMMARY.md or consult the full specification in `specs/006-scraper-accuracy-validation/`.*
