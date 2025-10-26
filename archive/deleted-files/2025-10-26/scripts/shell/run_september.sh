#!/bin/bash
# Phase 2: September 2025 Re-scraping (30 dates)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/september_remediation.log"

mkdir -p "$LOG_DIR"

echo "$(date): Starting September 2025 remediation (30 dates)..."

(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-09-01 --end-date 2025-09-30) 2>&1 | tee "$LOG_FILE"

echo "$(date): September complete! Counting recoveries..."
RECOVERED=$(grep "✅ Inserted:" "$LOG_FILE" | wc -l | tr -d ' ')
echo "Total trips recovered in September: $RECOVERED"
