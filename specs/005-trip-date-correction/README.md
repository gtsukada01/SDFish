# Trip Date Correction Project

**Status**: 🟡 AWAITING USER APPROVAL
**Created**: October 16, 2025
**Estimated Duration**: 4-5 hours
**Impact**: 8,523 trips (100% of database)

---

## Quick Summary

### The Problem
Your database stores **return/report dates** instead of **departure dates**, causing:
- Polaris Supreme trip on Oct 10 (source) displays as Oct 9 (dashboard) ❌
- Multi-day trips show wrong dates (3-day trip departed Sep 21, database shows Sep 24)
- Missing trips due to parser failures (Sep 21, Sep 18)
- Date filters exclude trips incorrectly

### The Solution
1. **Database Migration**: Correct all 8,523 trip dates (report_date → departure_date)
2. **Frontend Fix**: Fix timezone bug (10-10 showing as 10-09)
3. **Scraper Updates**: Fix both scrapers to use departure date logic
4. **Re-Scrape**: Capture missing Sep 21, Sep 18 trips

### The Approach
**Spec-Kit Governance** (like Seaforth fix):
- ✅ Constitution with data integrity principles
- ✅ Detailed specification with 10 functional requirements
- ✅ Comprehensive validation at every step
- ✅ Complete backup before any changes
- ✅ Dry-run testing before production execution

---

## Why This Approach?

### Lessons from Past Successes
**Seaforth Fix** (UPDATE_2025_10_16.md):
- Spec-driven approach prevented scope creep ✅
- Comprehensive backups enabled safe operations ✅
- Dry-run testing caught bugs before production ✅
- 96 trips fixed with 100% accuracy ✅

**Landing Cleanup** (landing-cleanup-report.md):
- User-reported bugs revealed critical data issues ✅
- Cleanup script consolidated 3 duplicate landings ✅
- 832 trips now visible in dashboard ✅

### This Fix is Bigger
- **8,523 trips** vs 96 trips (88x larger)
- **Every single trip** needs updating (not just problematic ones)
- **Database schema change** (trip_date semantics)
- **Two scrapers** need updating (not just one)
- **Frontend changes** required (timezone fix)

**Risk Level**: HIGH → **Governance Required**: spec-kit with constitution

---

## Project Structure

```
specs/005-trip-date-correction/
├── README.md              # This file - project overview
├── constitution.md        # Core principles & quality standards (v1.0.0)
├── spec.md                # Detailed specification (10 requirements)
├── checklists/
│   └── requirements.md    # Validation checklist (pending)
└── validation/
    ├── pre-migration-state.md     # Database before (pending)
    ├── migration-execution.md     # Step-by-step log (pending)
    ├── post-migration-state.md    # Database after (pending)
    └── spot-check-results.md      # Manual verification (pending)
```

---

## Core Principles (from constitution.md)

### 1. Data Integrity Above All
- Zero data loss (complete backup before changes)
- 100% reversible (backup can restore original state)
- Validation-first (dry-run before production)
- Complete audit trail (every change documented)

### 2. Correct Trip Date Semantics
- **Departure Date Standard**: trip_date = when boat LEFT dock
- **Calculation**: `departure_date = report_date - trip_duration_days`
- **Example**: 3-day trip reported on 09-24 → departed 09-21

### 3. Frontend Display Correctness
- UTC storage, local timezone display
- Fix timezone offset bug (10-10 showing as 10-09)
- Date filters work correctly

### 4. Scraper Logic Correction
- Both scrapers fixed (boats_scraper.py + socal_scraper.py)
- Future scrapes use correct departure date calculation
- No parser regressions

---

## Functional Requirements Summary

| ID | Requirement | Priority | Effort |
|----|-------------|----------|--------|
| FR-001 | Date Calculation Logic | CRITICAL | 30 min |
| FR-002 | Database Backup | CRITICAL | 30 min |
| FR-003 | Migration Script - Dry Run | CRITICAL | 60 min |
| FR-004 | Migration Script - Production | CRITICAL | 30 min |
| FR-005 | Frontend Timezone Fix | HIGH | 30 min |
| FR-006 | Scraper Update - boats_scraper.py | HIGH | 30 min |
| FR-007 | Scraper Update - socal_scraper.py | HIGH | 15 min |
| FR-008 | Re-Scrape Missing Dates | MEDIUM | 15 min |
| FR-009 | Post-Migration Validation | CRITICAL | 30 min |
| FR-010 | Audit Trail Documentation | HIGH | 45 min |

**Total**: 10 requirements, 4-5 hours estimated

---

## Quality Control Checklist

### Pre-Migration (MUST COMPLETE BEFORE EXECUTION)
- [ ] Constitution approved by user
- [ ] Specification approved by user
- [ ] Complete database backup created
- [ ] Backup validated (trip/catch counts match)
- [ ] Dry-run validation shows expected changes
- [ ] 10 trips manually spot-checked against source
- [ ] Edge cases tested (1/2 day, overnight, 5-day trips)

### Migration Execution (SAFETY CHECKS)
- [ ] Dry-run output reviewed and approved
- [ ] Production migration logged comprehensively
- [ ] Zero data loss verified (8,523 trips → 8,523 trips)
- [ ] All catches preserved (no orphaned catches)
- [ ] No NULL trip_dates created
- [ ] Transaction completed successfully

### Post-Migration (VALIDATION)
- [ ] Database state documented (validation report)
- [ ] 10 trips manually verified against source
- [ ] Dashboard displays correct dates (timezone fix applied)
- [ ] Date filters work correctly
- [ ] Both scrapers updated and tested
- [ ] Missing dates re-scraped (Sep 21, 18)
- [ ] Final audit report generated

---

## Rollback Plan

### If Anything Goes Wrong
```bash
# Restore from backup (all changes reversed)
python3 restore_from_backup.py --backup-file trip_date_backup_YYYYMMDD_HHMMSS.json --verify

# Verify rollback success
python3 -c "from boats_scraper import init_supabase; s=init_supabase();
trips = s.table('trips').select('id', count='exact').execute();
print(f'Trip count: {trips.count}')  # Should be 8,523"
```

### Rollback Triggers
- Any trip count mismatch
- Any catch count mismatch
- More than 5% of spot-checks fail
- Dashboard displays incorrect dates after fix
- Any validation check failure

---

## Example: What Changes

### Current (WRONG)
```
Source Website: "3 Day Trip" reported on 09-24-2025
Database Stores: trip_date = '2025-09-24' ❌ (return date)
Dashboard Shows: 09/23/2025 ❌ (timezone bug makes it even worse)
User Thinks: "I went fishing on Sep 21" 😕
```

### After Fix (CORRECT)
```
Source Website: "3 Day Trip" reported on 09-24-2025
Database Stores: trip_date = '2025-09-21' ✅ (departure date)
Dashboard Shows: 09/21/2025 ✅ (timezone fix applied)
User Thinks: "I went fishing on Sep 21" ✅
```

---

## Timeline

### Phase 1: Approval & Setup (30 min)
- User reviews constitution & specification
- User approves approach
- Create backup & validation scripts

### Phase 2: Development (2 hours)
- Build date calculation function
- Build migration script (dry-run + production modes)
- Fix frontend timezone bug
- Update both scrapers

### Phase 3: Testing (1 hour)
- Dry-run validation on full database
- Spot-check 10 trips against source
- Test edge cases (1/2 day, overnight, 5-day)
- Review dry-run output

### Phase 4: Execution (30 min)
- Execute migration script
- Verify zero data loss
- Generate post-migration reports

### Phase 5: Validation (1 hour)
- Re-scrape missing dates
- Verify dashboard displays correct dates
- Test scraper dry-runs
- Generate final audit reports

---

## Success Metrics

### Data Accuracy
- ✅ 100% of multi-day trips show departure dates (not return dates)
- ✅ 10/10 spot-checks match source website
- ✅ Edge cases validated: 1/2 day, overnight, 5-day trips
- ✅ Zero data loss: 8,523 trips → 8,523 trips

### Display Correctness
- ✅ Dashboard shows correct dates (no timezone offset)
- ✅ Date filters work correctly
- ✅ Polaris Supreme 10-10 trip displays as 10/10 (not 10/9)

### Scraper Correctness
- ✅ New scrapes use departure dates
- ✅ Missing dates captured (Sep 21, Sep 18)
- ✅ No parser regressions

---

## User Approval Required

**Before proceeding, please confirm:**

1. **Approach Approved?**
   - [ ] Constitution principles acceptable
   - [ ] Specification requirements clear
   - [ ] Quality control standards adequate
   - [ ] Timeline estimate reasonable

2. **Risk Acceptance?**
   - [ ] Understand this affects ALL 8,523 trips
   - [ ] Accept 4-5 hour development + testing time
   - [ ] Approve backup/rollback strategy
   - [ ] Ready to review dry-run results before production execution

3. **Priority Confirmation?**
   - [ ] This fix is high priority (blocks other work)
   - [ ] OR: This fix can wait (document and defer)
   - [ ] OR: Need more information before deciding

---

## Next Steps

### If Approved
1. User confirms: "Approved - proceed with spec-kit approach"
2. I'll create validation scripts and backup system
3. Build migration script with dry-run mode
4. Execute dry-run and show you results for review
5. Upon approval, execute production migration
6. Complete validation and generate reports

### If More Info Needed
1. Ask any questions about the approach
2. Review specific requirements in spec.md
3. Discuss timeline or risk concerns
4. Modify spec as needed

### If Deferred
1. Document this issue in KNOWN_ISSUES.md
2. Continue with other dashboard work
3. Revisit when timing is better

---

**Ready to proceed?**
Please reply with your decision: **Approved** / **More Info** / **Defer**
