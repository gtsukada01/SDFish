# Specification 010: Scraper Pipeline Hardening & Future-Proof Safeguards

**Version**: 1.0.0
**Date**: October 19, 2025
**Status**: DRAFT - PENDING APPROVAL
**Governed By**: SPEC 006 QC Validation Standards
**Triggered By**: 2025-10-19 Phantom Data Incident (18 corrupted trips across 10/19, 10/20)
**Author**: Fishing Intelligence Platform
**Priority**: P0 - CRITICAL (Data Integrity Failure)

---

## Executive Summary

### Problem Statement

On October 19, 2025, **18 phantom trips** were discovered in the production database dated 10/19 and 10/20 - dates that were scraped prematurely when boats had not yet reported. Root cause analysis revealed critical vulnerabilities in the scraper pipeline:

**Critical Defects Identified**:
1. **Parser blindly trusts requested date parameter** (boats_scraper.py:365) - stamps trips with requested date instead of validating actual report date from page header
2. **No future-date guard** (boats_scraper.py:522-589) - scrape_date_range allows processing dates beyond today without validation
3. **Duplicate check keys on date** (boats_scraper.py:444-451) - identical trips with different dates pass duplicate detection
4. **Website serves fallback content** - when future dates requested, source returns latest published report (10/16 data served for 10/19, 10/20 requests)
5. **No audit trail** - impossible to determine who ran scrape, with what arguments, when, or from which code version
6. **No timezone enforcement** - scraper relies on system time without Pacific Time validation
7. **No automated QC integration** - manual validation required, no post-scrape alerts

### Impact

**Data Integrity Crisis**:
- **18 phantom trips** injected into production (9 on 10/19, 9 on 10/20)
- **10/18 completely missing** (0 trips in database despite ~17 trips on source)
- **User trust compromised** - dashboard showing impossible data (boats reporting before trips occurred)
- **Analytics corrupted** - any analysis including 10/15-10/20 range contains phantom duplicates
- **Zero accountability** - no audit trail to track who/when/how corruption occurred

**Systemic Risk**:
- **Silent failures** - corruption went undetected until user manually noticed
- **Repeatable vulnerability** - same issue will recur without architectural changes
- **Production-readiness questioned** - 100% accuracy mandate compromised (SPEC-006)

### Solution

**Comprehensive Pipeline Hardening** following 2025 industry best practices:

1. **Source Date Validation** - Parse actual report date from page header, abort on mismatch with requested date
2. **Future Date Prevention** - Hard guard preventing scraping dates > today (requires explicit --allow-future flag)
3. **Complete Audit Trail** - scrape_jobs table tracking operator, arguments, Git SHA, date range, results for every run
4. **Timezone Standardization** - Enforce Pacific Time for all date logic, validation, scheduling
5. **Deep Deduplication** - Multi-field hash with N-day cross-check to detect phantom duplicates
6. **Automated QC Integration** - Post-scrape validation with alerts on anomalies
7. **Operator Authentication** - Require operator identity for all manual runs
8. **Fail-Safe Cleanup** - Atomic deletion/re-scrape with full audit logging

---

## Functional Requirements

### FR-001: Source Date Validation (Parser Hardening)

**Priority**: P0 - CRITICAL (Prevent Future Phantom Data)

**Requirement**: Parser MUST extract and validate actual report date from source page before stamping trips

**Current Defect** (boats_scraper.py:357-370):
```python
# DEFECT: Blindly trusts date parameter
trip = {
    'boat_name': boat_name,
    'landing_name': current_landing,
    'trip_date': date,  # ❌ NEVER VALIDATED AGAINST PAGE CONTENT
    'trip_duration': normalized_trip_type,
    'anglers': anglers,
    'catches': catches
}
```

**Required Behavior**:

1. **Parse Displayed Date from Page Header**
   - Extract date from "Dock Totals for Tuesday 10/15/2025" header
   - Validate header exists and is parseable
   - Normalize to YYYY-MM-DD format

2. **Abort on Date Mismatch**
   ```python
   def parse_boats_page(html: str, requested_date: str) -> List[Dict]:
       # NEW: Extract actual report date from page
       actual_date = extract_report_date_from_header(html)

       if actual_date is None:
           raise ParserError(f"Could not parse report date from page header")

       if actual_date != requested_date:
           raise DateMismatchError(
               f"Date mismatch: requested {requested_date}, "
               f"page shows {actual_date}. "
               f"Source may be serving fallback/cached content."
           )

       # Continue with normal parsing...
   ```

3. **Log and Alert**
   - Log ERROR level message with request URL, requested date, detected date
   - Alert user to investigate (Slack/email if configured)
   - Abort scraping, do NOT insert any trips

**Acceptance Criteria**:
- ✅ Parser extracts date from "Dock Totals for [Day] MM/DD/YYYY" header
- ✅ Date mismatch causes immediate abort (no trips inserted)
- ✅ Error message includes requested vs actual date
- ✅ Test case: Requesting future date (10/25/2025) aborts with clear error
- ✅ Test case: Requesting valid date (10/17/2025) passes and extracts correct date

---

### FR-002: Future Date Prevention (Range Hardening)

**Priority**: P0 - CRITICAL (Prevent Premature Scraping)

**Requirement**: scrape_date_range MUST enforce end_date <= today unless explicit override flag provided

**Current Defect** (boats_scraper.py:522-589):
```python
# DEFECT: No validation that end_date <= today
def scrape_date_range(start_date: str, end_date: str, dry_run: bool = False):
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()  # ❌ NO FUTURE CHECK

    while current <= end:  # ❌ WILL PROCESS FUTURE DATES
        date_str = current.strftime('%Y-%m-%d')
        # ... scrape date_str ...
```

**Required Behavior**:

1. **Default Clamp to Today (Pacific Time)**
   ```python
   def scrape_date_range(
       start_date: str,
       end_date: str,
       dry_run: bool = False,
       allow_future: bool = False  # NEW: Explicit override flag
   ):
       start = datetime.strptime(start_date, '%Y-%m-%d').date()
       end = datetime.strptime(end_date, '%Y-%m-%d').date()

       # NEW: Get today in Pacific Time (reports publish in PT)
       pacific = pytz.timezone('America/Los_Angeles')
       today = datetime.now(pacific).date()

       # NEW: Hard guard against future dates
       if end > today and not allow_future:
           raise FutureDateError(
               f"end_date {end_date} is in the future (today is {today}). "
               f"Use --allow-future flag if intentional (not recommended)."
           )

       if allow_future:
           logger.warning(
               f"⚠️  FUTURE DATE SCRAPING ENABLED: {end_date} > {today}. "
               f"This may produce phantom data if source serves fallback content."
           )
   ```

2. **Logging and Audit**
   - Log WARNING when --allow-future used (audit trail critical)
   - Log INFO for normal date ranges (start, end, today)
   - Include timezone in all log timestamps

**Acceptance Criteria**:
- ✅ Scraping 10/25/2025 (future) without --allow-future raises FutureDateError
- ✅ Scraping 10/25/2025 with --allow-future succeeds but logs WARNING
- ✅ Today calculation uses Pacific Time (America/Los_Angeles)
- ✅ Error message clearly explains issue and solution
- ✅ Audit trail captures all future date attempts

---

### FR-003: Scrape Jobs Audit Trail

**Priority**: P0 - CRITICAL (Accountability & Traceability)

**Requirement**: Every scrape operation MUST be logged to scrape_jobs table with full context

**Motivation**:
- **Zero audit trail** for 10/19 incident - cannot determine who ran scrape, when, with what args
- **Compliance requirement** - data lineage for every trip in database
- **Debugging essential** - link corrupted data back to scrape job and code version

**Database Schema**:

```sql
CREATE TABLE scrape_jobs (
    id BIGSERIAL PRIMARY KEY,

    -- Execution Context
    job_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    job_completed_at TIMESTAMPTZ,
    job_status VARCHAR(20) NOT NULL CHECK (job_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'ABORTED')),

    -- Operator Identity
    operator VARCHAR(255) NOT NULL,  -- Username/email of who ran scrape
    operator_source VARCHAR(50) NOT NULL,  -- 'CLI', 'CRON', 'API'

    -- Scrape Parameters
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    allow_future BOOLEAN DEFAULT FALSE,
    dry_run BOOLEAN DEFAULT FALSE,

    -- Code Version
    git_sha VARCHAR(40),  -- Git commit SHA at time of scrape
    scraper_version VARCHAR(20),  -- Semantic version of scraper

    -- Results
    dates_processed INT DEFAULT 0,
    trips_inserted INT DEFAULT 0,
    trips_updated INT DEFAULT 0,
    trips_failed INT DEFAULT 0,
    error_message TEXT,

    -- Metadata
    runtime_seconds NUMERIC(10,2),
    source_url_pattern VARCHAR(500),

    UNIQUE (operator, job_started_at)
);

CREATE INDEX idx_scrape_jobs_date_range ON scrape_jobs(start_date, end_date);
CREATE INDEX idx_scrape_jobs_operator ON scrape_jobs(operator);
CREATE INDEX idx_scrape_jobs_status ON scrape_jobs(job_status);
```

**Trip Linkage** (add to trips table):
```sql
ALTER TABLE trips ADD COLUMN scrape_job_id BIGINT REFERENCES scrape_jobs(id);
CREATE INDEX idx_trips_scrape_job ON trips(scrape_job_id);
```

**Implementation Requirements**:

1. **Job Creation (Start of Scrape)**
   ```python
   def create_scrape_job(
       operator: str,
       start_date: str,
       end_date: str,
       allow_future: bool = False,
       dry_run: bool = False
   ) -> int:
       """Create scrape job record, return job_id"""

       git_sha = get_git_sha()  # subprocess: git rev-parse HEAD
       scraper_version = get_scraper_version()  # From __version__

       job = supabase.table('scrape_jobs').insert({
           'operator': operator,
           'operator_source': get_operator_source(),  # CLI/CRON/API
           'start_date': start_date,
           'end_date': end_date,
           'allow_future': allow_future,
           'dry_run': dry_run,
           'git_sha': git_sha,
           'scraper_version': scraper_version,
           'job_status': 'RUNNING',
           'source_url_pattern': BOATS_URL_TEMPLATE
       }).execute()

       return job.data[0]['id']
   ```

2. **Job Updates (During Scrape)**
   ```python
   def update_scrape_job_progress(job_id: int, dates_processed: int, trips_inserted: int):
       """Update job progress incrementally"""
       supabase.table('scrape_jobs').update({
           'dates_processed': dates_processed,
           'trips_inserted': trips_inserted
       }).eq('id', job_id).execute()
   ```

3. **Job Completion (End of Scrape)**
   ```python
   def complete_scrape_job(
       job_id: int,
       status: str,  # SUCCESS/FAILED/ABORTED
       error_message: Optional[str] = None
   ):
       """Mark job as complete with final stats"""

       job_data = supabase.table('scrape_jobs').select('job_started_at').eq('id', job_id).execute()
       started_at = datetime.fromisoformat(job_data.data[0]['job_started_at'])
       runtime = (datetime.now(pytz.UTC) - started_at).total_seconds()

       supabase.table('scrape_jobs').update({
           'job_status': status,
           'job_completed_at': datetime.now(pytz.UTC).isoformat(),
           'runtime_seconds': runtime,
           'error_message': error_message
       }).eq('id', job_id).execute()
   ```

4. **Link Trips to Job**
   ```python
   # When inserting trips
   trip_data = {
       'boat_id': boat_id,
       'trip_date': date,
       'scrape_job_id': current_job_id,  # NEW: Link to job
       # ... other fields ...
   }
   ```

**Acceptance Criteria**:
- ✅ scrape_jobs table created in Supabase with all fields
- ✅ Every scrape creates job record before processing
- ✅ Job status updates to SUCCESS/FAILED on completion
- ✅ Git SHA captured for code traceability
- ✅ Operator identity required (--operator CLI arg or $SCRAPER_OPERATOR env)
- ✅ All trips link to scrape_job_id
- ✅ Query: "Show all trips from job 123" returns linked trips
- ✅ Query: "Show all jobs run by operator X" returns history

---

### FR-004: Timezone Standardization (Pacific Time Enforcement)

**Priority**: P1 - HIGH (Prevent Time Drift Issues)

**Requirement**: All date/time logic MUST use Pacific Time (America/Los_Angeles) consistently

**Motivation**:
- **Source publishes in Pacific Time** - sandiegofishreports.com operates on PT
- **System time unreliable** - cloud/serverless environments may use UTC or other zones
- **Cron scheduling issues** - automated runs must align with report publication times

**Implementation Requirements**:

1. **Central Timezone Constant**
   ```python
   # boats_scraper.py - TOP OF FILE
   import pytz

   PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

   def get_pacific_now() -> datetime:
       """Get current time in Pacific timezone"""
       return datetime.now(PACIFIC_TZ)

   def get_pacific_today() -> date:
       """Get today's date in Pacific timezone"""
       return get_pacific_now().date()
   ```

2. **Validate Scrape Timing**
   ```python
   def validate_scrape_timing(date_str: str, require_after_hour: int = 17):
       """
       Validate it's safe to scrape this date (reports publish ~5pm PT)

       Args:
           date_str: Date to scrape (YYYY-MM-DD)
           require_after_hour: Hour (PT) after which scraping is safe (default 17 = 5pm)
       """
       scrape_date = datetime.strptime(date_str, '%Y-%m-%d').date()
       pacific_now = get_pacific_now()
       today_pt = pacific_now.date()

       # If scraping today, check if reports are likely published
       if scrape_date == today_pt and pacific_now.hour < require_after_hour:
           raise ScrapingTooEarlyError(
               f"Scraping today's data ({scrape_date}) before {require_after_hour}:00 PT. "
               f"Current time: {pacific_now.strftime('%H:%M PT')}. "
               f"Reports typically publish after 5pm PT. "
               f"Use --allow-early flag to override (not recommended)."
           )
   ```

3. **Database Timestamp Storage**
   - All timestamp fields MUST be TIMESTAMPTZ (timezone-aware)
   - Store in UTC, convert to PT for display/logic
   - Log entries include timezone in ISO format

**Acceptance Criteria**:
- ✅ get_pacific_today() used for "today" calculation in future date guard
- ✅ Scraping today before 5pm PT raises ScrapingTooEarlyError
- ✅ All log timestamps include timezone (e.g., "2025-10-19T14:30:00-07:00")
- ✅ scrape_jobs.job_started_at stored as TIMESTAMPTZ
- ✅ Documentation clearly states Pacific Time assumption

---

### FR-005: Deep Deduplication with N-Day Cross-Check

**Priority**: P1 - HIGH (Detect Phantom Duplicates)

**Requirement**: Duplicate detection MUST identify identical trips across different dates

**Current Defect** (boats_scraper.py:425-474):
```python
# DEFECT: Includes trip_date in composite key
def check_trip_exists(...):
    query = supabase.table('trips').select('id') \
        .eq('boat_id', boat_id) \
        .eq('trip_date', trip_date) \  # ❌ DATE IN KEY - ALLOWS DUPLICATES ACROSS DATES
        .eq('trip_duration', trip_duration)
```

**Required Behavior**:

1. **Multi-Field Content Hash**
   ```python
   import hashlib
   import json

   def compute_trip_hash(
       boat_id: int,
       trip_duration: str,
       anglers: Optional[int],
       catches: List[Dict]
   ) -> str:
       """
       Compute deterministic hash of trip content (excluding date)

       Same boat + duration + anglers + catches = same hash
       Allows detection of identical trips on different dates
       """
       # Sort catches for deterministic hashing
       sorted_catches = sorted(catches, key=lambda c: c['species'])

       hash_input = {
           'boat_id': boat_id,
           'trip_duration': trip_duration,
           'anglers': anglers,
           'catches': sorted_catches
       }

       hash_str = json.dumps(hash_input, sort_keys=True)
       return hashlib.sha256(hash_str.encode()).hexdigest()[:16]
   ```

2. **N-Day Duplicate Check**
   ```python
   def check_duplicate_in_window(
       trip_hash: str,
       trip_date: str,
       window_days: int = 7
   ) -> Optional[Dict]:
       """
       Check if identical trip exists within ±N days

       Returns matching trip if found, None otherwise
       """
       date_obj = datetime.strptime(trip_date, '%Y-%m-%d').date()
       start_date = (date_obj - timedelta(days=window_days)).isoformat()
       end_date = (date_obj + timedelta(days=window_days)).isoformat()

       result = supabase.table('trips').select('*') \
           .eq('trip_hash', trip_hash) \
           .gte('trip_date', start_date) \
           .lte('trip_date', end_date) \
           .neq('trip_date', trip_date) \  # Exclude same date
           .execute()

       if result.data:
           return result.data[0]  # Return first match
       return None
   ```

3. **Schema Addition**
   ```sql
   ALTER TABLE trips ADD COLUMN trip_hash VARCHAR(16);
   CREATE INDEX idx_trips_hash ON trips(trip_hash);
   ```

4. **Insert Logic Update**
   ```python
   # Before inserting trip
   trip_hash = compute_trip_hash(boat_id, trip_duration, anglers, catches)

   duplicate = check_duplicate_in_window(trip_hash, trip_date, window_days=7)
   if duplicate:
       logger.warning(
           f"⚠️  POTENTIAL PHANTOM: Trip on {trip_date} matches trip on {duplicate['trip_date']}. "
           f"Boat: {boat_name}, Duration: {trip_duration}, Anglers: {anglers}. "
           f"This may be fallback data. Flagging for review."
       )

       # OPTION 1: Abort insertion
       raise DuplicateContentError(f"Duplicate trip found on {duplicate['trip_date']}")

       # OPTION 2: Flag for review
       trip_data['needs_review'] = True
       trip_data['review_reason'] = f"Duplicate content from {duplicate['trip_date']}"

   trip_data['trip_hash'] = trip_hash
   ```

**Acceptance Criteria**:
- ✅ trip_hash column added to trips table
- ✅ Hash computed from boat_id + duration + anglers + sorted catches
- ✅ Duplicate check searches ±7 days by default
- ✅ Test case: Inserting 10/16 trip, then identical trip on 10/19 → raises DuplicateContentError
- ✅ Test case: Two different trips on same date → no duplicate warning
- ✅ Duplicate detection logged at WARNING level with trip details

---

### FR-006: Automated QC Integration

**Priority**: P1 - HIGH (Post-Scrape Validation)

**Requirement**: scrape_date_range MUST automatically run QC validation after processing each date

**Implementation Requirements**:

1. **Inline QC After Each Date**
   ```python
   def scrape_date_range(..., auto_qc: bool = True):
       # ... existing scrape logic ...

       for current_date in date_range:
           date_str = current_date.strftime('%Y-%m-%d')

           # Scrape date
           trips = scrape_single_date(date_str)
           insert_trips(trips)

           # NEW: Auto QC validation
           if auto_qc:
               qc_result = run_qc_validation(date_str)

               if qc_result['status'] == 'FAIL':
                   logger.error(
                       f"❌ QC FAILED for {date_str}: {qc_result['summary']}"
                   )

                   if auto_qc_abort_on_fail:
                       # Rollback date, abort scrape
                       delete_trips_for_date(date_str)
                       raise QCValidationError(f"QC failed for {date_str}, aborting scrape")
                   else:
                       # Flag for review
                       flag_date_for_review(date_str, qc_result)
               else:
                   logger.info(f"✅ QC PASSED for {date_str}")
   ```

2. **QC Validation Function**
   ```python
   def run_qc_validation(date_str: str) -> Dict:
       """
       Run QC validation for single date using existing qc_validator.py logic

       Returns:
           {
               'status': 'PASS' | 'FAIL',
               'date': date_str,
               'source_count': int,
               'db_count': int,
               'mismatches': [],
               'summary': str
           }
       """
       # Reuse existing qc_validator.py logic
       from qc_validator import validate_single_date
       return validate_single_date(date_str)
   ```

3. **CLI Options**
   ```bash
   python3 boats_scraper.py \
       --start-date 2025-10-18 \
       --end-date 2025-10-19 \
       --auto-qc  # Enable automatic QC after each date
       --qc-abort-on-fail  # Abort entire scrape if any date fails QC
   ```

**Acceptance Criteria**:
- ✅ --auto-qc flag enables post-scrape QC validation
- ✅ QC runs after each date insertion
- ✅ QC failure logs ERROR with details
- ✅ --qc-abort-on-fail deletes failed date and aborts scrape
- ✅ QC results logged to scrape_jobs table

---

### FR-007: Operator Identity & Authentication

**Priority**: P2 - MEDIUM (Accountability)

**Requirement**: All manual scrape operations MUST include operator identity

**Implementation Requirements**:

1. **Require Operator Identification**
   ```python
   def get_operator_identity() -> str:
       """
       Get operator identity from CLI arg or environment

       Order of precedence:
       1. --operator CLI argument
       2. $SCRAPER_OPERATOR environment variable
       3. System username (fallback, logged as WARNING)
       """
       operator = args.operator or os.getenv('SCRAPER_OPERATOR')

       if not operator:
           import getpass
           operator = getpass.getuser()
           logger.warning(
               f"⚠️  No operator specified, using system username: {operator}. "
               f"Use --operator or set $SCRAPER_OPERATOR for proper audit trail."
           )

       return operator
   ```

2. **Operator Source Detection**
   ```python
   def get_operator_source() -> str:
       """Detect how scraper was invoked"""
       if os.getenv('CRON_JOB'):
           return 'CRON'
       elif sys.stdin.isatty():
           return 'CLI'
       else:
           return 'AUTOMATED'
   ```

3. **CLI Argument**
   ```python
   parser.add_argument(
       '--operator',
       type=str,
       help='Operator identity (email/username) for audit trail. '
            'Can also set $SCRAPER_OPERATOR environment variable.'
   )
   ```

**Acceptance Criteria**:
- ✅ --operator CLI argument accepted
- ✅ $SCRAPER_OPERATOR environment variable supported
- ✅ Operator identity stored in scrape_jobs.operator
- ✅ Warning logged if fallback to system username
- ✅ Documentation updated with operator identity requirement

---

### FR-008: Fail-Safe Cleanup & Re-Scrape Procedures

**Priority**: P2 - MEDIUM (Operational Safety)

**Requirement**: Provide safe, audited procedures for deleting corrupted data and re-scraping

**Implementation Requirements**:

1. **Safe Date Range Deletion**
   ```python
   def delete_date_range_with_audit(
       start_date: str,
       end_date: str,
       operator: str,
       reason: str,
       dry_run: bool = True
   ):
       """
       Safely delete all trips in date range with full audit trail

       Args:
           start_date: Start date (YYYY-MM-DD)
           end_date: End date (YYYY-MM-DD)
           operator: Who is performing deletion
           reason: Why deletion is necessary
           dry_run: If True, show what would be deleted without deleting
       """
       # Get trips to delete
       trips_query = supabase.table('trips').select('*') \
           .gte('trip_date', start_date) \
           .lte('trip_date', end_date) \
           .execute()

       trips_to_delete = trips_query.data

       if dry_run:
           print(f"DRY RUN: Would delete {len(trips_to_delete)} trips")
           print(f"Date range: {start_date} to {end_date}")
           print(f"Operator: {operator}")
           print(f"Reason: {reason}")
           for trip in trips_to_delete[:5]:  # Show first 5
               print(f"  - {trip['trip_date']} {trip['boat_name']} {trip['trip_duration']}")
           if len(trips_to_delete) > 5:
               print(f"  ... and {len(trips_to_delete) - 5} more")
           return

       # Create deletion audit record
       deletion_record = {
           'operator': operator,
           'deleted_at': datetime.now(pytz.UTC).isoformat(),
           'start_date': start_date,
           'end_date': end_date,
           'trips_deleted': len(trips_to_delete),
           'reason': reason,
           'trip_ids': [t['id'] for t in trips_to_delete]
       }

       # Backup to JSON before deleting
       backup_file = f"backup_{start_date}_{end_date}_{int(time.time())}.json"
       with open(backup_file, 'w') as f:
           json.dump({
               'deletion_metadata': deletion_record,
               'deleted_trips': trips_to_delete
           }, f, indent=2)

       print(f"✅ Backup saved to {backup_file}")

       # Delete trips (transaction-safe)
       try:
           for trip in trips_to_delete:
               # Delete catches first (foreign key)
               supabase.table('catches').delete().eq('trip_id', trip['id']).execute()
               # Delete trip
               supabase.table('trips').delete().eq('id', trip['id']).execute()

           print(f"✅ Deleted {len(trips_to_delete)} trips from {start_date} to {end_date}")

       except Exception as e:
           logger.error(f"❌ Deletion failed: {e}")
           print(f"⚠️  RESTORE FROM BACKUP: {backup_file}")
           raise
   ```

2. **CLI Tool**
   ```bash
   # Dry run first
   python3 delete_date_range.py \
       --start-date 2025-10-19 \
       --end-date 2025-10-20 \
       --operator "user@example.com" \
       --reason "Phantom data from premature scrape" \
       --dry-run

   # Execute after review
   python3 delete_date_range.py \
       --start-date 2025-10-19 \
       --end-date 2025-10-20 \
       --operator "user@example.com" \
       --reason "Phantom data from premature scrape"
   ```

**Acceptance Criteria**:
- ✅ delete_date_range.py script created
- ✅ Dry run shows exactly what would be deleted
- ✅ Backup JSON created before deletion
- ✅ Deletion audit record includes operator, reason, timestamp
- ✅ Transaction-safe deletion (all or nothing)
- ✅ Documentation includes recovery procedures

---

## Non-Functional Requirements

### NFR-001: Performance

**Requirements**:
- Source date extraction: <100ms per page
- Future date validation: <10ms
- Trip hash computation: <5ms per trip
- N-day duplicate check: <50ms per trip (indexed)
- Audit trail insertion: <20ms per job record

**Optimization**:
- Batch trip inserts (100 trips per transaction)
- Cache compiled date extraction regex
- Index trip_hash for fast duplicate lookups

---

### NFR-002: Backward Compatibility

**Requirements**:
- Existing trips without scrape_job_id, trip_hash remain valid
- QC validator continues working unchanged
- CLI maintains existing arguments (new flags are optional)
- Database migrations are additive only (no data loss)

**Migration Strategy**:
```sql
-- Add columns as nullable first
ALTER TABLE trips ADD COLUMN scrape_job_id BIGINT REFERENCES scrape_jobs(id);
ALTER TABLE trips ADD COLUMN trip_hash VARCHAR(16);

-- Backfill trip_hash for existing trips
UPDATE trips SET trip_hash = compute_hash_from_trip(...)
WHERE trip_hash IS NULL;

-- Cannot backfill scrape_job_id (historical jobs unknown)
-- Leave NULL for pre-audit-trail trips
```

---

### NFR-003: Monitoring & Alerting

**Requirements**:
- Log all safeguard triggers (date mismatch, future date, duplicate, etc.)
- Expose metrics via /metrics endpoint (optional)
- Integrate with existing logging infrastructure
- Alert on repeated safeguard triggers (potential attack/misconfiguration)

**Metrics to Track**:
- `scraper.date_mismatch.count` - How often source date ≠ requested date
- `scraper.future_date_blocked.count` - Future date attempts
- `scraper.duplicate_detected.count` - Phantom duplicate detections
- `scraper.qc_failures.count` - Post-scrape QC failures
- `scraper.jobs.total` - Total scrape jobs run
- `scraper.jobs.failed` - Failed jobs

---

## Implementation Plan

### Phase 1: Critical Safeguards (Days 1-2)

**Deliverables**:
- FR-001: Source date validation in parse_boats_page
- FR-002: Future date guard in scrape_date_range
- FR-003: scrape_jobs table and audit logging
- NFR-002: Database migrations

**Tasks**:
1. Create scrape_jobs table in Supabase
2. Implement extract_report_date_from_header() function
3. Add date mismatch detection and abort logic
4. Add future date validation with --allow-future flag
5. Implement create_scrape_job(), update_scrape_job_progress(), complete_scrape_job()
6. Update scrape_date_range to use job audit
7. Add --operator CLI argument

**Testing**:
- Test date extraction on 10 sample pages (valid dates)
- Test date mismatch abort (request 10/25, page shows 10/16)
- Test future date blocking (request 10/25 without --allow-future)
- Verify scrape_jobs record created for every run
- Verify Git SHA captured correctly

**Acceptance**:
- ✅ User approves date extraction logic
- ✅ All tests pass
- ✅ No existing functionality broken

---

### Phase 2: Deduplication & Timezone (Days 3-4)

**Deliverables**:
- FR-004: Pacific Time enforcement
- FR-005: Deep deduplication with trip_hash
- NFR-001: Performance benchmarks

**Tasks**:
1. Add trip_hash column to trips table
2. Implement compute_trip_hash() function
3. Implement check_duplicate_in_window() function
4. Add PACIFIC_TZ constant and get_pacific_today()
5. Add validate_scrape_timing() with --allow-early flag
6. Benchmark hash computation and duplicate check performance

**Testing**:
- Test trip hash stability (same trip → same hash)
- Test duplicate detection (10/16 trip, then 10/19 duplicate)
- Test Pacific Time calculation (mock system time as UTC)
- Test scraping today before 5pm PT (should abort)
- Benchmark 1000 trips: hash + duplicate check <5 seconds

**Acceptance**:
- ✅ Duplicate detection catches phantom trips
- ✅ Pacific Time used consistently
- ✅ Performance targets met

---

### Phase 3: QC Integration & Cleanup (Day 5)

**Deliverables**:
- FR-006: Automated QC integration
- FR-008: delete_date_range.py cleanup tool
- Documentation updates

**Tasks**:
1. Implement run_qc_validation() wrapper
2. Add --auto-qc and --qc-abort-on-fail flags
3. Integrate QC into scrape_date_range loop
4. Create delete_date_range.py script
5. Test dry-run deletion
6. Test actual deletion with backup
7. Update CLAUDE_OPERATING_GUIDE.md with new procedures

**Testing**:
- Test auto-QC detects mismatches
- Test --qc-abort-on-fail rollback
- Test delete_date_range dry run
- Test delete_date_range backup/restore
- Verify documentation accuracy

**Acceptance**:
- ✅ Auto-QC prevents bad data insertion
- ✅ Cleanup procedures documented and tested
- ✅ User approves operational procedures

---

### Phase 4: Recovery & Validation (Day 6)

**Deliverables**:
- Re-scrape 10/18, 10/19 with all safeguards enabled
- Validate 10/18, 10/19 data matches source
- Production deployment

**Tasks**:
1. Delete 10/18-10/20 range (already done for 10/19, 10/20)
2. Re-scrape 10/18 with --auto-qc --operator
3. Re-scrape 10/19 with --auto-qc --operator
4. Run comprehensive QC validation
5. Verify scrape_jobs audit trail
6. Update dashboards with recovered data

**Acceptance**:
- ✅ 10/18 fully scraped (~17 trips expected)
- ✅ 10/19 fully scraped (~9 trips expected)
- ✅ 100% QC pass rate
- ✅ All trips linked to scrape_jobs
- ✅ User confirms data accuracy

---

## Success Metrics

**After 30 Days of Operation**:

**Data Integrity**:
- Zero phantom trips detected (0 date mismatches)
- Zero future date violations (0 premature scrapes)
- Zero duplicate content across dates (N-day check active)
- 100% QC pass rate maintained (SPEC-006 standard)

**Audit Compliance**:
- 100% of scrapes logged to scrape_jobs table
- 100% of trips linked to scrape_job_id
- Git SHA captured for all jobs
- Operator identity tracked for all manual runs

**Operational**:
- Zero data corruption incidents
- <5% scrape failures (network/source issues acceptable)
- <1 hour recovery time for any incidents (cleanup tools ready)

---

## Risk Assessment

### Risk 1: Source Page Format Change
- **Severity**: HIGH
- **Mitigation**: Date extraction regex with fallback patterns, test suite for parser
- **Acceptance**: Parser gracefully fails with clear error, not silent corruption

### Risk 2: Performance Impact from Safeguards
- **Severity**: MEDIUM
- **Mitigation**: Benchmarking, indexing, batching
- **Acceptance**: <10% slowdown compared to current scraper

### Risk 3: False Positives in Duplicate Detection
- **Severity**: MEDIUM
- **Mitigation**: Configurable window_days, manual review queue, evidence capture
- **Acceptance**: <1% false positive rate (legitimate trips flagged)

### Risk 4: Migration Complexity
- **Severity**: LOW
- **Mitigation**: Additive schema changes only, comprehensive testing
- **Acceptance**: Zero data loss during migration

---

## Documentation & Artifacts

**Required Files**:
1. `specs/010-pipeline-hardening/spec.md` - This specification
2. `specs/010-pipeline-hardening/README.md` - Implementation summary
3. `delete_date_range.py` - Safe deletion tool
4. `migration_010_scrape_jobs.sql` - Database migration
5. `migration_010_trip_hash.sql` - Add trip_hash column
6. `test_safeguards.py` - Test suite for all safeguards

**Documentation Updates**:
- `CLAUDE_OPERATING_GUIDE.md` - Add safeguard procedures, delete/re-scrape workflows
- `README.md` - Reference SPEC-010 in system safeguards section
- `boats_scraper.py` - Inline comments explaining safeguards
- `COMPREHENSIVE_QC_VERIFICATION.md` - Document 10/19 incident and remediation

---

## Appendix A: Incident Timeline (2025-10-19)

**08:00 PT** - User notices 10/19 data in dashboard (9 trips)
**08:15 PT** - Investigation begins, suspects timezone issue
**08:30 PT** - Discovers 10/19 data is duplicates of 10/16 data (same boats, anglers, catches)
**08:35 PT** - Discovers 10/20 also has phantom duplicates (9 trips)
**08:40 PT** - Discovers 10/18 completely missing (0 trips)
**09:00 PT** - User performs root cause analysis, identifies parser defects
**09:15 PT** - Deletes 18 corrupted trips (9 from 10/19, 9 from 10/20)
**09:30 PT** - User requests comprehensive safeguard strategy
**10:00 PT** - SPEC-010 created to prevent recurrence

**Root Cause**: Scraper processed future dates (10/19, 10/20) when source served fallback content (10/16 data), parser blindly stamped trips with requested dates instead of validating actual report date.

**Immediate Fix**: Manual deletion of phantom trips
**Long-Term Fix**: SPEC-010 implementation (this document)

---

**End of Specification SPEC-010**

**Next Steps**:
1. User reviews and approves specification
2. Implement Phase 1 (Critical Safeguards)
3. Progressive deployment with testing after each phase
4. Full recovery of 10/18-10/19 data with safeguards enabled
