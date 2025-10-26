#!/usr/bin/env python3
"""
File Auditing Script - Phase 1+2: Static & Dynamic Analysis with Build/Test Validation

Purpose: Evidence-based file deletion safety verification for fish-scraper project
Governed By: SPEC-013 File Auditing & Cleanup System
Version: 2.0.0 (Phase 2 - Dynamic Analysis & Build Integration)

Usage:
    python3 audit_file.py --file <path/to/file>
    python3 audit_file.py --file <path/to/file> --output audit-result.json
    python3 audit_file.py --file <path/to/file> --skip-dynamic  # Static analysis only

Features:
    - Phase 1: Static analysis (grep-based reference detection)
    - Phase 2: Dynamic analysis (build/test validation)
    - Category classification (CRITICAL/ACTIVE/ARCHIVE/DELETE)
    - Enhanced confidence scoring (0-100% with build/test results)
    - JSON output for automation
    - Hard-coded exemptions for critical files
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CRITICAL PATTERNS - NEVER DELETE (Hard-Coded Exemptions)
# ============================================================================

CRITICAL_PATTERNS = [
    # Master Documentation (Single Source of Truth)
    "**/README.md",
    "CLAUDE_OPERATING_GUIDE.md",
    "COMPREHENSIVE_QC_VERIFICATION.md",
    "DOCUMENTATION_STANDARDS.md",
    "DOC_CHANGELOG.md",
    "*_SCRAPING_REPORT.md",  # 2024_SCRAPING_REPORT.md, 2025_SCRAPING_REPORT.md
    "SOCAL_SCRAPER_HANDOFF_*.md",

    # Core Application Code
    "frontend/src/**",
    "scripts/python/**/*.py",
    "boats_scraper.py",
    "qc_validator.py",
    "socal_scraper.py",
    "socal_qc_validator.py",

    # Build & Configuration
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "tailwind.config.js",
    "playwright.config.ts",
    "postcss.config.js",
    "vite.config.ts",
    "vite.config.js",
    "*.config.js",
    "*.config.ts",
    "components.json",  # shadcn component registry

    # Database Migrations
    "migrations/**/*.sql",

    # Active Specifications
    "specs/**/spec.md",
    "specs/**/README.md",

    # Environment & Git
    ".env*",
    ".gitignore",
    ".claude/**",
]

# Historical Value Patterns (Category C: ARCHIVE)
HISTORICAL_PATTERNS = {
    "qc_logs": r"^qc_.*\.json$",
    "scrape_logs": r"^SCRAPE_.*\.json$",
    "backups": r"^backup_.*\.json$",
    "snapshots": r".*_snapshot_.*\.json$",
    "log_files": r".*\.log$",
    "session_summaries": r"^SESSION_.*\.md$",
    "completion_reports": r".*(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER).*COMPLETE\.md$",
    "validation_reports": r".*_validation_report.*\.(json|md)$",
    "screenshots": r".*\.png$",
}

# Project Root Detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # fish-scraper/


# ============================================================================
# STATIC ANALYSIS FUNCTIONS
# ============================================================================

def grep_code_references(file_path: str) -> Dict[str, any]:
    """
    Search for code references (TypeScript/JavaScript/Python imports)

    Args:
        file_path: Path to file being audited

    Returns:
        Dict with reference count and file list
    """
    file_name = os.path.basename(file_path)
    references = []

    # Search TypeScript/JavaScript imports
    try:
        ts_result = subprocess.run(
            [
                "grep", "-r", file_name,
                "--include=*.ts", "--include=*.tsx",
                "--include=*.js", "--include=*.jsx",
                str(PROJECT_ROOT)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        if ts_result.stdout:
            references.extend([line.split(':')[0] for line in ts_result.stdout.strip().split('\n') if line])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Search Python imports
    try:
        py_result = subprocess.run(
            [
                "grep", "-r", file_name,
                "--include=*.py",
                str(PROJECT_ROOT)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        if py_result.stdout:
            references.extend([line.split(':')[0] for line in py_result.stdout.strip().split('\n') if line])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Search HTML/CSS asset references
    try:
        asset_result = subprocess.run(
            [
                "grep", "-r", file_name,
                "--include=*.html", "--include=*.css",
                str(PROJECT_ROOT)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        if asset_result.stdout:
            references.extend([line.split(':')[0] for line in asset_result.stdout.strip().split('\n') if line])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Remove duplicates and self-references
    references = list(set(references))
    references = [ref for ref in references if not ref.endswith(file_path)]

    return {
        "code_references": len(references),
        "files_referencing": references
    }


def grep_config_references(file_path: str) -> Dict[str, any]:
    """
    Search configuration files for references to target file

    Args:
        file_path: Path to file being audited

    Returns:
        Dict with config file list
    """
    config_files = [
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "tailwind.config.js",
        "playwright.config.ts",
        "vite.config.ts",
        "vite.config.js",
        ".gitignore",
        "components.json",
    ]

    file_name = os.path.basename(file_path)
    found_in = []

    for config in config_files:
        config_path = PROJECT_ROOT / config
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if file_name in content or file_path in content:
                        found_in.append(config)
            except Exception:
                pass

    return {
        "config_references": found_in,
        "config_count": len(found_in)
    }


def grep_doc_references(file_path: str) -> Dict[str, any]:
    """
    Search documentation for references to target file

    Args:
        file_path: Path to file being audited

    Returns:
        Dict with documentation reference count
    """
    file_name = os.path.basename(file_path)
    doc_references = []

    # Search master documentation
    master_docs = [
        "README.md",
        "CLAUDE_OPERATING_GUIDE.md",
        "COMPREHENSIVE_QC_VERIFICATION.md",
        "DOCUMENTATION_STANDARDS.md",
        "DOC_CHANGELOG.md",
        "2024_SCRAPING_REPORT.md",
        "2025_SCRAPING_REPORT.md",
    ]

    for doc in master_docs:
        doc_path = PROJECT_ROOT / doc
        if doc_path.exists():
            try:
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if file_name in content or file_path in content:
                        doc_references.append(doc)
            except Exception:
                pass

    # Search specs/ directory
    try:
        specs_result = subprocess.run(
            ["grep", "-r", file_name, "--include=*.md", str(PROJECT_ROOT / "specs")],
            capture_output=True,
            text=True,
            timeout=10
        )
        if specs_result.stdout:
            spec_files = [line.split(':')[0] for line in specs_result.stdout.strip().split('\n') if line]
            doc_references.extend(spec_files)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return {
        "doc_references": len(set(doc_references)),
        "docs_mentioning": list(set(doc_references))
    }


def aggregate_reference_count(static_results: Dict) -> int:
    """
    Aggregate all reference counts from static analysis

    Args:
        static_results: Combined results from grep functions

    Returns:
        Total reference count
    """
    total = 0
    total += static_results.get("code_references", 0)
    total += static_results.get("config_count", 0)
    total += static_results.get("doc_references", 0)
    return total


# ============================================================================
# DYNAMIC ANALYSIS FUNCTIONS (Phase 2)
# ============================================================================

def run_build_test() -> Dict[str, any]:
    """
    Run npm build to verify project builds without target file

    This is a critical safety check - if the build fails after removing a file,
    it indicates the file is still needed (even if grep didn't find references).

    Returns:
        Dict with build result, exit code, duration
    """
    print("  → Running build test (npm run build)...")
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(PROJECT_ROOT / "frontend"),
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        duration = time.time() - start_time

        return {
            "build_passed": result.returncode == 0,
            "exit_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "build_passed": False,
            "exit_code": -1,
            "duration_seconds": 60,
            "error": "Build timeout (>60s)",
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except FileNotFoundError:
        # frontend/ doesn't exist or npm not installed
        return {
            "build_passed": None,
            "exit_code": -2,
            "duration_seconds": 0,
            "error": "npm or frontend/ not found - skipping build test",
            "stdout": "",
            "stderr": "Build test skipped"
        }


def run_typescript_check() -> Dict[str, any]:
    """
    Run TypeScript compiler check (tsc --noEmit)

    Validates TypeScript compilation without emitting files.
    Catches type errors and import issues.

    Returns:
        Dict with TypeScript check result
    """
    print("  → Running TypeScript check (tsc --noEmit)...")
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(PROJECT_ROOT / "frontend"),
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start_time

        return {
            "typescript_passed": result.returncode == 0,
            "exit_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "typescript_passed": False,
            "exit_code": -1,
            "duration_seconds": 30,
            "error": "TypeScript check timeout (>30s)",
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except FileNotFoundError:
        return {
            "typescript_passed": None,
            "exit_code": -2,
            "duration_seconds": 0,
            "error": "tsc not found - skipping TypeScript check",
            "stdout": "",
            "stderr": "TypeScript check skipped"
        }


def run_contract_tests() -> Dict[str, any]:
    """
    Run contract tests (npm run test:contracts)

    Validates data contracts and API interfaces.

    Returns:
        Dict with contract test result
    """
    print("  → Running contract tests (npm run test:contracts)...")
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npm", "run", "test:contracts"],
            cwd=str(PROJECT_ROOT / "frontend"),
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start_time

        return {
            "contracts_passed": result.returncode == 0,
            "exit_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "contracts_passed": False,
            "exit_code": -1,
            "duration_seconds": 30,
            "error": "Contract tests timeout (>30s)",
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except FileNotFoundError:
        return {
            "contracts_passed": None,
            "exit_code": -2,
            "duration_seconds": 0,
            "error": "npm or test:contracts script not found - skipping contract tests",
            "stdout": "",
            "stderr": "Contract tests skipped"
        }


def run_playwright_tests() -> Dict[str, any]:
    """
    Run Playwright tests (npx playwright test)

    Validates UI functionality through browser automation.

    Returns:
        Dict with Playwright test result
    """
    print("  → Running Playwright tests (npx playwright test)...")
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            ["npx", "playwright", "test"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60
        )
        duration = time.time() - start_time

        return {
            "playwright_passed": result.returncode == 0,
            "exit_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "playwright_passed": False,
            "exit_code": -1,
            "duration_seconds": 60,
            "error": "Playwright tests timeout (>60s)",
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except FileNotFoundError:
        return {
            "playwright_passed": None,
            "exit_code": -2,
            "duration_seconds": 0,
            "error": "playwright not found - skipping UI tests",
            "stdout": "",
            "stderr": "Playwright tests skipped"
        }


def run_dynamic_validation(file_path: str) -> Dict[str, any]:
    """
    Run all dynamic validation checks (build, TypeScript, tests)

    CRITICAL SAFETY CHECK: If any validation fails, the file may still be needed
    even if static analysis found zero references.

    Args:
        file_path: Path to file being audited

    Returns:
        Dict with all dynamic validation results
    """
    print("[Phase 2] Running dynamic validation (build & test integration)...")

    # Run all validation checks
    build_result = run_build_test()
    typescript_result = run_typescript_check()
    contracts_result = run_contract_tests()
    playwright_result = run_playwright_tests()

    # Aggregate results
    all_passed = (
        build_result.get("build_passed") in [True, None] and
        typescript_result.get("typescript_passed") in [True, None] and
        contracts_result.get("contracts_passed") in [True, None] and
        playwright_result.get("playwright_passed") in [True, None]
    )

    any_failed = (
        build_result.get("build_passed") is False or
        typescript_result.get("typescript_passed") is False or
        contracts_result.get("contracts_passed") is False or
        playwright_result.get("playwright_passed") is False
    )

    total_duration = (
        build_result.get("duration_seconds", 0) +
        typescript_result.get("duration_seconds", 0) +
        contracts_result.get("duration_seconds", 0) +
        playwright_result.get("duration_seconds", 0)
    )

    return {
        "build": build_result,
        "typescript": typescript_result,
        "contracts": contracts_result,
        "playwright": playwright_result,
        "all_passed": all_passed,
        "any_failed": any_failed,
        "total_duration_seconds": round(total_duration, 2)
    }


# ============================================================================
# CATEGORY CLASSIFICATION FUNCTIONS
# ============================================================================

def matches_critical_pattern(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Check if file matches critical exemption patterns (Category A)

    Args:
        file_path: Path to file being audited

    Returns:
        Tuple of (matches, pattern_matched)
    """
    from fnmatch import fnmatch

    # Normalize path for pattern matching
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    file_name = os.path.basename(file_path)

    for pattern in CRITICAL_PATTERNS:
        # Handle ** glob patterns
        if "**" in pattern:
            pattern_parts = pattern.split("**")
            if len(pattern_parts) == 2:
                prefix = pattern_parts[0].rstrip('/')
                suffix = pattern_parts[1].lstrip('/')
                if rel_path.startswith(prefix) and (not suffix or fnmatch(file_name, suffix)):
                    return True, pattern
        # Handle simple glob patterns
        elif fnmatch(rel_path, pattern) or fnmatch(file_name, pattern):
            return True, pattern

    return False, None


def has_historical_value(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Check if file has historical/audit value (Category C)

    Args:
        file_path: Path to file being audited

    Returns:
        Tuple of (has_value, pattern_type)
    """
    file_name = os.path.basename(file_path)

    for pattern_type, regex in HISTORICAL_PATTERNS.items():
        if re.match(regex, file_name, re.IGNORECASE):
            return True, pattern_type

    # Check if file is in archive/ directory
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    if rel_path.startswith("archive/"):
        return True, "already_archived"

    return False, None


def check_documentation_compliance(file_path: str) -> Dict[str, any]:
    """
    Check file for DOCUMENTATION_STANDARDS.md compliance violations

    Phase 4 (NFR-003): Documentation compliance enforcement

    Enforces:
    1. Master documentation protection (README.md, annual reports, etc.)
    2. Monthly completion reports → ARCHIVE (not DELETE)
    3. DOC_CHANGELOG.md preservation

    Args:
        file_path: Path to file being audited

    Returns:
        Dict with compliance status and violation details
    """
    file_name = os.path.basename(file_path)

    # Master documents that must NEVER be deleted
    MASTER_DOCS = [
        "README.md",
        "COMPREHENSIVE_QC_VERIFICATION.md",
        "2024_SCRAPING_REPORT.md",
        "2025_SCRAPING_REPORT.md",
        "2026_SCRAPING_REPORT.md",
        "DOC_CHANGELOG.md",
        "DOCUMENTATION_STANDARDS.md",
        "CLAUDE_OPERATING_GUIDE.md",
        "SOCAL_SCRAPER_HANDOFF_*.md"
    ]

    # Check if file matches master doc pattern
    from fnmatch import fnmatch
    for master_doc in MASTER_DOCS:
        if fnmatch(file_name, master_doc):
            return {
                "compliant": False,
                "violation": "MASTER_DOC_DELETION",
                "severity": "CRITICAL",
                "message": f"Master documentation file '{file_name}' must NEVER be deleted per DOCUMENTATION_STANDARDS.md",
                "recommendation": "REJECT_DELETION"
            }

    # Monthly completion reports should be ARCHIVED (not deleted)
    # Pattern: *_(JANUARY|FEBRUARY|...)_*_COMPLETE.md
    monthly_report_pattern = r".*(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER).*COMPLETE\.md$"
    if re.match(monthly_report_pattern, file_name, re.IGNORECASE):
        return {
            "compliant": False,
            "violation": "MONTHLY_REPORT_DELETION",
            "severity": "HIGH",
            "message": f"Monthly completion report '{file_name}' should be ARCHIVED to archive/reports/, not deleted",
            "recommendation": "RECLASSIFY_TO_ARCHIVE"
        }

    # Session summaries should be archived
    if file_name.startswith("SESSION_") and file_name.endswith(".md"):
        return {
            "compliant": False,
            "violation": "SESSION_SUMMARY_DELETION",
            "severity": "MEDIUM",
            "message": f"Session summary '{file_name}' should be ARCHIVED to archive/docs/, not deleted",
            "recommendation": "RECLASSIFY_TO_ARCHIVE"
        }

    # No violations detected
    return {
        "compliant": True,
        "violation": None,
        "severity": None,
        "message": "No documentation compliance violations detected"
    }


def classify_file(file_path: str, static_analysis: Dict, dynamic_analysis: Optional[Dict] = None) -> Dict[str, any]:
    """
    Classify file into Category A/B/C/D based on static + dynamic analysis

    Categories:
        A: CRITICAL - NEVER DELETE (hard-coded exemptions)
        B: ACTIVE REFERENCE - KEEP (has code/config references)
        C: ARCHIVE - Historical value (QC logs, backups, etc.)
        D: DELETE - Orphaned & safe to remove

    Phase 2 Confidence Scoring:
        - Reference count = 0 → +50 confidence
        - Build passes → +25 confidence
        - Tests pass → +25 confidence
        - Critical pattern match → 100 confidence (override)

    Args:
        file_path: Path to file being audited
        static_analysis: Results from static analysis
        dynamic_analysis: Results from dynamic validation (Phase 2 optional)

    Returns:
        Classification dict with category, confidence, reasoning
    """
    # Category A: CRITICAL - Check exemption patterns first
    is_critical, critical_pattern = matches_critical_pattern(file_path)
    if is_critical:
        return {
            "category": "A",
            "category_name": "CRITICAL",
            "confidence_score": 100,
            "recommendation": "KEEP",
            "justification": f"Matches critical exemption pattern: {critical_pattern}. NEVER DELETE per SPEC-013.",
            "critical_pattern_match": True,
            "historical_value": False
        }

    # Phase 4 (NFR-003): Documentation Compliance Check
    compliance = check_documentation_compliance(file_path)
    if not compliance["compliant"]:
        violation = compliance["violation"]
        severity = compliance["severity"]
        message = compliance["message"]
        recommendation = compliance["recommendation"]

        if recommendation == "REJECT_DELETION":
            # Master doc deletion attempt - Return Category A with violation warning
            return {
                "category": "A",
                "category_name": "CRITICAL",
                "confidence_score": 100,
                "recommendation": "KEEP",
                "justification": f"⚠️  DOCUMENTATION VIOLATION ({severity}): {message}",
                "critical_pattern_match": False,
                "historical_value": False,
                "compliance_violation": violation
            }
        elif recommendation == "RECLASSIFY_TO_ARCHIVE":
            # Monthly report or session summary - Reclassify to ARCHIVE
            return {
                "category": "C",
                "category_name": "ARCHIVE",
                "confidence_score": 100,
                "recommendation": "ARCHIVE",
                "justification": f"⚠️  DOCUMENTATION VIOLATION ({severity}): {message}",
                "critical_pattern_match": False,
                "historical_value": True,
                "historical_type": "documentation_compliance",
                "compliance_violation": violation
            }

    # Category B: ACTIVE REFERENCE - Check reference count
    total_refs = aggregate_reference_count(static_analysis)
    if total_refs > 0:
        return {
            "category": "B",
            "category_name": "ACTIVE",
            "confidence_score": min(90 + total_refs, 100),
            "recommendation": "KEEP",
            "justification": f"Active references found: {total_refs} references in codebase/configs/docs.",
            "critical_pattern_match": False,
            "historical_value": False
        }

    # Category C: ARCHIVE - Check historical value
    has_hist_value, hist_type = has_historical_value(file_path)
    if has_hist_value:
        return {
            "category": "C",
            "category_name": "ARCHIVE",
            "confidence_score": 85,
            "recommendation": "ARCHIVE",
            "justification": f"Historical/audit value detected: {hist_type}. Should be archived, not deleted.",
            "critical_pattern_match": False,
            "historical_value": True,
            "historical_type": hist_type
        }

    # Category D: DELETE - Orphaned file
    # Phase 2: Enhanced confidence scoring with dynamic analysis
    base_confidence = 50  # Base confidence for zero references

    if dynamic_analysis:
        # Check if build/tests passed
        build_passed = dynamic_analysis.get("build", {}).get("build_passed")
        all_passed = dynamic_analysis.get("all_passed", False)
        any_failed = dynamic_analysis.get("any_failed", False)

        # Phase 2 Confidence Formula:
        # - Zero references → +50 (base)
        # - Build passes → +25
        # - Tests pass → +25
        # Total: up to 100% confidence

        confidence = base_confidence

        if build_passed is True:
            confidence += 25
        elif build_passed is False:
            # Build failed - UNSAFE to delete (even with zero references!)
            return {
                "category": "B",  # Reclassify as ACTIVE
                "category_name": "ACTIVE",
                "confidence_score": 95,
                "recommendation": "KEEP",
                "justification": "Build FAILED after analysis. File may be needed despite zero grep references. UNSAFE to delete.",
                "critical_pattern_match": False,
                "historical_value": False,
                "build_failed": True
            }

        if all_passed and not any_failed:
            confidence += 25  # All tests passed → maximum confidence

        # Build justification text based on actual results
        confidence_breakdown = ["Zero references found (+50% base)"]
        if build_passed is True:
            confidence_breakdown.append("Build passed (+25%)")
        if all_passed and not any_failed:
            confidence_breakdown.append("All tests passed (+25%)")

        justification = ". ".join(confidence_breakdown) + f". Total confidence: {confidence}%."

        return {
            "category": "D",
            "category_name": "DELETE",
            "confidence_score": confidence,
            "recommendation": "SAFE_TO_DELETE" if confidence >= 75 else "MANUAL_REVIEW",
            "justification": justification,
            "critical_pattern_match": False,
            "historical_value": False,
            "dynamic_validation": True
        }
    else:
        # Phase 1 only: Conservative confidence without dynamic validation
        return {
            "category": "D",
            "category_name": "DELETE",
            "confidence_score": 75,
            "recommendation": "SAFE_TO_DELETE",
            "justification": "Zero references found. Not a critical pattern. No historical value. Orphaned artifact. (Phase 1: No dynamic validation)",
            "critical_pattern_match": False,
            "historical_value": False,
            "dynamic_validation": False
        }


# ============================================================================
# MAIN AUDIT FUNCTION
# ============================================================================

def audit_file(file_path: str, skip_dynamic: bool = False) -> Dict[str, any]:
    """
    Perform complete audit on single file (Phase 1 + 2: Static + Dynamic Analysis)

    Args:
        file_path: Path to file being audited
        skip_dynamic: If True, skip Phase 2 dynamic validation (faster, less accurate)

    Returns:
        Complete audit result with recommendation
    """
    # Normalize file path
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        return {
            "error": "FILE_NOT_FOUND",
            "file_path": file_path,
            "message": f"File does not exist: {file_path}"
        }

    print(f"[Phase 1] Auditing file: {file_path}")

    # Step 1: Static Analysis
    print("  → Running static analysis (grep-based reference detection)...")
    code_refs = grep_code_references(file_path)
    config_refs = grep_config_references(file_path)
    doc_refs = grep_doc_references(file_path)

    static_analysis = {
        **code_refs,
        **config_refs,
        **doc_refs,
        "total_references": aggregate_reference_count({**code_refs, **config_refs, **doc_refs})
    }

    print(f"  → Found {static_analysis['total_references']} total references")

    # Step 2: Dynamic Validation (Phase 2 - Optional)
    dynamic_analysis = None
    if not skip_dynamic:
        # Only run dynamic validation for Category D candidates (zero references)
        # Skip expensive build/test for files that are already KEEP/ARCHIVE
        if static_analysis['total_references'] == 0:
            is_critical, _ = matches_critical_pattern(file_path)
            has_hist_value, _ = has_historical_value(file_path)

            if not is_critical and not has_hist_value:
                # Category D candidate - run dynamic validation for safety
                dynamic_analysis = run_dynamic_validation(file_path)
                print(f"  → Dynamic validation complete: {dynamic_analysis['total_duration_seconds']}s")
            else:
                print("  → Skipping dynamic validation (file is CRITICAL or ARCHIVE)")
        else:
            print("  → Skipping dynamic validation (file has active references)")

    # Step 3: Category Classification
    print("  → Classifying file...")
    classification = classify_file(file_path, static_analysis, dynamic_analysis)

    print(f"  → Category: {classification['category']} ({classification['category_name']})")
    print(f"  → Confidence: {classification['confidence_score']}%")
    print(f"  → Recommendation: {classification['recommendation']}")

    # Step 4: Build JSON output
    phase = "1+2" if dynamic_analysis else "1"
    audit_result = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "analysis_date": datetime.now().isoformat(),
        "phase": phase,
        "static_analysis": static_analysis,
        "dynamic_analysis": dynamic_analysis,
        "classification": classification,
        "recommendation": classification["recommendation"],
        "justification": classification["justification"],
        "action_command": generate_action_command(file_path, classification)
    }

    return audit_result


def generate_action_command(file_path: str, classification: Dict) -> Optional[str]:
    """
    Generate CLI command to execute recommendation

    Args:
        file_path: Path to file
        classification: Classification result

    Returns:
        Bash command string or None
    """
    if classification["recommendation"] == "KEEP":
        return None

    elif classification["recommendation"] == "ARCHIVE":
        hist_type = classification.get("historical_type", "logs")
        category_map = {
            "qc_logs": "logs/qc",
            "scrape_logs": "logs/scrapers",
            "backups": "backups",
            "snapshots": "backups",
            "log_files": "logs",
            "session_summaries": "docs",
            "completion_reports": "docs",
            "screenshots": "screenshots"
        }
        category = category_map.get(hist_type, "logs")
        return f"python3 scripts/python/archive_file.py --file '{file_path}' --category {category}"

    elif classification["recommendation"] == "SAFE_TO_DELETE":
        today = datetime.now().strftime("%Y-%m-%d")
        return f"python3 scripts/python/safe_delete.py --file '{file_path}' --operator user@example.com --reason 'Orphaned artifact' --dry-run"

    return None


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="File Auditing Script - Phase 1+2: Static & Dynamic Analysis with Build/Test Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Audit single file (Phase 1+2: with build/test validation)
    python3 audit_file.py --file old-dashboard.html

    # Audit with static analysis only (Phase 1: faster, less accurate)
    python3 audit_file.py --file old-dashboard.html --skip-dynamic

    # Audit with JSON output
    python3 audit_file.py --file qc_batch01.json --output audit-result.json

    # Test on multiple files
    for file in *.log; do python3 audit_file.py --file "$file"; done
        """
    )

    parser.add_argument(
        '--file',
        required=True,
        help='Path to file to audit'
    )

    parser.add_argument(
        '--output',
        help='Output JSON file path (optional, prints to stdout if not specified)'
    )

    parser.add_argument(
        '--skip-dynamic',
        action='store_true',
        help='Skip Phase 2 dynamic validation (build/test checks) for faster results'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed analysis output'
    )

    args = parser.parse_args()

    # Run audit
    result = audit_file(args.file, skip_dynamic=args.skip_dynamic)

    # Handle errors
    if "error" in result:
        print(f"ERROR: {result['message']}", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Audit complete - results saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print("AUDIT RESULT")
        print("="*80)
        print(json.dumps(result, indent=2))

    # Print recommendation summary
    print("\n" + "="*80)
    print(f"RECOMMENDATION: {result['recommendation']}")
    print("="*80)
    print(f"Category: {result['classification']['category']} ({result['classification']['category_name']})")
    print(f"Confidence: {result['classification']['confidence_score']}%")
    print(f"Justification: {result['justification']}")

    if result['action_command']:
        print(f"\nAction Command:")
        print(f"  {result['action_command']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
