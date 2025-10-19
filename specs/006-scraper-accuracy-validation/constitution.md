# Constitution v1.0.0: Scraper Accuracy & Data Integrity

**Date**: October 16, 2025
**Project**: 100% Accurate Scraping with Comprehensive QC
**Scope**: All fishing trip data from sandiegofishreports.com

---

## Core Principles

### 1. **Source of Truth: boats.php Page**
- **boats.php is the single source of truth**: `https://www.sandiegofishreports.com/dock_totals/boats.php?date=YYYY-MM-DD`
- **What You See Is What You Get**: Every data point visible on the page must be scraped exactly as shown
- **No Interpretation**: Do not add, modify, or calculate dates/values beyond what's shown
- **Zero Tolerance for Data Drift**: Database must be a perfect 1:1 replica of source

### 2. **Date Semantics Clarity**
- **Define What the Date Parameter Means**: The `?date=YYYY-MM-DD` parameter meaning must be validated before any scraping
- **No Assumptions**: Do not assume the date is departure, return, or report date without verification
- **Test with Known Examples**: Compare 2-3 boats.php dates against charter boat pages to understand date semantics
- **Document Findings**: Create clear documentation of what the date represents

### 3. **Field-Level Accuracy Standards**
- **Landing Name**: Must match exactly (character-for-character)
- **Boat Name**: Must match exactly (no normalization, no variations)
- **Trip Type**: Must match exactly ("1/2 Day AM" ≠ "Half Day AM")
- **Anglers Count**: Must match exactly (numeric precision)
- **Species Names**: Must match exactly (no standardization)
- **Catch Counts**: Must match exactly (numeric precision)

### 4. **Comprehensive QC Process**
- **Pre-Scrape Validation**: Verify source page structure hasn't changed
- **During Scrape**: Log every parsed field with source HTML context
- **Post-Scrape Validation**: Compare database against source page for 100% match
- **Automated QC**: Script that fetches source page and validates every field in database
- **Manual Spot Checks**: Human verification of 5-10 trips per scraping run

### 5. **Zero Failure Tolerance**
- **100% Success Rate Required**: If any trip on a page cannot be parsed, the entire page fails
- **No Silent Failures**: Every parsing error must be logged and reported
- **No Data Gaps**: If a boat is on the source page, it must be in the database
- **No Extra Data**: If a boat is in the database for a date, it must be on the source page

### 6. **Rollback Safety**
- **Backup Before Any Changes**: Complete backup before scraping new data
- **Transactional Scraping**: All trips from a date succeed or all fail (no partial inserts)
- **Validation Before Commit**: Verify data quality before committing to database
- **Rollback Documentation**: Clear procedure to restore from backup if QC fails

---

## Quality Control Standards

### Pre-Scraping Requirements
- [ ] Source page HTML structure validated
- [ ] Date semantics clearly understood and documented
- [ ] Parser logic reviewed and validated on 3 test dates
- [ ] Backup created and verified
- [ ] QC script ready and tested

### During-Scraping Requirements
- [ ] Every landing header detected and logged
- [ ] Every boat parsed and logged with source HTML snippet
- [ ] Every trip field extracted and logged
- [ ] Every species/count parsed and logged
- [ ] Any parsing failures halt the process immediately

### Post-Scraping Requirements
- [ ] QC script compares database against source for every date scraped
- [ ] 100% field-level match confirmed for all trips
- [ ] No missing boats (all boats on source page are in database)
- [ ] No extra boats (no database boats missing from source page)
- [ ] Manual spot check of 5-10 trips confirms accuracy

### QC Failure Response
- **Any mismatch triggers rollback**: Even 1 field mismatch = full rollback
- **Investigation Required**: Understand root cause before retry
- **Fix Confirmed**: Test fix on isolated date before full re-scrape
- **Re-validate**: Run full QC again after fix

---

## Date Semantics Investigation Protocol

Before any scraping, we must understand what `boats.php?date=YYYY-MM-DD` represents.

### Test Cases

**Test 1: Compare boats.php against charter boat page**
- boats.php?date=2025-09-30 shows "Polaris Supreme, 3 Day, 24 anglers"
- polarissupreme.php shows "09-30-2025 | 3 Day Trip | 24 Anglers"
- **Conclusion**: dates.php date matches charter boat report date

**Test 2: Multi-day trip date logic**
- boats.php?date=2025-10-10 shows "Polaris Supreme, 2 Day, 23 anglers"
- polarissupreme.php shows "10-10-2025 | 2 Day Trip | 23 Anglers"
- **Question**: Is 10-10 the departure date or return date?
- **Investigation**: Check if trip appears on earlier dates (10-08, 10-09)

**Test 3: Half-day trip date logic**
- boats.php?date=2025-09-30 shows "Dolphin, 1/2 Day AM, 11 anglers"
- **Expected**: 1/2 Day trips should only appear on departure date (same-day return)
- **Validation**: Confirm trip does not appear on adjacent dates

### Documentation Requirements

After investigation, document:
1. **What does boats.php?date represent?** (departure, return, or report date)
2. **How should multi-day trips be stored?** (as-is, or calculated departure)
3. **How should we handle duplicate checking?** (by what date + boat + trip type)
4. **What is the user expectation?** (when users see "09-30", what do they think it means?)

---

## Implementation Workflow

### Phase 1: Investigation & Validation (REQUIRED FIRST)
1. Run date semantics investigation protocol
2. Document findings in `date-semantics-report.md`
3. Validate parser logic on 3 test dates (1/2 day, 2 day, 5 day trips)
4. Create QC validation script
5. Test QC script on 3 dates to confirm it works

### Phase 2: Parser Verification
1. Review current parser code (boats_scraper.py)
2. Identify any date manipulation logic (REMOVE IT)
3. Ensure parser stores dates exactly as shown on source page
4. Test parser on 3 dates with QC validation
5. Confirm 100% accuracy before proceeding

### Phase 3: Production Scraping
1. Create backup of database
2. Scrape September-October 2025 (61 days)
3. Run QC validation after EVERY date (not batch)
4. Halt on first QC failure and investigate
5. Complete manual spot checks (10 random trips)

### Phase 4: Final Validation
1. Run comprehensive QC across all scraped dates
2. Generate validation report with pass/fail for each date
3. Document any edge cases or anomalies discovered
4. Provide user-facing summary of data accuracy

---

## Risk Mitigation

### Critical Risks

1. **Date Interpretation Error**
   - Risk: Storing wrong dates in database (like we just did)
   - Mitigation: Complete investigation protocol before any scraping
   - Detection: QC script compares dates against source page

2. **Parser Regression**
   - Risk: Code changes break existing parsing logic
   - Mitigation: Test on 3 dates before production
   - Detection: QC script catches field mismatches

3. **Source Page Changes**
   - Risk: Website HTML structure changes mid-scrape
   - Mitigation: Validate HTML structure before each scraping run
   - Detection: Parser fails with clear error message

4. **Incomplete Parsing**
   - Risk: Some boats/trips silently skipped
   - Mitigation: Count boats on page vs. database, must match exactly
   - Detection: QC script reports missing boats

---

## Success Criteria

### Data Accuracy (100% Required)
- ✅ Every boat on source page exists in database
- ✅ Every boat in database for that date exists on source page
- ✅ Every field (landing, boat, trip type, anglers, species, counts) matches exactly
- ✅ No date discrepancies between source and database
- ✅ Manual spot checks confirm accuracy

### QC Process (100% Required)
- ✅ QC script successfully validates all scraped dates
- ✅ Zero field-level mismatches detected
- ✅ Zero missing boats detected
- ✅ Zero extra boats detected
- ✅ Validation report generated with detailed metrics

### Rollback Capability (100% Required)
- ✅ Backup file exists and is valid
- ✅ Rollback procedure documented and tested
- ✅ Can restore database to pre-scrape state in < 5 minutes

---

## Lessons from Previous Failures

### Spec 005 Trip Date Correction (FAILED)
- **What Went Wrong**: Assumed dates needed calculation, subtracted trip duration
- **Result**: Stored dates too early (10-10 became 10-08)
- **Lesson**: Never manipulate source data without validation
- **Prevention**: Always validate date semantics before scraping

### Seaforth Parser Bug (FIXED)
- **What Went Wrong**: Landing header detection failed for certain formats
- **Result**: Missing boats, incorrect boat names
- **Lesson**: Parser must handle all landing header variations
- **Prevention**: Test parser on all known landings before production

### Current State (UNVALIDATED)
- **What We Don't Know**: What boats.php?date actually represents
- **Result**: 1,085 trips deleted, unsure if scraper is correct
- **Lesson**: Must validate assumptions before trusting data
- **Prevention**: Complete investigation protocol (Phase 1)

---

## Sign-Off

**Constitution Author**: Claude Code
**Date**: October 16, 2025
**Version**: 1.0.0
**Status**: DRAFT - Pending User Approval

**User Approval**: _________________ (Date: _________)

Once approved, this constitution governs ALL scraping operations. No data may be scraped without completing the investigation protocol and achieving 100% QC validation.
