#!/bin/bash

# Phase 5: ONLY Feb/March Missing Dates (8 dates total)
# Excludes October - will handle ghost data separately

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/phase5_feb_mar_only.log"

mkdir -p "$LOG_DIR"
echo "=== PHASE 5: Feb/March Missing Dates ===" | tee -a $LOG_FILE
echo "Start: $(date)" | tee -a $LOG_FILE
echo "Dates to process: 8 total" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# February missing dates (4 dates)
echo "Processing February missing dates..." | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-02-06 --end-date 2025-02-06) 2>&1 | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-02-12 --end-date 2025-02-13) 2>&1 | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-02-25 --end-date 2025-02-25) 2>&1 | tee -a $LOG_FILE

# March missing dates (4 dates)
echo "Processing March missing dates..." | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-03-03 --end-date 2025-03-03) 2>&1 | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-03-06 --end-date 2025-03-06) 2>&1 | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-03-11 --end-date 2025-03-11) 2>&1 | tee -a $LOG_FILE
(cd "$ROOT_DIR" && PYTHONPATH="scripts/python" python3 scripts/python/boats_scraper.py --start-date 2025-03-13 --end-date 2025-03-13) 2>&1 | tee -a $LOG_FILE

echo "=== PHASE 5 COMPLETE ===" | tee -a $LOG_FILE
echo "End: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "Summary:" | tee -a $LOG_FILE
echo "- February: 4 dates processed" | tee -a $LOG_FILE
echo "- March: 4 dates processed" | tee -a $LOG_FILE
echo "- Total: 8 dates" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "⏳ NEXT: Ghost data cleanup (Oct 17-31)" | tee -a $LOG_FILE
