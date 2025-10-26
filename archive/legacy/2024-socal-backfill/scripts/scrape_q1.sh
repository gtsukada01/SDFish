#!/bin/bash
# 2024 SoCal Backfill - Q1 (Jan-Mar)
# Scrapes January through March 2024 with monthly logging

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

cd "$PROJECT_ROOT"

echo "🚀 Starting 2024 SoCal Q1 Backfill (Jan-Mar)"
echo "=============================================="
echo "Project root: $PROJECT_ROOT"
echo "Log directory: $LOG_DIR"
echo ""

# January 2024
echo "📅 Scraping January 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-01-01 --end-date 2024-01-31 2>&1 | tee "$LOG_DIR/q1_jan.log"
echo "✅ January complete!"
echo ""

# February 2024
echo "📅 Scraping February 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-02-01 --end-date 2024-02-29 2>&1 | tee "$LOG_DIR/q1_feb.log"
echo "✅ February complete!"
echo ""

# March 2024
echo "📅 Scraping March 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-03-01 --end-date 2024-03-31 2>&1 | tee "$LOG_DIR/q1_mar.log"
echo "✅ March complete!"
echo ""

echo "🎉 Q1 2024 SCRAPING COMPLETE!"
echo "=============================="
echo ""
echo "Next step: QC validation"
echo "Run: python3 scripts/python/socal_qc_validator.py --start-date 2024-01-01 --end-date 2024-03-31 --output $LOG_DIR/qc_q1.json"
echo ""
