#!/bin/bash
# 2024 SoCal Backfill - Q2 (Apr-Jun)
# Scrapes April through June 2024 with monthly logging
# PEAK SEASON - Highest volume months

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

cd "$PROJECT_ROOT"

echo "🚀 Starting 2024 SoCal Q2 Backfill (Apr-Jun)"
echo "=============================================="
echo "⚠️  PEAK SEASON - High volume expected"
echo "Project root: $PROJECT_ROOT"
echo "Log directory: $LOG_DIR"
echo ""

# April 2024
echo "📅 Scraping April 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-04-01 --end-date 2024-04-30 2>&1 | tee "$LOG_DIR/q2_apr.log"
echo "✅ April complete!"
echo ""

# May 2024
echo "📅 Scraping May 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-05-01 --end-date 2024-05-31 2>&1 | tee "$LOG_DIR/q2_may.log"
echo "✅ May complete!"
echo ""

# June 2024
echo "📅 Scraping June 2024..."
python3 scripts/python/socal_scraper.py --start-date 2024-06-01 --end-date 2024-06-30 2>&1 | tee "$LOG_DIR/q2_jun.log"
echo "✅ June complete!"
echo ""

echo "🎉 Q2 2024 SCRAPING COMPLETE!"
echo "=============================="
echo ""
echo "Next step: QC validation"
echo "Run: python3 scripts/python/socal_qc_validator.py --start-date 2024-04-01 --end-date 2024-06-30 --output $LOG_DIR/qc_q2.json"
echo ""
