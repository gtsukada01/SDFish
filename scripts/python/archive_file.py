#!/usr/bin/env python3
"""
File Archival Script - Phase 3: Documentation Archival with DOC_CHANGELOG Integration

Purpose: Archive historical documentation files to appropriate subdirectories
Governed By: SPEC-013 File Auditing & Cleanup System
Version: 3.0.0 (Phase 3 - Safe Deletion & Batch Processing)

Usage:
    # Archive single file to logs subdirectory
    python3 archive_file.py --file qc_batch1.json --category logs

    # Archive to specific subdirectory
    python3 archive_file.py --file old_report.md --category reports

    # Dry-run to preview
    python3 archive_file.py --file qc_batch1.json --category logs --dry-run

    # Batch archive from file list
    python3 archive_file.py --batch archive_list.txt --category logs

Features:
    - Moves files to archive/ subdirectories (logs/, reports/, backups/, docs/, screenshots/)
    - Preserves file structure and metadata
    - Updates DOC_CHANGELOG.md automatically
    - Dry-run mode for preview
    - Batch archival support
    - Git-aware (updates working directory)

Archive Structure:
    archive/
    ├── logs/           # QC logs, scraper logs, validation logs
    ├── reports/        # Monthly completion reports, audit reports
    ├── backups/        # Database backups, snapshots
    ├── docs/           # Superseded documentation
    ├── screenshots/    # Historical screenshots
    └── scripts/        # Deprecated scripts
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Project root detection
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Archive root
ARCHIVE_ROOT = PROJECT_ROOT / "archive"

# Valid archive categories
VALID_CATEGORIES = [
    "logs",
    "reports",
    "backups",
    "docs",
    "screenshots",
    "scripts"
]


def get_archive_directory(category: str) -> Path:
    """
    Get archive directory for category

    Args:
        category: Archive category (logs, reports, backups, docs, screenshots, scripts)

    Returns:
        Path to archive subdirectory
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category: {category}. "
            f"Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    archive_dir = ARCHIVE_ROOT / category
    return archive_dir


def update_doc_changelog(
    file_path: str,
    archive_path: str,
    category: str,
    reason: str = "Archival per SPEC-013 file cleanup"
) -> None:
    """
    Update DOC_CHANGELOG.md with archival entry

    Args:
        file_path: Original file path
        archive_path: Archive destination path
        category: Archive category
        reason: Reason for archival
    """
    changelog_file = PROJECT_ROOT / "DOC_CHANGELOG.md"

    # Create changelog if it doesn't exist
    if not changelog_file.exists():
        with open(changelog_file, 'w') as f:
            f.write("# Documentation Changelog\n\n")
            f.write("Audit trail for all documentation changes per DOCUMENTATION_STANDARDS.md\n\n")
            f.write("---\n\n")

    # Read existing changelog
    with open(changelog_file, 'r') as f:
        content = f.read()

    # Find insertion point (after header)
    header_end = content.find("---")
    if header_end == -1:
        header_end = len(content)
    else:
        header_end += 4  # After "---\n"

    # Create archival entry
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"""
## [{date_str}] Archived: {os.path.basename(file_path)}

**Action**: Moved to archive/{category}/
**Original Path**: `{file_path}`
**Archive Path**: `{archive_path}`
**Reason**: {reason}
**Governed By**: SPEC-013 File Auditing & Cleanup System

---
"""

    # Insert entry
    updated_content = content[:header_end] + entry + content[header_end:]

    # Write back
    with open(changelog_file, 'w') as f:
        f.write(updated_content)

    print(f"  ✅ Updated DOC_CHANGELOG.md")


def archive_file(
    file_path: str,
    category: str,
    dry_run: bool = False,
    update_changelog: bool = True,
    reason: Optional[str] = None
) -> Dict:
    """
    Archive file to appropriate subdirectory

    Args:
        file_path: Path to file (relative or absolute)
        category: Archive category (logs, reports, backups, docs, screenshots, scripts)
        dry_run: If True, show what would happen without archiving
        update_changelog: If True, update DOC_CHANGELOG.md
        reason: Reason for archival (optional)

    Returns:
        Dict with archival result
    """
    # Convert to absolute path
    abs_file_path = Path(file_path).resolve()

    # Verify file exists
    if not abs_file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "dry_run": dry_run
        }

    # Get archive directory
    try:
        archive_dir = get_archive_directory(category)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "dry_run": dry_run
        }

    # Determine archive path (preserve filename)
    archive_path = archive_dir / abs_file_path.name

    # Check if file already exists in archive
    if archive_path.exists() and not dry_run:
        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = archive_path.stem
        suffix = archive_path.suffix
        archive_path = archive_dir / f"{stem}_{timestamp}{suffix}"

    # Convert to relative paths for display
    try:
        rel_file_path = str(abs_file_path.relative_to(PROJECT_ROOT))
        rel_archive_path = str(archive_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_file_path = str(abs_file_path)
        rel_archive_path = str(archive_path)

    print(f"\n{'='*70}")
    print(f"{'[DRY-RUN] ' if dry_run else ''}Archive File: {rel_file_path}")
    print(f"{'='*70}")

    if dry_run:
        print(f"  [DRY-RUN] Would move: {rel_file_path}")
        print(f"  [DRY-RUN] Destination: {rel_archive_path}")
        if update_changelog:
            print(f"  [DRY-RUN] Would update: DOC_CHANGELOG.md")
    else:
        # Create archive directory
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Move file to archive
        try:
            shutil.move(str(abs_file_path), str(archive_path))
            print(f"  ✅ Moved: {rel_file_path} → {rel_archive_path}")
        except Exception as e:
            return {
                "success": False,
                "error": f"Move failed: {e}",
                "dry_run": dry_run
            }

        # Update DOC_CHANGELOG.md
        if update_changelog:
            try:
                update_doc_changelog(
                    file_path=rel_file_path,
                    archive_path=rel_archive_path,
                    category=category,
                    reason=reason or "Archival per SPEC-013 file cleanup"
                )
            except Exception as e:
                print(f"  ⚠️  Warning: Failed to update DOC_CHANGELOG.md: {e}")

    print(f"\n{'='*70}")
    print(f"Archival Summary:")
    print(f"  Original file: {rel_file_path}")
    print(f"  Archive location: {rel_archive_path}")
    print(f"  Category: {category}")
    print(f"  Status: {'DRY-RUN (no changes made)' if dry_run else 'COMPLETED'}")
    print(f"{'='*70}\n")

    return {
        "success": True,
        "original_path": rel_file_path,
        "archive_path": rel_archive_path,
        "category": category,
        "dry_run": dry_run
    }


def batch_archive_files(
    file_list: List[str],
    category: str,
    dry_run: bool = False,
    update_changelog: bool = True
) -> Dict:
    """
    Archive multiple files to category subdirectory

    Args:
        file_list: List of file paths
        category: Archive category
        dry_run: If True, show what would happen without archiving
        update_changelog: If True, update DOC_CHANGELOG.md

    Returns:
        Dict with batch archival results
    """
    print(f"\n{'='*70}")
    print(f"Batch Archive: {len(file_list)} files to archive/{category}/")
    print(f"{'='*70}")

    results = {
        "total": len(file_list),
        "successful": 0,
        "failed": 0,
        "errors": [],
        "dry_run": dry_run
    }

    for i, file_path in enumerate(file_list, 1):
        print(f"\n[{i}/{len(file_list)}] Processing: {file_path}")

        result = archive_file(
            file_path=file_path,
            category=category,
            dry_run=dry_run,
            update_changelog=update_changelog
        )

        if result["success"]:
            results["successful"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "file": file_path,
                "error": result.get("error", "Unknown error")
            })

    # Print summary
    print(f"\n{'='*70}")
    print(f"Batch Archival Summary:")
    print(f"  Total files: {results['total']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Category: {category}")
    print(f"  Status: {'DRY-RUN (no changes made)' if dry_run else 'COMPLETED'}")
    print(f"{'='*70}\n")

    return results


def auto_detect_category(file_path: str) -> Optional[str]:
    """
    Auto-detect appropriate archive category based on file pattern

    Args:
        file_path: File path

    Returns:
        Category string or None if cannot detect
    """
    filename = os.path.basename(file_path).lower()

    # QC logs, scraper logs, validation logs
    if any(pattern in filename for pattern in ["qc_", ".log", "validation", "audit"]):
        return "logs"

    # Monthly reports, completion reports
    if any(pattern in filename for pattern in ["_report", "completion", "summary"]):
        return "reports"

    # Database backups, snapshots
    if any(pattern in filename for pattern in ["backup", "snapshot", "_backup_"]):
        return "backups"

    # Screenshots
    if any(pattern in filename for pattern in ["screenshot", ".png", ".jpg", ".jpeg"]):
        return "screenshots"

    # Scripts
    if filename.endswith((".py", ".sh", ".js", ".ts")) and "test_" in filename:
        return "scripts"

    # Documentation
    if filename.endswith(".md"):
        return "docs"

    return None


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Archive files to appropriate subdirectories (SPEC-013 Phase 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive QC log to logs/
  python3 archive_file.py --file qc_batch1.json --category logs

  # Archive monthly report to reports/
  python3 archive_file.py --file JUNE_2025_COMPLETE.md --category reports

  # Dry-run to preview
  python3 archive_file.py --file qc_batch1.json --category logs --dry-run

  # Batch archive from file list
  python3 archive_file.py --batch archive_list.txt --category logs

  # Auto-detect category
  python3 archive_file.py --file qc_batch1.json --auto-detect

Valid Categories:
  logs        - QC logs, scraper logs, validation logs
  reports     - Monthly completion reports, audit reports
  backups     - Database backups, snapshots
  docs        - Superseded documentation
  screenshots - Historical screenshots
  scripts     - Deprecated scripts
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--file',
        type=str,
        help='Single file to archive'
    )
    mode_group.add_argument(
        '--batch',
        type=str,
        help='File containing list of files to archive (one per line)'
    )

    # Category selection
    category_group = parser.add_mutually_exclusive_group(required=True)
    category_group.add_argument(
        '--category',
        type=str,
        choices=VALID_CATEGORIES,
        help='Archive category subdirectory'
    )
    category_group.add_argument(
        '--auto-detect',
        action='store_true',
        help='Auto-detect category based on file pattern'
    )

    # Optional flags
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be archived without actually archiving'
    )
    parser.add_argument(
        '--no-changelog',
        action='store_true',
        help='Skip DOC_CHANGELOG.md update'
    )
    parser.add_argument(
        '--reason',
        type=str,
        help='Reason for archival (for DOC_CHANGELOG.md)'
    )

    args = parser.parse_args()

    # Execute appropriate mode
    result = None

    if args.file:
        # Single file archival
        category = args.category

        # Auto-detect category if requested
        if args.auto_detect:
            category = auto_detect_category(args.file)
            if category is None:
                print(f"❌ Error: Could not auto-detect category for {args.file}")
                print(f"   Please specify --category manually")
                sys.exit(1)
            else:
                print(f"  🔍 Auto-detected category: {category}")

        result = archive_file(
            file_path=args.file,
            category=category,
            dry_run=args.dry_run,
            update_changelog=not args.no_changelog,
            reason=args.reason
        )

    elif args.batch:
        # Batch archival
        if not os.path.exists(args.batch):
            print(f"❌ Error: Batch file not found: {args.batch}")
            sys.exit(1)

        with open(args.batch, 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]

        category = args.category

        # Auto-detect category from first file if requested
        if args.auto_detect:
            if file_list:
                category = auto_detect_category(file_list[0])
                if category is None:
                    print(f"❌ Error: Could not auto-detect category")
                    print(f"   Please specify --category manually")
                    sys.exit(1)
                else:
                    print(f"  🔍 Auto-detected category: {category}")

        result = batch_archive_files(
            file_list=file_list,
            category=category,
            dry_run=args.dry_run,
            update_changelog=not args.no_changelog
        )

    # Exit with appropriate code
    if result and not result.get("success", True):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
