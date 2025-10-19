# Specification 009: Continuous Data Quality Auditor

**Version**: 1.0.0
**Date**: October 18, 2025
**Status**: ACTIVE - PROACTIVE QUALITY MONITORING
**Governed By**: SPEC 006 QC Validation Standards
**Triggered By**: SPEC 008 Phantom Trip Remediation
**Author**: Fishing Intelligence Platform
**Priority**: P1 - HIGH (Preventative Quality Control)

---

## Executive Summary

### Purpose

Following the SPEC-008 remediation of 115 corrupted trips (91.4% phantom data), establish a **continuous, randomized data quality auditing system** to proactively detect anomalies before they contaminate analytics or dashboards.

### Scope

**What This Does**:
- ✅ Random spot-checking of trip records by date, boat, and landing
- ✅ Field-level validation against authoritative source data
- ✅ Categorization of anomalies (PHANTOM, MISATTRIBUTED, PARTIAL)
- ✅ Automated audit reports with actionable remediation recommendations
- ✅ Continuous monitoring to prevent future data corruption

**What This Does NOT Do**:
- ❌ Automatic deletion or correction of trips (requires human approval)
- ❌ Replace comprehensive QC validation (SPEC-006 still primary)
- ❌ Monitor non-trip data (boats, landings, species tables)

### Success Criteria

**Target Metrics**:
- Daily audit coverage: 5-10% of recent trips randomly sampled
- QC confidence score: >99.5% VALID trips in production database
- Detection latency: <24 hours from scrape to anomaly detection
- False positive rate: <0.5% (legitimate trips flagged as invalid)

---

## Functional Requirements

### FR-001: Random Sampling Strategy

**Requirement**: Implement unbiased random sampling across time, boats, and landings

**Sampling Methodology**:

```python
# Sample Selection Algorithm
def select_audit_sample(
    date_range_days: int = 30,      # Last N days to sample from
    sample_size: int = 50,          # Total trips to audit
    min_boats_per_landing: int = 2, # Diversity requirement
    stratified: bool = True         # Stratify by landing/boat
):
    """
    Select random trip sample with stratification to ensure coverage
    across all landings and boats.

    Strategy:
    1. Get all trips from last N days
    2. Group by landing
    3. For each landing, randomly select trips ensuring boat diversity
    4. Return balanced sample across landings
    """
```

**Sampling Constraints**:
- **Temporal**: Sample from last 30-90 days (recent data most critical)
- **Spatial**: Ensure all active landings represented (San Diego + SoCal)
- **Boat Diversity**: Sample ≥2 boats per landing per audit run
- **Trip Type Diversity**: Include AM, PM, Twilight, multi-day trips

**Rotation Strategy**:
- Track previously audited trips in `audit_history.json`
- Prioritize trips NOT audited in last 30 days
- Ensure 100% coverage over 90-day rolling window

---

### FR-002: Multi-Level Validation Protocol

**Requirement**: Validate every sampled trip against source with evidence capture

**Validation Levels**:

**Level 1: Composite Key Validation**
```python
# CRITICAL: Does trip exist on source page?
validate_trip_exists(
    date=trip.trip_date,
    boat=trip.boat_name,
    duration=trip.trip_duration,
    anglers=trip.anglers
)
# Result: EXISTS / NOT_FOUND
```

**Level 2: Field-Level Accuracy**
```python
# Validate each field matches source exactly
validate_fields(
    landing_match=True/False,
    boat_match=True/False,
    duration_match=True/False,
    anglers_match=True/False,  # Allow ±1 tolerance
    catches_match=True/False   # Species + counts
)
# Result: EXACT_MATCH / FIELD_MISMATCH / SEVERE_MISMATCH
```

**Level 3: Anomaly Detection**
```python
# Statistical anomaly checks
detect_anomalies(
    anglers_outlier=check_zscore(trip.anglers, historical_mean),
    catch_outlier=check_zscore(trip.total_fish, historical_mean),
    duplicate_trip=check_unique_constraint_violation(trip)
)
# Result: NORMAL / STATISTICAL_OUTLIER / DUPLICATE
```

**Categorization Logic**:

| Category | Criteria | Action |
|----------|----------|--------|
| **VALID** | Level 1: EXISTS + Level 2: EXACT_MATCH + Level 3: NORMAL | ✅ No action |
| **PHANTOM** | Level 1: NOT_FOUND | ⚠️ DELETE candidate |
| **MISATTRIBUTED** | Level 1: EXISTS + Level 2: boat/landing mismatch | ⚠️ UPDATE candidate |
| **PARTIAL** | Level 1: EXISTS + Level 2: anglers ±1-2 or minor catch variance | 🔍 Manual review |
| **DUPLICATE** | Level 1: EXISTS + Level 3: duplicate detected | ⚠️ DELETE candidate |
| **STATISTICAL_OUTLIER** | Level 1: EXISTS + Level 3: z-score >3 | 🔍 Manual review |

---

### FR-003: Evidence Capture & Audit Trail

**Requirement**: Document every finding with verifiable evidence

**Evidence Package** (for each non-VALID trip):

```json
{
  "trip_id": 12345,
  "audit_date": "2025-10-18T14:30:00Z",
  "category": "PHANTOM",
  "severity": "CRITICAL",

  "database_record": {
    "trip_date": "2025-10-15",
    "boat_id": 65,
    "boat_name": "New Seaforth",
    "landing_id": 14,
    "landing_name": "Seaforth Sportfishing",
    "trip_duration": "1/2 Day AM",
    "anglers": 18,
    "catches": [
      {"species": "Calico Bass", "count": 45},
      {"species": "Sand Bass", "count": 12}
    ]
  },

  "source_verification": {
    "source_url": "https://www.sandiegofishreports.com/dock_totals/boats.php?date=2025-10-15",
    "source_snapshot": "... raw HTML/text from source ...",
    "boats_found_on_date": ["Premier", "Daily Double", "Mission Belle"],
    "matching_trip": null,
    "closest_match": {
      "boat": "New Seaforth",
      "anglers": 20,  // Different!
      "duration": "1/2 Day AM",
      "similarity_score": 0.85
    }
  },

  "validation_results": {
    "level_1_exists": false,
    "level_2_fields": {
      "boat_match": true,
      "anglers_match": false,
      "duration_match": true,
      "catches_match": "NOT_CHECKED"
    },
    "level_3_anomalies": []
  },

  "recommendation": {
    "action": "DELETE",
    "confidence": "HIGH",
    "reasoning": "Trip does not exist on source page for date 2025-10-15. No trip with 18 anglers found. Closest match has 20 anglers.",
    "requires_manual_review": false
  },

  "evidence_files": [
    "evidence/trip_12345_source_snapshot.html",
    "evidence/trip_12345_screenshot.png"
  ]
}
```

**Evidence Storage**:
- `specs/009-continuous-data-audit/evidence/` - HTML snapshots, screenshots
- `specs/009-continuous-data-audit/audit_reports/` - Daily audit reports
- `specs/009-continuous-data-audit/remediation_queue/` - Approved fix lists

---

### FR-004: Automated Reporting & Alerting

**Requirement**: Generate actionable reports with remediation recommendations

**Daily Audit Report Format**:

```markdown
# Data Auditor Report – 2025-10-18

## Executive Summary
- **Sample Size**: 50 trips
- **Date Range**: 2025-09-18 to 2025-10-18 (last 30 days)
- **Landings Covered**: 8 landings (San Diego + SoCal)
- **Boats Covered**: 15 boats

## Findings Summary

| Category | Count | % of Sample | Severity |
|----------|-------|-------------|----------|
| ✅ VALID | 48 | 96.0% | NONE |
| 🔴 PHANTOM | 1 | 2.0% | CRITICAL |
| 🟡 MISATTRIBUTED | 1 | 2.0% | HIGH |
| 🟠 PARTIAL | 0 | 0.0% | MEDIUM |
| 🔵 DUPLICATE | 0 | 0.0% | HIGH |
| ⚪ OUTLIER | 0 | 0.0% | LOW |

## QC Confidence Score: 96.0%
⚠️ **ALERT**: QC confidence below 99.5% target. Immediate investigation required.

## Critical Findings Requiring Immediate Action

### PHANTOM Trip Detected (1)
**Trip ID 12345** - 2025-10-15, New Seaforth, 1/2 Day AM, 18 anglers
- **Issue**: Trip does not exist on source page
- **Evidence**: `evidence/trip_12345_source_snapshot.html`
- **Recommendation**: DELETE after manual verification
- **Confidence**: HIGH

### MISATTRIBUTED Trip Detected (1)
**Trip ID 12346** - 2025-10-16, Daily Double (boat_id 84), 1/2 Day AM, 22 anglers
- **Issue**: Trip exists but belongs to "Premier" (boat_id 50), not Daily Double
- **Evidence**: `evidence/trip_12346_source_snapshot.html`
- **Recommendation**: UPDATE boat_id = 50 WHERE id = 12346
- **Confidence**: HIGH

## Remediation Action Plan

### Immediate Actions (Require Approval)
```sql
-- PHANTOM deletion
BEGIN TRANSACTION;
DELETE FROM catches WHERE trip_id = 12345;
DELETE FROM trips WHERE id = 12345;
COMMIT;

-- MISATTRIBUTED correction
BEGIN TRANSACTION;
UPDATE trips SET boat_id = 50 WHERE id = 12346;
COMMIT;
```

### Manual Review Queue (0 trips)
None

## Statistical Summary
- Mean anglers per trip: 18.5 (within normal range 15-25)
- Mean catches per trip: 42.3 (within normal range 20-60)
- No statistical outliers detected

## Audit Coverage
- Trips audited this run: 50
- Unique dates covered: 22
- Boats never audited: 2 (Malihini, Tomahawk)
- Next audit recommended: 2025-10-19

---

**Audit completed at**: 2025-10-18 14:35:22
**Next scheduled audit**: 2025-10-19 02:00:00
**Generated by**: Data Auditor Agent v1.0.0
```

**Alert Triggers**:
- QC confidence <99.5% → Email/Slack notification
- >5 PHANTOM trips detected → Critical alert
- >10% of sample non-VALID → Emergency review
- Same boat flagged 3+ times → Pattern investigation

---

### FR-005: Remediation Workflow Integration

**Requirement**: Integrate with existing remediation procedures (SPEC-008 style)

**Workflow**:

```
Daily Audit Run
    ↓
Generate Report with Findings
    ↓
If findings detected:
    ↓
Create Remediation Proposal
    ↓
User Reviews & Approves
    ↓
Execute Approved Actions
    ↓
Verify & Log Results
```

**Remediation Queue Management**:

```python
# Daily audit produces remediation candidates
remediation_queue = {
    "audit_date": "2025-10-18",
    "findings": [
        {
            "trip_id": 12345,
            "category": "PHANTOM",
            "action": "DELETE",
            "confidence": "HIGH",
            "evidence_file": "evidence/trip_12345_source_snapshot.html",
            "status": "PENDING_APPROVAL"
        }
    ]
}

# User approval process (similar to SPEC-008)
# After approval, execute actions with full audit trail
```

**Safety Protocols**:
- ❌ NO automated deletions/updates without approval
- ✅ All actions require explicit user sign-off
- ✅ Pre-action snapshot (like SPEC-008)
- ✅ Transaction-safe execution
- ✅ Post-action verification

---

## Non-Functional Requirements

### NFR-001: Performance

**Requirements**:
- Audit runtime: <5 minutes for 50-trip sample
- Source page fetch: <2 seconds per page (with caching)
- Report generation: <30 seconds
- Memory usage: <500MB during execution

**Optimization Strategies**:
- Cache source pages for 24 hours (reduce fetches)
- Parallel validation of trips (asyncio)
- Incremental reporting (stream results)

---

### NFR-002: Reliability

**Requirements**:
- Source unavailable: Retry 3x with exponential backoff, then skip trip
- Network failures: Log and continue (don't abort entire audit)
- Database errors: Rollback and alert, don't corrupt data
- Audit history: Persist after each trip validation (incremental saves)

**Error Handling**:
```python
try:
    validate_trip(trip)
except SourceUnavailableError:
    log_warning("Source unavailable for trip {trip.id}, will retry next audit")
    audit_result.category = "VALIDATION_FAILED"
    audit_result.retry_count += 1
except DatabaseError as e:
    log_critical("Database error during audit: {e}")
    alert_admin()
    raise  # Abort audit, don't corrupt data
```

---

### NFR-003: Scheduling & Automation

**Requirements**:
- Daily automated runs at 2:00 AM PST (low-traffic time)
- Configurable sampling parameters (size, date range, stratification)
- Continuous audit history tracking (no gaps)
- Alert escalation for repeated failures

**Cron Schedule**:
```bash
# Daily at 2 AM PST
0 2 * * * cd /Users/btsukada/Desktop/Fishing/fish-scraper && python3 data_auditor.py --sample-size 50 --date-range 30 --report-dir specs/009-continuous-data-audit/audit_reports/
```

**Configuration File** (`audit_config.yaml`):
```yaml
sampling:
  date_range_days: 30
  sample_size: 50
  stratified: true
  min_boats_per_landing: 2

validation:
  anglers_tolerance: 1  # ±1 angler acceptable
  catch_count_tolerance_pct: 5  # ±5% catch count variance acceptable
  enable_statistical_outlier_detection: true
  z_score_threshold: 3.0

reporting:
  output_dir: "specs/009-continuous-data-audit/audit_reports/"
  evidence_dir: "specs/009-continuous-data-audit/evidence/"
  generate_screenshots: false  # Set true for visual evidence
  alert_on_qc_below: 99.5  # Alert if QC confidence below this

scheduling:
  enabled: true
  cron_schedule: "0 2 * * *"  # Daily at 2 AM
  max_runtime_minutes: 30

alerts:
  email_enabled: false
  slack_webhook_url: null
  alert_on_critical_findings: true
```

---

## Implementation Plan

### Phase 1: Core Auditor Development (Days 1-2)

**Deliverables**:
- `data_auditor.py` - Main audit script
- `audit_config.yaml` - Configuration file
- `specs/009-continuous-data-audit/spec.md` - This specification

**Tasks**:
1. Implement random sampling algorithm with stratification
2. Build validation logic (3 levels)
3. Create evidence capture system
4. Develop report generation
5. Test on recent trips (last 7 days)

---

### Phase 2: Integration & Testing (Day 3)

**Deliverables**:
- Integration with existing QC validator infrastructure
- Test suite for validation logic
- Performance benchmarks

**Tasks**:
1. Reuse QC validator source fetching code
2. Test false positive rate (<0.5% target)
3. Validate evidence capture completeness
4. Benchmark performance (50 trips in <5 min)

---

### Phase 3: Automation & Scheduling (Day 4)

**Deliverables**:
- Automated scheduling via cron
- Alert system integration
- Audit history tracking

**Tasks**:
1. Set up cron job for daily 2 AM runs
2. Implement alert triggers (Slack/email optional)
3. Create audit history database (`audit_history.json`)
4. Test end-to-end automation

---

### Phase 4: Production Deployment (Day 5)

**Deliverables**:
- First production audit run
- 30-day baseline QC confidence score
- Remediation workflow integration

**Tasks**:
1. Run first production audit
2. Establish baseline metrics
3. Document remediation workflow
4. Train user on report interpretation

---

## Success Metrics

**After 30 Days of Operation**:

**Quality Metrics**:
- QC confidence score: >99.5% (target)
- False positive rate: <0.5%
- Phantom trip detection: >90% accuracy
- Misattribution detection: >95% accuracy

**Coverage Metrics**:
- 100% of trips audited at least once per 90 days
- All active landings covered weekly
- All active boats covered every 2 weeks

**Operational Metrics**:
- Daily audit success rate: >95%
- Mean audit runtime: <5 minutes
- Alert response time: <4 hours for critical findings

---

## Risk Assessment

### Risk 1: False Positives (Legitimate Trips Flagged)
- **Severity**: HIGH
- **Mitigation**: Conservative categorization, manual review queue, evidence capture
- **Acceptance Criteria**: <0.5% false positive rate

### Risk 2: Source Availability Issues
- **Severity**: MEDIUM
- **Mitigation**: Retry logic, cached source data, validation failure tracking
- **Acceptance Criteria**: >95% source fetch success rate

### Risk 3: Audit Fatigue (Too Many Reports)
- **Severity**: LOW
- **Mitigation**: Alert only on critical findings, weekly summary reports
- **Acceptance Criteria**: User reviews all critical alerts within 24 hours

---

## Documentation & Artifacts

**Required Files**:
1. `specs/009-continuous-data-audit/spec.md` - This specification
2. `data_auditor.py` - Main audit script
3. `audit_config.yaml` - Configuration file
4. `audit_reports/YYYY-MM-DD_audit_report.md` - Daily reports
5. `evidence/trip_{id}_*.{html,json}` - Evidence files
6. `audit_history.json` - Historical audit tracking
7. `remediation_queue.json` - Pending remediation actions

**Integration Documentation**:
- Link from `README.md` - Continuous monitoring section
- Update `COMPREHENSIVE_QC_VERIFICATION.md` - Add audit findings
- Reference from `CLAUDE_OPERATING_GUIDE.md` - Operational procedures

---

## Appendix: Comparison to SPEC-006 QC Validator

| Feature | SPEC-006 QC Validator | SPEC-009 Data Auditor |
|---------|----------------------|----------------------|
| **Scope** | Validate specific dates/ranges on-demand | Random sampling of recent trips |
| **Frequency** | Ad-hoc (post-scrape validation) | Daily automated runs |
| **Coverage** | 100% of targeted date range | 5-10% random sample |
| **Purpose** | Verify scraping accuracy immediately | Detect drift/corruption over time |
| **Action** | Block bad scrapes, fix immediately | Report anomalies for review |
| **Speed** | ~2-3 sec/date | <5 min for 50 trips |

**Complementary Systems**: Both systems work together for comprehensive quality assurance.

---

**End of Specification SPEC-009**

**Next Steps**: Implement Phase 1 (Core Auditor Development)
