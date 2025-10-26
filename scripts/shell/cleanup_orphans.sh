#!/bin/bash
#
# File Cleanup Orchestration Script - Phase 3: Automated Cleanup Workflow
#
# Purpose: Orchestrate complete file cleanup workflow (audit → archive → delete)
# Governed By: SPEC-013 File Auditing & Cleanup System
# Version: 3.0.0 (Phase 3 - Safe Deletion & Batch Processing)
#
# Usage:
#   # Full cleanup (dry-run first)
#   ./scripts/shell/cleanup_orphans.sh --dry-run
#
#   # Actual cleanup (after reviewing dry-run)
#   ./scripts/shell/cleanup_orphans.sh
#
#   # Cleanup specific directory
#   ./scripts/shell/cleanup_orphans.sh --dir logs/
#
#   # Skip dynamic validation for speed
#   ./scripts/shell/cleanup_orphans.sh --skip-dynamic
#
# Workflow:
#   1. Run batch_audit.py to classify all files
#   2. Archive Category C files (ARCHIVE)
#   3. Delete safe Category D files (DELETE with ≥75% confidence)
#   4. Generate cleanup report
#   5. Create git commit with changes
#
# Safety Features:
#   - Dry-run mode shows all changes before execution
#   - Backups created for all deletions
#   - AUDIT.json tracks all operations
#   - DOC_CHANGELOG.md updated for all archival
#   - Comprehensive reporting and logging

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SCRIPTS="$PROJECT_ROOT/scripts/python"

# Output directories
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_OUTPUT="$PROJECT_ROOT/audit-results-$TIMESTAMP"
CLEANUP_LOG="$PROJECT_ROOT/cleanup_log_$TIMESTAMP.txt"

# Default parameters
DRY_RUN=false
SKIP_DYNAMIC=false
TARGET_DIR="."
OPERATOR="${USER}@$(hostname)"
CLEANUP_REASON="Automated file cleanup per SPEC-013"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-dynamic)
      SKIP_DYNAMIC=true
      shift
      ;;
    --dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --operator)
      OPERATOR="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dry-run         Preview changes without executing"
      echo "  --skip-dynamic    Skip Phase 2 dynamic validation (faster)"
      echo "  --dir DIR         Target directory (default: current directory)"
      echo "  --operator EMAIL  Operator email (default: $USER@hostname)"
      echo "  --help            Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option $1${NC}"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}SPEC-013 File Cleanup Orchestration${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo -e "Project Root: $PROJECT_ROOT"
echo -e "Target Directory: $TARGET_DIR"
echo -e "Audit Output: $AUDIT_OUTPUT"
echo -e "Cleanup Log: $CLEANUP_LOG"
echo -e "Operator: $OPERATOR"
echo -e "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN (preview only)' || echo 'LIVE (actual cleanup)')"
echo -e "Dynamic Validation: $([ "$SKIP_DYNAMIC" = true ] && echo 'DISABLED' || echo 'ENABLED')"
echo -e "${BLUE}========================================================================${NC}"
echo ""

# Initialize log file
{
  echo "========================================================================="
  echo "File Cleanup Log - $TIMESTAMP"
  echo "========================================================================="
  echo "Project Root: $PROJECT_ROOT"
  echo "Target Directory: $TARGET_DIR"
  echo "Operator: $OPERATOR"
  echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'LIVE')"
  echo "========================================================================="
  echo ""
} > "$CLEANUP_LOG"

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Run batch audit
echo -e "${GREEN}[Step 1/5] Running batch audit...${NC}"
{
  echo "[Step 1] Batch Audit"
  echo "===================="
} >> "$CLEANUP_LOG"

AUDIT_CMD="python3 $PYTHON_SCRIPTS/batch_audit.py --dir $TARGET_DIR --output $AUDIT_OUTPUT"
if [ "$SKIP_DYNAMIC" = true ]; then
  AUDIT_CMD="$AUDIT_CMD --skip-dynamic"
fi

echo -e "  Command: $AUDIT_CMD"
if ! eval "$AUDIT_CMD" 2>&1 | tee -a "$CLEANUP_LOG"; then
  echo -e "${RED}❌ Error: Batch audit failed${NC}"
  exit 1
fi
echo ""

# Check if audit results exist
if [ ! -f "$AUDIT_OUTPUT/SUMMARY.json" ]; then
  echo -e "${RED}❌ Error: Audit results not found${NC}"
  exit 1
fi

# Parse summary statistics
TOTAL_FILES=$(jq -r '.total_files_audited' "$AUDIT_OUTPUT/SUMMARY.json")
CRITICAL_COUNT=$(jq -r '.category_breakdown["CRITICAL (A)"]' "$AUDIT_OUTPUT/SUMMARY.json")
ACTIVE_COUNT=$(jq -r '.category_breakdown["ACTIVE (B)"]' "$AUDIT_OUTPUT/SUMMARY.json")
ARCHIVE_COUNT=$(jq -r '.category_breakdown["ARCHIVE (C)"]' "$AUDIT_OUTPUT/SUMMARY.json")
DELETE_COUNT=$(jq -r '.category_breakdown["DELETE (D)"]' "$AUDIT_OUTPUT/SUMMARY.json")

echo -e "${GREEN}✅ Audit complete:${NC}"
echo -e "  Total files audited: $TOTAL_FILES"
echo -e "  Category A (CRITICAL): $CRITICAL_COUNT files → KEEP"
echo -e "  Category B (ACTIVE): $ACTIVE_COUNT files → KEEP"
echo -e "  Category C (ARCHIVE): $ARCHIVE_COUNT files → Archive"
echo -e "  Category D (DELETE): $DELETE_COUNT files → Evaluate for deletion"
echo ""

# Step 2: Archive Category C files
if [ "$ARCHIVE_COUNT" -gt 0 ]; then
  echo -e "${GREEN}[Step 2/5] Archiving Category C files...${NC}"
  {
    echo "[Step 2] Archive Category C Files"
    echo "=================================="
  } >> "$CLEANUP_LOG"

  # Extract file paths from category_C.json
  ARCHIVE_LIST="$AUDIT_OUTPUT/archive_files.txt"
  jq -r '.[].file_path' "$AUDIT_OUTPUT/category_C.json" > "$ARCHIVE_LIST"

  echo -e "  Found $ARCHIVE_COUNT files to archive"

  # Archive each file to appropriate category
  ARCHIVED=0
  ARCHIVE_ERRORS=0

  while IFS= read -r file_path; do
    # Auto-detect category
    ARCHIVE_CMD="python3 $PYTHON_SCRIPTS/archive_file.py --file '$file_path' --auto-detect"
    if [ "$DRY_RUN" = true ]; then
      ARCHIVE_CMD="$ARCHIVE_CMD --dry-run"
    fi

    echo -e "  Archiving: $file_path"
    if eval "$ARCHIVE_CMD" >> "$CLEANUP_LOG" 2>&1; then
      ARCHIVED=$((ARCHIVED + 1))
    else
      ARCHIVE_ERRORS=$((ARCHIVE_ERRORS + 1))
      echo -e "  ${YELLOW}⚠️  Warning: Failed to archive $file_path${NC}"
    fi
  done < "$ARCHIVE_LIST"

  echo -e "${GREEN}✅ Archival complete: $ARCHIVED/$ARCHIVE_COUNT files${NC}"
  if [ "$ARCHIVE_ERRORS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $ARCHIVE_ERRORS files failed to archive (see log)${NC}"
  fi
  echo ""
else
  echo -e "${GREEN}[Step 2/5] No Category C files to archive${NC}"
  echo ""
fi

# Step 3: Delete safe Category D files
if [ "$DELETE_COUNT" -gt 0 ]; then
  echo -e "${GREEN}[Step 3/5] Deleting safe Category D files...${NC}"
  {
    echo "[Step 3] Delete Safe Category D Files"
    echo "====================================="
  } >> "$CLEANUP_LOG"

  # Extract safe-to-delete files (≥75% confidence)
  DELETE_LIST="$AUDIT_OUTPUT/delete_files.txt"
  jq -r '.[] | select(.classification.recommendation == "SAFE_TO_DELETE") | .file_path' \
    "$AUDIT_OUTPUT/category_D.json" > "$DELETE_LIST"

  SAFE_DELETE_COUNT=$(wc -l < "$DELETE_LIST" | tr -d ' ')

  if [ "$SAFE_DELETE_COUNT" -gt 0 ]; then
    echo -e "  Found $SAFE_DELETE_COUNT files safe to delete (≥75% confidence)"

    # Delete files using batch mode
    DELETE_CMD="python3 $PYTHON_SCRIPTS/safe_delete.py --batch '$DELETE_LIST' --operator '$OPERATOR' --reason '$CLEANUP_REASON'"
    if [ "$DRY_RUN" = true ]; then
      DELETE_CMD="$DELETE_CMD --dry-run"
    fi

    if eval "$DELETE_CMD" >> "$CLEANUP_LOG" 2>&1; then
      echo -e "${GREEN}✅ Deletion complete: $SAFE_DELETE_COUNT files${NC}"
    else
      echo -e "${RED}❌ Error: Batch deletion failed (see log)${NC}"
    fi
  else
    echo -e "  No files meet ≥75% confidence threshold for safe deletion"
  fi

  # Report files needing manual review
  MANUAL_REVIEW_COUNT=$(jq -r '.[] | select(.classification.recommendation == "MANUAL_REVIEW") | .file_path' \
    "$AUDIT_OUTPUT/category_D.json" | wc -l | tr -d ' ')

  if [ "$MANUAL_REVIEW_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $MANUAL_REVIEW_COUNT files need manual review (<75% confidence)${NC}"
    echo -e "  Review: $AUDIT_OUTPUT/category_D.json"
  fi
  echo ""
else
  echo -e "${GREEN}[Step 3/5] No Category D files to delete${NC}"
  echo ""
fi

# Step 4: Generate cleanup report
echo -e "${GREEN}[Step 4/5] Generating cleanup report...${NC}"
{
  echo "[Step 4] Cleanup Report"
  echo "======================="
  echo ""
  echo "Summary Statistics:"
  echo "  Total files audited: $TOTAL_FILES"
  echo "  Category A (CRITICAL): $CRITICAL_COUNT files"
  echo "  Category B (ACTIVE): $ACTIVE_COUNT files"
  echo "  Category C (ARCHIVE): $ARCHIVE_COUNT files"
  echo "  Category D (DELETE): $DELETE_COUNT files"
  echo ""
  echo "Actions Taken:"
  echo "  Files archived: $ARCHIVED"
  echo "  Files deleted: $SAFE_DELETE_COUNT"
  echo "  Files needing manual review: $MANUAL_REVIEW_COUNT"
  echo ""
} >> "$CLEANUP_LOG"

echo -e "${GREEN}✅ Cleanup report saved to: $CLEANUP_LOG${NC}"
echo ""

# Step 5: Create git commit (if not dry-run)
if [ "$DRY_RUN" = false ] && [ "$ARCHIVED" -gt 0 ] || [ "$SAFE_DELETE_COUNT" -gt 0 ]; then
  echo -e "${GREEN}[Step 5/5] Creating git commit...${NC}"

  # Check if there are changes to commit
  if [ -n "$(git status --porcelain)" ]; then
    # Stage all changes
    git add -A

    # Create commit message
    COMMIT_MSG="Automated file cleanup per SPEC-013

Phase 3 cleanup orchestration:
- Audited: $TOTAL_FILES files
- Archived: $ARCHIVED files (Category C)
- Deleted: $SAFE_DELETE_COUNT files (Category D, ≥75% confidence)
- Manual review needed: $MANUAL_REVIEW_COUNT files

All deletions backed up to archive/deleted-files/
Audit trail: $CLEANUP_LOG

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    # Create commit
    git commit -m "$COMMIT_MSG"

    echo -e "${GREEN}✅ Git commit created${NC}"
    echo -e "  Run 'git log -1' to review commit"
  else
    echo -e "${YELLOW}ℹ️  No changes to commit${NC}"
  fi
  echo ""
else
  echo -e "${BLUE}[Step 5/5] Skipping git commit (dry-run mode)${NC}"
  echo ""
fi

# Final summary
echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}Cleanup Complete!${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo -e "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN (no changes made)' || echo 'LIVE (cleanup executed)')"
echo ""
echo -e "Results:"
echo -e "  Audit results: $AUDIT_OUTPUT/"
echo -e "  Cleanup log: $CLEANUP_LOG"
if [ "$DRY_RUN" = false ]; then
  echo -e "  Backups: archive/deleted-files/$(date +%Y-%m-%d)/"
  echo -e "  Audit trail: archive/deleted-files/$(date +%Y-%m-%d)/AUDIT.json"
fi
echo ""
echo -e "Next Steps:"
if [ "$DRY_RUN" = true ]; then
  echo -e "  1. Review audit results in $AUDIT_OUTPUT/"
  echo -e "  2. Run without --dry-run to execute cleanup"
else
  echo -e "  1. Review changes: git status"
  echo -e "  2. Review commit: git log -1"
  if [ "$MANUAL_REVIEW_COUNT" -gt 0 ]; then
    echo -e "  3. Manually review $MANUAL_REVIEW_COUNT files: $AUDIT_OUTPUT/category_D.json"
  fi
fi
echo -e "${BLUE}========================================================================${NC}"

# Exit with success
exit 0
