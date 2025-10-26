# Incoming Team Checklist - SPEC-010 Phase 1+2 Complete

**Date**: October 19, 2025
**Status**: Phase 1 + 2 Complete - Ready for Handoff
**Next Phase**: Execute migration, then Phase 3 or Recovery

---

## 📋 Day 1: Getting Oriented (30 minutes)

### ✅ Read Core Documentation (in order)

- [ ] **1. Read this checklist** (you are here - 5 min)
- [ ] **2. Read `SESSION-2025-10-19-SPEC-010-PHASE-1-2.md`** (executive summary - 10 min)
- [ ] **3. Read `HANDOFF.md`** (comprehensive guide - 15 min)
- [ ] **4. Skim `specs/010-pipeline-hardening/IMPLEMENTATION_LOG.md`** (reference as needed)

### ✅ Understand What's Complete

- [ ] **Phase 1**: FR-001, FR-002, FR-003 (100% complete, tested, deployed)
- [ ] **Phase 2**: FR-004, FR-005 (100% code complete, 1 migration pending)
- [ ] **Tests**: 8/8 passed (no failures)
- [ ] **Code**: boats_scraper.py updated (+480 lines)

### ✅ Understand What's Pending

- [ ] **FR-005 Migration**: trip_hash column (30 seconds to execute)
- [ ] **Recovery Scrape**: 10/18 missing (~17 trips expected)
- [ ] **Cleanup**: Delete 18 phantom trips from 10/19, 10/20
- [ ] **Phase 3**: FR-006 (Auto-QC) + FR-008 (Cleanup tool)
- [ ] **Phase 4**: Final validation

---

## 🚀 Day 1: Execute FR-005 Migration (30 seconds)

### ✅ Database Migration

- [ ] **1. Open Supabase SQL Editor**:
  ```
  https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq/sql/new
  ```

- [ ] **2. Copy migration SQL**:
  ```
  File: specs/010-pipeline-hardening/migration_010_trip_hash.sql
  Lines: 1-77 (full migration)
  ```

- [ ] **3. Execute migration** (click "Run" button)

- [ ] **4. Verify column exists**:
  ```sql
  SELECT column_name, data_type FROM information_schema.columns
  WHERE table_name = 'trips' AND column_name = 'trip_hash';

  -- Expected: 1 row (trip_hash | character varying)
  ```

- [ ] **5. Verify index exists**:
  ```sql
  SELECT indexname FROM pg_indexes
  WHERE tablename = 'trips' AND indexname = 'idx_trips_hash';

  -- Expected: 1 row (idx_trips_hash)
  ```

### ✅ Verification

- [ ] **Migration succeeded** (no errors in SQL Editor)
- [ ] **Column exists** (verification query returned 1 row)
- [ ] **Index exists** (verification query returned 1 row)

---

## 🧪 Day 1: Test Complete System (5 minutes)

### ✅ Test All Safeguards

- [ ] **1. Test normal operation**:
  ```bash
  python3 scripts/python/boats_scraper.py --start-date 2025-10-17 --end-date 2025-10-17 --dry-run
  ```
  **Expected**: Parses 16 trips, no errors, all safeguards working

- [ ] **2. Test early scraping guard** (only if before 5pm PT):
  ```bash
  python3 scripts/python/boats_scraper.py --start-date 2025-10-19 --end-date 2025-10-19 --dry-run
  ```
  **Expected**: Blocks with "Scraping today's data before 17:00 PT" error

- [ ] **3. Test future date guard**:
  ```bash
  python3 scripts/python/boats_scraper.py --start-date 2025-10-25 --end-date 2025-10-25 --dry-run
  ```
  **Expected**: Blocks with "end_date is N days in the future" error

### ✅ Verification

- [ ] **All tests passed** (expected errors occurred)
- [ ] **No regressions** (existing functionality working)
- [ ] **Safeguards active** (blocks as expected)

---

## 🔧 Day 1-2: Recovery Operations (2-4 hours)

### ✅ Scrape Missing 10/18 Date

- [ ] **1. Scrape 10/18**:
  ```bash
  python3 scripts/python/boats_scraper.py --start-date 2025-10-18 --end-date 2025-10-18 \
    --operator "Recovery Team - [Your Name]"
  ```
  **Expected**: ~17 trips inserted

- [ ] **2. Verify scrape_job created**:
  ```sql
  SELECT id, operator, dates_processed, trips_inserted, job_status
  FROM scrape_jobs
  ORDER BY job_started_at DESC
  LIMIT 1;

  -- Expected: 1 row with SUCCESS status
  ```

- [ ] **3. Verify trips inserted**:
  ```sql
  SELECT COUNT(*) FROM trips WHERE trip_date = '2025-10-18';

  -- Expected: ~17 trips
  ```

- [ ] **4. Run QC validation**:
  ```bash
  python3 scripts/python/qc_validator.py --date 2025-10-18 --output qc_10_18_recovery.json
  ```
  **Expected**: PASS (100% match)

### ✅ Delete Phantom Trips (Pending Phase 3 Tool)

**Note**: Wait for Phase 3 `delete_date_range.py` tool for safe deletion

**Manual deletion** (if urgent):
- [ ] **1. Backup phantom trips**:
  ```sql
  -- Save to file before deleting
  SELECT * FROM trips WHERE trip_date IN ('2025-10-19', '2025-10-20');
  ```

- [ ] **2. Count phantom trips**:
  ```sql
  SELECT trip_date, COUNT(*) FROM trips
  WHERE trip_date IN ('2025-10-19', '2025-10-20')
  GROUP BY trip_date;

  -- Expected: 10/19: 9 trips, 10/20: 9 trips (18 total)
  ```

- [ ] **3. Delete phantom trips** (use with caution):
  ```sql
  -- Delete catches first (foreign key)
  DELETE FROM catches WHERE trip_id IN (
    SELECT id FROM trips WHERE trip_date IN ('2025-10-19', '2025-10-20')
  );

  -- Delete trips
  DELETE FROM trips WHERE trip_date IN ('2025-10-19', '2025-10-20');
  ```

- [ ] **4. Verify deletion**:
  ```sql
  SELECT COUNT(*) FROM trips WHERE trip_date IN ('2025-10-19', '2025-10-20');

  -- Expected: 0 trips
  ```

### ✅ Verification

- [ ] **10/18 scraped** (~17 trips)
- [ ] **10/18 QC passed** (100% match)
- [ ] **Phantom trips deleted** (18 trips removed)
- [ ] **Audit trail** (scrape_job created for 10/18)

---

## 📋 Day 3-4: Phase 3 Implementation (4-6 hours)

### ✅ FR-006: Automated QC Integration

- [ ] **1. Design**:
  - Integrate `qc_validator.py` into `scrape_date_range()` loop
  - Call QC after each date processed
  - Add `--auto-qc` CLI flag

- [ ] **2. Implement**:
  - Add `run_qc_validation(date)` function
  - Update `scrape_date_range()` to call QC
  - Add `--qc-abort-on-fail` flag for strict mode

- [ ] **3. Test**:
  - Test with known-good date (should pass)
  - Test with known-bad date (should fail and abort)
  - Verify QC results logged in scrape_jobs

### ✅ FR-008: Safe Cleanup Tool

- [ ] **1. Design**:
  - Create `delete_date_range.py` script
  - Features: dry-run, backup to JSON, transaction-safe

- [ ] **2. Implement**:
  - `--start-date`, `--end-date`, `--operator`, `--reason` args
  - `--dry-run` mode (show what would be deleted)
  - Backup to JSON before deletion
  - Audit logging integration

- [ ] **3. Test**:
  - Dry-run mode (no actual deletion)
  - Real deletion with backup
  - Verify rollback capability

---

## ✅ Day 5: Phase 4 Final Validation (2-4 hours)

### ✅ Comprehensive Validation

- [ ] **1. Verify 10/18 complete**:
  ```bash
  python3 scripts/python/qc_validator.py --date 2025-10-18
  ```
  **Expected**: PASS

- [ ] **2. Verify no phantom trips**:
  ```sql
  SELECT COUNT(*) FROM trips WHERE trip_date IN ('2025-10-19', '2025-10-20');
  ```
  **Expected**: 0 trips

- [ ] **3. Run comprehensive QC**:
  ```bash
  python3 scripts/python/qc_validator.py --start-date 2025-10-15 --end-date 2025-10-20 \
    --output qc_final_validation.json
  ```
  **Expected**: 100% pass rate

- [ ] **4. Verify audit trail**:
  ```sql
  SELECT COUNT(*) FROM scrape_jobs;
  SELECT COUNT(*) FROM trips WHERE scrape_job_id IS NOT NULL;
  ```
  **Expected**: All new trips linked to scrape_jobs

### ✅ Documentation Updates

- [ ] **Update IMPLEMENTATION_LOG.md** (Phase 3+4 entries)
- [ ] **Update HANDOFF.md** (Phase 3+4 complete status)
- [ ] **Update README.md** (Phase 3+4 checkboxes)

### ✅ Production Deployment

- [ ] **Commit Phase 1+2+3+4 changes** (git commit)
- [ ] **Update CLAUDE_OPERATING_GUIDE.md** (new safeguards documented)
- [ ] **Sign-off on production readiness**

---

## 📚 Reference: File Locations

### Core Documentation
- `/Users/btsukada/Desktop/Fishing/fish-scraper/HANDOFF.md`
- `/Users/btsukada/Desktop/Fishing/fish-scraper/SESSION-2025-10-19-SPEC-010-PHASE-1-2.md`

### SPEC-010 Files
- `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/010-pipeline-hardening/spec.md`
- `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/010-pipeline-hardening/README.md`
- `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/010-pipeline-hardening/IMPLEMENTATION_LOG.md`

### Migrations
- `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/010-pipeline-hardening/migration_010_scrape_jobs.sql` (executed)
- `/Users/btsukada/Desktop/Fishing/fish-scraper/specs/010-pipeline-hardening/migration_010_trip_hash.sql` (pending)

### Code
- `/Users/btsukada/Desktop/Fishing/fish-scraper/boats_scraper.py` (Phase 1+2 code)
- `/Users/btsukada/Desktop/Fishing/fish-scraper/qc_validator.py` (for QC integration)

---

## 🆘 Troubleshooting

### Migration Fails
- **Issue**: SQL syntax error
- **Solution**: Check migration file syntax, ensure no inline comments in critical sections

### Tests Fail
- **Issue**: Safeguards not blocking as expected
- **Solution**: Check current Pacific Time, verify migration executed, check logs

### Recovery Scrape Fails
- **Issue**: Duplicate trips detected
- **Solution**: Check if 10/18 already scraped, use `--dry-run` first to verify

### Need Help
- **Documentation**: See HANDOFF.md for detailed troubleshooting
- **Logs**: Check boats_scraper.log for error messages
- **Database**: Query scrape_jobs table for audit trail

---

## ✅ Completion Criteria

### Phase 1+2 Handoff Complete When:
- [x] FR-005 migration executed (trip_hash column exists)
- [x] All tests passed (8/8)
- [x] 10/18 recovery scrape complete (~17 trips)
- [x] Phantom trips deleted (18 trips removed)
- [x] Documentation reviewed and understood

### Phase 3 Complete When:
- [ ] FR-006: Auto-QC integrated and tested
- [ ] FR-008: delete_date_range.py created and tested
- [ ] Documentation updated

### Phase 4 Complete When:
- [ ] Comprehensive QC validation passed (100%)
- [ ] All audit trail verified
- [ ] Production deployment approved

---

**Start Here**: Execute FR-005 migration, then test system, then recovery scrape.

**Questions?**: See HANDOFF.md or SESSION-2025-10-19-SPEC-010-PHASE-1-2.md

**Good luck!** 🚀
