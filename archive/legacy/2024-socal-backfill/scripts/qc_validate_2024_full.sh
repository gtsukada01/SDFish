#!/bin/bash

# Comprehensive QC Validation - Full Year 2024 SoCal Data
# =========================================================
# SPEC 006: 100% Accuracy Validation
# Validates all 366 days of 2024 against source pages
#
# Runtime: ~15 minutes (2-second delays between dates)
# Output: 4 quarterly JSON reports + 1 comprehensive summary

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="/Users/btsukada/Desktop/Fishing/fish-scraper"
QC_SCRIPT="${PROJECT_ROOT}/scripts/python/socal_qc_validator.py"
LOGS_DIR="${SCRIPT_DIR}/../logs"
REPORTS_DIR="${SCRIPT_DIR}/../reports"

# Create directories
mkdir -p "${LOGS_DIR}"
mkdir -p "${REPORTS_DIR}"

echo "============================================================================="
echo "🔍 2024 SoCal Data - Comprehensive QC Validation"
echo "============================================================================="
echo "Date: $(date)"
echo "Script: ${QC_SCRIPT}"
echo "Reports: ${REPORTS_DIR}"
echo ""

# ============================================================================
# Q1 2024: January - March (91 days)
# ============================================================================

echo ""
echo "============================================================================="
echo "📊 Q1 2024: Validating January - March (91 days)"
echo "============================================================================="

python3 "${QC_SCRIPT}" \
    --start-date 2024-01-01 \
    --end-date 2024-03-31 \
    --output "${REPORTS_DIR}/qc_2024_q1.json" \
    2>&1 | tee "${LOGS_DIR}/qc_2024_q1.log"

echo "✅ Q1 validation complete"
echo ""

# ============================================================================
# Q2 2024: April - June (91 days)
# ============================================================================

echo ""
echo "============================================================================="
echo "📊 Q2 2024: Validating April - June (91 days)"
echo "============================================================================="

python3 "${QC_SCRIPT}" \
    --start-date 2024-04-01 \
    --end-date 2024-06-30 \
    --output "${REPORTS_DIR}/qc_2024_q2.json" \
    2>&1 | tee "${LOGS_DIR}/qc_2024_q2.log"

echo "✅ Q2 validation complete"
echo ""

# ============================================================================
# Q3 2024: July - September (92 days)
# ============================================================================

echo ""
echo "============================================================================="
echo "📊 Q3 2024: Validating July - September (92 days)"
echo "============================================================================="

python3 "${QC_SCRIPT}" \
    --start-date 2024-07-01 \
    --end-date 2024-09-30 \
    --output "${REPORTS_DIR}/qc_2024_q3.json" \
    2>&1 | tee "${LOGS_DIR}/qc_2024_q3.log"

echo "✅ Q3 validation complete"
echo ""

# ============================================================================
# Q4 2024: October - December (92 days)
# ============================================================================

echo ""
echo "============================================================================="
echo "📊 Q4 2024: Validating October - December (92 days)"
echo "============================================================================="

python3 "${QC_SCRIPT}" \
    --start-date 2024-10-01 \
    --end-date 2024-12-31 \
    --output "${REPORTS_DIR}/qc_2024_q4.json" \
    2>&1 | tee "${LOGS_DIR}/qc_2024_q4.log"

echo "✅ Q4 validation complete"
echo ""

# ============================================================================
# Generate Comprehensive Summary
# ============================================================================

echo ""
echo "============================================================================="
echo "📊 Generating Comprehensive QC Summary"
echo "============================================================================="

python3 - <<PYTHON
import json
from pathlib import Path

reports_dir = Path("${REPORTS_DIR}")

# Load quarterly reports
q1 = json.load(open(reports_dir / "qc_2024_q1.json"))
q2 = json.load(open(reports_dir / "qc_2024_q2.json"))
q3 = json.load(open(reports_dir / "qc_2024_q3.json"))
q4 = json.load(open(reports_dir / "qc_2024_q4.json"))

quarters = [
    {"name": "Q1", "data": q1},
    {"name": "Q2", "data": q2},
    {"name": "Q3", "data": q3},
    {"name": "Q4", "data": q4},
]

# Aggregate statistics
total_dates = 0
total_passed = 0
total_failed = 0
total_errors = 0
total_skipped = 0

quarterly_summaries = []

for q in quarters:
    summary = q["data"]["summary"]

    total_dates += summary["total_dates"]
    total_passed += summary["passed"]
    total_failed += summary["failed"]
    total_errors += summary["errors"]
    total_skipped += summary["skipped"]

    quarterly_summaries.append({
        "quarter": q["name"],
        "date_range": q["data"]["date_range"],
        "total_dates": summary["total_dates"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "errors": summary["errors"],
        "skipped": summary["skipped"],
        "effective_dates": summary["effective_dates"],
        "pass_rate": summary["pass_rate"]
    })

# Calculate overall pass rate
effective_dates = total_dates - total_skipped
overall_pass_rate = round(total_passed / effective_dates * 100, 2) if effective_dates > 0 else 0

# Collect all failed dates with details
failed_dates = []
for q in quarters:
    for report in q["data"]["reports"]:
        if report["status"] == "FAIL":
            failed_dates.append({
                "date": report["date"],
                "quarter": q["name"],
                "missing_boats": report.get("missing_boats", []),
                "extra_boats": report.get("extra_boats", []),
                "mismatches": report.get("mismatches", []),
                "source_count": report.get("source_boat_count", 0),
                "database_count": report.get("database_boat_count", 0),
            })

# Collect skipped dates
skipped_dates = []
for q in quarters:
    for report in q["data"]["reports"]:
        if report["status"] == "SKIPPED":
            skipped_dates.append({
                "date": report["date"],
                "quarter": q["name"],
                "reason": report.get("reason", "Unknown"),
                "deleted_trips": report.get("deleted_trips", 0)
            })

# Build comprehensive report
comprehensive_report = {
    "validation_period": "Full Year 2024",
    "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
    },
    "overall_summary": {
        "total_dates": total_dates,
        "passed": total_passed,
        "failed": total_failed,
        "errors": total_errors,
        "skipped": total_skipped,
        "effective_dates": effective_dates,
        "pass_rate": overall_pass_rate,
        "status": "PASS" if total_failed == 0 and total_errors == 0 else "FAIL"
    },
    "quarterly_summaries": quarterly_summaries,
    "failed_dates": failed_dates,
    "skipped_dates": skipped_dates,
    "timestamp": q1["timestamp"]  # Use Q1 timestamp as baseline
}

# Save comprehensive report
output_path = reports_dir / "qc_2024_comprehensive.json"
with open(output_path, 'w') as f:
    json.dump(comprehensive_report, f, indent=2)

# Print summary to console
print("\n" + "="*80)
print("📊 2024 COMPREHENSIVE QC VALIDATION RESULTS")
print("="*80)
print(f"Total dates validated: {total_dates}")
print(f"✅ Passed: {total_passed}")
print(f"❌ Failed: {total_failed}")
print(f"⚠️  Errors: {total_errors}")
print(f"⏭️  Skipped (Dock Totals duplicates): {total_skipped}")
print(f"\nEffective dates: {effective_dates}")
print(f"Overall pass rate: {overall_pass_rate}%")
print("")

if total_failed == 0 and total_errors == 0:
    print("="*80)
    print("🎉 100% QC VALIDATION PASSED FOR ALL 2024 DATA!")
    if total_skipped > 0:
        print(f"   ({total_skipped} dates skipped as Dock Totals duplicates)")
    print("="*80)
else:
    print("="*80)
    print("❌ QC VALIDATION FAILED - ISSUES DETECTED")
    print("="*80)
    print(f"\nFailed dates: {len(failed_dates)}")
    for fd in failed_dates[:10]:  # Show first 10
        print(f"  - {fd['date']}: {len(fd['missing_boats'])} missing, {len(fd['extra_boats'])} extra, {len(fd['mismatches'])} mismatches")
    if len(failed_dates) > 10:
        print(f"  ... and {len(failed_dates) - 10} more")

print(f"\n✅ Comprehensive report saved: {output_path}")
print("")
PYTHON

echo ""
echo "============================================================================="
echo "🎉 2024 QC Validation Complete"
echo "============================================================================="
echo "Reports available at: ${REPORTS_DIR}/"
echo "  - qc_2024_q1.json          (Q1 detailed results)"
echo "  - qc_2024_q2.json          (Q2 detailed results)"
echo "  - qc_2024_q3.json          (Q3 detailed results)"
echo "  - qc_2024_q4.json          (Q4 detailed results)"
echo "  - qc_2024_comprehensive.json (Full year summary)"
echo ""
echo "Logs available at: ${LOGS_DIR}/"
echo "  - qc_2024_q1.log"
echo "  - qc_2024_q2.log"
echo "  - qc_2024_q3.log"
echo "  - qc_2024_q4.log"
echo ""
echo "============================================================================="
