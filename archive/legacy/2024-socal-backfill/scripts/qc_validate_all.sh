#!/bin/bash
# 2024 SoCal Backfill - Final QC Validation
# Validates all 366 dates (2024 was a leap year) against source

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

cd "$PROJECT_ROOT"

echo "🔍 Starting 2024 SoCal Final QC Validation"
echo "==========================================="
echo "Validating all 366 dates: 2024-01-01 → 2024-12-31"
echo "Project root: $PROJECT_ROOT"
echo "Log directory: $LOG_DIR"
echo ""

# Run comprehensive QC validation
echo "📊 Running comprehensive validation..."
python3 scripts/python/socal_qc_validator.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output "$LOG_DIR/qc_2024_full.json" 2>&1 | tee "$LOG_DIR/qc_2024_full.log"

echo ""
echo "✅ QC VALIDATION COMPLETE!"
echo "=========================="
echo ""
echo "Results saved to: $LOG_DIR/qc_2024_full.json"
echo "Log saved to: $LOG_DIR/qc_2024_full.log"
echo ""
echo "Check pass rate:"
echo "cat $LOG_DIR/qc_2024_full.json | jq '.summary.pass_rate'"
echo ""
echo "If 100% pass rate achieved:"
echo "  1. Copy final report: cp $LOG_DIR/qc_2024_full.json logs/"
echo "  2. Update README.md with 2024 SoCal completion"
echo "  3. Delete project: rm -rf 2024-socal-backfill/"
echo ""
