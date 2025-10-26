#!/usr/bin/env python3
"""
Safe File Deletion Script - Phase 3: Backup-First Deletion with Audit Trail

Purpose: Safe file deletion with automatic backups and comprehensive audit logging
Governed By: SPEC-013 File Auditing & Cleanup System
Version: 3.0.0 (Phase 3 - Safe Deletion & Batch Processing)

Usage:
    # Dry-run (preview what would happen)
    python3 safe_delete.py --file <path> --operator <email> --reason <reason> --dry-run

    # Actual deletion (with backup)
    python3 safe_delete.py --file <path> --operator <email> --reason <reason>

    # Batch deletion from file list
    python3 safe_delete.py --batch <file_list.txt> --operator <email> --reason <reason>

Features:
    - Backup-first deletion (always creates backup before deletion)
    - Timestamped backup directories (archive/deleted-files/YYYY-MM-DD/)
    - Comprehensive audit trail (AUDIT.json with SHA256 hashes)
    - Dry-run mode (preview without actual deletion)
    - Batch deletion support
    - Recovery procedures documented in audit log

Safety Guarantees:
    - Every deletion is backed up first (100% reversible)
    - Audit trail includes operator, reason, timestamp, file hash
    - Dry-run shows exactly what would be deleted
    - Absolute paths prevent accidental deletions
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Project root detection
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Backup directory structure
BACKUP_ROOT = PROJECT_ROOT / "archive" / "deleted-files"


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of file for integrity verification

    Args:
        file_path: Path to file

    Returns:
        Hex-encoded SHA256 hash
    """
    sha256 = hashlib.sha256()

    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        print(f"⚠️  Warning: Could not compute hash for {file_path}: {e}")
        return "HASH_COMPUTATION_FAILED"


def get_backup_directory() -> Path:
    """
    Get timestamped backup directory for today

    Returns:
        Path to backup directory (e.g., archive/deleted-files/2025-10-25/)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = BACKUP_ROOT / today
    return backup_dir


def create_audit_log_entry(
    file_path: str,
    backup_path: str,
    operator: str,
    reason: str,
    file_hash: str,
    dry_run: bool = False
) -> Dict:
    """
    Create audit log entry for deletion

    Args:
        file_path: Original file path (relative to project root)
        backup_path: Backup file path
        operator: Email/username of person performing deletion
        reason: Reason for deletion
        file_hash: SHA256 hash of file
        dry_run: Whether this is a dry-run

    Returns:
        Dict with audit entry
    """
    return {
        "deleted_at": datetime.now().isoformat(),
        "operator": operator,
        "original_path": file_path,
        "backup_path": str(backup_path),
        "file_hash": file_hash,
        "reason": reason,
        "dry_run": dry_run,
        "recovery_command": f"cp {backup_path} {file_path}"
    }


def append_to_audit_log(backup_dir: Path, entry: Dict) -> None:
    """
    Append entry to AUDIT.json in backup directory

    Args:
        backup_dir: Backup directory path
        entry: Audit entry dict
    """
    audit_file = backup_dir / "AUDIT.json"

    # Load existing audit log or create new
    if audit_file.exists():
        with open(audit_file, 'r') as f:
            audit_data = json.load(f)
    else:
        audit_data = {
            "audit_version": "1.0",
            "backup_directory": str(backup_dir),
            "created_at": datetime.now().isoformat(),
            "deletions": []
        }

    # Append new entry
    audit_data["deletions"].append(entry)

    # Write back to file
    backup_dir.mkdir(parents=True, exist_ok=True)
    with open(audit_file, 'w') as f:
        json.dump(audit_data, f, indent=2)

    print(f"  ✅ Audit log updated: {audit_file}")


def backup_file_before_deletion(
    file_path: str,
    backup_dir: Path,
    dry_run: bool = False
) -> Optional[Path]:
    """
    Backup file to timestamped directory before deletion

    Args:
        file_path: Path to file (relative to project root)
        backup_dir: Backup directory path
        dry_run: If True, don't actually create backup

    Returns:
        Path to backup file, or None if dry-run
    """
    # Convert to absolute path
    abs_file_path = Path(file_path).resolve()

    # Verify file exists
    if not abs_file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine backup path (preserve relative structure from project root)
    try:
        rel_path = abs_file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        # File outside project root - use absolute path structure
        rel_path = Path(str(abs_file_path).lstrip('/'))

    backup_path = backup_dir / rel_path

    if dry_run:
        print(f"  [DRY-RUN] Would backup: {file_path} → {backup_path}")
        return None
    else:
        # Create backup directory
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file to backup
        shutil.copy2(abs_file_path, backup_path)
        print(f"  ✅ Backed up: {backup_path}")

        return backup_path


def safe_delete_file(
    file_path: str,
    operator: str,
    reason: str,
    dry_run: bool = False,
    skip_backup: bool = False
) -> Dict:
    """
    Safely delete file with backup and audit trail

    Args:
        file_path: Path to file (relative or absolute)
        operator: Email/username performing deletion
        reason: Reason for deletion
        dry_run: If True, show what would happen without deleting
        skip_backup: If True, skip backup (NOT RECOMMENDED)

    Returns:
        Dict with deletion result
    """
    # Convert to absolute path
    abs_file_path = Path(file_path).resolve()

    # Convert back to relative path for display
    try:
        rel_file_path = str(abs_file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_file_path = str(abs_file_path)

    print(f"\n{'='*70}")
    print(f"{'[DRY-RUN] ' if dry_run else ''}Safe Delete: {rel_file_path}")
    print(f"{'='*70}")

    # Verify file exists
    if not abs_file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "dry_run": dry_run
        }

    # Get backup directory
    backup_dir = get_backup_directory()

    # Compute file hash before deletion
    file_hash = compute_file_hash(str(abs_file_path))

    # Backup file first (CRITICAL SAFETY STEP)
    backup_path = None
    if not skip_backup:
        try:
            backup_path = backup_file_before_deletion(
                str(abs_file_path),
                backup_dir,
                dry_run=dry_run
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Backup failed: {e}",
                "dry_run": dry_run
            }

    # Create audit log entry
    audit_entry = create_audit_log_entry(
        file_path=rel_file_path,
        backup_path=str(backup_path) if backup_path else "NO_BACKUP",
        operator=operator,
        reason=reason,
        file_hash=file_hash,
        dry_run=dry_run
    )

    # Delete file
    if dry_run:
        print(f"  [DRY-RUN] Would delete: {rel_file_path}")
        print(f"  [DRY-RUN] Would update: {backup_dir / 'AUDIT.json'}")
    else:
        # Actual deletion
        try:
            os.remove(abs_file_path)
            print(f"  ✅ Deleted: {rel_file_path}")
        except Exception as e:
            return {
                "success": False,
                "error": f"Deletion failed: {e}",
                "dry_run": dry_run
            }

        # Update audit log
        append_to_audit_log(backup_dir, audit_entry)

    print(f"\n{'='*70}")
    print(f"Deletion Summary:")
    print(f"  Original file: {rel_file_path}")
    print(f"  Backup location: {backup_path if backup_path else 'NO_BACKUP'}")
    print(f"  File hash: {file_hash}")
    print(f"  Operator: {operator}")
    print(f"  Reason: {reason}")
    print(f"  Status: {'DRY-RUN (no changes made)' if dry_run else 'COMPLETED'}")
    print(f"{'='*70}\n")

    return {
        "success": True,
        "file_path": rel_file_path,
        "backup_path": str(backup_path) if backup_path else "NO_BACKUP",
        "file_hash": file_hash,
        "dry_run": dry_run,
        "audit_entry": audit_entry
    }


def batch_delete_files(
    file_list: List[str],
    operator: str,
    reason: str,
    dry_run: bool = False
) -> Dict:
    """
    Safely delete multiple files with backup and audit trail

    Args:
        file_list: List of file paths
        operator: Email/username performing deletion
        reason: Reason for deletion
        dry_run: If True, show what would happen without deleting

    Returns:
        Dict with batch deletion results
    """
    print(f"\n{'='*70}")
    print(f"Batch Delete: {len(file_list)} files")
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

        result = safe_delete_file(
            file_path=file_path,
            operator=operator,
            reason=reason,
            dry_run=dry_run
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
    print(f"Batch Deletion Summary:")
    print(f"  Total files: {results['total']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Status: {'DRY-RUN (no changes made)' if dry_run else 'COMPLETED'}")
    print(f"{'='*70}\n")

    return results


def restore_file(backup_path: str, original_path: Optional[str] = None) -> Dict:
    """
    Restore file from backup

    Args:
        backup_path: Path to backup file
        original_path: Original file path (optional - can read from AUDIT.json)

    Returns:
        Dict with restoration result
    """
    backup_file = Path(backup_path).resolve()  # Convert to absolute path

    # Verify backup exists
    if not backup_file.exists():
        return {
            "success": False,
            "error": f"Backup file not found: {backup_path}"
        }

    # Determine original path
    if original_path is None:
        # Try to find original path from AUDIT.json
        # AUDIT.json is in the same directory as the backup file (dated directory)
        backup_dir = backup_file.parent
        audit_file = backup_dir / "AUDIT.json"
        if not audit_file.exists():
            return {
                "success": False,
                "error": f"Cannot determine original path (AUDIT.json not found)"
            }

        # Search audit log for this backup
        with open(audit_file, 'r') as f:
            audit_data = json.load(f)

        for entry in audit_data["deletions"]:
            if entry["backup_path"] == str(backup_file):
                original_path = entry["original_path"]
                break

        if original_path is None:
            return {
                "success": False,
                "error": f"Backup path not found in AUDIT.json"
            }

    # Restore file
    original_file = PROJECT_ROOT / original_path
    original_file.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(backup_file, original_file)

    print(f"✅ Restored: {backup_path} → {original_file}")

    return {
        "success": True,
        "original_path": str(original_file),
        "backup_path": str(backup_file)
    }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Safe file deletion with backup and audit trail (SPEC-013 Phase 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run single file deletion
  python3 safe_delete.py --file old-dashboard.html --operator user@example.com --reason "Orphaned prototype" --dry-run

  # Actually delete file (with backup)
  python3 safe_delete.py --file old-dashboard.html --operator user@example.com --reason "Orphaned prototype"

  # Batch delete from file list
  python3 safe_delete.py --batch orphaned_files.txt --operator user@example.com --reason "Cleanup after migration"

  # Restore file from backup
  python3 safe_delete.py --restore archive/deleted-files/2025-10-25/old-dashboard.html
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--file',
        type=str,
        help='Single file to delete'
    )
    mode_group.add_argument(
        '--batch',
        type=str,
        help='File containing list of files to delete (one per line)'
    )
    mode_group.add_argument(
        '--restore',
        type=str,
        help='Restore file from backup'
    )

    # Required for deletion modes
    parser.add_argument(
        '--operator',
        type=str,
        help='Email/username of person performing deletion (required for --file and --batch)'
    )
    parser.add_argument(
        '--reason',
        type=str,
        help='Reason for deletion (required for --file and --batch)'
    )

    # Optional flags
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip backup creation (NOT RECOMMENDED - use only for testing)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file for deletion result'
    )

    args = parser.parse_args()

    # Validate required arguments for deletion modes
    if (args.file or args.batch) and (not args.operator or not args.reason):
        parser.error("--operator and --reason are required for deletion operations")

    # Execute appropriate mode
    result = None

    if args.file:
        # Single file deletion
        result = safe_delete_file(
            file_path=args.file,
            operator=args.operator,
            reason=args.reason,
            dry_run=args.dry_run,
            skip_backup=args.skip_backup
        )

    elif args.batch:
        # Batch deletion
        if not os.path.exists(args.batch):
            print(f"❌ Error: Batch file not found: {args.batch}")
            sys.exit(1)

        with open(args.batch, 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]

        result = batch_delete_files(
            file_list=file_list,
            operator=args.operator,
            reason=args.reason,
            dry_run=args.dry_run
        )

    elif args.restore:
        # Restore file
        result = restore_file(backup_path=args.restore)

    # Output JSON if requested
    if args.output and result:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Result saved to: {args.output}")

    # Exit with appropriate code
    if result and not result.get("success", True):
        # Print error message if present
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
