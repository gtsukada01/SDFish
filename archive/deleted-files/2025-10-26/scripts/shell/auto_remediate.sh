#!/bin/bash
# Auto-remediation script - monitors audit completion and starts re-scraping

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
AUDIT_FILE="$ROOT_DIR/archive/reports/qc/current/qc_2025_full_audit.json"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/auto_remediate.log"
FAILED_DATES_FILE="$ROOT_DIR/archive/reports/qc/reference/failed_dates.txt"

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$FAILED_DATES_FILE")"

echo "$(date): Waiting for audit to complete..." | tee -a "$LOG_FILE"

# Wait for audit file to exist and be stable (not being written to)
while true; do
    if [ -f "$AUDIT_FILE" ]; then
        # Check if file size is stable (not being written to)
        SIZE1=$(stat -f%z "$AUDIT_FILE" 2>/dev/null || stat -c%s "$AUDIT_FILE" 2>/dev/null)
        sleep 2
        SIZE2=$(stat -f%z "$AUDIT_FILE" 2>/dev/null || stat -c%s "$AUDIT_FILE" 2>/dev/null)

        if [ "$SIZE1" = "$SIZE2" ]; then
            echo "$(date): ✅ Audit complete! File size: $SIZE1 bytes" | tee -a "$LOG_FILE"
            break
        fi
    fi
    sleep 5
done

# Extract summary
echo "" | tee -a "$LOG_FILE"
echo "=== AUDIT SUMMARY ===" | tee -a "$LOG_FILE"
cat "$AUDIT_FILE" | jq '.summary' | tee -a "$LOG_FILE"

# Extract failed dates
echo "" | tee -a "$LOG_FILE"
echo "=== EXTRACTING FAILED DATES ===" | tee -a "$LOG_FILE"
FAILED_DATES=$(cat "$AUDIT_FILE" | jq -r '.reports[] | select(.status == "FAIL") | .date' | tr '\n' ' ')
FAILED_COUNT=$(echo "$FAILED_DATES" | wc -w | tr -d ' ')

echo "Total failed dates: $FAILED_COUNT" | tee -a "$LOG_FILE"
echo "Failed dates: $FAILED_DATES" | tee -a "$LOG_FILE"

# Save failed dates to file for batch processing
echo "$FAILED_DATES" | tr ' ' '\n' > "$FAILED_DATES_FILE"

echo "" | tee -a "$LOG_FILE"
echo "$(date): ✅ Failed dates extracted to $(basename "$FAILED_DATES_FILE")" | tee -a "$LOG_FILE"
echo "$(date): 🚀 Ready for batch re-scraping!" | tee -a "$LOG_FILE"
