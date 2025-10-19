# Specification: 100% Accurate Scraping with Comprehensive QC

**Version**: 1.0.0
**Date**: October 16, 2025
**Status**: DRAFT
**Governed By**: constitution.md v1.0.0

---

## Executive Summary

### Problem Statement
Our fishing trip database contains incorrect data because:
1. **Wrong dates stored**: Dates are off by exactly the trip duration (2 Day trip shows 2 days too early)
2. **Unknown date semantics**: We don't know if boats.php?date represents departure, return, or report date
3. **No QC validation**: No automated way to verify scraped data matches source page 100%
4. **Silent failures**: Missing trips, incorrect fields go undetected

### Impact
- **User trust destroyed**: Data shown in dashboard doesn't match source website
- **Analytics invalid**: Any date-based analysis is wrong (moon phase correlations, etc.)
- **1,085 trips deleted**: Had to wipe Sept-Oct 2025 data (now at 7,475 trips from 8,560)

### Solution
1. **Investigate date semantics**: Test boats.php dates against charter boat pages to understand what they mean
2. **Fix parser logic**: Remove any date manipulation, store dates exactly as shown
3. **Build QC validation system**: Automated script that compares database against source for 100% match
4. **Re-scrape with validation**: Scrape Sept-Oct 2025 with QC validation after every date

---

## Functional Requirements

### FR-001: Date Semantics Investigation
**Priority**: CRITICAL (must complete before any scraping)

**Requirement**: Understand what `boats.php?date=YYYY-MM-DD` represents

**Investigation Test Cases**:

1. **Test boats.php against charter boat page**
   - Fetch polarissupreme.php (charter boat reports page)
   - Find trip dated "09-30-2025" (3 Day, 24 anglers)
   - Fetch boats.php?date=2025-09-30
   - Check if Polaris Supreme trip appears with same trip type and anglers
   - **Expected**: If dates match, then boats.php shows report/landing date

2. **Test multi-day trip date range**
   - boats.php?date=2025-10-10 shows "Polaris Supreme, 2 Day, 23 anglers"
   - Check boats.php?date=2025-10-08 (2 days earlier - potential departure)
   - Check boats.php?date=2025-10-09 (1 day earlier)
   - **Expected**: If trip only appears on 10-10, then date is report/landing date
   - **Expected**: If trip appears on multiple dates, need to understand the pattern

3. **Test half-day trip logic**
   - boats.php?date=2025-09-30 shows "Dolphin, 1/2 Day AM, 11 anglers"
   - **Expected**: 1/2 day trips should only appear once (same-day departure and return)

**Deliverable**: `date-semantics-report.md` documenting:
- What boats.php?date represents (departure, return, or report)
- How multi-day trips are shown (one date or multiple)
- Recommended database storage strategy
- Examples with screenshots/HTML snippets

**Acceptance Criteria**:
- ✅ All 3 test cases completed
- ✅ Clear conclusion documented
- ✅ User reviews and approves findings before proceeding

---

### FR-002: QC Validation Script
**Priority**: CRITICAL

**Requirement**: Build automated script that validates database matches source page 100%

**Script Capabilities**:

1. **Fetch source page**: GET boats.php?date=YYYY-MM-DD
2. **Parse all trips**: Extract every boat, trip type, anglers, species, counts
3. **Query database**: Get all trips for that date
4. **Field-level comparison**:
   - Landing name exact match
   - Boat name exact match
   - Trip type exact match
   - Anglers count exact match
   - Species names exact match (case-sensitive)
   - Catch counts exact match
5. **Report mismatches**: Any field that doesn't match 100%
6. **Report missing boats**: Boats on page but not in database
7. **Report extra boats**: Boats in database but not on page

**Output Format**:
```json
{
  "date": "2025-09-30",
  "status": "PASS" | "FAIL",
  "source_boat_count": 15,
  "database_boat_count": 15,
  "matches": 15,
  "mismatches": [],
  "missing_boats": [],
  "extra_boats": [],
  "field_errors": []
}
```

**Primary QC Test Case - Polaris Supreme Validation**:

**Test Setup**: Sequential scraping validation from 2025-09-09 to 2025-10-10 (32 consecutive dates)

**Expected Result**: Exactly 10 Polaris Supreme trips in database matching charter boat page

**Validation Steps**:
1. Scrape all boats.php pages from 2025-09-09 to 2025-10-10
2. Query database for Polaris Supreme trips in this date range
3. Compare against charter boat page (polarissupreme.php)

**Success Criteria**:
```python
# Primary validation test
polaris_trips = db.query(boat='Polaris Supreme', date_range='2025-09-09 to 2025-10-10')
assert len(polaris_trips) == 10, "Expected exactly 10 Polaris Supreme trips"

# Verify exact dates match charter boat page
expected_dates = [
    '2025-09-09',  # 2 Day, 14 anglers
    '2025-09-11',  # 2 Day, 17 anglers
    '2025-09-14',  # 3 Day, 24 anglers
    '2025-09-18',  # 4 Day, 10 anglers
    '2025-09-21',  # 3 Day, 22 anglers
    '2025-09-24',  # 3 Day, 24 anglers
    '2025-09-27',  # 3 Day, 18 anglers
    '2025-09-30',  # 3 Day, 24 anglers
    '2025-10-08',  # 5 Day, 22 anglers
    '2025-10-10',  # 2 Day, 23 anglers
]
assert set([t.trip_date for t in polaris_trips]) == set(expected_dates)
```

**What This Validates**:
- ✅ Sequential scraping works correctly (no skipped dates)
- ✅ No duplicate trips created (exactly 10, not 20)
- ✅ No missing trips (all 10 dates present)
- ✅ Dates stored exactly as shown on boats.php (no date manipulation)
- ✅ 100% accuracy against source of truth (charter boat page)

**Acceptance Criteria**:
- ✅ Script validates all fields for all boats on a page
- ✅ Polaris Supreme test case (10 trips) passes 100%
- ✅ Tested on 3 different dates with known good data
- ✅ 100% detection of field mismatches (no false negatives)
- ✅ Execution time < 10 seconds per date
- ✅ Clear, actionable error messages

---

### FR-003: Parser Date Logic Review
**Priority**: CRITICAL

**Requirement**: Ensure parser stores dates exactly as shown on source page

**Review Checklist**:
1. **No date manipulation**: Remove any code that calculates dates based on trip duration
2. **Store date parameter as-is**: `boats.php?date=2025-09-30` → `trip_date='2025-09-30'`
3. **No timezone conversions**: Store dates as simple YYYY-MM-DD strings
4. **Document any edge cases**: If any date logic exists, document why

**Code Changes**:
- **boats_scraper.py**: Review `parse_boats_page()` and trip insertion logic
- **socal_scraper.py**: Review date handling (if different from boats_scraper)
- **Spec 005 changes**: REVERT any date calculation logic added in Trip Date Correction project

**Acceptance Criteria**:
- ✅ No date subtraction or manipulation in parser code
- ✅ Tested on 3 dates, database dates match boats.php?date exactly
- ✅ QC validation script passes 100% on test dates

---

### FR-004: Landing Header Detection Validation
**Priority**: HIGH

**Requirement**: Verify parser detects all landing headers on boats.php pages

**Known Landings** (San Diego):
- Seaforth Sportfishing
- H&M Landing
- Fisherman's Landing
- Point Loma Sportfishing
- Oceanside Sea Center
- Helgren's Sportfishing
- (any others on test dates)

**Validation**:
1. Fetch boats.php for 3 different dates
2. Manually count landing headers on each page
3. Run parser and count detected landings
4. **Expected**: Parser count = manual count for all dates

**Acceptance Criteria**:
- ✅ All landings detected on test pages
- ✅ No false positives (landing names not on page)
- ✅ Case-insensitive and whitespace-tolerant matching

---

### FR-005: Species Parsing Validation
**Priority**: HIGH

**Requirement**: Verify species names and counts are parsed exactly as shown

**Test Cases**:
- "37 Bluefin Tuna" → species="Bluefin Tuna", count=37
- "44-62 LB Bluefin Tuna, 37" → species="Bluefin Tuna", count=37 (ignore weight)
- "126 Rockfish" → species="Rockfish", count=126
- "56 Spiny Lobster Released" → handle "Released" suffix correctly

**Edge Cases**:
- Multiple species on one line: "44 Bluefin Tuna, 4 Yellowfin Tuna"
- Weight ranges: "80-120 LB Yellowfin"
- Unknown species names (store as-is, don't standardize)

**Acceptance Criteria**:
- ✅ All species names stored exactly as shown (no normalization)
- ✅ All counts match source exactly
- ✅ Handles multi-species lines correctly
- ✅ QC validation passes on 10 random trips

---

### FR-006: Transactional Scraping
**Priority**: HIGH

**Requirement**: All trips from a date succeed or all fail (no partial inserts)

**Implementation**:
1. Parse all trips from boats.php?date
2. Validate all trips can be inserted (no constraint violations)
3. Begin database transaction
4. Insert all trips + catches
5. If any insert fails, rollback entire date
6. Commit only if all succeed

**Error Handling**:
- **Duplicate trip**: Skip with warning (not an error)
- **Parsing failure**: Fail entire date, log which boat failed
- **Database constraint violation**: Fail entire date, log error
- **Network error**: Retry 3 times, then fail date

**Acceptance Criteria**:
- ✅ Partial inserts impossible (all or nothing)
- ✅ Clear error messages when date fails
- ✅ Failed dates logged for retry
- ✅ Duplicate detection works correctly

---

### FR-007: Comprehensive Logging
**Priority**: MEDIUM

**Requirement**: Log every parsing step for debugging and audit trail

**Log Levels**:
- **INFO**: Date processing started/completed, boats found, trips inserted
- **WARNING**: Duplicate trips, unusual trip types, missing anglers
- **ERROR**: Parsing failures, database errors, validation failures
- **DEBUG**: HTML snippets, regex matches, field extraction

**Log Format**:
```
2025-10-16 18:30:15 | INFO  | Date 2025-09-30 | Found 15 boats across 5 landings
2025-10-16 18:30:16 | INFO  | Date 2025-09-30 | Seaforth Sportfishing | Parsed: Polaris Supreme (3 Day, 24 anglers, 3 species)
2025-10-16 18:30:17 | WARN  | Date 2025-09-30 | Polaris Supreme trip already exists, skipping
2025-10-16 18:30:18 | INFO  | Date 2025-09-30 | Inserted 14/15 trips (1 duplicate)
```

**Acceptance Criteria**:
- ✅ Every date has clear start/end log entries
- ✅ Every boat parsed is logged
- ✅ Errors include enough context to debug
- ✅ Log files rotated daily

---

### FR-008: Manual Spot Check Process
**Priority**: MEDIUM

**Requirement**: Human verification of sample trips to catch edge cases

**Process**:
1. After scraping batch of dates, randomly select 10 trips
2. For each trip, manually check source page
3. Verify all fields match (landing, boat, trip type, anglers, species, counts)
4. Document any discrepancies in spot check report
5. If > 1 discrepancy found, investigate and fix parser

**Spot Check Report Format**:
```markdown
## Spot Check Report - 2025-09-30

Trip 1: ✅ PASS
- Boat: Polaris Supreme
- Source: 3 Day, 24 anglers, 144 Bluefin
- Database: 3 Day, 24 anglers, 144 Bluefin

Trip 2: ❌ FAIL
- Boat: Liberty
- Source: 2 Day, 18 anglers, 44 Bluefin, 4 Yellowfin
- Database: 2 Day, 18 anglers, 44 Bluefin (MISSING 4 Yellowfin)
- Issue: Multi-species line parsing failed
```

**Acceptance Criteria**:
- ✅ Spot check completed for every 30 dates scraped
- ✅ 90%+ pass rate (9/10 or better)
- ✅ Any failures investigated and fixed
- ✅ Spot check report saved to validation folder

---

### FR-009: Backup and Rollback Capability
**Priority**: CRITICAL

**Requirement**: Ability to restore database to pre-scrape state if QC fails

**Backup Process**:
1. Before scraping, export all trips for date range being scraped
2. Save backup as JSON with metadata (timestamp, trip count, date range)
3. Verify backup file is valid and readable
4. Only proceed with scraping after backup confirmed

**Rollback Process**:
1. Delete all trips in scraped date range
2. Restore trips from backup JSON
3. Verify trip count matches backup metadata
4. Run QC validation on restored data
5. Only confirm rollback after QC passes

**Acceptance Criteria**:
- ✅ Backup created before any scraping
- ✅ Rollback tested on dev database
- ✅ Rollback completes in < 5 minutes for 1000 trips
- ✅ QC validation confirms restore success

---

### FR-010: Progressive Scraping with QC Gates
**Priority**: HIGH

**Requirement**: Validate data quality after every N dates to catch issues early

**Process**:
1. Scrape 5 dates
2. Run QC validation on all 5 dates
3. If QC passes, continue to next 5 dates
4. If QC fails, halt and investigate
5. Fix issue, rollback failed dates, re-scrape

**Benefits**:
- Catches parser issues after 5 dates (not 61)
- Limits damage from bad data
- Provides confidence to continue
- Generates validation metrics throughout scrape

**Acceptance Criteria**:
- ✅ QC runs automatically after every batch
- ✅ Scraper halts on first QC failure
- ✅ Clear report shows which date failed and why
- ✅ Can resume from last successful batch

---

## Non-Functional Requirements

### NFR-001: QC Performance
- QC validation completes in < 10 seconds per date
- Full 61-date validation completes in < 10 minutes
- Scraper + QC completes Sept-Oct 2025 in < 4 hours (with delays)

### NFR-002: Code Quality
- All QC code has docstrings and type hints
- Parser functions unit tested with known good HTML
- QC validation script has integration tests
- Code review before production use

### NFR-003: Documentation
- Clear README for QC validation script
- Step-by-step guide for running validation
- Troubleshooting guide for common QC failures
- Examples of validation reports (pass and fail)

---

## Implementation Plan

### Phase 1: Investigation (REQUIRED FIRST)
**Estimated Time**: 30 minutes

1. Run date semantics investigation (FR-001)
2. Document findings in `date-semantics-report.md`
3. Get user approval on findings
4. Determine correct date storage strategy

**Deliverables**:
- date-semantics-report.md
- User approval confirmation

---

### Phase 2: Build QC System
**Estimated Time**: 2 hours

1. Build QC validation script (FR-002)
2. Test on 3 known good dates
3. Verify 100% field-level matching
4. Document QC script usage

**Deliverables**:
- qc_validator.py (comprehensive validation script)
- qc_validator_README.md (usage guide)
- Test validation reports (3 dates)

---

### Phase 3: Fix Parser Logic
**Estimated Time**: 1 hour

1. Review and fix parser date logic (FR-003)
2. Validate landing header detection (FR-004)
3. Test species parsing (FR-005)
4. Run QC on 3 test dates to confirm fixes

**Deliverables**:
- Updated boats_scraper.py
- Test results showing 100% QC pass on 3 dates
- Code diff showing changes made

---

### Phase 4: Production Scraping
**Estimated Time**: 3-4 hours

1. Create backup (FR-009)
2. Scrape Sept-Oct 2025 in batches of 5 dates (FR-010)
3. Run QC after each batch (FR-002)
4. Halt on first failure, investigate, fix, resume
5. Complete manual spot checks (FR-008)

**Deliverables**:
- Backup file (sept_oct_2025_backup.json)
- QC validation reports for all 61 dates
- Spot check reports (every 30 dates)
- Final completion summary

---

### Phase 5: Final Validation
**Estimated Time**: 30 minutes

1. Run comprehensive QC across all scraped dates
2. Generate final validation report
3. Verify zero QC failures
4. Provide user-facing data quality summary

**Deliverables**:
- final-validation-report.md
- Data quality metrics (% accuracy, pass rate, etc.)
- Confirmation database ready for production use

---

## Success Criteria

### Data Quality (100% Required)
1. ✅ QC validation passes 100% for all scraped dates
2. ✅ Zero field-level mismatches detected
3. ✅ Zero missing boats detected
4. ✅ Zero extra boats detected
5. ✅ Manual spot checks 90%+ pass rate

### Process Quality (100% Required)
1. ✅ Date semantics investigation completed and approved
2. ✅ QC validation script tested and working
3. ✅ Parser logic reviewed and fixed
4. ✅ Backup created and verified
5. ✅ Rollback capability tested

### Deliverables (100% Required)
1. ✅ date-semantics-report.md
2. ✅ qc_validator.py with README
3. ✅ Updated boats_scraper.py
4. ✅ QC validation reports for all dates
5. ✅ final-validation-report.md

---

## Risk Mitigation

### Risk: Date semantics investigation reveals complex logic
**Mitigation**: Document complexity, implement carefully, test thoroughly

### Risk: QC validation finds 100% mismatch rate
**Mitigation**: Test QC script on known good data first, verify logic is correct

### Risk: Parser changes break existing functionality
**Mitigation**: Test on historical dates first, compare before/after results

### Risk: Source page structure changes mid-scrape
**Mitigation**: QC catches this immediately, halt and investigate

---

## Acceptance Testing

Before considering this spec complete:

1. ✅ Date semantics investigation passed user review
2. ✅ QC validator tested on 3 dates with 100% pass rate
3. ✅ Parser tested on 3 dates with QC validation
4. ✅ Backup/rollback tested successfully
5. ✅ Full scraping workflow tested on 10-date subset

---

## Sign-Off

**Specification Author**: Claude Code
**Date**: October 16, 2025
**Version**: 1.0.0
**Status**: DRAFT - Pending User Approval

**User Approval**: _________________ (Date: _________)

Once approved, this specification defines the complete scope of work for achieving 100% accurate scraping with comprehensive QC validation.
