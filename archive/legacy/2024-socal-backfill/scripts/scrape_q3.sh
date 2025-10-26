#!/bin/bash
# 2024 SoCal Backfill - Q3 (Jul-Sep)
# Scrapes July through September 2024 with monthly logging
# PEAK SEASON - Highest volume months

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

cd "$PROJECT_ROOT"

echo "🚀 Starting 2024 SoCal Q3 Backfill (Jul-Sep)"
echo "=============================================="
echo "⚠️  PEAK SEASON - High volume expected"
echo "Project root: $PROJECT_ROOT"
echo "Log directory: $LOG_DIR"
echo ""

# July 2024
echo "📅 Scraping July 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-07-01 --end-date 2024-07-31 2>&1 | tee "$LOG_DIR/q3_jul.log"
echo "✅ July complete!"
echo ""

# August 2024
echo "📅 Scraping August 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-08-01 --end-date 2024-08-31 2>&1 | tee "$LOG_DIR/q3_aug.log"
echo "✅ August complete!"
echo ""

# September 2024
echo "📅 Scraping September 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-09-01 --end-date 2024-09-30 2>&1 | tee "$LOG_DIR/q3_sep.log"
echo "✅ September complete!"
echo ""

echo "🎉 Q3 2024 SCRAPING COMPLETE!"
echo "=============================="
echo ""
echo "Next step: QC validation"
echo "Run: python3 scripts/python/socal_qc_validator.py --start-date 2024-07-01 --end-date 2024-09-30 --output $LOG_DIR/qc_q3.json"
echo ""
