# Specification 008: Phantom Trip Investigation & Remediation

**Version**: 1.0.0
**Date**: October 18, 2025
**Status**: ACTIVE - CRITICAL DATA INTEGRITY ISSUE
**Governed By**: SPEC 006 QC Validation Standards
**Author**: Fishing Intelligence Platform
**Priority**: P0 - CRITICAL

---

## Executive Summary

### Problem Statement

Following the landing name misattribution fix (SPEC 007), **116 trips remain unmatched** across 105 dates from two phantom boat records (boat_id 374 and 375). These trips fall into three potential categories:

1. **Phantom Data** - Trips that do not exist in source at all
2. **Misattributed Data** - Real trips assigned to wrong boat/landing
3. **Date-Shifted Data** - Real trips with incorrect dates due to timezone/parsing issues

**Critical Example** (User-reported):
```
Database shows: 10/18/2025, Seaforth Sportfishing, Full Day Offshore, 6 anglers, 3 Bluefin
Source shows: NO MATCHING TRIP EXISTS
```

This is a **critical data integrity failure** requiring surgical investigation and remediation.

### Impact Assessment

**Data Corruption Scope**:
- **116 unmatched trips** (66 Seaforth, 50 Helgrens)
- **105 affected dates** (2024-01-19 to 2025-10-31)
- **1.5% of total database** (116 / 7,958 trips)
- **Unknown composition**: Could be 100% phantom, 100% misattributed, or mixed

**User Trust Impact**:
- ❌ Dashboard displays trips that don't exist
- ❌ Analytics include corrupted data
- ❌ QC pass rate drops from 99.85% to unknown
- ❌ Credibility of entire dataset questioned

**Urgency**: IMMEDIATE - Cannot proceed with further development until resolved

### Solution Approach: Surgical Diagnosis First

**NOT ACCEPTABLE**:
- ❌ Delete all 116 trips blindly
- ❌ Assume all are phantom without verification
- ❌ Manual fixes without systematic investigation

**REQUIRED APPROACH**:
1. ✅ **Diagnostic Phase**: QC validate every trip against source
2. ✅ **Analysis Phase**: Categorize each trip with evidence
3. ✅ **Decision Phase**: User approval for each category's remediation
4. ✅ **Remediation Phase**: Execute fixes/deletes with full audit trail
5. ✅ **Verification Phase**: 100% QC validation post-remediation

---

## Functional Requirements

### FR-001: Complete Diagnostic Investigation
**Priority**: CRITICAL (must complete before any remediation)

**Requirement**: Run QC validator on ALL 105 affected dates to categorize every unmatched trip

**Investigation Protocol**:

**Step 1: Extract Affected Data**
```bash
# Get all trips still on boat_id 374 and 375
python3 << EOF
from boats_scraper import init_supabase
supabase = init_supabase()

for boat_id in [374, 375]:
    trips = supabase.table('trips').select('id, trip_date, trip_duration, anglers, boat_id').eq('boat_id', boat_id).execute()

    # Save to JSON for audit trail
    import json
    with open(f'diagnostic_trips_boat_{boat_id}.json', 'w') as f:
        json.dump(trips.data, f, indent=2)

    # Extract unique dates
    dates = sorted(set(t['trip_date'] for t in trips.data))
    with open(f'diagnostic_dates_boat_{boat_id}.txt', 'w') as f:
        f.write('\n'.join(dates))
EOF
```

**Step 2: Run QC Validator**
```bash
# Validate ALL affected dates against source
python3 scripts/python/qc_validator.py \
  --dates-file unmatched_dates_for_qc.txt \
  --output qc_diagnostic_report.json \
  --verbose \
  --include-missing-boats \
  --include-extra-boats

# Expected output:
# - For each date: which trips exist in source vs database
# - Missing boats: boats in DB but not in source (phantoms)
# - Extra boats: boats in source but not in DB (misattributions)
# - Field mismatches: trips that exist but with different details
```

**Step 3: Categorize Every Trip**

For each of the 116 unmatched trips, QC validator MUST determine:

| Category | Criteria | Action Required |
|----------|----------|-----------------|
| **PHANTOM** | Trip does NOT exist in source on ANY date | DELETE + log reason |
| **MISATTRIBUTED** | Trip exists in source but assigned to wrong boat | UPDATE boat_id + log change |
| **DATE-SHIFTED** | Trip exists in source but on different date | UPDATE trip_date + boat_id + log |
| **FIELD-MISMATCH** | Trip exists but anglers/duration don't match | MANUAL REVIEW required |
| **UNKNOWN** | Cannot determine (source unavailable, etc.) | MANUAL REVIEW required |

**Deliverables**:
- `qc_diagnostic_report.json` - Complete QC results for 105 dates
- `trip_categorization.json` - Every trip categorized with evidence
- `diagnostic_summary.md` - Human-readable summary with counts

**Acceptance Criteria**:
- ✅ All 105 dates successfully validated
- ✅ All 116 trips categorized (no "unknown" unless truly unresolvable)
- ✅ Each categorization includes evidence (source data snippet, reasoning)
- ✅ User reviews and approves categorization before remediation

---

### FR-002: Evidence-Based Categorization
**Priority**: CRITICAL

**Requirement**: Every trip categorization MUST include verifiable evidence from source

**Evidence Template** (for each trip):
```json
{
  "trip_id": 12379,
  "trip_date": "2024-05-25",
  "trip_duration": "1/2 Day Twilight",
  "anglers": 19,
  "current_boat": "Seaforth Sportfishing (ID 374)",
  "current_landing": "Seaforth Sportfishing (ID 14)",

  "category": "MISATTRIBUTED",

  "evidence": {
    "source_url": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2024-05-25",
    "source_snapshot": "New Seaforth\nSeaforth Sportfishing\nSan Diego, CA\n19 Anglers1/2 Day Twilight\n...",
    "correct_boat": "New Seaforth",
    "correct_boat_id": 65,
    "match_confidence": "exact",
    "reasoning": "Exact match on date, landing, duration, and anglers. Source shows 'New Seaforth' boat."
  },

  "recommended_action": "UPDATE trips SET boat_id = 65 WHERE id = 12379",
  "risk_level": "low"
}
```

**Phantom Trip Evidence Example**:
```json
{
  "trip_id": 11125,
  "trip_date": "2025-10-17",
  "trip_duration": "Full Day Offshore",
  "anglers": 6,
  "current_boat": "Seaforth Sportfishing (ID 374)",

  "category": "PHANTOM",

  "evidence": {
    "source_url": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-17",
    "source_snapshot": "Aztec: 25 anglers, 3 Day\nEl Gato Dos: 5 anglers, 3/4 Day\n...",
    "boats_on_date": ["Aztec", "El Gato Dos", "New Seaforth", "Pacific Voyager", "San Diego", "Tribute", "Voyager"],
    "matching_trips": [],
    "reasoning": "No trip in Seaforth section matches '6 anglers, Full Day Offshore'. All boats accounted for with different trip details. Trip does not exist in source."
  },

  "recommended_action": "DELETE FROM trips WHERE id = 11125",
  "risk_level": "low"
}
```

**Date-Shifted Evidence Example**:
```json
{
  "trip_id": 16315,
  "trip_date": "2024-09-02",
  "trip_duration": "2.5 Day",
  "anglers": 29,
  "current_boat": "Seaforth Sportfishing (ID 374)",

  "category": "DATE-SHIFTED",

  "evidence": {
    "source_date_checked": "2024-09-02",
    "source_url_checked": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2024-09-02",
    "found_on_date": "2024-09-04",
    "source_url_found": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2024-09-04",
    "source_snapshot": "Polaris Supreme\nSeaforth Sportfishing\n29 Anglers2.5 Day\n...",
    "correct_boat": "Polaris Supreme",
    "correct_boat_id": 80,
    "timezone_shift": "+2 days",
    "reasoning": "Trip exists on 2024-09-04 (not 09-02). Matches boat 'Polaris Supreme' with exact duration and anglers."
  },

  "recommended_action": "UPDATE trips SET trip_date = '2024-09-04', boat_id = 80 WHERE id = 16315",
  "risk_level": "medium"
}
```

**Deliverables**:
- `trip_categorization_detailed.json` - Full evidence for every trip
- `evidence_snapshots/` - HTML snapshots of source pages for audit

**Acceptance Criteria**:
- ✅ Every trip has complete evidence structure
- ✅ Evidence is verifiable (URLs, source snapshots saved)
- ✅ Reasoning is clear and documented
- ✅ Recommended actions are specific SQL statements

---

### FR-003: User Decision Matrix
**Priority**: CRITICAL (no remediation without approval)

**Requirement**: User MUST review and approve remediation plan for each category

**Decision Template**:

**Category 1: PHANTOM TRIPS**
```
Count: XX trips
Evidence: All trips checked against source, none exist
Recommended Action: DELETE FROM trips WHERE id IN (...)
Risk Assessment: LOW - trips don't exist, safe to delete
Data Loss: XX trips permanently removed

User Decision:
[ ] APPROVE deletion of all phantom trips
[ ] REVIEW individually (list trip IDs for review: _______)
[ ] REJECT - need more investigation

User Signature: _________________ Date: _______
```

**Category 2: MISATTRIBUTED TRIPS**
```
Count: XX trips
Evidence: Trips exist in source but assigned to wrong boat
Recommended Action: UPDATE boat_id for XX trips
Risk Assessment: LOW - exact matches found
Data Preserved: All trips preserved with correct attribution

User Decision:
[ ] APPROVE all misattribution fixes
[ ] REVIEW sample (N=10) before approving all
[ ] REJECT - need more investigation

User Signature: _________________ Date: _______
```

**Category 3: DATE-SHIFTED TRIPS**
```
Count: XX trips
Evidence: Trips exist but on different dates (timezone issue)
Recommended Action: UPDATE trip_date AND boat_id for XX trips
Risk Assessment: MEDIUM - date changes affect analytics
Data Preserved: All trips preserved with correct dates

User Decision:
[ ] APPROVE all date-shift fixes
[ ] REVIEW all individually before approving
[ ] REJECT - need root cause analysis first

User Signature: _________________ Date: _______
```

**Category 4: MANUAL REVIEW REQUIRED**
```
Count: XX trips
Evidence: Uncertain categorization, need human judgment
Recommended Action: Manual investigation required

User Decision:
[ ] ASSIGN to: _______________ for investigation
[ ] DEFER until after other categories processed
[ ] DELETE as likely phantom (risky)

User Signature: _________________ Date: _______
```

**Deliverables**:
- `user_decision_matrix.md` - Approval form with all categories
- `approved_remediation_plan.json` - User-approved actions

**Acceptance Criteria**:
- ✅ User reviews category counts and evidence samples
- ✅ User makes explicit decision for each category
- ✅ User signature/approval documented
- ✅ Remediation script only executes approved actions

---

### FR-004: Surgical Remediation with Audit Trail
**Priority**: CRITICAL

**Requirement**: Execute ONLY user-approved remediations with complete audit logging

**Remediation Protocol**:

**Step 1: Pre-Remediation Snapshot**
```bash
# Create complete backup BEFORE any changes
python3 << EOF
from boats_scraper import init_supabase
import json
from datetime import datetime

supabase = init_supabase()

snapshot = {
    'timestamp': datetime.now().isoformat(),
    'boats': {}
}

for boat_id in [374, 375]:
    trips = supabase.table('trips').select('*').eq('boat_id', boat_id).execute()
    snapshot['boats'][boat_id] = {
        'trip_count': len(trips.data),
        'trips': trips.data
    }

with open(f'pre_remediation_snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
    json.dump(snapshot, f, indent=2)
EOF
```

**Step 2: Transaction-Safe Deletions**
```sql
-- ONLY execute for user-approved PHANTOM trips
BEGIN TRANSACTION;

-- Delete catches first (foreign key constraint)
DELETE FROM catches
WHERE trip_id IN (
    SELECT id FROM trips
    WHERE id IN (...approved phantom trip IDs...)
);

-- Delete trips
DELETE FROM trips
WHERE id IN (...approved phantom trip IDs...);

-- Verify deletion count matches expected
SELECT COUNT(*) FROM trips WHERE id IN (...);
-- Expected: 0

-- If verification passes:
COMMIT;

-- If verification fails:
ROLLBACK;
```

**Step 3: Transaction-Safe Updates**
```sql
-- ONLY execute for user-approved MISATTRIBUTED trips
BEGIN TRANSACTION;

-- Update boat_id for misattributed trips
UPDATE trips
SET boat_id = CASE
    WHEN id = 12379 THEN 65
    WHEN id = 12556 THEN 65
    -- ... all approved updates
    END
WHERE id IN (...approved misattributed trip IDs...);

-- Verify update count
SELECT COUNT(*) FROM trips
WHERE id IN (...)
AND boat_id IN (...expected boat IDs...);
-- Expected: XX (approved count)

-- If verification passes:
COMMIT;

-- If verification fails:
ROLLBACK;
```

**Step 4: Audit Logging**
```python
# Log every action taken
audit_log = {
    'timestamp': datetime.now().isoformat(),
    'user_approved_by': 'USER_NAME',
    'spec': 'SPEC-008',
    'actions': [
        {
            'action_type': 'DELETE',
            'trip_ids': [...],
            'reason': 'PHANTOM - trips do not exist in source',
            'evidence_file': 'trip_categorization_detailed.json',
            'sql_executed': 'DELETE FROM trips WHERE...',
            'rows_affected': XX,
            'success': True
        },
        {
            'action_type': 'UPDATE',
            'trip_ids': [...],
            'old_boat_id': 374,
            'new_boat_id': 65,
            'reason': 'MISATTRIBUTED - trips belong to New Seaforth',
            'evidence_file': 'trip_categorization_detailed.json',
            'sql_executed': 'UPDATE trips SET...',
            'rows_affected': XX,
            'success': True
        }
    ],
    'summary': {
        'total_trips_deleted': XX,
        'total_trips_updated': XX,
        'total_trips_unchanged': XX
    }
}

with open('remediation_audit_log.json', 'w') as f:
    json.dump(audit_log, f, indent=2)
```

**Deliverables**:
- `pre_remediation_snapshot_*.json` - Complete backup before changes
- `remediation_audit_log.json` - Complete log of all actions
- `remediation_sql_log.sql` - All SQL statements executed
- `remediation_summary.md` - Human-readable summary

**Acceptance Criteria**:
- ✅ Snapshot created and verified before ANY changes
- ✅ Only user-approved actions executed
- ✅ All changes in transactions with verification
- ✅ Complete audit trail for every action
- ✅ Rollback capability tested and confirmed

---

### FR-005: Post-Remediation Verification
**Priority**: CRITICAL

**Requirement**: 100% QC validation after remediation to confirm data integrity restored

**Verification Protocol**:

**Step 1: Re-run QC Validator on ALL 105 Dates**
```bash
# Validate same dates that were investigated
python3 scripts/python/qc_validator.py \
  --dates-file unmatched_dates_for_qc.txt \
  --output qc_post_remediation.json \
  --strict-mode

# Expected result: 100% pass rate on all dates
```

**Step 2: Verify Phantom Boats Empty**
```sql
-- Check boat_id 374 and 375 have zero trips
SELECT boat_id, COUNT(*) as trip_count
FROM trips
WHERE boat_id IN (374, 375)
GROUP BY boat_id;

-- Expected: 0 rows (both boats have zero trips)
```

**Step 3: Verify Total Trip Count**
```sql
-- Ensure total trips = original - deleted
SELECT COUNT(*) as total_trips FROM trips;

-- Expected: 7,958 - (phantom deletions) = XXXX
-- Document expected count before remediation
```

**Step 4: Spot Check Fixed Trips**
```bash
# Manually verify 10 random trips that were fixed
# For each:
# 1. Check database trip details
# 2. Verify against source page
# 3. Confirm boat/landing/date all match source
```

**Step 5: Database Integrity Checks**
```sql
-- No orphaned catches
SELECT COUNT(*) FROM catches c
LEFT JOIN trips t ON c.trip_id = t.id
WHERE t.id IS NULL;
-- Expected: 0

-- No duplicate trips
SELECT boat_id, trip_date, trip_duration, anglers, COUNT(*)
FROM trips
GROUP BY boat_id, trip_date, trip_duration, anglers
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- All boats exist
SELECT COUNT(*) FROM trips t
LEFT JOIN boats b ON t.boat_id = b.id
WHERE b.id IS NULL;
-- Expected: 0
```

**Deliverables**:
- `qc_post_remediation.json` - Full QC report showing 100% pass
- `verification_checklist.md` - All verification steps completed
- `spot_check_report.md` - Manual verification of sample trips
- `database_integrity_report.md` - All integrity checks passed

**Acceptance Criteria**:
- ✅ QC validator shows 100% pass rate on all affected dates
- ✅ Boat_id 374 and 375 have zero trips
- ✅ Total trip count matches expected (original - deletions)
- ✅ All 10 spot checks match source perfectly
- ✅ All database integrity checks pass
- ✅ No orphaned data, duplicates, or broken foreign keys

---

## Success Criteria

### Data Quality Metrics

**Before Remediation**:
- Total trips: 7,958
- Unmatched trips: 116 (1.5%)
- Phantom boat trips (374): 66
- Phantom boat trips (375): 50
- QC issues: 116 trips unverified
- QC pass rate: ~98.5% (estimated)

**After Remediation** (Targets):
- Total trips: 7,958 - XX (phantoms deleted)
- Unmatched trips: 0 ✅
- Trips on boat 374: 0 ✅
- Trips on boat 375: 0 ✅
- QC pass rate: 100.0% ✅
- User confidence: RESTORED ✅

### Remediation Performance Metrics

**Targets**:
- Categorization accuracy: 100% (all trips correctly categorized)
- QC validation time: <30 minutes for 105 dates
- User review time: Depends on findings, allow 1-2 hours
- Remediation execution: <10 minutes (automated with verification)
- Post-verification: <15 minutes

**Quality Gates** (MUST pass before proceeding):
1. ✅ All 116 trips categorized with evidence
2. ✅ User approval obtained for all categories
3. ✅ Pre-remediation snapshot created and verified
4. ✅ Remediation executes only approved actions
5. ✅ Post-remediation QC shows 100% pass
6. ✅ Database integrity checks all pass

---

## Rollback Plan

### Scenario: QC Validation Fails Post-Remediation

**If post-remediation QC <100% pass rate:**

```bash
# 1. STOP immediately - do not delete phantom boats
# 2. Restore from pre-remediation snapshot
python3 << EOF
from boats_scraper import init_supabase
import json

supabase = init_supabase()

# Load snapshot
with open('pre_remediation_snapshot_YYYYMMDD_HHMMSS.json') as f:
    snapshot = json.load(f)

# Restore trips for each boat
for boat_id, data in snapshot['boats'].items():
    for trip in data['trips']:
        # Re-insert trip (will fail if already exists)
        try:
            supabase.table('trips').insert(trip).execute()
        except:
            # Already exists, skip
            pass

print(f"Restored {len(data['trips'])} trips to boat {boat_id}")
EOF

# 3. Investigate QC failures
# 4. Fix root cause
# 5. Restart from FR-001
```

### Scenario: Remediation Script Fails

**If remediation script errors during execution:**

```sql
-- Transaction will auto-rollback on error
-- Verify nothing changed:
SELECT COUNT(*) FROM trips WHERE boat_id IN (374, 375);
-- Expected: Same count as before remediation

-- Review error logs
cat remediation_audit_log.json

-- Fix script and retry
```

### Scenario: User Rejects Findings

**If user does not approve remediation plan:**

```
-- No changes made (remediation requires user approval)
-- Options:
1. Refine investigation methodology
2. Gather additional evidence
3. Perform manual investigation on uncertain trips
4. Restart from FR-001 with improved criteria
```

---

## Phase Execution Plan

### Phase 1: Diagnostic (Days 1-2)
**Goal**: Complete investigation of all 116 unmatched trips

**Tasks**:
1. Extract all trips from boat_id 374 and 375 → affected dates list
2. Run QC validator on all 105 affected dates
3. Categorize every trip with evidence
4. Generate categorization report with evidence snapshots
5. Produce summary statistics (X phantoms, Y misattributed, etc.)

**Deliverables**:
- `qc_diagnostic_report.json`
- `trip_categorization_detailed.json`
- `diagnostic_summary.md`

**Exit Criteria**: All 116 trips categorized, ready for user review

---

### Phase 2: User Decision (Day 3)
**Goal**: Obtain user approval for remediation plan

**Tasks**:
1. Present categorization summary to user
2. Show evidence samples for each category
3. Explain recommended actions and risks
4. Obtain user approval/rejection for each category
5. Document decisions in approval form

**Deliverables**:
- `user_decision_matrix.md` (signed)
- `approved_remediation_plan.json`

**Exit Criteria**: User approval obtained, ready to execute

---

### Phase 3: Remediation (Day 4)
**Goal**: Execute approved fixes/deletes with full audit trail

**Tasks**:
1. Create pre-remediation snapshot
2. Execute approved deletions (phantoms)
3. Execute approved updates (misattributions, date-shifts)
4. Log all actions in audit trail
5. Verify transaction success

**Deliverables**:
- `pre_remediation_snapshot_*.json`
- `remediation_audit_log.json`
- `remediation_sql_log.sql`

**Exit Criteria**: All approved actions executed successfully

---

### Phase 4: Verification (Day 5)
**Goal**: Confirm 100% data integrity restored

**Tasks**:
1. Re-run QC validator on all 105 dates
2. Verify phantom boats empty
3. Spot check 10 fixed trips
4. Run database integrity checks
5. Generate final verification report

**Deliverables**:
- `qc_post_remediation.json` (100% pass)
- `verification_checklist.md`
- `spot_check_report.md`
- `final_remediation_report.md`

**Exit Criteria**: All verification checks pass, ready to close out

---

### Phase 5: Cleanup (Day 6)
**Goal**: Remove phantom boat records, update documentation

**Tasks**:
1. Delete boat_id 374 and 375 (now have zero trips)
2. Update database statistics
3. Update project documentation
4. Archive all diagnostic/remediation artifacts
5. Close SPEC-008

**Deliverables**:
- `cleanup_log.md`
- Updated `README.md` and `COMPREHENSIVE_QC_VERIFICATION.md`
- `SPEC-008-COMPLETION-REPORT.md`

**Exit Criteria**: Phantom boats deleted, documentation updated, issue resolved

---

## Risk Assessment

### Critical Risks

**Risk 1: Deleting Legitimate Data**
- **Severity**: CRITICAL
- **Likelihood**: LOW (with proper investigation)
- **Mitigation**:
  - Every deletion requires QC evidence
  - User approval mandatory
  - Pre-remediation snapshot for rollback
  - Conservative categorization (when in doubt, manual review)

**Risk 2: Missing Phantom Trips**
- **Severity**: HIGH
- **Likelihood**: MEDIUM
- **Mitigation**:
  - Comprehensive QC validation on ALL affected dates
  - Evidence-based categorization with conservative thresholds
  - Post-remediation QC to catch any remaining issues

**Risk 3: Creating New Data Issues**
- **Severity**: HIGH
- **Likelihood**: LOW
- **Mitigation**:
  - Transaction-safe SQL with verification
  - Rollback capability tested
  - Post-remediation database integrity checks

### Medium Risks

**Risk 4: Long Investigation Timeline**
- **Severity**: MEDIUM
- **Likelihood**: HIGH (105 dates to validate)
- **Mitigation**:
  - Automated QC validation where possible
  - Parallel investigation by category
  - Clear decision criteria to avoid analysis paralysis

**Risk 5: User Approval Delays**
- **Severity**: MEDIUM
- **Likelihood**: MEDIUM
- **Mitigation**:
  - Clear, concise categorization summary
  - Evidence samples readily available
  - Decision matrix with clear options

---

## Documentation Standards

### Required Artifacts

**Diagnostic Phase**:
1. `specs/008-phantom-trip-investigation/spec.md` - This specification
2. `specs/008-phantom-trip-investigation/diagnostic_trips_boat_374.json` - All trips from boat 374
3. `specs/008-phantom-trip-investigation/diagnostic_trips_boat_375.json` - All trips from boat 375
4. `specs/008-phantom-trip-investigation/unmatched_dates_for_qc.txt` - All affected dates
5. `specs/008-phantom-trip-investigation/qc_diagnostic_report.json` - QC results
6. `specs/008-phantom-trip-investigation/trip_categorization_detailed.json` - Evidence for every trip
7. `specs/008-phantom-trip-investigation/diagnostic_summary.md` - Human-readable summary

**Decision Phase**:
8. `specs/008-phantom-trip-investigation/user_decision_matrix.md` - User approval form
9. `specs/008-phantom-trip-investigation/approved_remediation_plan.json` - Approved actions

**Remediation Phase**:
10. `specs/008-phantom-trip-investigation/pre_remediation_snapshot_*.json` - Backup
11. `specs/008-phantom-trip-investigation/remediation_audit_log.json` - Action log
12. `specs/008-phantom-trip-investigation/remediation_sql_log.sql` - SQL executed

**Verification Phase**:
13. `specs/008-phantom-trip-investigation/qc_post_remediation.json` - Final QC
14. `specs/008-phantom-trip-investigation/verification_checklist.md` - All checks
15. `specs/008-phantom-trip-investigation/spot_check_report.md` - Manual verification
16. `specs/008-phantom-trip-investigation/final_remediation_report.md` - Summary

**Archive Location**: All artifacts in `specs/008-phantom-trip-investigation/`

---

## User Acceptance

**Before proceeding with ANY remediation, user MUST review and approve**:

1. ✅ This specification document (SPEC 008)
2. ✅ Diagnostic categorization results (trip_categorization_detailed.json)
3. ✅ User decision matrix with approval for each category
4. ✅ Remediation plan with specific SQL statements
5. ✅ Rollback plan tested and confirmed working

**User Sign-Off**:

I have reviewed the diagnostic findings and approve the remediation plan as documented in `approved_remediation_plan.json`.

User Signature: _____________________________ Date: _______

---

**End of Specification SPEC-008**

**Next Steps**: Execute Phase 1 (Diagnostic) per this specification.
