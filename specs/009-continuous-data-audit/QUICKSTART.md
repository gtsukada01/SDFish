# Data Auditor Agent - Quick Start Guide

**Status**: ✅ READY TO USE
**Created**: October 18, 2025
**Location**: `/Users/btsukada/Desktop/Fishing/fish-scraper/`

---

## 🎯 What Is This?

A **continuous quality monitoring system** that randomly spot-checks your fishing trip database to detect phantom/misattributed entries BEFORE they corrupt your analytics.

**Triggered By**: SPEC-008 remediation (115 corrupted trips = 91.4% phantoms)
**Purpose**: Prevent future data corruption through proactive monitoring

---

## 🚀 Run Your First Audit (30 seconds)

```bash
cd /Users/btsukada/Desktop/Fishing/fish-scraper

# Quick test (5 trips, last 7 days)
python3 scripts/python/data_auditor.py --sample-size 5 --date-range 7
```

**Expected Output**:
```
✅ Audit complete!
Report: specs/009-continuous-data-audit/audit_reports/2025-10-18_audit_report.md

Quick Summary:
  ✅ VALID: 4
  🟡 MISATTRIBUTED: 1
```

---

## 📊 Check the Report

```bash
# Read human-friendly report
cat specs/009-continuous-data-audit/audit_reports/2025-10-18_audit_report.md

# Check QC confidence score
grep "QC Confidence" specs/009-continuous-data-audit/audit_reports/2025-10-18_audit_report.md
```

**What to Look For**:
- **QC Confidence ≥99.5%**: Database is healthy ✅
- **QC Confidence <99.5%**: Investigation needed ⚠️
- **PHANTOM trips detected**: Delete after verification 🔴
- **MISATTRIBUTED trips**: Update boat_id after investigation 🟡

---

## 🔍 Investigate Findings

```bash
# List all evidence files
ls specs/009-continuous-data-audit/evidence/

# Check specific trip evidence
cat specs/009-continuous-data-audit/evidence/trip_12345_evidence.json | jq '.'
```

**Evidence Shows**:
- Database record (what your DB says)
- Source verification (what source page says)
- Category (VALID, PHANTOM, MISATTRIBUTED, etc.)
- Recommended action (NONE, DELETE, INVESTIGATE)
- Confidence level (HIGH, MEDIUM, LOW)

---

## ⚙️ Production Usage

### Daily Audits (Recommended)

```bash
# Audit 50 trips from last 30 days
python3 scripts/python/data_auditor.py --sample-size 50 --date-range 30

# Runtime: ~5 minutes
# Recommended frequency: Daily
```

### Weekly Full Scans

```bash
# Audit 100 trips from last 60 days
python3 scripts/python/data_auditor.py --sample-size 100 --date-range 60

# Runtime: ~10 minutes
# Recommended frequency: Weekly
```

### Automated Monitoring (Set & Forget)

```bash
# Set up daily cron job (runs at 2 AM)
crontab -e

# Add this line:
0 2 * * * cd /Users/btsukada/Desktop/Fishing/fish-scraper && python3 scripts/python/data_auditor.py --sample-size 50 --date-range 30 >> data_auditor_cron.log 2>&1
```

---

## 🚨 Alert Responses

### Alert: QC Confidence <99.5%

```bash
# 1. Read the report
cat specs/009-continuous-data-audit/audit_reports/YYYY-MM-DD_audit_report.md

# 2. Check findings section
# 3. Verify evidence for each flagged trip
# 4. Take action based on category (see below)
```

### Action for PHANTOM Trips

```sql
-- ⚠️ VERIFY MANUALLY FIRST!
-- 1. Open source URL from evidence file
-- 2. Confirm trip does NOT exist
-- 3. Then execute:

BEGIN TRANSACTION;
DELETE FROM catches WHERE trip_id = 12345;
DELETE FROM trips WHERE id = 12345;
-- Verify: SELECT COUNT(*) FROM trips WHERE id = 12345; -- Expected: 0
COMMIT;
```

### Action for MISATTRIBUTED Trips

```sql
-- ⚠️ INVESTIGATE FIRST!
-- 1. Find correct boat from evidence
-- 2. Look up correct boat_id in boats table
-- 3. Then execute:

BEGIN TRANSACTION;
UPDATE trips SET boat_id = 65 WHERE id = 12346;  -- Example: correcting to "New Seaforth"
-- Verify: SELECT boat_id FROM trips WHERE id = 12346; -- Expected: 65
COMMIT;
```

---

## 📈 Monitoring Dashboard (Weekly Check)

```bash
# Check last 7 days of audits
grep "QC Confidence" specs/009-continuous-data-audit/audit_reports/*.md

# Count total findings
grep "PHANTOM" specs/009-continuous-data-audit/audit_reports/*.md | wc -l
grep "MISATTRIBUTED" specs/009-continuous-data-audit/audit_reports/*.md | wc -l

# Show trend
ls -lt specs/009-continuous-data-audit/audit_reports/ | head -10
```

---

## 🎯 Success Metrics

**After 30 days, you should see**:

✅ QC Confidence consistently >99.5%
✅ <1 PHANTOM trip per week (ideally 0)
✅ <2 MISATTRIBUTED trips per week
✅ All findings resolved within 48 hours

**If NOT meeting targets**:
1. Check scraper logs for errors
2. Verify SPEC-006 QC validation running post-scrape
3. Review parser logic for drift
4. Consider re-running SPEC-008 style investigation

---

## 📚 Full Documentation

- **README.md**: Complete guide, configuration, troubleshooting
- **spec.md**: Technical specification with requirements
- **SPEC-008**: Remediation procedures (if you find issues)
- **SPEC-006**: QC validator (complementary system)

---

## 🔧 Troubleshooting

### "No trips found in date range"
```bash
# Check database connectivity
python3 -c "from boats_scraper import init_supabase; s=init_supabase(); print(s.table('trips').select('count').execute())"

# Try shorter date range
python3 scripts/python/data_auditor.py --sample-size 5 --date-range 3
```

### "Source unavailable" errors
```bash
# Check internet connectivity
curl https://www.sandiegofishreports.com/dock_totals/boats.php?date=$(date +%Y-%m-%d)

# Retry with longer timeout (add to script if needed)
```

### High false positive rate (VALID trips flagged)
```bash
# Check validation logic in evidence files
cat specs/009-continuous-data-audit/evidence/trip_*.json | jq '.validation_results'

# May indicate parser drift - consult SPEC-006
```

---

## 💡 Pro Tips

1. **Run after scraping**: Always audit after adding new data
2. **Stratified sampling**: Default settings ensure good coverage
3. **Evidence is key**: Always check evidence before deleting
4. **Trend monitoring**: Watch QC confidence over time
5. **Integration**: Use with SPEC-006 for comprehensive QA

---

## 🎬 Next Steps

1. ✅ Run your first audit (see "Run Your First Audit" above)
2. ✅ Review the report
3. ✅ Check evidence for any non-VALID trips
4. ✅ Set up daily cron job (optional but recommended)
5. ✅ Monitor QC confidence weekly

**Questions?** Check README.md or spec.md for detailed documentation.

---

**Created**: October 18, 2025
**Version**: 1.0.0
**Status**: ✅ PRODUCTION READY
