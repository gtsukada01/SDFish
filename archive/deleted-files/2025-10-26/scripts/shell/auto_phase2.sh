#!/bin/bash
# Auto-watcher: Starts Phase 2 (September) when Phase 1 (August) completes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
AUGUST_LOG="$ROOT_DIR/archive/logs/august_remediation.log"

echo "$(date): Watching for August completion..."

# Wait for August process to finish
while ps -p $1 > /dev/null 2>&1; do
    sleep 5
done

echo "$(date): ✅ August complete! Counting final recoveries..."
AUGUST_COUNT=$(grep "✅ Inserted:" "$AUGUST_LOG" | wc -l | tr -d ' ')
echo "August total: $AUGUST_COUNT trips recovered"

echo ""
echo "$(date): 🚀 Starting Phase 2: September remediation..."
"$SCRIPT_DIR/run_september.sh"

echo "$(date): ✅ September complete!"
