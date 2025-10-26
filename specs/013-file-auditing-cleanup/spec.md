# Specification 013: Automated File Auditing & Cleanup System

**Version**: 2.0.0 (Enterprise-Grade)
**Date**: October 25, 2025 (Enhanced with Industry Benchmarking)
**Status**: DRAFT - PENDING APPROVAL
**Governed By**: DOCUMENTATION_STANDARDS.md (Single Source of Truth)
**Triggered By**: Repository cleanup requirement - 200+ orphaned files cluttering workspace
**Author**: Fishing Intelligence Platform
**Priority**: P2 - MEDIUM (Developer Experience & Maintainability)

---

## Executive Summary

### Problem Statement

The fish-scraper repository has accumulated **200+ files** over 10 months of development, many of which are orphaned artifacts from completed features, historical logs, and superseded documentation. Without systematic auditing, developers face:

**Critical Challenges**:
1. **Unclear Deletion Safety** - No systematic way to determine if a file is still needed
2. **Fear of Breaking Production** - Developers avoid cleanup due to risk of deleting critical assets
3. **Manual Grep Workflows** - Time-consuming reference searches for each file
4. **No Audit Trail** - Deletions lack documentation of reasoning and evidence
5. **Inconsistent Standards** - No clear rules for what constitutes "safe to delete"
6. **Repository Bloat** - Slower git operations, harder codebase navigation
7. **Violation of Documentation Standards** - Monthly completion reports duplicating master docs (per DOCUMENTATION_STANDARDS.md)

### Impact

**Developer Productivity Crisis**:
- **30+ minutes per file** for manual safety verification
- **200+ files = 100+ hours** of manual audit work
- **High cognitive load** - developers must know entire codebase to assess safety
- **Regression risk** - accidental deletion of critical files breaks production

**Codebase Quality Issues**:
- **Orphaned artifacts** create confusion about current architecture
- **Historical logs** (500+ .json/.log files) obscure active work
- **Duplicate documentation** violates single source of truth mandate
- **Git performance** degraded by large file count

**Compliance Issues**:
- **DOCUMENTATION_STANDARDS.md violation** - monthly completion files should be archived
- **CLAUDE.md mandate** - master docs (README.md, COMPREHENSIVE_QC_VERIFICATION.md) must never be deleted
- **No audit trail** for file deletions (who, when, why)

### Solution

**AI-Powered File Auditing System** with enterprise-grade compliance (IIA 2024, COBIT, COSO AI Frameworks):

**Core Features** (Phases 1-4):
1. **Claude-Optimized Auditing Prompt** - Structured analysis with evidence-based decision making
2. **Multi-Layer Verification** - Static analysis (grep) + Dynamic validation (build/test)
3. **Category Classification System** - CRITICAL/ACTIVE/ARCHIVE/DELETE with confidence scoring
4. **Automated Batch Processing** - Audit 200+ files with single command
5. **Safe Deletion Protocol** - Backup-first with full audit trail
6. **Documentation Compliance** - Enforces DOCUMENTATION_STANDARDS.md rules
7. **Master Doc Protection** - Hard-coded exemptions for critical files

**Enterprise Enhancements** (Phase 5):
8. **Continuous Monitoring** - Weekly automated audits via GitHub Actions, drift detection
9. **Governance Metadata** - Ownership, purpose, retention policy tracking per COBIT 2024
10. **Sandbox Validation** - CI/CD-integrated testing before actual deletion
11. **Sensitive Data Detection** - PII/credential scanning with secure deletion (GDPR/ICT4Peace)
12. **Self-Healing Rollback** - Automatic recovery from failed deletions within 60 seconds

---

## Functional Requirements

### FR-001: Claude-Optimized Auditing Prompt

**Priority**: P0 - CRITICAL (Foundation for All Decisions)

**Requirement**: Create structured Claude prompt template that produces evidence-based, auditable file deletion decisions with JSON output for automation.

**Design Principles**:
- **Evidence-based** - All decisions backed by grep results, build tests, config checks
- **Conservative bias** - When uncertain, recommend KEEP or MANUAL REVIEW
- **Structured output** - JSON schema for automation and batch processing
- **Confidence scoring** - 0-100% confidence with clear thresholds
- **Project-aware** - Understands fish-scraper architecture (frontend/, scripts/python/, etc.)

**Prompt Structure**:

```markdown
# File Deletion Audit Prompt

## Context
Project: SD Fishing Dashboard (React 18 + Python scrapers)
File: {{FILE_PATH}}

## Phase 1: Static Analysis
- Direct references (grep -r "{{FILE_NAME}}" codebase)
- Configuration appearances (package.json, tsconfig.json, etc.)
- Documentation mentions (*.md files)

## Phase 2: Dynamic Analysis
- Build test (npm run build without file)
- Test suite validation (npm test, playwright test)
- Import error detection (tsc --noEmit)

## Phase 3: Classification
- Category A: CRITICAL (never delete)
- Category B: ACTIVE (referenced by code)
- Category C: ARCHIVE (historical value)
- Category D: DELETE (orphaned, safe to remove)

## Phase 4: Evidence & Decision
- Reference count: [number]
- Config appearances: [list]
- Build impact: [PASS/FAIL]
- Confidence: [0-100%]
- Recommendation: [KEEP/ARCHIVE/DELETE/REVIEW]

## Phase 5: JSON Output
{
  "file_path": "path/to/file",
  "category": "D",
  "confidence_score": 95,
  "recommendation": "SAFE_TO_DELETE",
  "justification": "Zero references, build passes, not critical",
  "action_command": "mv path/to/file archive/deleted-files/2025-10-25/"
}
```

**Acceptance Criteria**:
- ✅ Prompt template supports variable substitution ({{FILE_PATH}}, {{FILE_NAME}})
- ✅ All project-specific exemptions documented (README.md, CLAUDE_OPERATING_GUIDE.md, etc.)
- ✅ JSON output schema defined for automation
- ✅ Confidence thresholds documented (≥75% for auto-delete)
- ✅ Example walkthroughs included in prompt

---

### FR-002: Static Analysis - Reference Detection

**Priority**: P0 - CRITICAL (Primary Safety Check)

**Requirement**: Systematically search codebase for all references to target file before deletion.

**Search Scope**:

1. **Code Imports/Requires**
   ```bash
   # TypeScript/JavaScript imports
   grep -r "{{FILE_NAME}}" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" .

   # Python imports
   grep -r "{{FILE_NAME}}" --include="*.py" .
   ```

2. **Configuration Files**
   ```bash
   # Package configs
   grep -r "{{FILE_PATH}}" --include="package.json" --include="tsconfig.json" .

   # Build configs
   grep -r "{{FILE_PATH}}" --include="*.config.js" --include="*.config.ts" .

   # Playwright/test configs
   grep -r "{{FILE_PATH}}" --include="playwright.config.ts" .
   ```

3. **Asset References**
   ```bash
   # HTML/CSS references
   grep -r "{{FILE_NAME}}" --include="*.html" --include="*.css" .

   # Image/icon references
   grep -r "{{FILE_NAME}}" --include="*.svg" --include="*.png" .
   ```

4. **Documentation References**
   ```bash
   # Check if file is documented
   grep -r "{{FILE_NAME}}" --include="*.md" README.md specs/ archive/ .
   ```

**Result Format**:
```json
{
  "static_analysis": {
    "code_references": 0,
    "config_references": [],
    "asset_references": 0,
    "doc_references": 1,
    "total_references": 1
  }
}
```

**Acceptance Criteria**:
- ✅ All grep searches executed with proper file filters
- ✅ Results aggregated into reference count
- ✅ Configuration file appearances listed explicitly
- ✅ Zero false negatives (all references found)
- ✅ Search completes in <5 seconds per file

---

### FR-003: Dynamic Analysis - Build & Test Validation

**Priority**: P0 - CRITICAL (Verify Production Safety)

**Requirement**: Validate that removing the file does not break builds, tests, or runtime functionality.

**Validation Tests**:

1. **Frontend Build Test**
   ```bash
   cd frontend
   npm run build  # Must complete without errors

   # Expected output:
   # ✅ Built successfully
   # ❌ ERROR: Cannot find module './missing-file'
   ```

2. **TypeScript Compilation Test**
   ```bash
   cd frontend
   npx tsc --noEmit  # Must have no errors related to target file

   # Expected: Zero import errors for deleted file
   ```

3. **Test Suite Validation**
   ```bash
   # Contract tests
   npm --prefix frontend run test:contracts

   # Playwright UI tests
   npx playwright test

   # Expected: All tests pass
   ```

4. **Dev Server Test** (Optional - slower)
   ```bash
   cd frontend
   timeout 10 npm run dev  # Should start without errors
   ```

**Test Orchestration**:
```python
def run_dynamic_validation(file_path: str) -> Dict:
    """Run all dynamic tests, return aggregated results"""

    results = {
        "build_test": run_build_test(),
        "typescript_test": run_typescript_check(),
        "contract_tests": run_contract_tests(),
        "ui_tests": run_playwright_tests(),
        "all_passed": False
    }

    results["all_passed"] = all([
        results["build_test"]["passed"],
        results["typescript_test"]["passed"],
        results["contract_tests"]["passed"],
        results["ui_tests"]["passed"]
    ])

    return results
```

**Acceptance Criteria**:
- ✅ Build test executed and result captured
- ✅ TypeScript errors detected and reported
- ✅ Test suite failures attributed to file deletion
- ✅ Dynamic tests complete in <60 seconds total
- ✅ Test failures trigger KEEP recommendation (≥1 failure = UNSAFE)

---

### FR-004: Multi-Category Classification System

**Priority**: P0 - CRITICAL (Decision Framework)

**Requirement**: Classify every file into exactly one category with clear rules and exemptions.

**Category Definitions**:

#### **Category A: CRITICAL - NEVER DELETE**
Files essential for production operation. **HARD-CODED EXEMPTIONS** - bypass all analysis.

**Automatic Exemptions**:
```python
CRITICAL_PATTERNS = [
    # Master documentation (single source of truth)
    "**/README.md",
    "**/CLAUDE_OPERATING_GUIDE.md",
    "**/COMPREHENSIVE_QC_VERIFICATION.md",
    "**/DOCUMENTATION_STANDARDS.md",
    "**/DOC_CHANGELOG.md",
    "**/*_SCRAPING_REPORT.md",  # 2024/2025 annual reports

    # Core application code
    "frontend/src/**",
    "scripts/python/**/*.py",

    # Build configuration
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/tailwind.config.js",
    "frontend/playwright.config.ts",

    # Database migrations
    "migrations/**/*.sql",

    # Active specifications
    "specs/**/spec.md",

    # Environment configs
    ".env*",
    ".gitignore",
    ".claude/**"
]
```

**Decision Logic**:
```python
if any(fnmatch.fnmatch(file_path, pattern) for pattern in CRITICAL_PATTERNS):
    return {
        "category": "A",
        "recommendation": "KEEP",
        "confidence_score": 100,
        "justification": "Protected by hard-coded exemption (critical file)"
    }
```

#### **Category B: ACTIVE REFERENCE - KEEP**
Files with active references in codebase.

**Criteria**:
- Reference count > 0 (from static analysis)
- Imported by active code
- Referenced in package.json scripts
- Linked from active documentation

**Example**: Component file used by 3 other components

#### **Category C: HISTORICAL VALUE - ARCHIVE**
Files with no active references but audit/historical value.

**Criteria**:
- Zero active references
- Completed specification documents
- QC validation reports (qc_*.json)
- Scraping logs (*.log older than 30 days)
- Monthly completion reports (violating DOCUMENTATION_STANDARDS.md)
- Backup snapshots (backup_*.json)

**Archive Destinations**:
```
archive/
├── logs/           # *.log files
├── reports/
│   ├── qc/         # qc_*.json files
│   └── scrape/     # SCRAPE_*.json files
├── backups/        # backup_*.json files
├── docs/           # Completed specs, monthly reports
└── screenshots/    # Historical UI screenshots
```

#### **Category D: SAFE TO DELETE - ORPHANED**
Files meeting ALL criteria - true orphans.

**Criteria (ALL MUST BE TRUE)**:
- ✅ Zero references in codebase (grep returns nothing)
- ✅ Not in any configuration file
- ✅ Build/tests pass without it
- ✅ Not master documentation (README.md, etc.)
- ✅ Not in critical directories (src/, scripts/python/, migrations/)
- ✅ No historical audit value
- ✅ Confidence score ≥75%

**Example**: `old-dashboard.html` from early prototype, fully replaced

**Classification Algorithm**:
```python
def classify_file(file_path: str, static_analysis: Dict, dynamic_analysis: Dict) -> str:
    """Determine category A/B/C/D"""

    # Check critical patterns first
    if is_critical_file(file_path):
        return "A"

    # Active references = keep
    if static_analysis["total_references"] > 0:
        return "B"

    # Has historical value = archive
    if has_historical_value(file_path):
        return "C"

    # All criteria met = safe to delete
    if all([
        static_analysis["total_references"] == 0,
        dynamic_analysis["all_passed"],
        not is_master_doc(file_path),
        not in_critical_directory(file_path)
    ]):
        return "D"

    # Uncertain = manual review
    return "MANUAL_REVIEW"
```

**Acceptance Criteria**:
- ✅ Every file assigned exactly one category
- ✅ Critical patterns protect master docs
- ✅ Historical value detection accurate (QC logs, backups, etc.)
- ✅ Category D only assigned when ALL safety criteria met
- ✅ Uncertain cases default to MANUAL_REVIEW (conservative bias)

---

### FR-005: Safe Deletion Protocol with Audit Trail

**Priority**: P0 - CRITICAL (Prevent Data Loss)

**Requirement**: All file deletions MUST be reversible, audited, and follow backup-first protocol.

**Deletion Workflow**:

1. **Pre-Deletion Backup**
   ```python
   def backup_file_before_deletion(file_path: str, operator: str, reason: str) -> str:
       """
       Create timestamped backup before deletion

       Returns: backup file path
       """
       timestamp = datetime.now().strftime('%Y-%m-%d')
       backup_dir = f"archive/deleted-files/{timestamp}"
       os.makedirs(backup_dir, exist_ok=True)

       # Preserve directory structure in backup
       relative_path = file_path.lstrip('./')
       backup_path = os.path.join(backup_dir, relative_path)
       os.makedirs(os.path.dirname(backup_path), exist_ok=True)

       # Copy file to backup location
       shutil.copy2(file_path, backup_path)

       # Create audit metadata
       audit_file = os.path.join(backup_dir, "AUDIT.json")
       audit_entry = {
           "file_path": file_path,
           "backup_path": backup_path,
           "deleted_at": datetime.utcnow().isoformat(),
           "operator": operator,
           "reason": reason,
           "file_size": os.path.getsize(file_path),
           "file_hash": compute_file_hash(file_path)
       }

       # Append to audit log
       if os.path.exists(audit_file):
           with open(audit_file, 'r') as f:
               audit_log = json.load(f)
       else:
           audit_log = {"deletions": []}

       audit_log["deletions"].append(audit_entry)

       with open(audit_file, 'w') as f:
           json.dump(audit_log, f, indent=2)

       return backup_path
   ```

2. **Git Commit Before Deletion**
   ```bash
   # Create safety commit before any deletions
   git add -A
   git commit -m "Pre-deletion safety checkpoint - $(date +%Y-%m-%d)"

   # Now deletions are reversible via git revert
   ```

3. **Deletion Execution**
   ```python
   def safe_delete_file(
       file_path: str,
       operator: str,
       reason: str,
       dry_run: bool = True
   ) -> Dict:
       """
       Safely delete file with full audit trail

       Args:
           file_path: Path to file to delete
           operator: Who is performing deletion (email/username)
           reason: Why file is being deleted
           dry_run: If True, show what would happen without deleting
       """

       if dry_run:
           print(f"DRY RUN: Would delete {file_path}")
           print(f"Operator: {operator}")
           print(f"Reason: {reason}")
           return {"status": "dry_run", "file_path": file_path}

       # Backup first
       backup_path = backup_file_before_deletion(file_path, operator, reason)
       print(f"✅ Backed up to {backup_path}")

       # Delete file
       os.remove(file_path)
       print(f"✅ Deleted {file_path}")

       return {
           "status": "deleted",
           "file_path": file_path,
           "backup_path": backup_path,
           "operator": operator,
           "timestamp": datetime.utcnow().isoformat()
       }
   ```

4. **Batch Deletion with Transaction Safety**
   ```python
   def batch_delete_files(
       files_to_delete: List[str],
       operator: str,
       dry_run: bool = True
   ) -> Dict:
       """
       Delete multiple files with rollback capability
       """
       results = {
           "total": len(files_to_delete),
           "deleted": [],
           "failed": [],
           "backed_up": []
       }

       try:
           for file_path in files_to_delete:
               result = safe_delete_file(
                   file_path,
                   operator,
                   reason="Batch cleanup - orphaned file",
                   dry_run=dry_run
               )

               if result["status"] == "deleted":
                   results["deleted"].append(file_path)
                   results["backed_up"].append(result["backup_path"])

       except Exception as e:
           logger.error(f"Batch deletion failed: {e}")
           print(f"⚠️  ROLLBACK: Restore from backups in {backup_dir}")
           results["error"] = str(e)

       return results
   ```

5. **Recovery Procedure**
   ```bash
   # Restore single file
   cp archive/deleted-files/2025-10-25/path/to/file path/to/file

   # Restore all files from date
   rsync -av archive/deleted-files/2025-10-25/ ./

   # OR revert via git
   git revert <commit-sha>
   ```

**Acceptance Criteria**:
- ✅ Every deletion creates timestamped backup first
- ✅ Audit log includes operator, reason, timestamp, file hash
- ✅ Dry-run mode shows what would be deleted without deleting
- ✅ Batch deletions are transaction-safe (all or nothing)
- ✅ Recovery procedures documented and tested
- ✅ Git safety commit created before any deletions
- ✅ Backup directory structured by date (archive/deleted-files/YYYY-MM-DD/)

---

### FR-006: Continuous Monitoring & Drift Detection

**Priority**: P1 - HIGH (Enterprise-Grade Compliance)

**Requirement**: Implement continuous file audit monitoring to detect orphaned files and repository drift automatically.

**Motivation**:
- **Continuous audit** - Modern AI governance frameworks (IIA 2024, COBIT) emphasize ongoing compliance validation
- **Drift detection** - Catch orphaned files as they're created, not months later
- **Proactive cleanup** - Alert developers when files become unused after code refactoring

**Implementation Requirements**:

1. **GitHub Actions Workflow**
   ```yaml
   # .github/workflows/file-audit.yml
   name: Continuous File Audit

   on:
     schedule:
       - cron: '0 2 * * 0'  # Weekly on Sunday at 2am
     workflow_dispatch:

   jobs:
     audit:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Run file audit
           run: |
             python3 scripts/python/batch_audit.py \
               --dir . \
               --output audit-results/ \
               --changed-since 7  # Only files modified in last 7 days

         - name: Check for orphaned files
           run: |
             # Count Category D (DELETE) files
             orphan_count=$(jq '[.[] | select(.recommendation == "SAFE_TO_DELETE")] | length' audit-results/summary.json)

             if [ $orphan_count -gt 10 ]; then
               echo "::warning::Found $orphan_count orphaned files - consider cleanup"
             fi

         - name: Upload audit report
           uses: actions/upload-artifact@v3
           with:
             name: file-audit-report
             path: audit-results/
   ```

2. **Incremental Auditing**
   ```python
   def incremental_audit(days_back: int = 7) -> List[str]:
       """
       Audit only files modified in last N days

       Reduces audit time from 30 minutes → 2 minutes for weekly drift detection
       """
       # Get files modified since last audit
       result = subprocess.run(
           ['git', 'diff', '--name-only', f'HEAD@{{{days_back} days ago}}', 'HEAD'],
           capture_output=True,
           text=True
       )

       modified_files = result.stdout.strip().split('\n')

       # Audit only these files
       return [f for f in modified_files if should_audit(f)]
   ```

3. **Drift Alert System**
   ```python
   def check_for_drift(audit_results: List[Dict]) -> Dict:
       """
       Detect concerning patterns in audit results

       Returns alerts for:
       - Files that transitioned from ACTIVE → DELETE (orphaned)
       - Critical files with declining reference counts
       - Accumulation of historical files (Category C)
       """
       alerts = []

       # Load previous audit results
       previous_results = load_previous_audit()

       for file in audit_results:
           prev = previous_results.get(file["file_path"])

           if prev:
               # File became orphaned
               if prev["category"] == "B" and file["category"] == "D":
                   alerts.append({
                       "severity": "WARNING",
                       "file": file["file_path"],
                       "message": f"File transitioned ACTIVE → DELETE (orphaned after refactoring)"
                   })

               # Reference count declining
               if prev["reference_count"] > file["reference_count"]:
                   alerts.append({
                       "severity": "INFO",
                       "file": file["file_path"],
                       "message": f"Reference count declined: {prev['reference_count']} → {file['reference_count']}"
                   })

       return {
           "alerts": alerts,
           "drift_detected": len(alerts) > 0
       }
   ```

4. **Cron Alternative (Non-GitHub)**
   ```bash
   # Add to crontab -e
   # Run weekly file audit
   0 2 * * 0 cd /path/to/fish-scraper && python3 scripts/python/batch_audit.py --changed-since 7 --email-alerts
   ```

**Acceptance Criteria**:
- ✅ GitHub Actions workflow runs weekly automatically
- ✅ Incremental audit completes in <5 minutes (only modified files)
- ✅ Drift alerts generated for ACTIVE → DELETE transitions
- ✅ Audit reports uploaded as workflow artifacts
- ✅ Email/Slack notifications for high orphan counts (>10 files)

---

### FR-007: Governance Metadata & Traceability

**Priority**: P1 - HIGH (AI Accountability Frameworks)

**Requirement**: Extend JSON audit outputs with governance metadata for ownership, purpose, and lifecycle tracking.

**Motivation**:
- **AI governance compliance** - COBIT 2024, COSO AI frameworks emphasize data traceability
- **Accountability** - Track who owns each file and why it exists
- **Lifecycle management** - Understand file purpose and planned retention

**Metadata Schema**:

```json
{
  "file_path": "qc_june_batch03_2024.json",
  "governance_metadata": {
    "owner": "data-quality-team",
    "purpose": "QC validation evidence for June 2024 scraping batch 3",
    "project_phase": "completed",
    "created_date": "2024-06-15",
    "last_modified": "2024-06-15",
    "retention_policy": "archive_after_90_days",
    "data_classification": "internal",
    "regulatory_impact": "none"
  },
  "audit_history": [
    {
      "audit_date": "2025-10-25",
      "category": "C",
      "recommendation": "ARCHIVE",
      "operator": "audit-bot",
      "notes": "90-day retention period expired"
    }
  ]
}
```

**Implementation Requirements**:

1. **Metadata Extraction**
   ```python
   def extract_governance_metadata(file_path: str) -> Dict:
       """
       Extract or infer governance metadata from file

       Sources:
       - Git history (owner = last modifier, created_date = first commit)
       - Filename patterns (purpose from qc_*, SCRAPE_*, backup_* conventions)
       - File location (project_phase from archive/ vs active directories)
       """
       # Get git history
       git_log = subprocess.run(
           ['git', 'log', '--follow', '--format=%an|%ae|%ad', '--', file_path],
           capture_output=True,
           text=True
       )

       commits = git_log.stdout.strip().split('\n')

       if commits:
           # Last modifier
           last_commit = commits[0].split('|')
           owner = last_commit[1]  # Email

           # First commit (created date)
           first_commit = commits[-1].split('|')
           created_date = first_commit[2]
       else:
           owner = "unknown"
           created_date = None

       # Infer purpose from filename
       purpose = infer_purpose_from_filename(file_path)

       # Infer project phase from location
       if file_path.startswith("archive/"):
           project_phase = "archived"
       elif file_path.startswith("specs/") and "COMPLETE" in file_path:
           project_phase = "completed"
       else:
           project_phase = "active"

       return {
           "owner": owner,
           "purpose": purpose,
           "project_phase": project_phase,
           "created_date": created_date,
           "last_modified": os.path.getmtime(file_path),
           "retention_policy": infer_retention_policy(file_path),
           "data_classification": "internal",
           "regulatory_impact": check_regulatory_impact(file_path)
       }
   ```

2. **Audit History Tracking**
   ```python
   def append_audit_history(file_path: str, audit_result: Dict):
       """
       Maintain audit history for each file across multiple audits

       Stored in: .audit-history/<file_hash>.json
       """
       file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
       history_file = f".audit-history/{file_hash}.json"

       if os.path.exists(history_file):
           with open(history_file, 'r') as f:
               history = json.load(f)
       else:
           history = {"file_path": file_path, "audit_history": []}

       # Append new audit entry
       history["audit_history"].append({
           "audit_date": datetime.utcnow().isoformat(),
           "category": audit_result["category"],
           "recommendation": audit_result["recommendation"],
           "operator": audit_result.get("operator", "audit-bot"),
           "confidence_score": audit_result["confidence_score"],
           "notes": audit_result.get("justification", "")
       })

       with open(history_file, 'w') as f:
           json.dump(history, f, indent=2)
   ```

3. **Retention Policy Automation**
   ```python
   def check_retention_expiry(file_path: str, metadata: Dict) -> bool:
       """
       Check if file exceeded retention policy

       Policies:
       - QC logs: Archive after 90 days
       - Scrape logs: Archive after 180 days
       - Backup snapshots: Delete after 30 days
       - Session summaries: Archive immediately
       """
       policy = metadata.get("retention_policy")
       created = datetime.fromisoformat(metadata["created_date"])
       age_days = (datetime.now() - created).days

       policies = {
           "archive_after_90_days": 90,
           "archive_after_180_days": 180,
           "delete_after_30_days": 30,
           "archive_immediately": 0
       }

       threshold = policies.get(policy, float('inf'))
       return age_days > threshold
   ```

**Acceptance Criteria**:
- ✅ All audit outputs include governance_metadata section
- ✅ Owner extracted from git history (last modifier)
- ✅ Purpose inferred from filename patterns (qc_*, SCRAPE_*, backup_*)
- ✅ Project phase detected from file location (archive/, specs/)
- ✅ Audit history persisted across multiple audits (.audit-history/)
- ✅ Retention policy automation triggers ARCHIVE recommendations

---

### FR-008: Sandbox Validation Stage

**Priority**: P1 - HIGH (CI/CD Integration Best Practice)

**Requirement**: Add dry-run sandbox deployment step where deletions execute in temporary environment before actual commits.

**Motivation**:
- **CI/CD-integrated cleanup** - Mirrors modern DevOps sandbox testing
- **Regression prevention** - Catch build/test failures before production deletion
- **Rollback safety** - Validate full application functionality in isolated environment

**Implementation Requirements**:

1. **Sandbox Environment Creation**
   ```bash
   # Create temporary sandbox with deleted files
   create_sandbox() {
       local files_to_delete="$1"
       local sandbox_dir="/tmp/file-audit-sandbox-$(date +%s)"

       # Clone repository to sandbox
       git clone . "$sandbox_dir"
       cd "$sandbox_dir"

       # Remove files in sandbox (not in actual repo)
       while IFS= read -r file; do
           rm -f "$file"
           echo "Removed $file from sandbox"
       done < "$files_to_delete"

       echo "$sandbox_dir"
   }
   ```

2. **Full Build/Test Validation in Sandbox**
   ```python
   def validate_in_sandbox(files_to_delete: List[str]) -> Dict:
       """
       Create sandbox, remove files, run full build/test suite

       Returns validation results with detailed error reporting
       """
       # Create sandbox
       sandbox_dir = create_sandbox_environment()

       # Copy current repo to sandbox
       shutil.copytree('.', sandbox_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git'))

       # Remove files in sandbox
       for file in files_to_delete:
           file_in_sandbox = os.path.join(sandbox_dir, file)
           if os.path.exists(file_in_sandbox):
               os.remove(file_in_sandbox)

       # Run full validation suite
       results = {
           "sandbox_path": sandbox_dir,
           "files_removed": len(files_to_delete),
           "validations": {}
       }

       # Frontend build
       build_result = subprocess.run(
           ['npm', '--prefix', f'{sandbox_dir}/frontend', 'run', 'build'],
           capture_output=True,
           text=True
       )
       results["validations"]["frontend_build"] = {
           "passed": build_result.returncode == 0,
           "stderr": build_result.stderr if build_result.returncode != 0 else ""
       }

       # TypeScript check
       ts_result = subprocess.run(
           ['npx', 'tsc', '--noEmit'],
           cwd=f'{sandbox_dir}/frontend',
           capture_output=True,
           text=True
       )
       results["validations"]["typescript"] = {
           "passed": ts_result.returncode == 0,
           "stderr": ts_result.stderr if ts_result.returncode != 0 else ""
       }

       # Playwright tests
       playwright_result = subprocess.run(
           ['npx', 'playwright', 'test'],
           cwd=sandbox_dir,
           capture_output=True,
           text=True
       )
       results["validations"]["ui_tests"] = {
           "passed": playwright_result.returncode == 0,
           "stderr": playwright_result.stderr if playwright_result.returncode != 0 else ""
       }

       # Python scrapers (import check)
       python_result = subprocess.run(
           ['python3', '-m', 'py_compile', 'scripts/python/boats_scraper.py'],
           cwd=sandbox_dir,
           capture_output=True,
           text=True
       )
       results["validations"]["python_scrapers"] = {
           "passed": python_result.returncode == 0,
           "stderr": python_result.stderr if python_result.returncode != 0 else ""
       }

       # Cleanup sandbox
       shutil.rmtree(sandbox_dir)

       # Overall result
       results["all_passed"] = all(v["passed"] for v in results["validations"].values())

       return results
   ```

3. **GitHub Actions Sandbox Integration**
   ```yaml
   # .github/workflows/validate-deletions.yml
   name: Validate File Deletions in Sandbox

   on:
     pull_request:
       types: [opened, synchronize]

   jobs:
     sandbox-validation:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Detect deleted files
           id: deleted
           run: |
             git diff --name-only --diff-filter=D origin/main...HEAD > deleted_files.txt
             echo "count=$(wc -l < deleted_files.txt)" >> $GITHUB_OUTPUT

         - name: Run sandbox validation
           if: steps.deleted.outputs.count > 0
           run: |
             python3 scripts/python/sandbox_validate.py \
               --file-list deleted_files.txt \
               --output sandbox-results.json

         - name: Check sandbox results
           run: |
             all_passed=$(jq '.all_passed' sandbox-results.json)
             if [ "$all_passed" != "true" ]; then
               echo "::error::Sandbox validation failed - deletions would break build/tests"
               exit 1
             fi
   ```

4. **CLI Sandbox Mode**
   ```bash
   # Validate deletions in sandbox before executing
   python3 scripts/python/safe_delete.py \
     --file-list orphaned_files.txt \
     --sandbox-validate \
     --operator "user@example.com"

   # Output:
   # ✅ Sandbox validation passed (4 files tested)
   # ✅ Frontend build: PASS
   # ✅ TypeScript check: PASS
   # ✅ UI tests: PASS
   # ✅ Python scrapers: PASS
   #
   # Proceed with actual deletion? [y/N]
   ```

**Acceptance Criteria**:
- ✅ Sandbox environment created in /tmp/ directory
- ✅ Files removed in sandbox (not in actual repo)
- ✅ Full build/test suite executed in sandbox
- ✅ Validation failures prevent actual deletion
- ✅ GitHub Actions integration validates PRs with deletions
- ✅ CLI --sandbox-validate flag runs sandbox check before deletion

---

### FR-009: Sensitive Data Detection

**Priority**: P0 - CRITICAL (Security & Compliance)

**Requirement**: Check files for sensitive information (tokens, PII, API keys) before deletion and enforce secure deletion procedures.

**Motivation**:
- **Secure deletion compliance** - ICT4Peace, GDPR emphasize secure handling of sensitive data
- **Prevent credential leaks** - Deleted files with tokens may still exist in git history
- **Regulatory compliance** - PII requires special handling before deletion

**Sensitive Data Patterns**:

```python
SENSITIVE_PATTERNS = {
    "api_keys": [
        r"['\"]?api[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
        r"['\"]?secret[_-]?key['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
        r"SUPABASE[_-]?.*?KEY\s*[:=]\s*['\"]([A-Za-z0-9_\-\.]{20,})['\"]"
    ],
    "tokens": [
        r"ghp_[A-Za-z0-9]{36}",  # GitHub personal access token
        r"gho_[A-Za-z0-9]{36}",  # GitHub OAuth token
        r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"
    ],
    "credentials": [
        r"password\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
        r"passwd\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
        r"PGPASSWORD\s*[:=]\s*['\"]([^'\"]{8,})['\"]"
    ],
    "pii": [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\(\d{3}\)\s*\d{3}-\d{4}",  # Phone number
    ],
    "private_keys": [
        r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
        r"-----BEGIN OPENSSH PRIVATE KEY-----"
    ]
}
```

**Implementation Requirements**:

1. **Sensitive Data Scanner**
   ```python
   def scan_for_sensitive_data(file_path: str) -> Dict:
       """
       Scan file for sensitive information

       Returns findings with pattern matches and severity
       """
       findings = {
           "file_path": file_path,
           "has_sensitive_data": False,
           "findings": [],
           "severity": "NONE"
       }

       # Skip binary files
       if is_binary_file(file_path):
           return findings

       try:
           with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
               content = f.read()
       except Exception as e:
           logger.warning(f"Could not read {file_path}: {e}")
           return findings

       # Scan for each pattern category
       for category, patterns in SENSITIVE_PATTERNS.items():
           for pattern in patterns:
               matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

               for match in matches:
                   findings["has_sensitive_data"] = True
                   findings["findings"].append({
                       "category": category,
                       "pattern": pattern,
                       "line_number": content[:match.start()].count('\n') + 1,
                       "matched_text": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0),
                       "severity": get_severity(category)
                   })

       # Determine overall severity
       if findings["findings"]:
           severities = [f["severity"] for f in findings["findings"]]
           findings["severity"] = max(severities, key=lambda s: {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}[s])

       return findings

   def get_severity(category: str) -> str:
       """Map category to severity level"""
       severity_map = {
           "api_keys": "CRITICAL",
           "tokens": "CRITICAL",
           "credentials": "CRITICAL",
           "private_keys": "CRITICAL",
           "pii": "HIGH"
       }
       return severity_map.get(category, "MEDIUM")
   ```

2. **Secure Deletion Workflow**
   ```python
   def secure_delete_with_git_purge(file_path: str, operator: str, reason: str) -> Dict:
       """
       Securely delete file with sensitive data + purge from git history

       Steps:
       1. Backup to encrypted archive
       2. Remove from working directory
       3. Purge from git history (BFG Repo-Cleaner or git-filter-repo)
       4. Alert security team
       """
       # Scan for sensitive data first
       scan_result = scan_for_sensitive_data(file_path)

       if not scan_result["has_sensitive_data"]:
           # Normal deletion
           return safe_delete_file(file_path, operator, reason)

       # SENSITIVE DATA FOUND - Enhanced procedure
       logger.warning(f"⚠️  SENSITIVE DATA DETECTED in {file_path}")
       logger.warning(f"Findings: {len(scan_result['findings'])} matches, Severity: {scan_result['severity']}")

       # Backup to encrypted archive (not plain JSON)
       encrypted_backup = backup_with_encryption(file_path, operator, reason)

       # Delete from working directory
       os.remove(file_path)

       # Purge from git history
       purge_from_git_history(file_path)

       # Alert security team
       send_security_alert({
           "file": file_path,
           "operator": operator,
           "severity": scan_result["severity"],
           "findings_count": len(scan_result["findings"]),
           "action": "PURGED_FROM_GIT_HISTORY"
       })

       return {
           "status": "securely_deleted",
           "file_path": file_path,
           "encrypted_backup": encrypted_backup,
           "git_purged": True,
           "security_alert_sent": True
       }

   def purge_from_git_history(file_path: str):
       """
       Remove file from entire git history using git-filter-repo

       WARNING: Rewrites history - requires force push
       """
       # Using git-filter-repo (preferred over BFG)
       subprocess.run([
           'git', 'filter-repo',
           '--invert-paths',
           '--path', file_path,
           '--force'
       ], check=True)

       logger.info(f"✅ Purged {file_path} from git history")
   ```

3. **Pre-Deletion Sensitive Data Check**
   ```python
   def audit_file_with_sensitive_check(file_path: str) -> Dict:
       """
       Enhanced audit that includes sensitive data scanning
       """
       # Standard audit
       audit_result = standard_audit(file_path)

       # Add sensitive data scan
       sensitive_scan = scan_for_sensitive_data(file_path)
       audit_result["sensitive_data_scan"] = sensitive_scan

       # Override recommendation if sensitive data found
       if sensitive_scan["has_sensitive_data"]:
           audit_result["recommendation"] = "SECURE_DELETE"
           audit_result["justification"] += f"\n⚠️  SENSITIVE DATA DETECTED ({sensitive_scan['severity']}): Requires secure deletion with git history purge."
           audit_result["action_command"] = f"python3 scripts/python/secure_delete.py --file {file_path} --purge-git-history"

       return audit_result
   ```

4. **Allowlist for False Positives**
   ```python
   # Allow specific files known to contain example/test credentials
   SENSITIVE_DATA_ALLOWLIST = [
       ".env.example",  # Example env file with placeholder tokens
       "tests/fixtures/sample_api_response.json",  # Test fixtures
       "docs/API_EXAMPLES.md"  # Documentation with example keys
   ]

   def is_allowlisted(file_path: str) -> bool:
       """Check if file is allowlisted for sensitive data"""
       return any(file_path.endswith(pattern) for pattern in SENSITIVE_DATA_ALLOWLIST)
   ```

**Acceptance Criteria**:
- ✅ All files scanned for sensitive data before deletion
- ✅ API keys, tokens, credentials, PII patterns detected
- ✅ CRITICAL severity triggers secure deletion workflow
- ✅ Git history purged for files with sensitive data (git-filter-repo)
- ✅ Security team alerted for CRITICAL findings
- ✅ Encrypted backups for sensitive files (not plain JSON)
- ✅ Allowlist prevents false positives on example/test files

---

### FR-010: Self-Healing & Automatic Rollback

**Priority**: P1 - HIGH (DevOps Rollback Standards)

**Requirement**: Implement automatic rollback when deleted file causes build/test regression, with remediation logging.

**Motivation**:
- **Modern DevOps standards** - Auto-rollback on deployment failures
- **Regression prevention** - Catch indirect dependencies missed by static analysis
- **Zero-downtime cleanup** - Maintain production stability during cleanup operations

**Implementation Requirements**:

1. **Post-Deletion Validation Hook**
   ```python
   def delete_with_rollback_protection(
       file_path: str,
       operator: str,
       reason: str
   ) -> Dict:
       """
       Delete file with automatic rollback on regression

       Steps:
       1. Backup file
       2. Delete file
       3. Run build/test validation
       4. If validation fails → auto-rollback + log remediation
       5. If validation passes → commit deletion
       """
       # Step 1: Backup
       backup_path = backup_file_before_deletion(file_path, operator, reason)

       # Step 2: Delete
       os.remove(file_path)
       logger.info(f"🗑️  Deleted {file_path} (backup: {backup_path})")

       # Step 3: Validate
       logger.info("🔍 Running post-deletion validation...")
       validation_result = run_post_deletion_validation()

       if validation_result["all_passed"]:
           # Step 5: Success - commit deletion
           logger.info(f"✅ Validation passed - deletion successful")

           # Git commit
           subprocess.run(['git', 'add', file_path], check=True)
           subprocess.run([
               'git', 'commit', '-m',
               f"Remove {file_path}\n\nOperator: {operator}\nReason: {reason}\n\n🤖 Generated with Claude Code"
           ], check=True)

           return {
               "status": "deleted",
               "file_path": file_path,
               "backup_path": backup_path,
               "validation_passed": True
           }
       else:
           # Step 4: Failure - auto-rollback
           logger.error(f"❌ Validation failed - rolling back deletion of {file_path}")

           # Restore file
           shutil.copy2(backup_path, file_path)
           logger.info(f"♻️  Restored {file_path} from backup")

           # Log remediation
           log_rollback_remediation({
               "file_path": file_path,
               "operator": operator,
               "deletion_reason": reason,
               "rollback_reason": "Post-deletion validation failed",
               "validation_failures": validation_result["failures"],
               "timestamp": datetime.utcnow().isoformat()
           })

           return {
               "status": "rolled_back",
               "file_path": file_path,
               "backup_path": backup_path,
               "validation_passed": False,
               "failures": validation_result["failures"],
               "rollback_performed": True
           }

   def run_post_deletion_validation() -> Dict:
       """
       Run critical validation checks after file deletion

       Checks:
       - Frontend build
       - TypeScript compilation
       - Unit tests
       - Integration tests (optional)
       """
       results = {
           "all_passed": True,
           "failures": []
       }

       # Frontend build
       build_result = subprocess.run(
           ['npm', '--prefix', 'frontend', 'run', 'build'],
           capture_output=True,
           text=True
       )
       if build_result.returncode != 0:
           results["all_passed"] = False
           results["failures"].append({
               "check": "frontend_build",
               "error": build_result.stderr
           })

       # TypeScript check
       ts_result = subprocess.run(
           ['npx', 'tsc', '--noEmit'],
           cwd='frontend',
           capture_output=True,
           text=True
       )
       if ts_result.returncode != 0:
           results["all_passed"] = False
           results["failures"].append({
               "check": "typescript",
               "error": ts_result.stderr
           })

       # Contract tests
       test_result = subprocess.run(
           ['npm', '--prefix', 'frontend', 'run', 'test:contracts'],
           capture_output=True,
           text=True
       )
       if test_result.returncode != 0:
           results["all_passed"] = False
           results["failures"].append({
               "check": "contract_tests",
               "error": test_result.stderr
           })

       return results
   ```

2. **Remediation Logging**
   ```python
   def log_rollback_remediation(rollback_info: Dict):
       """
       Log rollback event for future investigation

       Stored in: .rollback-log/YYYY-MM-DD-HH-MM-SS.json
       """
       log_dir = ".rollback-log"
       os.makedirs(log_dir, exist_ok=True)

       timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
       log_file = os.path.join(log_dir, f"{timestamp}.json")

       with open(log_file, 'w') as f:
           json.dump(rollback_info, f, indent=2)

       logger.warning(f"⚠️  Rollback logged: {log_file}")

       # Append to master rollback log
       master_log = os.path.join(log_dir, "master_log.json")

       if os.path.exists(master_log):
           with open(master_log, 'r') as f:
               master = json.load(f)
       else:
           master = {"rollbacks": []}

       master["rollbacks"].append(rollback_info)

       with open(master_log, 'w') as f:
           json.dump(master, f, indent=2)
   ```

3. **Rollback Notification System**
   ```python
   def send_rollback_notification(rollback_info: Dict):
       """
       Alert operator that deletion was rolled back

       Channels:
       - Email (if configured)
       - Slack (if webhook configured)
       - GitHub Issue (if API token configured)
       """
       message = f"""
       🔄 File Deletion Rolled Back

       **File**: {rollback_info['file_path']}
       **Operator**: {rollback_info['operator']}
       **Deletion Reason**: {rollback_info['deletion_reason']}
       **Rollback Reason**: {rollback_info['rollback_reason']}

       **Validation Failures**:
       {format_failures(rollback_info['validation_failures'])}

       **Action Required**: Investigate why {rollback_info['file_path']} caused build/test failures.
       File may have indirect dependencies not caught by static analysis.

       **Rollback Log**: .rollback-log/{timestamp}.json
       """

       # Email notification (if SMTP configured)
       if os.getenv('SMTP_HOST'):
           send_email(
               to=rollback_info['operator'],
               subject=f"File Deletion Rolled Back: {rollback_info['file_path']}",
               body=message
           )

       # Slack notification (if webhook configured)
       if os.getenv('SLACK_WEBHOOK_URL'):
           send_slack_message(os.getenv('SLACK_WEBHOOK_URL'), message)

       # GitHub Issue (if API token configured)
       if os.getenv('GITHUB_API_TOKEN'):
           create_github_issue(
               title=f"File deletion rollback: {rollback_info['file_path']}",
               body=message,
               labels=["rollback", "investigation-required"]
           )
   ```

4. **Rollback Analytics Dashboard**
   ```python
   def generate_rollback_report() -> Dict:
       """
       Analyze rollback patterns for continuous improvement

       Metrics:
       - Rollback rate (% of deletions rolled back)
       - Most common validation failures
       - Files with repeated rollbacks
       """
       master_log = ".rollback-log/master_log.json"

       if not os.path.exists(master_log):
           return {"rollback_count": 0}

       with open(master_log, 'r') as f:
           data = json.load(f)

       rollbacks = data["rollbacks"]

       # Calculate metrics
       report = {
           "total_rollbacks": len(rollbacks),
           "rollback_rate": len(rollbacks) / get_total_deletions() * 100,
           "common_failures": Counter([
               f["check"] for r in rollbacks for f in r["validation_failures"]
           ]).most_common(5),
           "repeated_files": Counter([
               r["file_path"] for r in rollbacks
           ]).most_common(10)
       }

       return report
   ```

**Acceptance Criteria**:
- ✅ Post-deletion validation runs automatically after file deletion
- ✅ Build/test failures trigger automatic rollback
- ✅ Rolled-back files restored from backup within seconds
- ✅ Rollback events logged to .rollback-log/ directory
- ✅ Operator notified via email/Slack/GitHub issue
- ✅ Rollback analytics track patterns for continuous improvement
- ✅ Zero production downtime from failed file deletions

---

## Non-Functional Requirements

### NFR-001: Performance & Scalability

**Requirements**:
- Static analysis (grep): <5 seconds per file, <15 minutes for 200 files
- Dynamic analysis (build/test): <60 seconds per file
- Full audit cycle: <30 minutes for 200 files (parallelizable)
- JSON output generation: <100ms per file
- Batch deletion: <10 seconds for 50 files

**Optimization Strategies**:
- Parallel grep searches (xargs -P)
- Cached build/test results (skip if no TypeScript/JS files)
- Batch configuration checks (single read of package.json)
- Incremental audit (skip files audited in last 7 days)

**Acceptance Criteria**:
- ✅ 200 file audit completes in <30 minutes
- ✅ Performance benchmarks documented
- ✅ Parallel processing implemented for grep searches

---

### NFR-002: Audit Trail & Compliance

**Requirements**:
- Every deletion logged with ISO timestamps
- Operator identity required (no anonymous deletions)
- Deletion reason required (free text, min 10 chars)
- File hash captured for integrity verification
- Audit log retention: permanent (never delete AUDIT.json)
- Backup retention: 90 days minimum

**Audit Log Schema**:
```json
{
  "deletions": [
    {
      "file_path": "old-dashboard.html",
      "backup_path": "archive/deleted-files/2025-10-25/old-dashboard.html",
      "deleted_at": "2025-10-25T14:30:00Z",
      "operator": "user@example.com",
      "reason": "Orphaned prototype - replaced by React dashboard",
      "file_size": 12543,
      "file_hash": "abc123def456",
      "audit_evidence": {
        "reference_count": 0,
        "build_test_passed": true,
        "confidence_score": 98
      }
    }
  ]
}
```

**Acceptance Criteria**:
- ✅ AUDIT.json created in backup directory
- ✅ Operator identity captured from CLI argument or environment variable
- ✅ Deletion reason validated (min 10 characters)
- ✅ File hash computed and stored
- ✅ Audit evidence (reference count, confidence, etc.) included

---

### NFR-003: Documentation Compliance

**Requirements**:
- Enforce DOCUMENTATION_STANDARDS.md rules automatically
- Flag monthly completion files for archival (not deletion)
- Protect master documentation (README.md, CLAUDE_OPERATING_GUIDE.md, etc.)
- Respect archive/ directory structure (logs/, reports/, backups/, docs/, screenshots/)
- Update DOC_CHANGELOG.md when documentation files archived

**Compliance Checks**:
```python
def check_documentation_compliance(file_path: str) -> Dict:
    """
    Verify file handling complies with DOCUMENTATION_STANDARDS.md
    """
    violations = []

    # Check master doc protection
    if is_master_doc(file_path):
        violations.append({
            "rule": "Single Source of Truth",
            "severity": "CRITICAL",
            "message": f"{file_path} is master documentation - NEVER DELETE"
        })

    # Check for monthly completion reports
    if re.match(r".*_(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)_\d{4}_COMPLETE\.md", file_path):
        violations.append({
            "rule": "No Monthly Completion Files",
            "severity": "HIGH",
            "message": f"{file_path} should be ARCHIVED, not deleted. Add to annual report instead."
        })

    # Check archive structure
    if file_path.startswith("archive/") and not any([
        file_path.startswith("archive/logs/"),
        file_path.startswith("archive/reports/"),
        file_path.startswith("archive/backups/"),
        file_path.startswith("archive/docs/"),
        file_path.startswith("archive/screenshots/")
    ]):
        violations.append({
            "rule": "Archive Directory Structure",
            "severity": "MEDIUM",
            "message": f"{file_path} not in standard archive subdirectory"
        })

    return {
        "compliant": len(violations) == 0,
        "violations": violations
    }
```

**Acceptance Criteria**:
- ✅ Master documentation protected by hard-coded exemptions
- ✅ Monthly completion files flagged for ARCHIVE (not DELETE)
- ✅ Archive directory structure enforced
- ✅ Documentation compliance violations logged at WARNING level
- ✅ DOC_CHANGELOG.md updated when docs archived

---

## Implementation Plan

### Phase 1: Core Auditing Logic (Days 1-2)

**Deliverables**:
- FR-001: Claude prompt template in `.claude/prompts/audit-file-deletion.md`
- FR-002: Static analysis implementation (grep-based reference detection)
- FR-004: Category classification system with hard-coded exemptions
- JSON output schema definition

**Tasks**:
1. Create `.claude/prompts/audit-file-deletion.md` with full prompt template
2. Implement `audit_file.py` with static analysis functions:
   - `grep_code_references(file_path)`
   - `grep_config_references(file_path)`
   - `grep_doc_references(file_path)`
   - `aggregate_reference_count(results)`
3. Implement category classification:
   - `CRITICAL_PATTERNS` list (master docs, core code, configs)
   - `classify_file(file_path, static_analysis)`
   - `has_historical_value(file_path)` (QC logs, backups, etc.)
4. Define JSON output schema
5. Create example walkthroughs in prompt

**Testing**:
- Test grep searches on 10 sample files (known references)
- Test critical pattern matching (README.md → Category A)
- Test historical value detection (qc_batch01.json → Category C)
- Verify JSON schema with sample outputs
- Test prompt with Claude CLI on 5 files

**Acceptance**:
- ✅ Static analysis finds all references (zero false negatives)
- ✅ Critical files always classified as Category A
- ✅ JSON output valid and parseable
- ✅ Claude prompt produces consistent results

---

### Phase 2: Dynamic Analysis & Build Integration (Days 3-4)

**Deliverables**:
- FR-003: Build and test validation
- Dynamic analysis integration into audit workflow
- Confidence scoring system

**Tasks**:
1. Implement dynamic validation functions:
   - `run_build_test()` - npm run build
   - `run_typescript_check()` - npx tsc --noEmit
   - `run_contract_tests()` - npm run test:contracts
   - `run_playwright_tests()` - npx playwright test
2. Create test orchestration:
   - `run_dynamic_validation(file_path)` wrapper
   - Result caching (avoid re-running for same file)
   - Timeout handling (kill tests after 60s)
3. Implement confidence scoring:
   - Reference count = 0 → +50 confidence
   - Build passes → +25 confidence
   - Tests pass → +25 confidence
   - Critical pattern match → 100 confidence (override)
4. Integrate dynamic analysis into `audit_file.py`

**Testing**:
- Test build with known missing dependency (should fail)
- Test build with orphaned file (should pass)
- Test confidence scoring edge cases
- Verify timeout handling (kill runaway tests)
- Benchmark dynamic analysis performance (<60s)

**Acceptance**:
- ✅ Build failures detected and attributed to file
- ✅ Test suite failures trigger UNSAFE classification
- ✅ Confidence score accurately reflects safety
- ✅ Dynamic validation completes in <60 seconds
- ✅ Build/test caching improves performance

---

### Phase 3: Safe Deletion & Batch Processing (Day 5)

**Deliverables**:
- FR-005: Safe deletion protocol with backups
- Batch processing script for 200+ files
- Dry-run mode for all operations

**Tasks**:
1. Implement safe deletion:
   - `backup_file_before_deletion(file_path, operator, reason)`
   - `safe_delete_file(file_path, operator, reason, dry_run)`
   - `batch_delete_files(files, operator, dry_run)`
2. Create audit trail:
   - `create_audit_log(backup_dir)` - AUDIT.json generation
   - `compute_file_hash(file_path)` - SHA256 hash
   - Append deletion entries to audit log
3. Implement recovery procedures:
   - `restore_file(backup_path, original_path)`
   - `restore_batch(backup_dir)`
4. Create batch audit script:
   - `batch_audit.py --dir . --output audit-results/`
   - Parallel processing with multiprocessing
   - Progress reporting (X/200 files audited)
5. Create CLI tools:
   - `audit_file.py` - Single file audit
   - `batch_audit.py` - Directory audit
   - `safe_delete.py` - Interactive deletion with dry-run

**Testing**:
- Test backup creation and directory structure
- Test dry-run mode (no actual deletions)
- Test batch deletion with rollback
- Test recovery procedures (restore files)
- Test AUDIT.json generation and appending
- Audit 50 files and verify results

**Acceptance**:
- ✅ Dry-run shows exactly what would be deleted
- ✅ Backups created in archive/deleted-files/YYYY-MM-DD/
- ✅ AUDIT.json includes all required fields
- ✅ Recovery procedures tested and documented
- ✅ Batch audit handles 200+ files without errors

---

### Phase 4: Documentation Compliance & Production Deployment (Day 6)

**Deliverables**:
- NFR-003: Documentation compliance enforcement
- DOC_CHANGELOG.md updates
- Complete documentation and operational procedures
- Production deployment with full 200 file audit

**Tasks**:
1. Implement documentation compliance:
   - `check_documentation_compliance(file_path)`
   - Integration into classification logic
   - Violation reporting and warnings
2. Create archival workflows:
   - `archive_file.py --file path/to/file --category logs`
   - Automatic subdirectory placement (logs/, reports/, backups/, docs/)
   - DOC_CHANGELOG.md update automation
3. Update project documentation:
   - Add SPEC-013 to README.md
   - Update DOCUMENTATION_STANDARDS.md with auditing procedures
   - Create operational guide for file cleanup
4. Production deployment:
   - Run full audit on all 200+ files
   - Review results and classify edge cases
   - Archive historical files (Category C)
   - Delete orphaned files (Category D) with backups
   - Create git commit with cleanup results

**Testing**:
- Test master doc protection (README.md → CRITICAL violation)
- Test monthly report detection and ARCHIVE recommendation
- Test DOC_CHANGELOG.md update automation
- Verify archive directory structure compliance
- Full audit on test repository (validate all 200 files)

**Acceptance**:
- ✅ Master docs protected from deletion
- ✅ Monthly completion reports archived (not deleted)
- ✅ DOC_CHANGELOG.md updated with archival entries
- ✅ Full repository audit completed
- ✅ 100+ orphaned files identified and safely removed
- ✅ User approves cleanup results

---

### Phase 5: Enterprise-Grade Enhancements (Days 7-9)

**Deliverables**:
- FR-006: Continuous monitoring & drift detection
- FR-007: Governance metadata & traceability
- FR-008: Sandbox validation stage
- FR-009: Sensitive data detection
- FR-010: Self-healing & automatic rollback

**Tasks**:

**Day 7: Continuous Monitoring (FR-006)**
1. Implement GitHub Actions workflow:
   - `.github/workflows/file-audit.yml` - Weekly automatic audits
   - Incremental audit (files modified in last 7 days)
   - Drift alert system (ACTIVE → DELETE transitions)
2. Create cron alternative for non-GitHub environments
3. Implement drift detection:
   - Compare current audit vs previous audit
   - Alert on reference count declines
   - Track orphaned file accumulation

**Day 8: Governance & Sandbox (FR-007, FR-008)**
1. Governance metadata extraction:
   - Git history parsing (owner, created_date)
   - Purpose inference from filename patterns
   - Project phase detection (active/archived/completed)
   - Retention policy automation
2. Audit history tracking (.audit-history/)
3. Sandbox validation:
   - Create temporary sandbox environment
   - Remove files in sandbox, run full build/test
   - GitHub Actions PR validation integration
   - CLI --sandbox-validate flag

**Day 9: Security & Self-Healing (FR-009, FR-010)**
1. Sensitive data scanner:
   - Pattern detection (API keys, tokens, credentials, PII)
   - Severity classification (CRITICAL/HIGH/MEDIUM)
   - Allowlist for false positives (.env.example)
2. Secure deletion workflow:
   - Encrypted backups for sensitive files
   - Git history purge (git-filter-repo)
   - Security team alerts
3. Self-healing rollback:
   - Post-deletion validation hook
   - Automatic rollback on build/test failures
   - Remediation logging (.rollback-log/)
   - Notification system (email/Slack/GitHub issues)
   - Rollback analytics dashboard

**Testing**:
- Test GitHub Actions workflow (weekly trigger, incremental audit)
- Test governance metadata extraction (10 sample files)
- Test sandbox validation (remove 5 files, verify build/test)
- Test sensitive data scanner (API keys, tokens, PII)
- Test secure deletion + git purge (create test file with token)
- Test automatic rollback (intentionally break build, verify restore)
- Test notification systems (email, Slack webhooks)
- Full integration test: Audit → Sandbox → Delete → Validate → Rollback (if needed)

**Acceptance**:
- ✅ GitHub Actions runs weekly, alerts on >10 orphaned files
- ✅ Governance metadata enriches all audit outputs
- ✅ Sandbox validation prevents unsafe deletions
- ✅ Sensitive data detection triggers secure deletion workflow
- ✅ Failed deletions auto-rollback within seconds
- ✅ Zero production breakages from file cleanup
- ✅ Full enterprise compliance (IIA 2024, COBIT, COSO frameworks)

---

## Success Metrics

**After 30 Days of Operation**:

**Safety Metrics**:
- Zero critical files deleted (src/, scripts/python/, migrations/, master docs)
- Zero production breakages from file deletion
- 100% backup coverage (every deletion has recoverable backup)
- 100% audit trail (every deletion logged with operator, reason, timestamp)

**Efficiency Metrics**:
- 200 file audit completes in <30 minutes (vs 100+ hours manual)
- 95%+ audit automation rate (≤10 files require manual review)
- 50%+ repository size reduction (orphaned files removed)
- Zero false positives (files marked DELETE incorrectly)

**Compliance Metrics**:
- 100% DOCUMENTATION_STANDARDS.md compliance (no master doc violations)
- All monthly completion reports archived to annual reports
- Archive directory structure maintained (logs/, reports/, backups/, docs/)
- DOC_CHANGELOG.md updated for all documentation moves

**Enterprise Metrics** (Phase 5):
- **Continuous Monitoring**: Weekly automated audits running with <5 minute runtime (incremental)
- **Drift Detection**: <24 hour alert turnaround for ACTIVE → DELETE transitions
- **Governance Traceability**: 100% of audited files include metadata (owner, purpose, retention policy)
- **Sandbox Validation**: Zero unsafe deletions (100% validation before commit)
- **Sensitive Data Protection**: 100% scan rate before deletion, zero credential leaks
- **Self-Healing**: <1% rollback rate (≤2 rollbacks per 200 deletions)
- **Industry Compliance**: Full alignment with IIA 2024, COBIT, COSO AI governance frameworks

**Operational Excellence**:
- **Mean Time to Recovery** (MTTR): <60 seconds for automatic rollback
- **Audit History**: 100% retention of audit trails across multiple runs
- **Notification Reliability**: 100% alert delivery for critical events (rollbacks, sensitive data)
- **Rollback Rate Improvement**: <5% month-over-month (continuous learning)

---

## Risk Assessment

### Risk 1: False Positive - Critical File Marked DELETE
- **Severity**: CRITICAL
- **Mitigation**: Hard-coded exemption list, conservative confidence thresholds (≥75%), dry-run first, backup before delete
- **Acceptance**: Zero critical files deleted in Phase 4 production deployment

### Risk 2: Build/Test Cache Invalidation
- **Severity**: MEDIUM
- **Mitigation**: Clear npm cache before dynamic tests, fresh build for each audit run
- **Acceptance**: Build tests accurately reflect file removal impact

### Risk 3: Grep Misses Indirect References
- **Severity**: MEDIUM
- **Mitigation**: Multiple search patterns (filename, path, import styles), dynamic build test as fallback
- **Acceptance**: Zero production errors from "missing file" after deletion

### Risk 4: Performance Degradation on Large Repos
- **Severity**: LOW
- **Mitigation**: Parallel processing, grep optimizations, cached results, incremental audits
- **Acceptance**: 200 file audit completes in <30 minutes

### Risk 5: Incomplete Backup Recovery
- **Severity**: LOW
- **Mitigation**: Git safety commit before deletions, file hash verification, recovery procedure testing
- **Acceptance**: 100% file recovery success in testing

---

## Documentation & Artifacts

**Required Files**:
1. `specs/013-file-auditing-cleanup/spec.md` - This specification
2. `specs/013-file-auditing-cleanup/README.md` - Implementation summary
3. `.claude/prompts/audit-file-deletion.md` - Claude auditing prompt template
4. `scripts/python/audit_file.py` - Single file auditing tool
5. `scripts/python/batch_audit.py` - Directory auditing tool
6. `scripts/python/safe_delete.py` - Safe deletion tool with backups
7. `scripts/python/archive_file.py` - Documentation archival tool
8. `scripts/shell/cleanup_orphans.sh` - Automated cleanup wrapper

**Documentation Updates**:
- `README.md` - Reference SPEC-013 in project maintenance section
- `DOCUMENTATION_STANDARDS.md` - Add file auditing procedures, archival workflows
- `DOC_CHANGELOG.md` - Document all file moves and deletions
- `.claude/prompts/audit-file-deletion.md` - Complete prompt with examples

**Audit Output Files**:
- `audit-results/` - Directory containing JSON audit results for all files
- `archive/deleted-files/YYYY-MM-DD/` - Timestamped backup directories
- `archive/deleted-files/YYYY-MM-DD/AUDIT.json` - Deletion audit trail

---

## Appendix A: Example Audit Workflow

**Scenario**: Audit `old-dashboard.html` file

**Step 1: Static Analysis**
```bash
$ grep -r "old-dashboard.html" . --include="*.ts" --include="*.tsx" --include="*.html"
# → No results (0 references)

$ grep -r "old-dashboard" frontend/package.json frontend/index.html
# → No results (not in configs)
```

**Step 2: Dynamic Analysis**
```bash
$ cd frontend && npm run build
# → ✅ Built successfully (no errors)

$ npx tsc --noEmit
# → ✅ No TypeScript errors

$ npm run test:contracts
# → ✅ All tests passed
```

**Step 3: Classification**
- Not in CRITICAL_PATTERNS (not master doc)
- Reference count: 0
- Build/tests pass without it
- No historical value (early prototype)
- **Category: D (SAFE TO DELETE)**

**Step 4: Confidence Scoring**
- Reference count = 0 → +50
- Build passes → +25
- Tests pass → +25
- **Total: 100% confidence**

**Step 5: JSON Output**
```json
{
  "file_path": "old-dashboard.html",
  "analysis_date": "2025-10-25T14:30:00Z",
  "reference_count": 0,
  "config_references": [],
  "build_test_passed": true,
  "test_suite_passed": true,
  "category": "D",
  "confidence_score": 100,
  "recommendation": "SAFE_TO_DELETE",
  "justification": "Zero references in codebase, all builds/tests pass without file, not critical directory, no historical value. Orphaned prototype replaced by React dashboard.",
  "action_command": "python3 scripts/python/safe_delete.py --file old-dashboard.html --operator user@example.com --reason 'Orphaned prototype'",
  "risk_factors": []
}
```

**Step 6: Safe Deletion**
```bash
# Dry-run first
$ python3 scripts/python/safe_delete.py \
    --file old-dashboard.html \
    --operator "user@example.com" \
    --reason "Orphaned prototype - replaced by React dashboard" \
    --dry-run

DRY RUN: Would delete old-dashboard.html
Operator: user@example.com
Reason: Orphaned prototype - replaced by React dashboard
Backup path: archive/deleted-files/2025-10-25/old-dashboard.html

# Execute after review
$ python3 scripts/python/safe_delete.py \
    --file old-dashboard.html \
    --operator "user@example.com" \
    --reason "Orphaned prototype - replaced by React dashboard"

✅ Backed up to archive/deleted-files/2025-10-25/old-dashboard.html
✅ Deleted old-dashboard.html
✅ Audit log updated: archive/deleted-files/2025-10-25/AUDIT.json
```

---

## Appendix B: Batch Audit Example

**Scenario**: Audit all .log files in repository

```bash
# Find all .log files
$ find . -name "*.log" -not -path "*/node_modules/*" > log_files.txt
# → 47 files found

# Run batch audit
$ python3 scripts/python/batch_audit.py \
    --file-list log_files.txt \
    --output audit-results/logs/ \
    --parallel 4

Auditing 47 files...
[████████████████████] 47/47 (100%) - Elapsed: 12m 34s

Summary:
  Category A (CRITICAL): 0 files
  Category B (ACTIVE): 0 files
  Category C (ARCHIVE): 45 files  ← Historical QC/scrape logs
  Category D (DELETE): 2 files    ← Empty or corrupted logs

Recommendations:
  ARCHIVE: 45 files → archive/logs/
  DELETE: 2 files → archive/deleted-files/2025-10-25/

# Review results
$ cat audit-results/logs/summary.json | jq .

# Archive historical logs
$ python3 scripts/python/archive_file.py \
    --file-list audit-results/logs/archive_candidates.txt \
    --category logs

✅ Archived 45 files to archive/logs/
✅ Updated DOC_CHANGELOG.md

# Delete orphaned logs with backup
$ python3 scripts/python/safe_delete.py \
    --file-list audit-results/logs/delete_candidates.txt \
    --operator "user@example.com" \
    --reason "Corrupted/empty log files"

✅ Backed up 2 files to archive/deleted-files/2025-10-25/
✅ Deleted 2 files
✅ Audit log updated
```

---

**End of Specification SPEC-013**

**Next Steps**:
1. User reviews and approves specification
2. Implement Phase 1 (Core Auditing Logic)
3. Implement Phase 2 (Dynamic Analysis)
4. Implement Phase 3 (Safe Deletion & Batch Processing)
5. Implement Phase 4 (Documentation Compliance & Production Deployment)
6. Full repository cleanup with 200+ file audit
