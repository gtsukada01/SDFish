# Specification: Landing Name Misattribution Fix (Boat ID 374)

**Version**: 1.0.0
**Date**: October 17, 2025
**Status**: DRAFT
**Governed By**: SPEC 006 QC Validation Standards
**Author**: Fishing Intelligence Platform

---

## Executive Summary

### Problem Statement

The scraper incorrectly assigned **195 fishing trips** to boat ID 374 named "Seaforth Sportfishing", which is actually the **landing name**, not a boat name. This occurred because the parser matched the repeated landing name in each boat entry as a valid boat name, failing to skip it.

**Affected Data**:
- **195 trips** spanning **180 unique dates** (2024-01-13 to 2025-10-31)
- **Month distribution**: Heavy concentration in Jul-Oct 2024 (85 trips) and Jul-Oct 2025 (76 trips)
- **Real boats affected**: Apollo, Aztec, New Seaforth, San Diego, El Gato Dos, Polaris Supreme, etc.

### Impact Assessment

**Data Integrity**:
- ❌ 195 trips have wrong boat attribution (2.4% of 7,958 total trips)
- ❌ Boat performance statistics are incorrect for Seaforth landing
- ❌ Trip filtering by boat name produces misleading results
- ❌ Moon phase correlation analysis includes misattributed data

**User Trust**:
- ❌ Dashboard shows "Seaforth Sportfishing" as a boat (it's actually the landing)
- ❌ Trip counts for real boats (El Gato Dos, New Seaforth, etc.) are underreported
- ❌ QC validation pass rate drops from 99.85% to ~97.6% with this issue

### Root Cause Analysis

**Parser Logic Gap** (boats_scraper.py line 279-280):
```python
# CURRENT CODE (BUGGY):
if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line):
    boat_name = line
    # ❌ PROBLEM: Doesn't check if boat_name == current_landing
    logger.info(f"Found boat: {boat_name}")
```

**HTML Structure on boats.php**:
```
Seaforth Sportfishing Fish Counts    ← Landing header
Boat  Trip Details  Dock Totals       ← Table header
Apollo                                ← Real boat name
Seaforth Sportfishing                 ← Landing name (REPEATED for each boat)
San Diego, CA                         ← Location
21 Anglers2 Day                       ← Trip info
84 Bluefin Tuna, 62 Yellowtail        ← Catches
```

**Why It Happened**:
1. The regex matches BOTH "Apollo" AND "Seaforth Sportfishing" as valid boat names
2. Parser expects to skip the landing name (line 283 comment) but doesn't validate
3. In some cases, "Seaforth Sportfishing" gets captured as the boat_name instead of being skipped
4. get_or_create_boat() creates boat ID 374 with name "Seaforth Sportfishing"
5. Trips continue to be assigned to this incorrect boat over 22 months

### Solution Overview

**Phase 1: Parser Fix** (COMPLETED)
- ✅ Add validation: `if boat_name == current_landing: skip`
- ✅ Prevents future occurrences

**Phase 2: Data Cleanup** (THIS SPEC)
- 🔄 Re-scrape 180 affected dates to get correct boat names
- 🔄 Match database trips to source page trips (duration + anglers)
- 🔄 Update boat_id for all 195 trips
- 🔄 Delete boat ID 374 after verification

**Phase 3: QC Validation** (MANDATORY)
- 🔄 Run qc_validator.py on all 180 affected dates
- 🔄 Verify 100% match between database and source
- 🔄 Confirm zero trips remain on boat ID 374

---

## Functional Requirements

### FR-001: Pre-Fix Validation & Snapshot
**Priority**: CRITICAL (must complete before any modifications)

**Requirement**: Create complete snapshot of current state for rollback capability

**Validation Steps**:
1. **Export affected trips**:
   ```sql
   SELECT id, trip_date, trip_duration, anglers, boat_id, landing_id
   FROM trips
   WHERE boat_id = 374
   ORDER BY trip_date;
   ```
   - Save to `pre_fix_snapshot_boat_374.json`
   - Expected: 195 trips

2. **Document trip distribution**:
   - Count trips per month
   - Identify date range (earliest to latest)
   - List all affected dates (should be 180)

3. **Verify no duplicate boat_id + trip_date + duration + anglers**:
   ```sql
   SELECT boat_id, trip_date, trip_duration, anglers, COUNT(*)
   FROM trips
   WHERE boat_id = 374
   GROUP BY boat_id, trip_date, trip_duration, anglers
   HAVING COUNT(*) > 1;
   ```
   - Expected: 0 duplicates

**Deliverables**:
- `pre_fix_snapshot_boat_374.json` - Complete backup
- `pre_fix_analysis.md` - Trip distribution and stats
- `rollback_plan.md` - How to restore if fix fails

**Acceptance Criteria**:
- ✅ All 195 trips backed up to JSON
- ✅ Trip counts match database query
- ✅ Rollback procedure documented and tested

---

### FR-002: Source Data Re-Scraping with Validation
**Priority**: CRITICAL

**Requirement**: Re-scrape all 180 affected dates to obtain correct boat names

**Scraping Protocol**:
1. **For each date in affected_dates.txt**:
   - Fetch `boats.php?date=YYYY-MM-DD` with 3-second delay
   - Parse Seaforth Sportfishing section ONLY
   - Extract all boats except "Seaforth Sportfishing" (landing name)
   - Log boat names found: Apollo, Aztec, El Gato Dos, New Seaforth, etc.

2. **Validation at scrape time**:
   - ❌ REJECT if any boat name == "Seaforth Sportfishing"
   - ❌ REJECT if boat name matches any known landing name
   - ✅ ACCEPT only if boat name is in expected Seaforth boats list

3. **Expected Boats List** (validation reference):
   - Apollo (boat_id: 85)
   - Aztec (boat_id: 62)
   - Cortez (boat_id: 91)
   - El Gato Dos (boat_id: 63)
   - Highliner (boat_id: 64)
   - New Seaforth (boat_id: 65)
   - Outer Limits (boat_id: 105)
   - Pacific Voyager (boat_id: 66)
   - Pacifica (boat_id: 77)
   - Polaris Supreme (boat_id: 80)
   - San Diego (boat_id: 67)
   - Sea Watch (boat_id: 68)
   - Tribute (boat_id: 69)
   - Voyager (boat_id: 86)

**Trip Matching Algorithm**:
```
FOR EACH db_trip in trips_374:
    scraped_trips = fetch_seaforth_trips(db_trip.trip_date)

    # Primary match: duration + anglers
    match = find_trip(scraped_trips, where={
        trip_duration: db_trip.trip_duration,
        anglers: db_trip.anglers
    })

    # Secondary match: anglers only (if duration has minor formatting differences)
    if no_match:
        match = find_trip(scraped_trips, where={
            anglers: db_trip.anglers,
            trip_duration: similar_to(db_trip.trip_duration)
        })

    if match:
        correct_boat_id = get_boat_id(match.boat_name)
        log_match(db_trip.id, match.boat_name, correct_boat_id)
    else:
        log_no_match(db_trip.id, db_trip.trip_date, db_trip.trip_duration, db_trip.anglers)
        mark_for_manual_review()
```

**Deliverables**:
- `fix_execution_log.txt` - Detailed log of every trip processed
- `matched_trips.json` - All successful matches (trip_id → correct_boat_id)
- `unmatched_trips.json` - Trips requiring manual review
- `fix_summary.json` - Success/error counts

**Acceptance Criteria**:
- ✅ All 180 dates successfully scraped
- ✅ No "Seaforth Sportfishing" in matched boat names
- ✅ ≥95% match rate (≥185 of 195 trips matched automatically)
- ✅ All unmatched trips flagged for manual review

---

### FR-003: Database Update with Transaction Safety
**Priority**: CRITICAL

**Requirement**: Update boat_id for all matched trips with rollback capability

**Transaction Protocol**:
```sql
BEGIN TRANSACTION;

-- Update trips with correct boat_id
UPDATE trips
SET boat_id = {correct_boat_id}
WHERE id IN ({matched_trip_ids});

-- Verify update count
SELECT COUNT(*) FROM trips WHERE id IN ({matched_trip_ids}) AND boat_id = {correct_boat_id};
-- Expected: {matched_trip_count}

-- If verification passes:
COMMIT;

-- If verification fails:
ROLLBACK;
```

**Safety Checks** (run BEFORE commit):
1. **Verify no trips lost**:
   ```sql
   SELECT COUNT(*) FROM trips WHERE boat_id = 374;
   ```
   - Expected: 195 - {matched_count}

2. **Verify boat_id exists**:
   ```sql
   SELECT id, name FROM boats WHERE id IN ({updated_boat_ids});
   ```
   - Expected: All IDs found with correct names

3. **Verify no landing names as boat names**:
   ```sql
   SELECT DISTINCT b.name
   FROM boats b
   JOIN trips t ON t.boat_id = b.id
   WHERE t.id IN ({updated_trip_ids})
   AND b.name IN ('Seaforth Sportfishing', 'H&M Landing', 'Fisherman''s Landing', ...);
   ```
   - Expected: 0 results

**Update Execution**:
- Process in batches of 50 trips
- Log every UPDATE statement
- Verify after each batch
- ROLLBACK entire batch if any verification fails

**Deliverables**:
- `update_log.sql` - All SQL UPDATE statements executed
- `post_update_verification.txt` - Verification results after each batch
- `update_summary.json` - Total updated, errors, rollbacks

**Acceptance Criteria**:
- ✅ All matched trips updated successfully
- ✅ Zero trips lost or duplicated
- ✅ All updated trips pass safety checks
- ✅ Rollback plan tested and confirmed working

---

### FR-004: Comprehensive QC Validation
**Priority**: CRITICAL

**Requirement**: Validate ALL 180 affected dates match source page 100%

**QC Validation Protocol**:

**Step 1: Run QC Validator on ALL Affected Dates**
```bash
python3 qc_validator.py \
  --dates-file affected_dates.txt \
  --output qc_landing_fix_validation.json \
  --strict-mode
```

**Expected Results**:
- **Pass Rate**: 100% (180/180 dates)
- **Field-Level Validation**: All boats, trip types, anglers, species, counts match
- **Zero Mismatches**: No trips with boat name = landing name

**Step 2: Validate Boat ID 374 Status**
```sql
SELECT COUNT(*) FROM trips WHERE boat_id = 374;
```
- Expected: 0 (or count of unmatched trips requiring manual review)

**Step 3: Validate Trip Redistribution**
```sql
SELECT b.name, COUNT(t.id) as trip_count
FROM trips t
JOIN boats b ON b.id = t.boat_id
WHERE t.trip_date BETWEEN '2024-01-13' AND '2025-10-31'
  AND b.landing_id = 14  -- Seaforth landing
GROUP BY b.name
ORDER BY trip_count DESC;
```
- Expected: Trips distributed across real boats (New Seaforth, San Diego, etc.)
- Expected: "Seaforth Sportfishing" = 0 or absent

**Step 4: Spot Check Manual Verification**
Manually verify 10 random trips from fix:
1. Pick 10 random trip_ids from matched_trips.json
2. For each trip:
   - Open boats.php?date={trip_date}
   - Find trip with matching duration + anglers
   - Verify boat name in database matches source
3. Expected: 10/10 perfect matches

**Deliverables**:
- `qc_landing_fix_validation.json` - Full QC report
- `spot_check_report.md` - Manual verification results
- `final_trip_distribution.json` - Trip counts per boat

**Acceptance Criteria**:
- ✅ 100% QC pass rate on all affected dates
- ✅ Boat ID 374 has 0 trips (or documented exceptions)
- ✅ 10/10 spot checks perfect match
- ✅ Trip distribution looks reasonable (no boat has unexpected spike)

---

### FR-005: Boat ID 374 Cleanup
**Priority**: HIGH (after 100% validation)

**Requirement**: Delete boat ID 374 after confirming zero trips assigned

**Cleanup Protocol**:

**Step 1: Final Verification**
```sql
-- Count trips on boat 374
SELECT COUNT(*) FROM trips WHERE boat_id = 374;
-- Expected: 0

-- If 0 trips, proceed to delete
-- If > 0 trips, document exceptions and get user approval
```

**Step 2: Boat Deletion**
```sql
BEGIN TRANSACTION;

-- Delete boat record
DELETE FROM boats WHERE id = 374;

-- Verify deletion
SELECT * FROM boats WHERE id = 374;
-- Expected: 0 rows

COMMIT;
```

**Step 3: Audit Trail**
```sql
-- Log deletion event
INSERT INTO audit_log (action, table_name, record_id, details, timestamp)
VALUES (
  'DELETE',
  'boats',
  374,
  'Deleted boat "Seaforth Sportfishing" after fixing 195 landing name misattributions',
  NOW()
);
```

**Deliverables**:
- `boat_374_deletion_log.txt` - Deletion event log
- `final_boats_list.json` - Updated boats table without ID 374

**Acceptance Criteria**:
- ✅ Boat ID 374 deleted from database
- ✅ Zero trips orphaned (no trips with boat_id = 374)
- ✅ Deletion logged in audit trail

---

## Success Metrics

### Data Quality Metrics

**Before Fix**:
- Total trips: 7,958
- Trips with boat_id = 374: 195 (2.4%)
- Affected dates: 180
- QC issues: 195 trips with landing name as boat

**After Fix** (Target):
- Total trips: 7,958 (no change)
- Trips with boat_id = 374: 0 ✅
- Affected dates QC pass rate: 100% (180/180) ✅
- Overall QC pass rate: 99.85% → 100.0% ✅

### Fix Performance Metrics

**Targets**:
- Match rate: ≥95% (≥185 of 195 trips)
- QC pass rate: 100% on all affected dates
- Manual review required: ≤10 trips
- Execution time: <30 minutes (180 dates × 5 sec/date = 15 min + processing)

### Validation Metrics

**Required Checks**:
- ✅ Pre-fix snapshot created
- ✅ All affected dates re-scraped successfully
- ✅ ≥95% automatic match rate achieved
- ✅ All matched trips updated in database
- ✅ QC validation 100% pass on affected dates
- ✅ Boat ID 374 deleted
- ✅ Spot check 10/10 perfect matches
- ✅ Zero data loss (7,958 trips before = 7,958 trips after)

---

## Rollback Plan

### Scenario: Fix Fails Validation

**If QC validation <100% pass rate:**
1. STOP immediately - do not delete boat 374
2. Restore from `pre_fix_snapshot_boat_374.json`:
   ```sql
   BEGIN TRANSACTION;

   -- Restore all trips to boat_id = 374
   UPDATE trips
   SET boat_id = 374
   WHERE id IN ({snapshot_trip_ids});

   -- Verify restoration
   SELECT COUNT(*) FROM trips WHERE boat_id = 374;
   -- Expected: 195

   COMMIT;
   ```
3. Investigate QC failures
4. Fix issues and restart from FR-001

### Scenario: Data Loss Detected

**If total trip count ≠ 7,958:**
1. ROLLBACK all transactions immediately
2. Check `pre_fix_snapshot_boat_374.json` integrity
3. Restore from backup
4. Investigate and fix before retrying

### Scenario: Unexpected Boat Names Found

**If matched boat names not in expected list:**
1. PAUSE fix execution
2. Document unexpected boat names
3. Verify against source page manually
4. Update expected boats list if legitimate
5. Resume with updated validation

---

## Implementation Checklist

### Phase 1: Preparation
- [ ] Create SPEC 007 directory: `specs/007-landing-name-misattribution-fix/`
- [ ] Write `pre_fix_snapshot_boat_374.json`
- [ ] Write `affected_dates.txt` (180 dates)
- [ ] Write `expected_boats_list.txt` (14 boats)
- [ ] Write `rollback_plan.md`

### Phase 2: Snapshot & Validation
- [ ] Export all 195 trips to JSON snapshot
- [ ] Document trip distribution by month
- [ ] Test rollback procedure with 1 trip
- [ ] Get user approval to proceed

### Phase 3: Fix Execution
- [ ] Run fix script with validation checkpoints
- [ ] Monitor match rate (target ≥95%)
- [ ] Log all matched trips
- [ ] Flag unmatched trips for manual review

### Phase 4: Database Update
- [ ] Update trips in batches of 50
- [ ] Verify after each batch
- [ ] Run safety checks before commit
- [ ] Log all SQL statements

### Phase 5: QC Validation
- [ ] Run qc_validator.py on all 180 dates
- [ ] Verify 100% pass rate
- [ ] Spot check 10 random trips
- [ ] Document any exceptions

### Phase 6: Cleanup
- [ ] Verify boat 374 has 0 trips
- [ ] Delete boat 374 from database
- [ ] Update documentation
- [ ] Archive fix logs

---

## Documentation

**Required Artifacts**:
1. `pre_fix_snapshot_boat_374.json` - Backup before fix
2. `affected_dates.txt` - All 180 dates requiring fix
3. `expected_boats_list.txt` - Validation reference
4. `fix_execution_log.txt` - Detailed fix log
5. `matched_trips.json` - Successful matches
6. `unmatched_trips.json` - Manual review required
7. `qc_landing_fix_validation.json` - QC results
8. `spot_check_report.md` - Manual verification
9. `rollback_plan.md` - Recovery procedures
10. `fix_summary_report.md` - Final summary with metrics

**Archive Location**: `specs/007-landing-name-misattribution-fix/artifacts/`

---

## Risk Assessment

### High Risks
1. **Data Loss**: Trips accidentally deleted during update
   - **Mitigation**: Pre-fix snapshot + transaction safety + batch verification

2. **Wrong Boat Assignment**: Trips matched to incorrect boats
   - **Mitigation**: QC validation 100% pass required + spot checks

3. **Partial Fix**: Some trips fixed, others left on boat 374
   - **Mitigation**: Complete execution log + final verification before boat deletion

### Medium Risks
1. **Low Match Rate**: <95% automatic matching
   - **Mitigation**: Manual review process for unmatched trips

2. **QC Failures**: Some dates don't pass validation
   - **Mitigation**: Rollback plan + re-fix failed dates

### Low Risks
1. **Long Execution Time**: >30 minutes
   - **Mitigation**: Progress logging + resumable execution

---

## User Acceptance

**Before proceeding with fix execution, user MUST review and approve**:
1. ✅ This specification document (SPEC 007)
2. ✅ Pre-fix snapshot (all 195 trips backed up)
3. ✅ Rollback plan (tested and confirmed working)
4. ✅ Expected boats list (14 boats verified)

**User sign-off required**: _____________________________  Date: _______

---

**End of Specification**
