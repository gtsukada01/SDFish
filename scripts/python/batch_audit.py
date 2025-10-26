#!/usr/bin/env python3
"""
Batch File Auditing Script - Phase 3: Parallel Processing for 200+ Files

Purpose: Audit multiple files with parallel processing for performance
Governed By: SPEC-013 File Auditing & Cleanup System
Version: 3.0.0 (Phase 3 - Safe Deletion & Batch Processing)

Usage:
    # Audit all files in directory
    python3 batch_audit.py --dir . --output audit-results/

    # Audit specific file patterns
    python3 batch_audit.py --pattern "*.log" --output audit-results/

    # Audit from file list
    python3 batch_audit.py --file-list files.txt --output audit-results/

    # Skip dynamic validation for speed
    python3 batch_audit.py --dir . --output audit-results/ --skip-dynamic

    # Parallel processing (default: 4 workers)
    python3 batch_audit.py --dir . --output audit-results/ --workers 8

Features:
    - Parallel processing with multiprocessing for speed
    - Progress reporting (X/200 files audited)
    - Category-wise result aggregation
    - JSON output for automation
    - Summary statistics and recommendations
    - Integration with audit_file.py (Phase 1+2)

Performance:
    - Single-threaded: ~200 files in 15-20 minutes (static only)
    - Parallel (4 workers): ~200 files in 4-5 minutes (static only)
    - With dynamic validation: Varies based on DELETE candidates
"""

import os
import sys
import json
import argparse
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from multiprocessing import Pool, cpu_count
from functools import partial

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import audit_file module
try:
    from audit_file import audit_file
except ImportError:
    print("❌ Error: audit_file.py not found in same directory")
    print("   Please ensure audit_file.py exists in scripts/python/")
    sys.exit(1)


def find_files_in_directory(
    directory: str,
    pattern: Optional[str] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    Find all files in directory matching pattern

    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.log", "**/*.json")
        exclude_patterns: Patterns to exclude (e.g., ["node_modules/**", ".git/**"])

    Returns:
        List of file paths relative to project root
    """
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Default exclude patterns
    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules/**",
            ".git/**",
            ".next/**",
            "build/**",
            "dist/**",
            "__pycache__/**",
            "*.pyc",
            ".DS_Store",
            "venv/**",
            "env/**",
            ".venv/**"
        ]

    files = []

    # Walk directory
    for root, dirs, filenames in os.walk(dir_path):
        # Filter out excluded directories
        dirs[:] = [
            d for d in dirs
            if not any(fnmatch.fnmatch(d, p.rstrip('/**')) for p in exclude_patterns)
        ]

        for filename in filenames:
            file_path = Path(root) / filename

            # Check if file matches pattern
            if pattern:
                rel_path = file_path.relative_to(dir_path)
                if not fnmatch.fnmatch(str(rel_path), pattern):
                    continue

            # Check if file matches exclude patterns
            try:
                rel_from_project = file_path.relative_to(PROJECT_ROOT)
            except ValueError:
                # File outside project root
                rel_from_project = file_path

            exclude = False
            for exclude_pattern in exclude_patterns:
                if fnmatch.fnmatch(str(rel_from_project), exclude_pattern):
                    exclude = True
                    break

            if not exclude:
                files.append(str(file_path.relative_to(PROJECT_ROOT)))

    return sorted(files)


def audit_file_wrapper(file_path: str, skip_dynamic: bool = False) -> Dict:
    """
    Wrapper for audit_file() with error handling for multiprocessing

    Args:
        file_path: Path to file
        skip_dynamic: Whether to skip dynamic validation

    Returns:
        Audit result dict or error dict
    """
    try:
        result = audit_file(file_path, skip_dynamic=skip_dynamic)
        return result
    except Exception as e:
        # Return error result
        return {
            "file_path": file_path,
            "error": str(e),
            "classification": {
                "category": "ERROR",
                "category_name": "ERROR",
                "recommendation": "MANUAL_REVIEW"
            }
        }


def batch_audit_files(
    file_list: List[str],
    output_dir: str,
    skip_dynamic: bool = False,
    workers: int = 4
) -> Dict:
    """
    Audit multiple files with parallel processing

    Args:
        file_list: List of file paths to audit
        output_dir: Output directory for results
        skip_dynamic: Whether to skip dynamic validation
        workers: Number of parallel workers

    Returns:
        Dict with batch audit results
    """
    print(f"\n{'='*70}")
    print(f"Batch File Audit - SPEC-013 Phase 3")
    print(f"{'='*70}")
    print(f"Total files: {len(file_list)}")
    print(f"Workers: {workers}")
    print(f"Dynamic validation: {'DISABLED' if skip_dynamic else 'ENABLED'}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*70}\n")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create partial function with skip_dynamic parameter
    audit_func = partial(audit_file_wrapper, skip_dynamic=skip_dynamic)

    # Progress tracking
    results = []
    errors = []

    # Parallel processing with progress reporting
    if workers > 1:
        with Pool(processes=workers) as pool:
            # Use imap for progress tracking
            for i, result in enumerate(pool.imap(audit_func, file_list), 1):
                results.append(result)

                # Check for errors
                if "error" in result:
                    errors.append(result)

                # Progress reporting (every 10 files)
                if i % 10 == 0 or i == len(file_list):
                    print(f"  [{i}/{len(file_list)}] Progress: {i/len(file_list)*100:.1f}%")
    else:
        # Single-threaded processing
        for i, file_path in enumerate(file_list, 1):
            result = audit_func(file_path)
            results.append(result)

            if "error" in result:
                errors.append(result)

            # Progress reporting
            if i % 10 == 0 or i == len(file_list):
                print(f"  [{i}/{len(file_list)}] Progress: {i/len(file_list)*100:.1f}%")

    # Aggregate results by category
    category_counts = {
        "A": [],  # CRITICAL
        "B": [],  # ACTIVE
        "C": [],  # ARCHIVE
        "D": [],  # DELETE
        "ERROR": []
    }

    for result in results:
        category = result["classification"]["category"]
        category_counts[category].append(result)

    # Write individual results to files
    for category, category_results in category_counts.items():
        if category_results:
            category_file = output_path / f"category_{category}.json"
            with open(category_file, 'w') as f:
                json.dump(category_results, f, indent=2)
            print(f"  ✅ Saved {len(category_results)} results to: {category_file}")

    # Generate summary report
    summary = {
        "audit_date": datetime.now().isoformat(),
        "total_files_audited": len(file_list),
        "workers": workers,
        "skip_dynamic": skip_dynamic,
        "category_breakdown": {
            "CRITICAL (A)": len(category_counts["A"]),
            "ACTIVE (B)": len(category_counts["B"]),
            "ARCHIVE (C)": len(category_counts["C"]),
            "DELETE (D)": len(category_counts["D"]),
            "ERROR": len(category_counts["ERROR"])
        },
        "recommendations": {
            "KEEP": len(category_counts["A"]) + len(category_counts["B"]),
            "ARCHIVE": len(category_counts["C"]),
            "DELETE": len(category_counts["D"]),
            "MANUAL_REVIEW": len(category_counts["ERROR"])
        },
        "errors": len(errors)
    }

    # Calculate deletion safety stats for Category D
    delete_candidates = category_counts["D"]
    if delete_candidates:
        safe_to_delete = [
            r for r in delete_candidates
            if r["classification"]["recommendation"] == "SAFE_TO_DELETE"
        ]
        needs_review = [
            r for r in delete_candidates
            if r["classification"]["recommendation"] == "MANUAL_REVIEW"
        ]

        summary["deletion_safety"] = {
            "total_candidates": len(delete_candidates),
            "safe_to_delete": len(safe_to_delete),
            "needs_manual_review": len(needs_review),
            "safety_rate": f"{len(safe_to_delete)/len(delete_candidates)*100:.1f}%"
        }

    # Write summary
    summary_file = output_path / "SUMMARY.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Batch Audit Summary")
    print(f"{'='*70}")
    print(f"Total files audited: {summary['total_files_audited']}")
    print(f"\nCategory Breakdown:")
    print(f"  Category A (CRITICAL): {summary['category_breakdown']['CRITICAL (A)']} files → KEEP")
    print(f"  Category B (ACTIVE):   {summary['category_breakdown']['ACTIVE (B)']} files → KEEP")
    print(f"  Category C (ARCHIVE):  {summary['category_breakdown']['ARCHIVE (C)']} files → archive/")
    print(f"  Category D (DELETE):   {summary['category_breakdown']['DELETE (D)']} files → Evaluate for deletion")
    print(f"  Errors:                {summary['category_breakdown']['ERROR']} files → MANUAL_REVIEW")

    if "deletion_safety" in summary:
        print(f"\nDeletion Safety Analysis:")
        print(f"  Total DELETE candidates: {summary['deletion_safety']['total_candidates']}")
        print(f"  Safe to delete (≥75% confidence): {summary['deletion_safety']['safe_to_delete']}")
        print(f"  Needs manual review (<75% confidence): {summary['deletion_safety']['needs_manual_review']}")
        print(f"  Safety rate: {summary['deletion_safety']['safety_rate']}")

    print(f"\nRecommended Actions:")
    print(f"  1. Review Category D candidates: {output_path / 'category_D.json'}")
    print(f"  2. Archive Category C files: python3 scripts/python/archive_file.py")
    print(f"  3. Delete safe files: python3 scripts/python/safe_delete.py --batch")
    print(f"\nSummary saved to: {summary_file}")
    print(f"{'='*70}\n")

    return summary


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Batch file auditing with parallel processing (SPEC-013 Phase 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Audit all files in current directory
  python3 batch_audit.py --dir . --output audit-results/

  # Audit all .log files
  python3 batch_audit.py --dir . --pattern "*.log" --output audit-results/

  # Audit from file list
  python3 batch_audit.py --file-list orphaned_files.txt --output audit-results/

  # Skip dynamic validation for speed (static analysis only)
  python3 batch_audit.py --dir . --output audit-results/ --skip-dynamic

  # Use 8 parallel workers
  python3 batch_audit.py --dir . --output audit-results/ --workers 8

  # Audit specific patterns with exclusions
  python3 batch_audit.py --dir . --pattern "*.json" --exclude "node_modules/**" --output audit-results/
        """
    )

    # Input sources (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--dir',
        type=str,
        help='Directory to audit recursively'
    )
    input_group.add_argument(
        '--file-list',
        type=str,
        help='File containing list of files to audit (one per line)'
    )

    # Filtering
    parser.add_argument(
        '--pattern',
        type=str,
        help='Glob pattern to match files (e.g., "*.log", "**/*.json")'
    )
    parser.add_argument(
        '--exclude',
        type=str,
        action='append',
        help='Patterns to exclude (can be specified multiple times)'
    )

    # Output
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for audit results'
    )

    # Performance options
    parser.add_argument(
        '--workers',
        type=int,
        default=min(4, cpu_count()),
        help=f'Number of parallel workers (default: 4, max: {cpu_count()})'
    )
    parser.add_argument(
        '--skip-dynamic',
        action='store_true',
        help='Skip Phase 2 dynamic validation for faster results'
    )

    args = parser.parse_args()

    # Build file list
    file_list = []

    if args.dir:
        # Find files in directory
        try:
            file_list = find_files_in_directory(
                directory=args.dir,
                pattern=args.pattern,
                exclude_patterns=args.exclude
            )
        except Exception as e:
            print(f"❌ Error finding files: {e}")
            sys.exit(1)

    elif args.file_list:
        # Read file list from file
        if not os.path.exists(args.file_list):
            print(f"❌ Error: File list not found: {args.file_list}")
            sys.exit(1)

        with open(args.file_list, 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]

    if not file_list:
        print("❌ Error: No files found to audit")
        sys.exit(1)

    # Validate workers count
    if args.workers < 1:
        print(f"❌ Error: Workers must be ≥1 (got {args.workers})")
        sys.exit(1)

    if args.workers > cpu_count():
        print(f"⚠️  Warning: Workers ({args.workers}) exceeds CPU count ({cpu_count()})")
        print(f"   Reducing to {cpu_count()} workers")
        args.workers = cpu_count()

    # Run batch audit
    try:
        summary = batch_audit_files(
            file_list=file_list,
            output_dir=args.output,
            skip_dynamic=args.skip_dynamic,
            workers=args.workers
        )

        # Exit with success
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error during batch audit: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
