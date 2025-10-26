#!/bin/bash
# Auto-complete remaining 2025 SoCal months
# Runs May-September sequentially without manual intervention

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "🚀 Starting automated SoCal 2025 backfill (May-September)"
echo "=========================================================="
echo ""

# May
echo "📅 Starting May 2025..."
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date 2025-05-01 --end-date 2025-05-31) 2>&1 | tee "$LOG_DIR/socal_may_2025_scrape.log"
echo "✅ May complete!"
echo ""

# June
echo "📅 Starting June 2025..."
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date 2025-06-01 --end-date 2025-06-30) 2>&1 | tee "$LOG_DIR/socal_june_2025_scrape.log"
echo "✅ June complete!"
echo ""

# July
echo "📅 Starting July 2025..."
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date 2025-07-01 --end-date 2025-07-31) 2>&1 | tee "$LOG_DIR/socal_july_2025_scrape.log"
echo "✅ July complete!"
echo ""

# August
echo "📅 Starting August 2025..."
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date 2025-08-01 --end-date 2025-08-31) 2>&1 | tee "$LOG_DIR/socal_august_2025_scrape.log"
echo "✅ August complete!"
echo ""

# September
echo "📅 Starting September 2025..."
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date 2025-09-01 --end-date 2025-09-30) 2>&1 | tee "$LOG_DIR/socal_september_2025_scrape.log"
echo "✅ September complete!"
echo ""

echo "🎉 ALL MONTHS COMPLETE!"
echo "======================="
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/verify_socal_baseline.py)
