# Specification: Trip Date Correction Project

**Version**: 1.0.0
**Date**: October 16, 2025
**Status**: DRAFT
**Governed By**: constitution.md v1.0.0

---

## Executive Summary

### Problem Statement
The fishing trip database stores **return/report dates** instead of **departure dates** in the `trip_date` field, causing:
- Multi-day trips to show incorrect dates (3-day trip on 09-21 shows as 09-24)
- Dashboard date filters to exclude trips incorrectly
- User confusion ("I went fishing on the 21st" but dashboard shows the 24th)
- Misalignment with source website (sandiegofishreports.com uses departure dates)

### Impact
- **8,523 trips affected**: All San Diego (8,021) + SoCal (502) trips
- **Data accuracy**: 0% for multi-day trips, 100% for 1/2 day trips
- **User experience**: Dashboard date filters produce unexpected results
- **Analytics**: Moon phase correlations use wrong dates for multi-day trips

### Solution
1. **Database Migration**: Correct all 8,523 trip dates to use departure dates
2. **Frontend Fix**: Fix timezone display bug (10-10 showing as 10-09)
3. **Scraper Updates**: Update both scrapers to use departure date logic
4. **Re-scrape Missing**: Capture missing Sep 21, Sep 18 Polaris Supreme trips

---

## Functional Requirements

### FR-001: Date Calculation Logic
**Priority**: CRITICAL
**Requirement**: Implement function to calculate departure date from report date and trip duration

**Logic**:
```python
departure_date = report_date - trip_duration_days

# Examples:
# Report: 2025-10-10, Duration: "2 Day"     → Departure: 2025-10-08
# Report: 2025-10-08, Duration: "5 Day"     → Departure: 2025-10-03
# Report: 2025-10-10, Duration: "1/2 Day"   → Departure: 2025-10-10 (same day)
# Report: 2025-10-10, Duration: "Overnight" → Departure: 2025-10-09
```

**Edge Cases**:
- `1/2 Day AM/PM`: Same-day trips (0 days subtracted)
- `Overnight`: 1 day subtracted
- `Full Day`: 0 days subtracted (same-day trip)
- `1.5 Day`, `2.5 Day`: Round to nearest whole number

**Acceptance Criteria**:
- ✅ All trip duration patterns correctly parsed
- ✅ Edge cases handled (1/2 day, overnight, decimals)
- ✅ Unit tests pass 100% (10/10 test cases)

---

### FR-002: Database Backup
**Priority**: CRITICAL
**Requirement**: Create complete backup before ANY changes

**Backup Contents**:
- All trips (id, boat_id, trip_date, trip_duration, anglers)
- All catches (trip_id, species, count)
- Metadata (timestamp, trip_count, catch_count, date_range)

**Validation**:
- Backup file size matches expected (JSON ~5-10MB)
- Trip count in backup equals database count
- Catch count in backup equals database count
- Date range spans full coverage (earliest to latest trip)

**Acceptance Criteria**:
- ✅ Backup created successfully
- ✅ Backup validated (counts match database)
- ✅ Backup file accessible and readable
- ✅ Restore procedure tested on dev database

---

### FR-003: Migration Script - Dry Run Mode
**Priority**: CRITICAL
**Requirement**: Migration script MUST support dry-run mode

**Dry-Run Behavior**:
- Calculate all date changes
- Log proposed changes (boat, old_date, new_date, trip_duration)
- Validate calculations against spot-checks
- NO database writes
- Generate dry-run report

**Output Example**:
```
DRY RUN MODE - No changes will be made

Polaris Supreme (Boat ID: 80):
  2025-10-10 → 2025-10-08 (2 Day trip)
  2025-10-08 → 2025-10-03 (5 Day trip)
  2025-09-30 → 2025-09-27 (3 Day trip)

Total trips to update: 8,523
Total trips unchanged: 0 (all trips affected)
```

**Acceptance Criteria**:
- ✅ Dry-run produces detailed change log
- ✅ No database writes occur in dry-run mode
- ✅ Spot-check validation: 10/10 calculations correct
- ✅ Edge cases logged correctly (1/2 day trips unchanged)

---

### FR-004: Migration Script - Production Mode
**Priority**: CRITICAL
**Requirement**: Update all trip dates in database

**Execution**:
1. Verify backup exists and is valid
2. Begin transaction (rollback on any error)
3. For each trip:
   - Calculate new departure date
   - Update trip_date field
   - Log change (trip_id, old_date, new_date)
4. Commit transaction
5. Generate post-migration report

**Safety Checks**:
- Verify trip count unchanged (before: 8,523 → after: 8,523)
- Verify catch count unchanged
- Verify no NULL trip_dates created
- Verify all dates within valid range (2024-01-01 to 2025-12-31)

**Acceptance Criteria**:
- ✅ All 8,523 trips updated successfully
- ✅ Zero data loss (trip/catch counts unchanged)
- ✅ Transaction safety (all-or-nothing update)
- ✅ Comprehensive audit log generated

---

### FR-005: Frontend Timezone Fix
**Priority**: HIGH
**Requirement**: Fix dashboard date display showing dates 1 day earlier

**Current Bug**:
- Database: `2025-10-10`
- Dashboard displays: `10/9/2025` ❌

**Root Cause**: JavaScript Date object timezone conversion

**Fix**:
```typescript
// WRONG (current):
new Date(trip_date) // Interprets as midnight UTC, displays in local timezone

// CORRECT (fixed):
const [year, month, day] = trip_date.split('-')
new Date(year, month - 1, day) // Parse as local date, no timezone offset
```

**Acceptance Criteria**:
- ✅ Database date 2025-10-10 displays as 10/10/2025
- ✅ All date displays match database values
- ✅ Date filters work correctly (09/15-10/15 shows all trips in range)
- ✅ No timezone offset issues for any dates

---

### FR-006: Scraper Update - boats_scraper.py
**Priority**: HIGH
**Requirement**: Update San Diego scraper to use departure date logic

**Current Code** (line 131):
```python
'trip_date': date,  # WRONG: stores report date
```

**Updated Code**:
```python
'trip_date': calculate_departure_date(date, normalized_trip_type),  # CORRECT: stores departure date
```

**Testing**:
- Dry-run on 3 recent dates
- Compare output against corrected database
- Verify no parser regressions (landing detection, catch parsing)

**Acceptance Criteria**:
- ✅ New scrapes use departure dates
- ✅ Dry-run validation: 3/3 dates correct
- ✅ No parser regressions introduced
- ✅ Duplicate detection still works

---

### FR-007: Scraper Update - socal_scraper.py
**Priority**: HIGH
**Requirement**: Update SoCal scraper to use departure date logic

**Current Code** (line 363):
```python
'trip_date': date,  # WRONG: stores report date
```

**Updated Code**:
```python
'trip_date': calculate_departure_date(date, normalized_trip_type),  # CORRECT: stores departure date
```

**Testing**: Same as FR-006 (3-date dry-run validation)

**Acceptance Criteria**:
- ✅ New scrapes use departure dates
- ✅ Dry-run validation: 3/3 dates correct
- ✅ No parser regressions introduced
- ✅ Regional filtering still works

---

### FR-008: Re-Scrape Missing Dates
**Priority**: MEDIUM
**Requirement**: Capture missing Polaris Supreme trips (Sep 21, Sep 18)

**Missing Trips**:
- 2025-09-21: 3 Day, 22 anglers, 132 Bluefin + 3 Dolphin + 68 Yellowfin
- 2025-09-18: 4 Day, 10 anglers, 60 Bluefin

**Root Cause**: Parser failure on those dates (Seaforth landing not detected)

**Solution**:
1. Fix scraper parser (already done - apply Seaforth fix lessons)
2. Re-run scraper for Sep 18-21 date range
3. Verify trips inserted with correct departure dates

**Acceptance Criteria**:
- ✅ Both missing trips captured
- ✅ Correct boat names (Polaris Supreme, not "Seaforth Sportfishing")
- ✅ Correct catch data matches source website
- ✅ Correct departure dates (using new logic)

---

### FR-009: Post-Migration Validation
**Priority**: CRITICAL
**Requirement**: Comprehensive validation after migration

**Validation Checks**:
1. **Data Integrity**:
   - Trip count unchanged: 8,523 trips
   - Catch count unchanged: ~30,000 catches
   - No NULL trip_dates
   - No orphaned catches (all catches have valid trip_id)

2. **Date Correctness**:
   - Spot-check 10 random trips against source website
   - Verify multi-day trips show earlier dates
   - Verify 1/2 day trips unchanged
   - Verify date range spans correct period

3. **Dashboard Display**:
   - 10 random trips display correct dates
   - Date filters produce expected results
   - Polaris Supreme 10-10 trip displays as 10/10 (not 10/9)

4. **Scraper Correctness**:
   - Dry-run on 3 dates produces correct results
   - Missing dates re-scraped successfully
   - No parser regressions

**Acceptance Criteria**:
- ✅ All validation checks pass 100%
- ✅ Manual spot-check: 10/10 trips correct
- ✅ Dashboard displays correct dates
- ✅ Scrapers produce correct dates

---

### FR-010: Audit Trail Documentation
**Priority**: HIGH
**Requirement**: Complete documentation of all changes

**Required Documents**:
- `validation/pre-migration-state.md` - Database state before changes
- `validation/migration-execution.md` - Step-by-step log of migration
- `validation/post-migration-state.md` - Database state after changes
- `validation/spot-check-results.md` - Manual verification results
- `validation/scraper-validation.md` - Scraper dry-run results

**Acceptance Criteria**:
- ✅ All documents created and complete
- ✅ Audit trail can reconstruct entire process
- ✅ Future developers can understand changes made
- ✅ Rollback procedure documented if needed

---

## Non-Functional Requirements

### NFR-001: Performance
- Migration script completes in < 5 minutes for 8,523 trips
- Dashboard date display performance unchanged
- Scraper speed unchanged (2-5 second delays maintained)

### NFR-002: Maintainability
- All code well-documented with inline comments
- Functions have clear docstrings with examples
- Validation scripts reusable for future fixes
- Constitution/spec provide clear guidance

### NFR-003: Reliability
- Transaction safety (all-or-nothing updates)
- Comprehensive error handling (log all failures)
- Backup/restore tested and verified
- Rollback procedure documented and tested

---

## Success Criteria

### Must-Have (Blocking Release)
1. ✅ All 8,523 trips updated with correct departure dates
2. ✅ Zero data loss (trip/catch counts unchanged)
3. ✅ Dashboard displays correct dates (timezone fix applied)
4. ✅ Both scrapers updated with correct logic
5. ✅ Manual spot-check: 10/10 trips verified correct

### Should-Have (High Priority)
1. ✅ Missing dates re-scraped (Sep 21, 18)
2. ✅ Comprehensive validation reports generated
3. ✅ Rollback procedure tested on dev database
4. ✅ Scraper dry-run validation: 3/3 dates correct

### Nice-to-Have (Optional)
1. Automated unit tests for date calculation function
2. Automated integration tests for migration script
3. Dashboard analytics showing date distribution
4. Performance monitoring for migration execution

---

## Risks & Mitigation

### Risk 1: Data Loss During Migration
**Probability**: Low
**Impact**: CRITICAL
**Mitigation**: Complete backup before changes, transaction safety, rollback procedure

### Risk 2: Incorrect Date Calculations
**Probability**: Medium
**Impact**: HIGH
**Mitigation**: Dry-run validation, spot-checking 10 trips, unit tests

### Risk 3: Scraper Regressions
**Probability**: Low
**Impact**: MEDIUM
**Mitigation**: Dry-run testing, compare against corrected database, test parsing logic

### Risk 4: Frontend Display Issues
**Probability**: Low
**Impact**: LOW
**Mitigation**: Test timezone fix on multiple dates, verify date filters work

---

## Timeline Estimate

- **Phase 1**: Backup & Validation (30 minutes)
- **Phase 2**: Build Migration Script (60 minutes)
- **Phase 3**: Dry-Run Testing (30 minutes)
- **Phase 4**: Execute Migration (5 minutes)
- **Phase 5**: Post-Migration Validation (30 minutes)
- **Phase 6**: Frontend Fix (30 minutes)
- **Phase 7**: Scraper Updates (45 minutes)
- **Phase 8**: Re-Scrape Missing Dates (15 minutes)
- **Phase 9**: Final Validation & Documentation (45 minutes)

**Total Estimated Time**: 4-5 hours

---

## Sign-Off

**Specification Author**: Claude Code
**Date**: October 16, 2025
**Version**: 1.0.0
**Status**: DRAFT - Pending User Approval

**User Approval**: _________________ (Date: _________)

Once approved, this specification defines the complete scope of work for the Trip Date Correction project.
