#!/bin/bash
# 2024 SoCal Backfill - Q4 (Oct-Dec)
# Scrapes October through December 2024 with monthly logging

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

cd "$PROJECT_ROOT"

echo "🚀 Starting 2024 SoCal Q4 Backfill (Oct-Dec)"
echo "=============================================="
echo "Project root: $PROJECT_ROOT"
echo "Log directory: $LOG_DIR"
echo ""

# October 2024
echo "📅 Scraping October 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-10-01 --end-date 2024-10-31 2>&1 | tee "$LOG_DIR/q4_oct.log"
echo "✅ October complete!"
echo ""

# November 2024
echo "📅 Scraping November 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-11-01 --end-date 2024-11-30 2>&1 | tee "$LOG_DIR/q4_nov.log"
echo "✅ November complete!"
echo ""

# December 2024
echo "📅 Scraping December 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-12-01 --end-date 2024-12-31 2>&1 | tee "$LOG_DIR/q4_dec.log"
echo "✅ December complete!"
echo ""

echo "🎉 Q4 2024 SCRAPING COMPLETE!"
echo "=============================="
echo ""
echo "Next step: QC validation"
echo "Run: python3 scripts/python/socal_qc_validator.py --start-date 2024-10-01 --end-date 2024-12-31 --output $LOG_DIR/qc_q4.json"
echo ""
