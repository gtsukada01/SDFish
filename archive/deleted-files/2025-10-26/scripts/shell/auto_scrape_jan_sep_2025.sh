#!/bin/bash
# Auto-scrape SoCal Jan-Sep 2025
# Shows real-time progress for visual monitoring

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "🚀 SoCal 2025 Backfill - Auto-Scraper"
echo "======================================"
echo ""

# Function to scrape a month and show progress
scrape_month() {
    local month=$1
    local start_date=$2
    local end_date=$3
    local log_file="$LOG_DIR/socal_${month}_2025_scrape.log"

    echo ""
    echo "📅 Starting $month 2025 ($start_date to $end_date)..."
    echo "----------------------------------------"

    # Run scraper and tail log in real-time
    (cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/socal_scraper.py --start-date "$start_date" --end-date "$end_date") 2>&1 | tee "$log_file" | grep -E "(Processing:|✅ Inserted:|⚠️|❌|SUMMARY)" &

    SCRAPER_PID=$!
    wait $SCRAPER_PID

    # Show summary
    echo ""
    echo "✅ $month 2025 complete!"
    tail -20 "$log_file" | grep -A 10 "SCRAPING SUMMARY"
    echo ""
}

# February already running - wait for it
echo "⏳ February 2025 in progress..."
echo "   (Started separately - will continue when done)"
echo ""

# Wait for February to finish by monitoring the log
while ! grep -q "SCRAPING SUMMARY" "$LOG_DIR/socal_feb_2025_scrape.log" 2>/dev/null; do
    sleep 10
done

echo "✅ February 2025 complete!"
echo ""

# March through September
scrape_month "march" "2025-03-01" "2025-03-31"
scrape_month "april" "2025-04-01" "2025-04-30"
scrape_month "may" "2025-05-01" "2025-05-31"
scrape_month "june" "2025-06-01" "2025-06-30"
scrape_month "july" "2025-07-01" "2025-07-31"
scrape_month "august" "2025-08-01" "2025-08-31"
scrape_month "september" "2025-09-01" "2025-09-30"

echo ""
echo "🎉 ALL MONTHS COMPLETE!"
echo "======================="
echo ""

# Final verification
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/verify_socal_baseline.py)
