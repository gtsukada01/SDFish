# Implementation Plan: Southern California Regional Expansion

**Branch**: `004-socal-regional-expansion` | **Date**: 2025-10-16 | **Spec**: specs/004-socal-regional-expansion/spec.md

## Summary

Expand the Fishing Intelligence Platform from San Diego-only coverage to **full Southern California coastal coverage** by switching the data source from sandiegofishreports.com to socalfishreports.com. This adds **5 new landing regions** (Avila Beach, Santa Barbara, Oxnard, Marina Del Rey, Newport Beach) with an estimated **150-300 new trips** and **10-15 new boats**, while preserving all existing San Diego data integrity.

## Technical Context

**Language/Version**: Python 3.8+ with existing dependencies
**Primary Tools**: boats_scraper.py (validated scraper v3.0), BeautifulSoup4, Supabase client
**Data Source**: socalfishreports.com (identical structure to sandiegofishreports.com)
**Database**: Supabase PostgreSQL with normalized schema (landings → boats → trips → catches)
**Testing**: Dry run validation, database queries, dashboard visual verification
**Target Platform**: Backend scraper (CLI) + Frontend dashboard (React 18 + shadcn/ui)
**Performance Goals**: Complete 30-day historical backfill in < 3 hours, maintain 2-5 second delays
**Constraints**: Preserve existing 8,000+ San Diego trips, no duplicate detection across sources, ethical scraping standards
**Scale/Scope**: Add 5 landings, 10-15 boats, 150-300 trips, 500-1500 catches (30-day initial backfill)

## Constitution Check

**Data Fidelity First**: ✅
- Scraper preserves exact species names from source (no normalization)
- Boat names and landing names stored as-is from HTML
- Catch counts validated as positive integers before insertion
- Regional naming variations logged for manual review (not auto-corrected)

**Spec-Led Delivery**: ✅
- spec.md defines WHAT (5 new regions, data integrity requirements)
- plan.md defines HOW (URL change, validation approach, phased execution)
- tasks.md will enumerate concrete steps with dependencies
- All changes validated through dry run before production

**Observable Resilience**: ✅
- Pre-scraping validation report captures baseline state
- Post-scraping validation report shows all insertions/skips
- Comprehensive logging with color-coded console output
- Rollback scripts documented for data removal if needed

**Responsive Clarity**: ✅
- Dashboard updates automatically show new landing filter options
- React components support regional filtering (existing architecture)
- shadcn/ui Select components scale to accommodate new regions
- Mobile-responsive design already tested (no changes needed)

**Fast Progressive UX**: ✅
- Scraper processes dates progressively with 2-5 second delays
- Database insertions atomic per-trip (existing pattern)
- Dashboard real-time filtering via Supabase queries
- No frontend performance impact (same query patterns)

**Constitution Gate Status**: ✅ PASS (no violations identified; phased execution ensures safety)

## Project Structure

### Specification Files (this feature)
```
specs/004-socal-regional-expansion/
├── spec.md              # Stakeholder specification (COMPLETE)
├── plan.md              # This file (technical approach)
├── research.md          # Phase 0 findings (optional)
├── tasks.md             # Executable task list (Phase 2)
├── landing.md           # Progress log with RESET timestamps (Phase 3+)
└── validation/          # Validation scripts and reports
    ├── pre-scrape-report.txt
    ├── post-scrape-report.txt
    └── species-variations.txt
```

### Existing Scraper Files (to be modified)
```
fish-scraper/
├── boats_scraper.py           # MODIFY: Change BASE_URL (line 46)
├── check_scraper_status.py    # USE: Pre-scraping validation
├── validate_data.py           # USE: Post-scraping validation
├── requirements.txt           # NO CHANGE: Dependencies already installed
└── SCRAPER_DOCS.md            # UPDATE: Document regional expansion
```

### Frontend Files (auto-updates via database)
```
fishing-dashboard/
├── src/lib/fetchRealData.ts   # AUTO: Fetches new landings from database
├── src/components/HeaderFilters.tsx  # AUTO: Populates landing dropdown
├── src/App.tsx                # NO CHANGE: Existing filter logic works
└── README.md                  # UPDATE: Document regional coverage
```

**Structure Decision**: Minimal code changes (1 line in scraper), maximum validation (3 validation reports). Frontend updates automatically via database-driven queries.

## Phase 0: Pre-Flight Validation

### Objectives
1. Verify socalfishreports.com structure matches expectations
2. Confirm all 5 expected landings present in source data
3. Validate existing scraper logic compatibility
4. Generate baseline database state report

### Validation Steps

**1. Source Structure Inspection**
```bash
# Fetch sample page and inspect HTML
curl "https://www.socalfishreports.com/dock_totals/boats.php?date=2025-10-13" > /tmp/socal_sample.html

# Verify "Fish Counts" pattern present
grep -c "Fish Counts" /tmp/socal_sample.html
# Expected: 5+ (one per landing)

# Extract landing names
grep "Fish Counts" /tmp/socal_sample.html | sed 's/ Fish Counts.*//'
# Expected: Patriot Sportfishing, Santa Barbara Landing, Channel Islands Sportfishing,
#           Marina Del Rey Sportfishing, Newport Landing
```

**2. Parser Compatibility Test**
```python
# Test boats_scraper.py parse_boats_page() with SoCal HTML
from boats_scraper import parse_boats_page
html = open('/tmp/socal_sample.html').read()
trips = parse_boats_page(html, '2025-10-13')
print(f"Parsed {len(trips)} trips")
print(f"Landings found: {set(t['landing_name'] for t in trips)}")
# Expected: 5 landings, 10-15 trips
```

**3. Baseline Database State**
```python
# Run check_scraper_status.py
python3 check_scraper_status.py > specs/004-socal-regional-expansion/validation/pre-scrape-report.txt

# Expected output:
# - Landings: 4-7 (San Diego landings)
# - Boats: 70-80 (San Diego boats)
# - Trips: 8,000+ (San Diego trips)
# - Latest date: 2025-10-15 or later
```

**Decision Point**: Proceed to Phase 1 only if:
- ✅ All 5 expected landings found in source HTML
- ✅ Parser extracts trips without errors
- ✅ Baseline report shows stable database state

**Output**: `research.md` (if any structural differences found), validation reports in `validation/` folder

## Phase 1: Configuration & Validation Scripts

*Prerequisite: Phase 0 validation passed*

### Objectives
1. Update scraper configuration to use SoCal source
2. Create validation scripts for new regional data
3. Prepare rollback scripts for safe execution
4. Document expected database changes

### Implementation Tasks

**1. Update Scraper Configuration**
```python
# boats_scraper.py (line 46)
# BEFORE:
BASE_URL = "https://www.sandiegofishreports.com"

# AFTER:
BASE_URL = "https://www.socalfishreports.com"
```

**2. Create Validation Script**
```python
# specs/004-socal-regional-expansion/validation/validate_regional_expansion.py
"""
Validate regional expansion data quality
- Checks: Landing names match expected (5 new)
- Checks: Boat-landing associations correct
- Checks: No San Diego data corruption
- Checks: Species variations logged
"""
```

**3. Create Rollback Script**
```python
# specs/004-socal-regional-expansion/validation/rollback_expansion.py
"""
Rollback regional expansion if validation fails
- Exports new trips to JSON backup
- Deletes catches for new trips
- Deletes new trips
- Deletes new boats
- Deletes new landings
- Validates database restored to baseline
"""
```

**4. Create Expected Landing List**
```python
# specs/004-socal-regional-expansion/validation/expected_landings.py
EXPECTED_NEW_LANDINGS = [
    "Patriot Sportfishing",
    "Santa Barbara Landing",
    "Channel Islands Sportfishing",
    "Marina Del Rey Sportfishing",
    "Newport Landing"
]

EXPECTED_SAN_DIEGO_LANDINGS = [
    "Seaforth Sportfishing",
    "H&M Landing",
    "Fisherman's Landing",
    "Point Loma Sportfishing"
]
```

**Output**: Modified boats_scraper.py, 3 validation scripts, expected data definitions

## Phase 2: Dry Run Testing

*Prerequisite: Phase 1 configuration complete*

### Objectives
1. Test scraper with new source on single day
2. Validate parsing logic extracts all expected data
3. Verify no errors or warnings in logs
4. Confirm data quality before production run

### Testing Sequence

**Test 1: Single Day Dry Run**
```bash
# Dry run for October 13, 2025 (known good data from Phase 0)
python3 boats_scraper.py \
  --start-date 2025-10-13 \
  --end-date 2025-10-13 \
  --dry-run

# Expected output in logs:
# - "Processing: Patriot Sportfishing" ✅
# - "Processing: Santa Barbara Landing" ✅
# - "Processing: Channel Islands Sportfishing" ✅
# - "Processing: Marina Del Rey Sportfishing" ✅
# - "Processing: Newport Landing" ✅
# - "Found boat: Aloha Spirit" (Channel Islands)
# - "Found boat: Betty-O" (Marina Del Rey)
# - "Found boat: Aggressor" (Newport Beach)
# - "DRY RUN - Would insert X trips" (10-15 trips estimated)
```

**Test 2: Multi-Day Dry Run**
```bash
# Test 3-day range to validate date iteration
python3 boats_scraper.py \
  --start-date 2025-10-13 \
  --end-date 2025-10-15 \
  --dry-run

# Verify:
# - All 3 dates processed
# - Delay timing correct (2-5 seconds between dates)
# - No parsing errors across multiple days
```

**Test 3: Log Analysis**
```bash
# Check for any warnings or errors
grep "ERROR" boats_scraper.log
grep "WARNING" boats_scraper.log

# Expected: Clean (or only expected warnings like duplicate trips)
```

**Decision Point**: Proceed to Phase 3 only if:
- ✅ All 5 landings detected in dry run
- ✅ 10-15 trips parsed per day (reasonable)
- ✅ No ERROR messages in logs
- ✅ Species parsing successful (all catches have counts > 0)

**Output**: boats_scraper.log with dry run results, validation that parser works with new source

## Phase 3: Production Execution (30-Day Backfill)

*Prerequisite: Phase 2 dry run passed*

### Objectives
1. Execute production scrape for last 30 days
2. Populate database with new regional data
3. Monitor progress with real-time logging
4. Generate post-scraping validation report

### Execution Plan

**Step 1: Determine Date Range**
```python
# Calculate 30 days back from today
from datetime import datetime, timedelta
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)
print(f"Scrape range: {start_date} to {end_date}")
```

**Step 2: Production Scrape**
```bash
# Execute 30-day backfill (estimated 2-3 hours with delays)
python3 boats_scraper.py \
  --start-date 2025-09-16 \
  --end-date 2025-10-16

# Monitor progress:
# - Watch console output for colored status messages
# - Check boats_scraper.log for detailed logging
# - Expect ~5-10 minutes per date (delays + parsing)
```

**Step 3: Real-Time Monitoring**
```bash
# In separate terminal, watch log file
tail -f boats_scraper.log | grep -E "(Processing:|✅ Inserted:|⚠️  Duplicate:)"

# In another terminal, check database growth
watch -n 60 'python3 -c "from boats_scraper import init_supabase; s = init_supabase(); print(\"Landings:\", s.table(\"landings\").select(\"count\").execute().data[0][\"count\"], \"Boats:\", s.table(\"boats\").select(\"count\").execute().data[0][\"count\"], \"Trips:\", s.table(\"trips\").select(\"count\").execute().data[0][\"count\"])"'
```

**Step 4: Completion Verification**
```bash
# Generate post-scraping report
python3 specs/004-socal-regional-expansion/validation/validate_regional_expansion.py \
  > specs/004-socal-regional-expansion/validation/post-scrape-report.txt

# Expected report contents:
# - New landings: 5 (names listed)
# - New boats: 10-15 (names + landing associations)
# - New trips: 150-300 (breakdown by landing)
# - Skipped trips: X duplicates (if any)
# - Species variations: List of unique species names
# - San Diego data integrity: PASSED (8,000+ trips unchanged)
```

**Output**:
- Populated database with new regional data
- `post-scrape-report.txt` with complete validation
- `species-variations.txt` with regional species differences
- Updated `landing.md` with RESET timestamp

## Phase 4: Dashboard Validation

*Prerequisite: Phase 3 production execution complete*

### Objectives
1. Verify dashboard displays new landing options
2. Test filtering by new regions
3. Validate trip data displays correctly
4. Confirm metrics aggregate properly

### Validation Steps

**Step 1: Start Dashboard**
```bash
cd fishing-dashboard
npm start
# → http://localhost:8081
```

**Step 2: Visual Verification Checklist**
- [ ] Landing filter dropdown shows 9+ options (4 San Diego + 5 new)
- [ ] Selecting "Channel Islands Sportfishing" shows offshore trips
- [ ] Boat names match new regions (e.g., "Aloha Spirit" for Channel Islands)
- [ ] Species shown reflect regional patterns (different from San Diego)
- [ ] Trip durations include multi-day trips (Channel Islands 2-3 day trips)
- [ ] Summary metrics update correctly when filtering by new regions
- [ ] No console errors in browser DevTools

**Step 3: Data Accuracy Spot Check**
```bash
# Query database for specific trip to verify dashboard accuracy
python3 -c "
from boats_scraper import init_supabase
s = init_supabase()

# Get a Channel Islands trip
result = s.table('trips') \
  .select('*, boats(name, landings(name)), catches(species, count)') \
  .eq('boats.landings.name', 'Channel Islands Sportfishing') \
  .limit(1) \
  .execute()

print('Database trip:', result.data[0])
"

# Compare with dashboard display for same trip
```

**Step 4: Filter Performance Test**
- Change landing filter 5 times → all load < 2s
- Change boat filter 5 times → all load < 2s
- Apply date range filter → loads < 2s
- Reset all filters → loads < 2s

**Decision Point**: Mark complete if:
- ✅ All 5 new landings appear in filter dropdown
- ✅ Filtering shows correct boats/trips for each landing
- ✅ Data accuracy matches database queries
- ✅ No performance degradation (< 2s filter response)

**Output**: Dashboard validation report in `landing.md`, screenshots (optional)

## Phase 5: Documentation Updates

*Prerequisite: Phase 4 dashboard validation passed*

### Objectives
1. Update scraper documentation with regional coverage
2. Update dashboard README with new features
3. Document data quality findings
4. Create maintenance guide for ongoing scraping

### Documentation Tasks

**1. Update SCRAPER_DOCS.md**
```markdown
## Data Source

**Primary Source**: https://www.socalfishreports.com
**Coverage**: Full Southern California coast (Avila Beach to Newport Beach)

### Supported Landings (9 total)

**San Diego Region** (Legacy):
- Seaforth Sportfishing
- H&M Landing
- Fisherman's Landing
- Point Loma Sportfishing

**New Regions** (Added Oct 2025):
- Patriot Sportfishing (Avila Beach)
- Santa Barbara Landing (Santa Barbara)
- Channel Islands Sportfishing (Oxnard)
- Marina Del Rey Sportfishing (Marina Del Rey)
- Newport Landing (Newport Beach)
```

**2. Update fishing-dashboard/README.md**
```markdown
## Features

- ✅ **Regional Coverage**: Avila Beach to Newport Beach (200+ mile coastline)
- ✅ **9 Major Landings**: Complete Southern California sportfishing data
- ✅ **Real-Time Filtering**: Filter by landing, boat, species, trip duration
- ✅ **10,000+ Trips**: Historical and current catch data
```

**3. Create Maintenance Guide**
```markdown
# specs/004-socal-regional-expansion/MAINTENANCE.md

## Weekly Scraping

```bash
# Update database with latest week
python3 boats_scraper.py --start-date $(date -v-7d +%Y-%m-%d)
```

## Monthly Validation

```bash
# Check for new landings or boats
python3 specs/004-socal-regional-expansion/validation/validate_regional_expansion.py
```

## Species Name Standardization (Future)

Track species variations in `species-variations.txt`, plan standardization project when variations > 50
```

**4. Update landing.md**
```markdown
# Landing Log: Southern California Regional Expansion

## RESET 2025-10-16T12:00:00-07:00 - Regional Expansion Complete

### Phase 5 Complete: Documentation Updated

**Summary**:
- 5 new landing regions added successfully
- 15 new boats created and associated
- 287 new trips inserted (30-day backfill)
- 943 new catches recorded
- Dashboard validated and operational
- Documentation updated

**Validation Results**: ✅ ALL CHECKS PASSED
```

**Output**: Updated documentation across 4 files, maintenance guide for future operations

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|------------|------------|-------------------------------------|
| URL change from sandiegofishreports.com to socalfishreports.com | Expands coverage to 5 new regions with 10+ new boats | Could scrape both sources separately, but socalfishreports.com includes all San Diego data plus new regions, consolidating to single source is cleaner |
| 30-day backfill (150-300 trips) | Provides immediate historical context for new regions | Could start with just 1 week, but users expect comparable historical data across all regions for trend analysis |
| Validation script for regional data quality | Ensures boat-landing associations correct across 5 new regions | Could manually spot-check, but automated validation prevents systematic errors (e.g., wrong landing assignments) |

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Pre-flight validation (URL test, parser compatibility)
- [ ] Phase 1: Configuration & validation scripts
- [ ] Phase 2: Dry run testing (1-day, 3-day)
- [ ] Phase 3: Production execution (30-day backfill)
- [ ] Phase 4: Dashboard validation
- [ ] Phase 5: Documentation updates

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [ ] Phase 0 Validation: Pending
- [ ] Phase 2 Dry Run: Pending
- [ ] Phase 3 Production: Pending
- [ ] Phase 4 Dashboard: Pending
- [ ] All NEEDS CLARIFICATION resolved: N/A (none in spec)

---

*Based on Constitution v1.0.0 – See `CLAUDE.md` for full requirements*
