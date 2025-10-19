# SPEC-009: Continuous Data Quality Auditor

**Status**: ✅ PRODUCTION READY
**Version**: 1.0.0
**Date**: October 18, 2025
**Purpose**: Proactive random spot-checking to detect phantom/misattributed trips before they corrupt analytics

---

## 🎯 Overview

Following the SPEC-008 remediation of 115 corrupted trips (91.4% phantoms), this auditor provides **continuous quality monitoring** through randomized sampling and validation.

### What It Does

✅ **Random Sampling**: Stratified selection across landings, boats, and dates
✅ **Multi-Level Validation**: Existence, field accuracy, and anomaly detection
✅ **Evidence Capture**: Complete audit trail with source snapshots
✅ **Actionable Reports**: Clear remediation recommendations
✅ **Alert System**: Automatic warnings when QC confidence degrades

### What It Does NOT Do

❌ Automatic deletion/correction (requires human approval)
❌ Replace SPEC-006 QC validator (complementary systems)
❌ Monitor non-trip data (boats, landings, species tables)

---

## 🚀 Quick Start

### Basic Usage

```bash
# Audit 50 trips from last 30 days (default)
python3 data_auditor.py

# Custom sample size and date range
python3 data_auditor.py --sample-size 100 --date-range 60

# Smaller test run
python3 data_auditor.py --sample-size 10 --date-range 7
```

### Output

After running, you'll see:

```
✅ Audit complete!
Report: specs/009-continuous-data-audit/audit_reports/2025-10-18_audit_report.md

Quick Summary:
  ✅ VALID: 48
  🔴 PHANTOM: 1
  🟡 MISATTRIBUTED: 1
```

---

## 📊 Understanding Reports

### Report Structure

Each audit generates two files:

1. **`YYYY-MM-DD_audit_report.md`** - Human-readable summary
2. **`YYYY-MM-DD_audit_results.json`** - Machine-readable details

### Category Definitions

| Category | Meaning | Action Required |
|----------|---------|-----------------|
| ✅ **VALID** | Trip matches source exactly | None |
| 🔴 **PHANTOM** | Trip doesn't exist in source | DELETE (after approval) |
| 🟡 **MISATTRIBUTED** | Trip exists but on wrong boat | UPDATE boat_id (after investigation) |
| 🟠 **PARTIAL** | Trip exists with minor field mismatches | Manual review |
| 🔵 **DUPLICATE** | Duplicate trip entry | DELETE duplicate |
| ⚪ **STATISTICAL_OUTLIER** | Unusual metrics (e.g., >100 anglers) | Manual review |
| ⚫ **VALIDATION_FAILED** | Source unavailable during validation | Retry later |

### QC Confidence Score

```
QC Confidence = (VALID trips / Total trips) × 100%
```

**Target**: ≥99.5%
**Alert Threshold**: <99.5% triggers investigation
**Critical**: <95% indicates systemic data quality issues

---

## 🔍 Sample Report Walkthrough

```markdown
# Data Auditor Report – 2025-10-18

## Executive Summary
- **Sample Size**: 50 trips
- **Date Range**: 2025-09-18 to 2025-10-18 (last 30 days)
- **Landings Covered**: 8 landings
- **Boats Covered**: 15 boats

## Findings Summary
| Category | Count | % of Sample | Severity |
|----------|-------|-------------|----------|
| ✅ VALID | 48 | 96.0% | NONE |
| 🔴 PHANTOM | 1 | 2.0% | CRITICAL |
| 🟡 MISATTRIBUTED | 1 | 2.0% | HIGH |

## QC Confidence Score: 96.0%
⚠️ **ALERT**: QC confidence below 99.5% target. Immediate investigation required.

## Critical Findings Requiring Immediate Action

### PHANTOM Trip Detected
**Trip ID 12345** - 2025-10-15, New Seaforth, 1/2 Day AM, 18 anglers
- **Issue**: Trip does not exist on source page
- **Evidence**: `evidence/trip_12345_evidence.json`
- **Recommendation**: DELETE after manual verification
- **Confidence**: HIGH

## Remediation Action Plan

### Immediate Actions (Require Approval)
```sql
-- PHANTOM deletion
BEGIN TRANSACTION;
DELETE FROM catches WHERE trip_id = 12345;
DELETE FROM trips WHERE id = 12345;
COMMIT;
```
```

---

## 🔬 Evidence Files

For each non-VALID trip, detailed evidence is saved in `evidence/trip_{id}_evidence.json`:

```json
{
  "trip_id": 12345,
  "category": "PHANTOM",
  "severity": "CRITICAL",
  "database_record": {
    "boat_name": "New Seaforth",
    "trip_date": "2025-10-15",
    "anglers": 18,
    "catches": [...]
  },
  "source_verification": {
    "source_url": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-15",
    "boats_found_on_date": ["Premier", "Daily Double", "Mission Belle"],
    "validation_status": "PASS"
  },
  "validation_results": {
    "level_1_exists": false,
    "in_extra_boats": true
  },
  "recommendation": {
    "action": "DELETE",
    "confidence": "HIGH",
    "reasoning": "Trip exists in database but not found on source page (extra boat)"
  }
}
```

---

## 🛠️ Remediation Workflow

### Step 1: Review Findings

```bash
# Read the audit report
cat specs/009-continuous-data-audit/audit_reports/2025-10-18_audit_report.md

# Check detailed evidence for non-VALID trips
cat specs/009-continuous-data-audit/evidence/trip_12345_evidence.json | jq '.'
```

### Step 2: Verify Evidence

For PHANTOM trips:
1. Open the source URL from evidence
2. Manually verify trip does NOT exist
3. Check if it might be on a different date (date-shifted)

For MISATTRIBUTED trips:
1. Check if trip exists on a different boat
2. Identify correct boat_id
3. Verify field matches

### Step 3: Execute Approved Actions

⚠️ **CRITICAL**: Only proceed with deletions/updates after manual verification

```sql
-- Create backup snapshot first (similar to SPEC-008)
BEGIN TRANSACTION;

-- Execute approved deletions
DELETE FROM catches WHERE trip_id IN (12345, 12346);
DELETE FROM trips WHERE id IN (12345, 12346);

-- Verify deletion count
SELECT COUNT(*) FROM trips WHERE id IN (12345, 12346);
-- Expected: 0

COMMIT;
```

### Step 4: Post-Remediation Validation

```bash
# Re-run auditor to verify fixes
python3 data_auditor.py --sample-size 20 --date-range 30

# Should show improved QC confidence
```

---

## 📅 Automated Monitoring (Optional)

### Daily Cron Job

```bash
# Edit crontab
crontab -e

# Add daily audit at 2 AM
0 2 * * * cd /Users/btsukada/Desktop/Fishing/fish-scraper && python3 data_auditor.py --sample-size 50 --date-range 30 >> data_auditor_cron.log 2>&1
```

### Weekly Summary Script

Create `weekly_audit_summary.sh`:

```bash
#!/bin/bash
# Generate weekly audit summary

AUDIT_DIR="specs/009-continuous-data-audit/audit_reports"
WEEK_AGO=$(date -v-7d +%Y-%m-%d)

echo "=== Weekly Data Quality Summary ==="
echo "Date Range: Last 7 days"
echo ""

# Count findings by category
grep "QC Confidence" $AUDIT_DIR/*_audit_report.md | \
  awk -F': ' '{sum+=$2; count++} END {print "Average QC Confidence: " sum/count "%"}'

echo ""
grep "PHANTOM" $AUDIT_DIR/*_audit_report.md | wc -l | \
  xargs echo "Total PHANTOM trips detected:"

grep "MISATTRIBUTED" $AUDIT_DIR/*_audit_report.md | wc -l | \
  xargs echo "Total MISATTRIBUTED trips detected:"
```

---

## 🔧 Configuration

Edit `audit_config.yaml` (optional, uses defaults if missing):

```yaml
sampling:
  date_range_days: 30        # Sample from last N days
  sample_size: 50            # Total trips to audit
  stratified: true           # Ensure landing/boat diversity
  min_boats_per_landing: 2   # Minimum boats per landing

validation:
  anglers_tolerance: 1                # ±1 angler acceptable
  catch_count_tolerance_pct: 5        # ±5% catch variance acceptable
  enable_statistical_outlier_detection: true
  z_score_threshold: 3.0              # Statistical outlier threshold

reporting:
  output_dir: "specs/009-continuous-data-audit/audit_reports/"
  evidence_dir: "specs/009-continuous-data-audit/evidence/"
  generate_screenshots: false         # Set true for visual evidence
  alert_on_qc_below: 99.5            # Alert threshold %
```

---

## 📈 Performance Metrics

**Target Metrics** (after 30 days of operation):

✅ QC confidence score: >99.5%
✅ False positive rate: <0.5%
✅ Phantom trip detection: >90% accuracy
✅ 100% coverage: All trips audited once per 90 days

**Operational Metrics**:

- Audit runtime: <5 minutes for 50 trips
- Source fetch: <2 seconds per page (with caching)
- Memory usage: <500MB during execution

---

## 🚨 Alerts & Troubleshooting

### Alert: QC Confidence <99.5%

**Action**:
1. Review audit report immediately
2. Check if findings are legitimate issues or false positives
3. Investigate date range - recent scraping issues?
4. Run targeted QC validation on flagged dates

### Alert: >5 PHANTOM Trips Detected

**Action**:
1. **CRITICAL** - Potential scraper malfunction
2. Check recent scraper logs for errors
3. Validate against source manually
4. Do NOT delete until verified

### Alert: High MISATTRIBUTION Rate

**Action**:
1. Check for landing name changes (boats moving between landings)
2. Verify boat name parsing in scraper
3. Review recent SPEC-007 type issues

---

## 🔄 Integration with SPEC-006 QC Validator

**Complementary Systems**:

| Feature | SPEC-006 QC Validator | SPEC-009 Data Auditor |
|---------|----------------------|----------------------|
| **Scope** | Validate specific dates on-demand | Random sampling of recent trips |
| **Frequency** | Ad-hoc (post-scrape) | Daily automated runs |
| **Coverage** | 100% of targeted range | 5-10% random sample |
| **Purpose** | Verify scraping accuracy immediately | Detect drift/corruption over time |
| **Action** | Block bad scrapes, fix | Report anomalies for review |

**Best Practice**:
- Use **SPEC-006** immediately after scraping new data
- Use **SPEC-009** for continuous monitoring of historical data
- Both systems work together for comprehensive QA

---

## 📚 Related Documentation

- **SPEC-006**: QC Validator (field-level validation)
- **SPEC-008**: Phantom Trip Investigation (remediation procedures)
- **COMPREHENSIVE_QC_VERIFICATION.md**: Master QC validation report
- **CLAUDE_OPERATING_GUIDE.md**: Operational procedures

---

## 🧪 Testing

```bash
# Quick test (5 trips, 7 days)
python3 data_auditor.py --sample-size 5 --date-range 7

# Expected output:
# ✅ Audit complete!
# QC Confidence: ~95-100%
# VALID: 4-5/5

# Full test (50 trips, 30 days)
python3 data_auditor.py --sample-size 50 --date-range 30

# Expected runtime: <5 minutes
# Expected QC confidence: >99%
```

---

## 🎯 Success Criteria

**After 30 days of operation, the system should demonstrate**:

✅ **Quality Metrics**:
- QC confidence score: >99.5%
- False positive rate: <0.5%
- Phantom detection accuracy: >90%

✅ **Coverage Metrics**:
- 100% of trips audited at least once per 90 days
- All active landings covered weekly
- All active boats covered every 2 weeks

✅ **Operational Metrics**:
- Daily audit success rate: >95%
- Mean audit runtime: <5 minutes
- Alert response time: <4 hours for critical findings

---

## 📞 Support

**For questions or issues**:
1. Check audit report evidence files
2. Review SPEC-009 specification document
3. Consult CLAUDE_OPERATING_GUIDE.md for operational procedures
4. Review SPEC-008 for similar remediation workflows

---

**Last Updated**: October 18, 2025
**Maintained By**: Fishing Intelligence Platform
**Version**: 1.0.0 (Production Ready)
