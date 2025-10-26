# Documentation Standards & Guidelines

**Purpose**: Maintain single source of truth, prevent documentation sprawl, ensure audit trail continuity

**Last Updated**: October 17, 2025
**Status**: ACTIVE - All contributors must follow these standards

---

## Core Principles

### 1. Single Source of Truth
- **README.md** is the ONLY entry point for project status
- All other documents are LINKED from README, never duplicated
- Stats, metrics, and status updates appear in ONE place only

### 2. Consolidation Over Creation
- **DO NOT** create new monthly/batch .md files
- **DO** update existing annual reports (2024_SCRAPING_REPORT.md, 2025_SCRAPING_REPORT.md)
- **DO** append new months/issues to master documents
- **ONLY** create new docs when absolutely required by compliance or new major initiatives

### 3. Context Continuity
- **PREFER** updating over deleting
- **ARCHIVE** superseded docs (don't delete)
- **MIGRATE** data from old docs to consolidated reports before archiving
- **PRESERVE** historical context even when consolidating

### 4. Audit Trail Compliance
- **UPDATE** DOC_CHANGELOG.md for every documentation change
- **DOCUMENT** accepted issues/exceptions in appendices
- **TRACK** all QC results in master verification reports
- **MAINTAIN** clear version history

---

## File Structure Rules

### Master Documents (Never Delete)
```
README.md                           # Single source of truth - ALWAYS current
COMPREHENSIVE_QC_VERIFICATION.md    # Master QC validation report
2024_SCRAPING_REPORT.md            # 2024 consolidated annual report
2025_SCRAPING_REPORT.md            # 2025 consolidated annual report
DOC_CHANGELOG.md                    # Audit trail for all doc changes
DOCUMENTATION_STANDARDS.md          # This file - governance rules
```

### Reference Documents (Update as Needed)
```
2024_SCRAPING_PROGRESS.md          # Detailed 2024 tracking
FINAL_VALIDATION_REPORT.md         # SPEC 006 technical validation
SPEC_006_SUMMARY.md                # SPEC 006 overview
```

### Archive Folder (Historical Preservation)
```
archive/
├── JUNE_JULY_2024_COMPLETE.md     # Superseded by 2024_SCRAPING_REPORT.md
├── AUGUST_SEPTEMBER_2024_COMPLETE.md
├── APRIL_2025_COMPLETION_SUMMARY.md
└── ... (other superseded monthly reports)
```

---

## Update Workflows

### When a New Month Completes

**❌ DO NOT:**
```
# Create new file
touch NOVEMBER_2025_COMPLETION.md  # WRONG!
```

**✅ DO:**
```markdown
# Update 2025_SCRAPING_REPORT.md
1. Add November to monthly breakdown table
2. Update overall statistics
3. Document any issues in Known Issues appendix
4. Update QC validation section

# Update README.md
1. Update total trip count
2. Update completion percentage
3. Update "Last Updated" timestamp

# Update DOC_CHANGELOG.md
1. Add entry for November completion
2. List all files modified
3. Note any new QC issues
```

### When QC Issues Found

**Example: New accepted issue like August 7 Dolphin boat**

**✅ Process:**
1. Document in `COMPREHENSIVE_QC_VERIFICATION.md` → Known Issues Appendix
2. Update README.md QC pass rate if needed
3. Add entry to `DOC_CHANGELOG.md`
4. Update annual report (2025_SCRAPING_REPORT.md) with issue details

---

## Template: README.md Future Updates

### Sample Monthly Update (November 2025)
```markdown
## 🎉 MILESTONE ACHIEVED - 100% COMPLETE (Nov 17, 2025)

**DATABASE COVERAGE VERIFIED**:
- ✅ **2024 Backfill**: 100% COMPLETE - 366/366 dates, 4,203 trips
- ✅ **2025 Jan-Nov**: 100% COMPLETE - 335/335 dates, 4,200 trips
  - [Previous months unchanged]
  - November: 31 dates (445 trips) ✨ **JUST COMPLETED**

**TOTAL DATABASE**: 8,403 trips across 701 unique dates (100% coverage)

**QC PASS RATE**: 99.86% (700/701 dates passed, 1 accepted issue on Aug 7)
- ⚠️ **Aug 7, 2025**: Dolphin boat species count variance (accepted)
```

---

## Template: Known Issues Appendix

### Known Issues / Accepted Exceptions

**Purpose**: Track all accepted QC issues that don't block production deployment

**Format**:
```markdown
### [Date] - [Boat Name] ([Status])

**Issue**: Brief description
**Impact**: Percentage or trip count affected
**Decision**: Why accepted
**Tracked In**: Which batch QC file

**Example**:

### August 7, 2025 - Dolphin Boat (✅ ACCEPTED)

**Issue**: Species count mismatches on 5 fields
  - Cabezon: source=3, db=1
  - Barracuda: Missing in DB (count=2)
  - Calico Bass: source=48, db=51
  - Rockfish: source=28, db=21
  - Sheephead: Extra in DB (count=1)

**Impact**: 1 trip out of 7,958 total (0.013% error rate)
**Decision**: Accepted as production-ready per stakeholder confirmation
**Tracked In**: qc_august_batch02_2025.json
**Date Logged**: October 17, 2025
```

---

## Template: DOC_CHANGELOG.md Entry

### Standard Changelog Entry Format
```markdown
## YYYY-MM-DD: [Brief Description]

### Changes Made

**Files Created**:
- [filename] - Purpose and content summary

**Files Modified**:
- [filename] - What changed and why
- [filename] - Specific updates

**Files Archived**:
- [filename] → archive/[filename] - Why superseded

### Rationale
Brief explanation of why these changes were necessary

### Impact
- Documentation hierarchy updated
- Single source of truth maintained
- Audit trail preserved

### Files Affected Summary
**Created**: N files
**Modified**: N files
**Archived**: N files

---
```

---

## Template: Annual Report Structure

### Master Annual Report Template (e.g., 2026_SCRAPING_REPORT.md)

```markdown
# 2026 Scraping - Complete Report

**Status**: [IN PROGRESS | COMPLETE]
**Coverage**: X/Y dates (Z%)
**Last Updated**: [Date]

---

## Executive Summary
[Overall stats, key achievements, gaps]

---

## Monthly Completion Reports

### January 2026
**Status**: [✅ COMPLETE | ⏳ PENDING]
**Dates**: X days
**Trips**: Y trips
**Batches**: Z batches
**QC Pass Rate**: 100%

**Key Details**:
- [Notable achievements or issues]

---

[Repeat for each month]

---

## Known Issues / Accepted Exceptions

### [Date] - [Issue Description]
[Use Known Issues template from above]

---

## QC Validation Summary

**Overall Metrics**:
- Total Dates Validated: X
- QC Pass Rate: Y%
- Field Mismatches: Z
- Accepted Issues: N

**Spotcheck Results**:
- [Date 1]: PASS
- [Date 2]: PASS
- [etc.]

---

## Navigation

**Related Documents**:
- [README.md](README.md) - Single source of truth
- [2025_SCRAPING_REPORT.md](2025_SCRAPING_REPORT.md) - Previous year
- [COMPREHENSIVE_QC_VERIFICATION.md](COMPREHENSIVE_QC_VERIFICATION.md) - QC standards
```

---

## Checklist: Before Creating New Documentation

**Ask yourself these questions FIRST**:

- [ ] Does this information belong in an existing master document?
- [ ] Could this be an appendix to README.md or annual report?
- [ ] Will this file become obsolete in 1-3 months?
- [ ] Am I duplicating information that exists elsewhere?
- [ ] Is there a compelling compliance/audit reason for a separate file?

**If YES to any of first 4 questions**: DO NOT create new file, update existing

**If YES to question 5 only**: Create new file, add to DOC_CHANGELOG.md

---

## Navigation Best Practices

### Every Major Document Should Have:

1. **Header Section**:
```markdown
**Status**: [Current status]
**Last Updated**: [Date]
**Purpose**: [Why this doc exists]
```

2. **Table of Contents** (for docs >200 lines):
```markdown
## 📑 Table of Contents
1. [Section 1](#section-1)
2. [Section 2](#section-2)
```

3. **Navigation Footer**:
```markdown
---

## Navigation

**Related Documents**:
- [README.md](README.md) - Main project documentation
- [Other relevant docs]

**This Document**:
- Purpose: [Brief description]
- Maintained By: [Team/Role]
- Update Frequency: [As needed / Monthly / etc.]
```

---

## Review Schedule

### Monthly Review (1st of each month)
- [ ] Update README.md with previous month completion
- [ ] Update annual report (2025_SCRAPING_REPORT.md)
- [ ] Update COMPREHENSIVE_QC_VERIFICATION.md if new issues
- [ ] Add entry to DOC_CHANGELOG.md
- [ ] Archive any superseded files
- [ ] Verify all navigation links work

### Quarterly Review (Jan 1, Apr 1, Jul 1, Oct 1)
- [ ] Review all master documents for accuracy
- [ ] Consolidate any standalone files created
- [ ] Update DOCUMENTATION_STANDARDS.md if needed
- [ ] Verify archive/ folder is organized
- [ ] Update navigation sections across all docs

### Annual Review (Jan 1)
- [ ] Create new annual report (YYYY_SCRAPING_REPORT.md)
- [ ] Archive previous year's monthly tracking docs
- [ ] Update README.md with new year structure
- [ ] Review and update all templates
- [ ] Conduct full documentation audit

---

## Enforcement

**Before Committing Documentation Changes**:

1. ✅ Verify changes follow these standards
2. ✅ Update DOC_CHANGELOG.md
3. ✅ Update README.md if needed
4. ✅ Test all navigation links
5. ✅ Review for duplicate information
6. ✅ Confirm single source of truth maintained

**On Pull Requests**:
- Documentation changes MUST include DOC_CHANGELOG.md update
- New .md files in root MUST have justification in PR description
- Standalone monthly reports WILL BE REJECTED (use annual reports)

---

## FAQ

**Q: When should I create a new document?**
A: Only when starting a new major initiative (new SPEC, new data source, new compliance requirement) or when required by audit/compliance. Otherwise, update existing docs.

**Q: What if I have a lot of new information for one month?**
A: Add it to the annual report as a detailed subsection. Annual reports can be long - that's fine.

**Q: Where do I track temporary/in-progress work?**
A: Use TODO.md (gitignored) or project management tools. Don't create .md files for temporary status.

**Q: Can I create a new doc for a specific feature or spec?**
A: Yes, if it's a formal SPEC (like SPEC 006). Put in specs/ folder with proper numbering.

**Q: How do I handle QC files (JSON)?**
A: QC JSON files are data, not documentation. They can proliferate as needed. Summarize results in COMPREHENSIVE_QC_VERIFICATION.md.

---

**Document Owner**: Documentation Team
**Approval Required**: Yes, for any changes to this standards document
**Version**: 1.0
**Effective Date**: October 17, 2025

---

## Appendix: Example Consolidation

### Before (Documentation Sprawl)
```
JUNE_2024_COMPLETE.md
JULY_2024_COMPLETE.md
JUNE_JULY_2024_COMPLETE.md
AUGUST_2024_COMPLETE.md
SEPTEMBER_2024_COMPLETE.md
AUGUST_SEPTEMBER_2024_COMPLETE.md
APRIL_2025_COMPLETION_SUMMARY.md
MAY_2025_COMPLETION_REPORT.md
UPDATE_2025_10_15.md
UPDATE_2025_10_16.md
```

### After (Consolidated)
```
2024_SCRAPING_REPORT.md (consolidated all 2024 months)
2025_SCRAPING_REPORT.md (consolidated all 2025 months)
archive/
├── JUNE_JULY_2024_COMPLETE.md
├── AUGUST_SEPTEMBER_2024_COMPLETE.md
├── [all other monthly reports]
```

**Result**: 10 files → 2 master files + archived historical detail
**Benefit**: One place to check 2024 status, one place to check 2025 status
