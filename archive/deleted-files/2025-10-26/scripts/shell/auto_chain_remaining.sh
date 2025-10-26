#!/bin/bash
# Auto-chain May through September 2025 SoCal scrapes
# Monitors each month and automatically starts the next

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "🚀 SoCal 2025 Auto-Chain Monitor"
echo "=================================="
echo ""

# Function to wait for scrape to complete by monitoring log file
wait_for_month() {
    local month=$1
    local log_file="$LOG_DIR/socal_${month}_2025_scrape.log"

    echo "⏳ Monitoring $month 2025..."

    # Wait until SCRAPING SUMMARY appears in log (indicates completion)
    while ! grep -q "SCRAPING SUMMARY" "$log_file" 2>/dev/null; do
        sleep 10
    done

    echo "✅ $month 2025 complete!"
    echo ""
}

# Function to start a month's scrape
start_month() {
    local month=$1
    local start_date=$2
    local end_date=$3
    local log_file="$LOG_DIR/socal_${month}_2025_scrape.log"

    echo "📅 Starting $month 2025 ($start_date to $end_date)..."
    (cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date "$start_date" --end-date "$end_date") 2>&1 | tee "$log_file" &

    # Wait a few seconds for scrape to initialize
    sleep 5
}

# May is already running - just wait for it
echo "📅 May 2025 already in progress..."
wait_for_month "may"

# June
start_month "june" "2025-06-01" "2025-06-30"
wait_for_month "june"

# July
start_month "july" "2025-07-01" "2025-07-31"
wait_for_month "july"

# August
start_month "august" "2025-08-01" "2025-08-31"
wait_for_month "august"

# September
start_month "september" "2025-09-01" "2025-09-30"
wait_for_month "september"

echo ""
echo "🎉 ALL MONTHS COMPLETE! (Jan-Sep 2025)"
echo "======================================"
echo ""

# Final verification
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/verify_socal_baseline.py)
