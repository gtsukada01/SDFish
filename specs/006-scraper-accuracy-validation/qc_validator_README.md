# QC Validator - Usage Guide

**Version**: 1.0.0
**Date**: October 16, 2025
**Purpose**: 100% Data Accuracy Verification for Fishing Trip Database

---

## Overview

The QC Validator verifies that the database perfectly matches the source website (`boats.php` pages) with **zero tolerance** for mismatches.

### What It Validates

✅ **Field-level accuracy** (landing, boat, trip type, anglers, species, counts)
✅ **No missing boats** (all boats on source page are in database)
✅ **No extra boats** (no database boats missing from source page)
✅ **Polaris Supreme test** (10 trips from 09-09 to 10-10 match charter boat page)

---

## Installation

The QC validator uses the same dependencies as the scraper:

```bash
cd /Users/btsukada/Desktop/Fishing/fish-scraper
pip3 install requests beautifulsoup4 lxml supabase colorama
```

Make the script executable:

```bash
chmod +x qc_validator.py
```

---

## Usage Examples

### 1. Validate Single Date

```bash
python3 qc_validator.py --date 2025-09-30
```

**Output**:
```
================================================================================
🔍 QC VALIDATION: 2025-09-30
================================================================================
🌐 Fetching: https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-09-30
✅ Fetched 45231 bytes
📊 Source page: 15 trips
📊 Database: 15 trips
✅ Match: Polaris Supreme
✅ Match: Liberty
... (all boats)
================================================================================
✅ QC PASSED: 2025-09-30
📊 Matches: 15/15
⚠️  Mismatches: 0
⚠️  Missing boats: 0
⚠️  Extra boats: 0
================================================================================
```

### 2. Validate Date Range

```bash
python3 qc_validator.py --start-date 2025-09-01 --end-date 2025-09-30 --output sept_2025_qc.json
```

Validates all 30 dates in September and saves detailed JSON report.

### 3. Run Polaris Supreme Test

```bash
python3 qc_validator.py --polaris-test --output polaris_test_report.json
```

**Expected Result**: PASS (10 trips, correct dates)

```
================================================================================
🎯 POLARIS SUPREME VALIDATION TEST
================================================================================
📊 Expected: 10 trips
📊 Database: 10 trips
✅ Trip count: PASS (10 trips)
✅ Trip dates: PASS (all dates match)
================================================================================
✅ POLARIS SUPREME TEST: PASSED
================================================================================
```

---

## QC Report Format

### Single Date Report (JSON)

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
  "field_errors": [],
  "timestamp": "2025-10-16T19:30:45.123456"
}
```

### Failed Date Report (with errors)

```json
{
  "date": "2025-09-15",
  "status": "FAIL",
  "source_boat_count": 12,
  "database_boat_count": 11,
  "matches": 10,
  "mismatches": [
    {
      "boat": "Liberty",
      "errors": [
        "Species count mismatch: 'bluefin tuna' source=44 db=40",
        "Missing species: 'yellowfin tuna' (count=4) not in database"
      ]
    }
  ],
  "missing_boats": [
    {
      "boat": "Polaris Supreme",
      "landing": "Seaforth Sportfishing",
      "trip_type": "3 Day",
      "anglers": 22
    }
  ],
  "extra_boats": [],
  "field_errors": [
    "Species count mismatch: 'bluefin tuna' source=44 db=40",
    "Missing species: 'yellowfin tuna' (count=4) not in database"
  ],
  "timestamp": "2025-10-16T19:35:12.654321"
}
```

### Polaris Supreme Test Report

```json
{
  "test": "Polaris Supreme Validation",
  "status": "PASS",
  "expected_trips": 10,
  "actual_trips": 10,
  "expected_dates": [
    "2025-09-09",
    "2025-09-11",
    "2025-09-14",
    "2025-09-18",
    "2025-09-21",
    "2025-09-24",
    "2025-09-27",
    "2025-09-30",
    "2025-10-08",
    "2025-10-10"
  ],
  "actual_dates": [
    "2025-09-09",
    "2025-09-11",
    "2025-09-14",
    "2025-09-18",
    "2025-09-21",
    "2025-09-24",
    "2025-09-27",
    "2025-09-30",
    "2025-10-08",
    "2025-10-10"
  ],
  "missing_dates": [],
  "extra_dates": [],
  "timestamp": "2025-10-16T19:40:00.123456"
}
```

---

## Validation Workflow

### Pre-Scraping Validation

**Before scraping new dates**, run QC on existing good data to verify the validator works:

```bash
# Test on 3 known good dates (from 2024 data)
python3 qc_validator.py --date 2024-10-15
python3 qc_validator.py --date 2024-09-20
python3 qc_validator.py --date 2024-08-10
```

**Expected**: All should PASS (if 2024 data is good)

### Post-Scraping Validation

**After scraping**, validate immediately:

```bash
# Validate newly scraped dates
python3 qc_validator.py --start-date 2025-09-01 --end-date 2025-09-05 --output batch1_qc.json
```

**If PASS**: Continue to next batch
**If FAIL**: Halt, investigate, fix, rollback, re-scrape

### Progressive Validation (Recommended)

Scrape in batches of 5 dates, then validate:

```bash
# Batch 1: Scrape Sept 1-5
python3 boats_scraper.py --start-date 2025-09-01 --end-date 2025-09-05

# Validate Batch 1
python3 qc_validator.py --start-date 2025-09-01 --end-date 2025-09-05

# If PASS, continue to Batch 2
python3 boats_scraper.py --start-date 2025-09-06 --end-date 2025-09-10
python3 qc_validator.py --start-date 2025-09-06 --end-date 2025-09-10

# ... repeat
```

---

## Interpreting Results

### PASS Status ✅

```
status: "PASS"
matches: 15
mismatches: []
missing_boats: []
extra_boats: []
```

**Meaning**: 100% accuracy confirmed. Database matches source page perfectly.

**Action**: No action needed. Safe to continue.

---

### FAIL Status - Mismatch ❌

```
status: "FAIL"
mismatches: [
  {
    "boat": "Liberty",
    "errors": ["Anglers mismatch: source=18 db=17"]
  }
]
```

**Meaning**: Database has wrong data for this trip.

**Action**:
1. Check source page manually: `boats.php?date=2025-09-30`
2. Check database query: `SELECT * FROM trips WHERE boat_id=... AND trip_date='2025-09-30'`
3. Investigate parsing logic in `boats_scraper.py`
4. Fix parser if needed
5. Delete bad data, re-scrape

---

### FAIL Status - Missing Boat ❌

```
status: "FAIL"
missing_boats: [
  {
    "boat": "Polaris Supreme",
    "landing": "Seaforth Sportfishing",
    "trip_type": "3 Day",
    "anglers": 22
  }
]
```

**Meaning**: Boat is on source page but NOT in database.

**Action**:
1. Check if scraper ran for this date
2. Check scraper logs for parsing errors
3. Investigate landing header detection (Seaforth fix applied?)
4. Re-scrape this date

---

### FAIL Status - Extra Boat ❌

```
status: "FAIL"
extra_boats: [
  {
    "boat": "Mystery Boat",
    "landing": "Unknown Landing",
    "trip_date": "2025-09-30"
  }
]
```

**Meaning**: Database has a trip that's NOT on source page.

**Action**:
1. Check source page manually
2. Check if date is wrong in database
3. Likely a scraping bug - delete and re-scrape

---

## Troubleshooting

### "Supabase connection failed"

**Fix**: Check internet connection and Supabase credentials in script.

### "Failed to fetch source page"

**Fix**:
- Check internet connection
- Check if sandiegofishreports.com is accessible
- Try again in a few seconds (temporary network issue)

### "Species count mismatch" (off by 1-2)

**Cause**: Parsing regex might be splitting multi-species lines incorrectly.

**Fix**: Review `parse_species_counts()` function in boats_scraper.py

### Polaris Supreme test shows only 8 trips instead of 10

**Cause**: 2 trips missing from database (parsing failed or scraper didn't run for those dates)

**Fix**:
- Check which dates are missing from `missing_dates` field
- Re-scrape those specific dates
- Run Polaris test again

---

## Performance

- **Single date**: ~5-10 seconds (fetch + parse + DB query)
- **30 dates**: ~3-5 minutes (with 2-second delays)
- **61 dates** (Sept-Oct): ~6-10 minutes

---

## Integration with Scraping Workflow

### Complete Workflow (Phase 4)

```bash
# 1. Backup existing data
python3 -c "from boats_scraper import init_supabase; ..."  # Backup script

# 2. Scrape Batch 1 (Sept 1-5)
python3 boats_scraper.py --start-date 2025-09-01 --end-date 2025-09-05

# 3. QC Validate Batch 1
python3 qc_validator.py --start-date 2025-09-01 --end-date 2025-09-05 --output qc_batch1.json

# 4. Check QC results
cat qc_batch1.json | jq '.summary.passed'  # Should be 5

# 5. If PASS, continue to Batch 2
# 6. If FAIL, investigate, fix, rollback, re-scrape

# ... repeat for all batches

# Final: Run Polaris Supreme test
python3 qc_validator.py --polaris-test --output polaris_final_test.json
```

---

## Success Criteria

**QC validation is successful when**:
- ✅ All dates return `status: "PASS"`
- ✅ Zero mismatches detected
- ✅ Zero missing boats detected
- ✅ Zero extra boats detected
- ✅ Polaris Supreme test returns `status: "PASS"`

**At that point**: Database is confirmed 100% accurate and ready for production use.

---

## Log Files

- **qc_validator.log**: Detailed execution log (same format as boats_scraper.log)
- **JSON reports**: Structured validation results for automation/analysis

---

## Next Steps

After QC validation passes:
1. Generate final validation report
2. Document data quality metrics
3. Confirm database ready for production
4. Update CLAUDE.md with new trip counts

---

**Questions or issues?** Check the spec: `specs/006-scraper-accuracy-validation/spec.md`
