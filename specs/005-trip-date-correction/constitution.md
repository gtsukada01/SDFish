# Constitution v1.0.0: Trip Date Correction Project

**Date**: October 16, 2025
**Project**: Trip Date Semantics Correction
**Scope**: All 8,523+ trips in database (San Diego + SoCal)

---

## Core Principles

### 1. **Data Integrity Above All**
- **Zero Data Loss**: Every trip must be accounted for in backup before modification
- **Reversibility**: All changes must be 100% reversible via backup
- **Validation-First**: No changes without comprehensive pre/post validation
- **Audit Trail**: Complete documentation of every change made

### 2. **Correct Trip Date Semantics**
- **Departure Date Standard**: `trip_date` field SHALL represent when the boat LEFT the dock
- **Industry Alignment**: Match sandiegofishreports.com convention (organizes by departure)
- **User Mental Model**: Users think "I went fishing on Tuesday" = departure date
- **Calculation Logic**: `departure_date = report_date - trip_duration_days`

### 3. **Multi-Day Trip Accuracy**
- **Example**: 3-day trip reported on 09-24 → departed 09-21
- **Validation**: Verify calculations against source website spot checks
- **Edge Cases**: 1/2 day trips (same-day departure/return) require special handling
- **Timezone Handling**: All dates stored in UTC, displayed in local timezone

### 4. **Frontend Display Correctness**
- **UTC Storage**: Database stores dates in UTC (YYYY-MM-DD)
- **Local Display**: Frontend displays in user's local timezone
- **Bug Fix**: Prevent timezone offset causing date display errors (10-10 showing as 10-09)
- **Consistency**: All date displays must match database values

### 5. **Scraper Logic Correction**
- **Both Scrapers**: Fix `boats_scraper.py` AND `socal_scraper.py`
- **Future-Proof**: New scrapes use correct departure date calculation
- **No Regression**: Ensure fix doesn't break existing parser logic
- **Testing**: Dry-run validation on 3 sample dates before production

---

## Quality Control Standards

### Pre-Migration Validation
- [ ] Complete database backup created
- [ ] Backup verified (trip count, catch count, date range matches)
- [ ] Dry-run validation shows expected changes
- [ ] Sample verification: 10 trips manually checked against source
- [ ] Edge case testing: 1/2 day, overnight, 5-day trips validated

### Migration Execution
- [ ] Run in DRY RUN mode first
- [ ] Compare dry-run results against manual calculations
- [ ] Execute migration with full logging
- [ ] Verify zero data loss (trip counts unchanged)
- [ ] Verify date changes match expected pattern

### Post-Migration Validation
- [ ] All 8,523+ trips still in database
- [ ] All catches preserved (no orphaned catches)
- [ ] Date changes follow correct logic (multi-day trips show earlier dates)
- [ ] Sample verification: 10 trips manually checked post-migration
- [ ] Dashboard displays correct dates (timezone fix applied)
- [ ] No duplicate trips created (trip_date changed but still unique)

### Scraper Validation
- [ ] Both scrapers updated with correct logic
- [ ] Dry-run test on 3 dates (recent, historical, multi-day trips)
- [ ] Compare new logic output against corrected database
- [ ] Verify no new bugs introduced (landing detection, catch parsing)
- [ ] Test duplicate prevention still works with new dates

---

## Risk Mitigation

### Critical Risks
1. **Data Loss**: Mitigated by complete backup before any changes
2. **Incorrect Calculations**: Mitigated by spot-checking 10+ trips against source
3. **Duplicate Creation**: Mitigated by testing on isolated boat first
4. **Scraper Regression**: Mitigated by dry-run testing before production use

### Rollback Triggers
- Any trip count mismatch (before: 8,523 → after: must equal 8,523)
- Any catch count mismatch
- Any validation check failure
- More than 5% of trips fail manual spot-check
- Dashboard displays incorrect dates after fix

### Rollback Procedure
```bash
# Restore from backup
python3 restore_from_backup.py --backup-file trip_date_backup_YYYYMMDD_HHMMSS.json --verify
```

---

## Success Criteria

### Data Accuracy
- ✅ All multi-day trips show departure dates (not return dates)
- ✅ Source website spot-checks: 100% match (10/10 trips)
- ✅ Edge cases validated: 1/2 day, overnight, 5-day trips correct
- ✅ No data loss: All trips and catches preserved

### Display Correctness
- ✅ Dashboard shows correct dates (no timezone offset)
- ✅ Polaris Supreme example: 10-10 source → 10-10 display (currently shows 10-09)
- ✅ Date filters work correctly (09/15-10/15 shows all trips in range)

### Scraper Correctness
- ✅ New scrapes use departure date logic
- ✅ Dry-run validation: 3/3 dates produce correct results
- ✅ No parser regressions (landing detection, boat parsing still work)
- ✅ Missing dates re-scraped: Sep 21, Sep 18 captured successfully

### System Health
- ✅ No performance degradation (queries still fast)
- ✅ No duplicate trips created
- ✅ All foreign key constraints maintained
- ✅ Database indexes still functional

---

## Testing Strategy

### Phase 1: Calculation Function (Unit Tests)
```python
def test_calculate_departure_date():
    assert calculate_departure_date('2025-10-10', '2 Day') == '2025-10-08'
    assert calculate_departure_date('2025-10-08', '5 Day') == '2025-10-03'
    assert calculate_departure_date('2025-09-24', '3 Day') == '2025-09-21'
    assert calculate_departure_date('2025-10-10', '1/2 Day AM') == '2025-10-10'
    assert calculate_departure_date('2025-10-10', 'Overnight') == '2025-10-09'
```

### Phase 2: Migration Script (Integration Tests)
- Test on single boat (Polaris Supreme) first
- Verify all 6 trips update correctly
- Check catches still linked properly
- Validate no duplicates created

### Phase 3: Full Migration (Production Tests)
- Dry-run on full database
- Compare output against manual calculations
- Verify backup can restore original state
- Execute with full audit logging

### Phase 4: Scraper Updates (End-to-End Tests)
- Dry-run on Sep 21 (known missing date)
- Compare against corrected database values
- Verify new trips use departure dates
- Re-scrape missing dates (Sep 21, 18)

---

## Documentation Requirements

### Validation Reports
- `pre-migration-validation.md` - Database state before changes
- `migration-execution.md` - Step-by-step execution log
- `post-migration-validation.md` - Database state after changes
- `spot-check-results.md` - Manual verification of 10 trips

### Code Documentation
- `calculate_departure_date()` function with docstring and examples
- Migration script with inline comments explaining logic
- Frontend timezone fix with before/after examples
- Scraper updates with regression test notes

### Handoff Documentation
- Update `specs/005-trip-date-correction/README.md` with full project summary
- Update main CLAUDE.md with lessons learned
- Create troubleshooting guide for future date issues

---

## Lessons from Previous Fixes

### From Seaforth Parser Fix (UPDATE_2025_10_16.md)
- ✅ Spec-driven approach prevents scope creep
- ✅ Comprehensive backups enable safe operations
- ✅ Dry-run testing catches bugs before production
- ✅ Detailed logging aids debugging
- ✅ Validation reports provide confidence

### From Landing Cleanup (landing-cleanup-report.md)
- ✅ User-reported bugs are critical data quality signals
- ✅ Spot-checking source data reveals scraper issues
- ✅ Duplicate detection prevents cascading errors
- ✅ Clean data enables better analytics

### Applied to This Project
- Start with comprehensive specification
- Build validation at every step
- Test on small dataset before full migration
- Maintain complete audit trail
- Document everything for future reference

---

## Sign-Off

**Constitution Author**: Claude Code
**Date**: October 16, 2025
**Version**: 1.0.0
**Status**: DRAFT - Pending User Approval

**User Approval**: _________________ (Date: _________)

Once approved, this constitution governs ALL work on the Trip Date Correction project.
