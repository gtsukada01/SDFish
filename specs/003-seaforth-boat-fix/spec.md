# Feature Specification: Seaforth Boat Attribution Fix

**Feature Branch**: `003-seaforth-boat-fix`
**Created**: 2025-10-15
**Status**: In Progress
**Input**: User description: "Re-scrape 22 dates from sandiegofishreports.com to correctly attribute 85 Seaforth fishing trips to actual boats"

## Problem Statement

Between September 24 and October 15, 2025 (22 dates), a buggy scraper incorrectly attributed 85 Seaforth fishing trips to a boat named "Seaforth Sportfishing" (boat ID 329), which is actually the landing name, not a boat name. The correct boat names should be "New Seaforth", "San Diego", "Pacific Voyager", "Highliner", etc.

**Impact**:
- Database contains incorrect boat attributions
- Dashboard displays misleading trip data
- Statistical analysis of boat performance is invalid for these 85 trips

**Root Cause**: The deleted scraper (`sd_fish_scraper.py`) used the "author" field (e.g., "Seaforth Staff") as the boat name instead of parsing the actual boat name from the structured data.

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT needs to be validated and WHY
- ❌ Avoid HOW to implement scraping logic (that's already done in `boats_scraper.py`)
- 👥 Written for data quality stakeholders and project maintainers
- 🐟 Honour data fidelity: all re-scraped data must match source exactly
- ⚡ Capture validation expectations (boat name format, species consistency)
- 📋 Specify rollback and audit trail requirements

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As a **data quality manager**, I need to **correct 85 misattributed fishing trips** so that **dashboard users see accurate boat names and trip statistics**.

**Success Outcome**: When users filter by "Seaforth Sportfishing" landing, they see trips correctly attributed to individual boats like "New Seaforth" and "San Diego", not to a boat named "Seaforth Sportfishing".

### Acceptance Scenarios

1. **Given** boat ID 329 exists with 85 trips spanning Sept 24 - Oct 15, 2025
   **When** re-scraping validation runs
   **Then** all 85 trips are backed up before deletion

2. **Given** source data at sandiegofishreports.com boats.php pages for the 22 dates
   **When** parser extracts boat information
   **Then** boat names match actual boats ("New Seaforth", "San Diego", etc.) NOT landing names ("Seaforth Sportfishing")

3. **Given** re-scraped data is parsed and validated
   **When** trips are inserted into database
   **Then** each trip has correct boat ID, trip date, trip duration, anglers, and catches

4. **Given** re-scraping completes successfully
   **When** validation report is generated
   **Then** report shows 85+ trips inserted with correct boat names and confirms boat ID 329 has zero trips remaining

5. **Given** validation report confirms zero trips on boat ID 329
   **When** cleanup process runs
   **Then** boat ID 329 is deleted from database

### Edge Cases

- **What happens when** source website returns different number of trips than expected (not exactly 85)?
  → System logs discrepancy and generates detailed comparison report showing date-by-date differences

- **What happens when** network failures occur during re-scraping?
  → System logs failures and allows resuming from last successful date without re-processing already completed dates

- **What happens when** parsed boat name doesn't match expected format (e.g., contains landing name)?
  → System halts insertion for that trip, logs validation error, and requires manual review before proceeding

- **What happens when** duplicate trips are detected (trip already exists with same boat_id, date, duration)?
  → Database unique constraint prevents insertion, system logs as "already correct" and continues

- **What happens when** species names are inconsistent between old and new data?
  → System logs species comparison for manual review but does not block insertion (species names may legitimately vary in reporting)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Data Validation

- **FR-001**: System MUST backup all 85 existing trips from boat ID 329 before deletion
  - Backup includes: trip ID, boat ID, trip date, trip duration, anglers, catches (species + counts)
  - Backup format must allow restore if validation fails

- **FR-002**: System MUST validate boat names match expected format before database insertion
  - ✅ Valid: Proper noun format (e.g., "New Seaforth", "San Diego", "Pacific Voyager")
  - ❌ Invalid: Landing names (e.g., "Seaforth Sportfishing"), author names (e.g., "Seaforth Staff")
  - System must reject and log any boat names that don't match valid format

- **FR-003**: System MUST verify trip data completeness before insertion
  - Trip date: REQUIRED (YYYY-MM-DD format)
  - Boat ID: REQUIRED (valid foreign key to boats table)
  - Trip duration: REQUIRED (text format: "1/2 Day AM", "Full Day Offshore", etc.)
  - Anglers: OPTIONAL (NULL or positive integer)
  - Catches: REQUIRED (at least one species with count > 0)

- **FR-004**: System MUST prevent duplicate trip insertion
  - Check unique constraint: (boat_id, trip_date, trip_duration)
  - Log when duplicate is detected (indicates trip was already correctly attributed)
  - Continue processing without error when duplicate constraint prevents insertion

#### Data Processing

- **FR-005**: System MUST re-scrape exactly 22 dates: September 24, 2025 to October 15, 2025
  - Source: `https://www.sandiegofishreports.com/dock_totals/boats.php?date=YYYY-MM-DD`
  - Only process Seaforth Sportfishing landing section from each page
  - Use existing `boats_scraper.py` parser (validated correct implementation)

- **FR-006**: System MUST extract boat data using correct parsing structure
  - Structure: Landing header → Boat name → Landing name (skip) → Location (skip) → Anglers + Trip type → Catches
  - Boat name extraction: First line after "Seaforth Sportfishing Fish Counts" header
  - Trip data extraction: Subsequent lines containing angler count and trip duration

- **FR-007**: System MUST delete all trips from boat ID 329 after backup is confirmed
  - Cascade delete associated catches (foreign key cascade)
  - Verify zero trips remain on boat ID 329 before attempting boat deletion

- **FR-008**: System MUST delete boat ID 329 "Seaforth Sportfishing" after all trips are reassigned
  - Only delete if trip count = 0
  - Log if boat cannot be deleted (e.g., foreign key violations)

#### Validation and Reporting

- **FR-009**: System MUST generate pre-scraping validation report
  - Current state: boat ID 329 trip count, date range, boat names
  - Expected state: number of dates to process, expected trip count range
  - Validation checks: `boats_scraper.py` exists and has correct parser logic

- **FR-010**: System MUST generate post-scraping validation report
  - Trips inserted: count, boat names, date range
  - Trips skipped: count, reasons (duplicates, validation failures)
  - Boat ID 329 status: trip count (must be 0), deletion status
  - Species comparison: old vs new distributions for manual review
  - Validation summary: pass/fail status with detailed findings

- **FR-011**: System MUST log all data modifications with full audit trail
  - Backup timestamp and file location
  - Deletion timestamp: boat ID 329 trips and boat record
  - Insertion timestamp: each new trip with boat assignment
  - Validation results: pass/fail for each quality check

#### Rollback Capability

- **FR-012**: System MUST support rollback if validation fails
  - Restore procedure documented and tested
  - Backup data format allows full restoration
  - Rollback instructions included in validation report

- **FR-013**: System MUST test on single date before batch processing all 22 dates
  - Test date: 2025-10-15 (most recent)
  - Dry-run mode: parse and validate without database insertion
  - Manual approval required before proceeding to full batch

### Key Entities

- **Trip**: Represents a fishing trip by a specific boat on a specific date
  - Attributes: trip_id, boat_id (foreign key), trip_date, trip_duration, anglers
  - Relationships: belongs to one Boat, has many Catches
  - Critical constraint: unique (boat_id, trip_date, trip_duration)

- **Boat**: Represents an individual fishing boat operated by a landing
  - Attributes: boat_id, boat_name, landing_id (foreign key)
  - Relationships: belongs to one Landing, has many Trips
  - Validation: boat_name must be proper noun (actual boat), NOT landing name

- **Catch**: Represents fish caught during a trip
  - Attributes: catch_id, trip_id (foreign key), species, count
  - Relationships: belongs to one Trip
  - Validation: count must be positive integer

- **Landing**: Represents a fishing landing/dock where boats operate
  - Attributes: landing_id, landing_name
  - Example: "Seaforth Sportfishing" (ID 14)
  - Relationships: has many Boats

### Success Criteria

1. **Data Accuracy**: 85+ trips correctly attributed to actual boat names ("New Seaforth", "San Diego", "Pacific Voyager", etc.)

2. **Zero Misattributions**: Boat ID 329 "Seaforth Sportfishing" deleted, zero trips remain with landing name as boat name

3. **Complete Audit Trail**: Full backup of deleted data, detailed logs of all insertions and deletions

4. **Validation Passed**: Post-scraping report confirms:
   - All boat names match valid format
   - Species distributions consistent with source data
   - No foreign key violations or orphaned records
   - Dashboard displays correct boat names for date range

5. **Rollback Ready**: Documented and tested restore procedure in case validation fails

---

## Assumptions

1. The source website (sandiegofishreports.com) structure has not changed since original scraping
   - boats.php page format remains consistent
   - Seaforth Sportfishing section structure unchanged

2. The `boats_scraper.py` parser correctly extracts boat names
   - Code review confirmed line 252-253 uses proper boat name extraction
   - Test run on single date required to verify parsing accuracy

3. Database foreign key constraints are properly configured
   - Cascade delete on trips → catches
   - Landing ID 14 exists for "Seaforth Sportfishing"
   - Unique constraint on (boat_id, trip_date, trip_duration) prevents duplicates

4. Expected trip count is approximately 85, but may vary
   - Some dates may have more/fewer trips than originally scraped
   - Validation should compare total count but not require exact match

5. Network access to sandiegofishreports.com is available
   - 2-5 second delays between requests honored (ethical scraping)
   - Retry logic handles transient network failures

---

## Dependencies

1. **External Dependencies**:
   - sandiegofishreports.com website availability
   - Supabase database connection (PRODUCTION: `https://ulsbtwqhwnrpkourphiq.supabase.co`)

2. **Internal Dependencies**:
   - `boats_scraper.py` (validated correct parser)
   - Supabase schema: landings, boats, trips, catches tables
   - Python dependencies: BeautifulSoup4, requests, supabase-py, colorama

3. **Documentation Dependencies**:
   - SCRAPER_DOCS.md v3.0 (updated with scraper migration warning)
   - UPDATE_2025_10_16.md (summary document)
   - Constitution v1.0.0 (quality control principles)

---

## Scope Boundaries

### In Scope
- Re-scraping 22 dates (Sept 24 - Oct 15, 2025) for Seaforth Sportfishing only
- Validating boat name format and trip data completeness
- Generating validation reports with before/after comparison
- Deleting boat ID 329 and reassigning trips to correct boats
- Full audit trail with rollback capability

### Out of Scope
- Re-scraping other landings (H&M, Fisherman's Landing, etc.)
- Fixing historical data before Sept 24, 2025
- Modifying `boats_scraper.py` parser logic (already correct)
- Re-scraping dates after Oct 15, 2025 (will be handled by regular scraping process)
- Species name standardization (separate data quality effort)

---

## Review & Acceptance Checklist
*Quality validation for this specification*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs) - only references existing validated tools
- [x] Focused on data quality and business needs
- [x] Written for non-technical stakeholders (data quality managers)
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable (85+ trips, zero misattributions, validation report)
- [x] Scope is clearly bounded (22 dates, Seaforth only, specific date range)
- [x] Dependencies and assumptions identified (website structure, parser accuracy, database schema)
- [x] Data fidelity, performance, and audit expectations captured

---

## Execution Status
*Updated during spec creation*

- [x] User description parsed
- [x] Key concepts extracted (boat misattribution, re-scraping, validation)
- [x] Ambiguities marked (none - all based on concrete existing work)
- [x] User scenarios defined (data quality manager correcting misattributions)
- [x] Requirements generated (13 functional requirements with validation criteria)
- [x] Entities identified (Trip, Boat, Catch, Landing)
- [x] Review checklist passed

**Status**: ✅ READY FOR PLANNING (`/speckit.plan`)
