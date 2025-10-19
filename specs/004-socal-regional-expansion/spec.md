# Feature Specification: Southern California Regional Expansion

**Feature Branch**: `004-socal-regional-expansion`
**Created**: 2025-10-16
**Status**: Draft
**Input**: User requirement: "Add Orange County, Los Angeles, and Channel Islands fishing data to the database"

## Problem Statement

The current fishing intelligence platform only collects data from **San Diego landings** (Seaforth Sportfishing, H&M Landing, Fisherman's Landing, Point Loma Sportfishing). This excludes **5 major fishing regions** along the Southern California coast that provide valuable fishing data:

1. **Avila Beach** (Patriot Sportfishing)
2. **Santa Barbara** (Santa Barbara Landing)
3. **Oxnard/Channel Islands** (Channel Islands Sportfishing)
4. **Marina Del Rey** (Marina Del Rey Sportfishing)
5. **Newport Beach** (Newport Landing)

**Impact**:
- Dashboard shows incomplete picture of Southern California fishing activity
- Users cannot compare conditions across different regions
- Missing data from 5+ major sportfishing operations
- No multi-day offshore trip data from Channel Islands boats

**Opportunity**: Data source (socalfishreports.com) has identical structure to current sandiegofishreports.com, allowing expansion with minimal code changes.

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT needs to be validated and WHY
- ❌ Avoid HOW to implement scraping logic (already validated in boats_scraper.py)
- 👥 Written for data stakeholders and platform users
- 🐟 Honor data fidelity: all scraped data must match source exactly
- ⚡ Capture validation expectations (new landing formats, boat naming consistency)
- 📋 Specify quality checks and rollback requirements

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As an **angler planning a Southern California fishing trip**, I need to **view catch reports from all major landings along the coast** so that **I can choose the best location and boat for current conditions**.

**Success Outcome**: When users open the dashboard, they see trips from Avila Beach to Newport Beach (200+ mile coastline), with clear regional filtering and boat comparisons across all 5 new regions.

### Acceptance Scenarios

1. **Given** the scraper processes socalfishreports.com for October 13, 2025
   **When** parsing completes successfully
   **Then** database contains trips from all 5 new regions with correct landing associations

2. **Given** user filters dashboard by "Channel Islands Sportfishing" landing
   **When** viewing trip results
   **Then** trips show boats like "Aloha Spirit", "Island Fox", "Speed Twin" with offshore catches (not San Diego boats)

3. **Given** new landing "Santa Barbara Landing" has trips on October 13, 2025
   **When** scraper runs with socalfishreports.com source
   **Then** landing is created with ID, name is "Santa Barbara Landing" (not abbreviated or modified)

4. **Given** boat "Betty-O" operates from "Marina Del Rey Sportfishing"
   **When** boat record is created
   **Then** boat.landing_id correctly references Marina Del Rey Sportfishing landing

5. **Given** database already has 8,000 trips from San Diego landings
   **When** new regional data is added
   **Then** existing San Diego data remains unchanged (no duplicates, no modifications)

6. **Given** user views dashboard filtered to "Newport Beach" region
   **When** comparing catch data
   **Then** species distributions reflect Newport Beach fishing patterns (different from San Diego)

### Edge Cases

- **What happens when** landing name has slight variations ("Channel Islands Sportfishing" vs "CI Sportfishing")?
  → System uses exact name from source, creates new landing if variation detected, logs for manual review

- **What happens when** same boat name appears at multiple landings (e.g., "Liberty" in San Diego AND Newport)?
  → Each boat is unique per landing (boat_id tied to landing_id), no conflicts occur

- **What happens when** source website has downtime or structure changes?
  → Scraper logs error, continues with remaining dates, generates report of failed dates for retry

- **What happens when** new trip types appear (e.g., "Whale Watching", "Overnight Kelp Fishing")?
  → System accepts any trip type text, stores as-is, logs new variations for review

- **What happens when** species names differ by region (e.g., "Rockfish" vs "Pacific Rockfish")?
  → System stores species names exactly as written in source (no automatic standardization), logs for data quality review

---

## Requirements *(mandatory)*

### Functional Requirements

#### Data Source Migration

- **FR-001**: System MUST switch data source from sandiegofishreports.com to socalfishreports.com
  - URL pattern: `https://www.socalfishreports.com/dock_totals/boats.php?date=YYYY-MM-DD`
  - Validate identical HTML structure before production run
  - Document any structural differences from San Diego source

- **FR-002**: System MUST preserve all existing San Diego landing data
  - No modifications to existing 8,000+ trips
  - No duplicate detection across different sources (San Diego vs SoCal treated as separate datasets initially)
  - Existing boat/landing associations remain intact

#### Landing Detection and Creation

- **FR-003**: System MUST automatically detect new landing names from source
  - Extract landing name from "XXX Fish Counts" header pattern
  - Create new landing record if name not in database
  - Store exact name without abbreviation or modification

- **FR-004**: System MUST validate landing names match expected regions
  - Expected landings (validate presence in source):
    - Patriot Sportfishing (Avila Beach)
    - Santa Barbara Landing (Santa Barbara)
    - Channel Islands Sportfishing (Oxnard)
    - Marina Del Rey Sportfishing (Marina Del Rey)
    - Newport Landing (Newport Beach)
  - Log if expected landing is missing from source data
  - Flag if unexpected landing name appears

#### Boat Association

- **FR-005**: System MUST associate boats with correct landing
  - Each boat linked to single landing via landing_id foreign key
  - Boat names unique per landing (same name at different landings = different boats)
  - Preserve boat-landing associations across scraping runs

- **FR-006**: System MUST detect new boats automatically
  - Create boat record with correct landing_id
  - Store exact boat name from source (no normalization)
  - Log new boat creations for verification

#### Trip Data Integrity

- **FR-007**: System MUST validate trip data completeness before insertion
  - Required fields: boat_id, trip_date, trip_duration, catches (at least 1)
  - Optional fields: anglers (can be NULL)
  - Reject trips missing required data, log rejection reason

- **FR-008**: System MUST prevent duplicate trips within new dataset
  - Check unique constraint: (boat_id, trip_date, trip_duration)
  - Skip duplicates with log message (not error)
  - Count skipped duplicates for validation report

#### Species and Catch Data

- **FR-009**: System MUST preserve regional species naming variations
  - Store species names exactly as written in source
  - No automatic standardization or normalization
  - Generate species variation report for manual review

- **FR-010**: System MUST validate catch counts are positive integers
  - Reject catches with count <= 0
  - Reject catches with non-numeric counts
  - Log validation failures for data quality review

### Data Quality Requirements

- **FR-011**: System MUST generate pre-scraping validation report
  - Current database state: landing count, boat count, trip count, latest trip date
  - Expected new landings (5) and estimated new boats (10-15)
  - Date range to be scraped
  - Source URL validation

- **FR-012**: System MUST generate post-scraping validation report
  - New landings created (names, IDs)
  - New boats created (names, landing associations, counts)
  - Trips inserted by landing (breakdown)
  - Trips skipped (duplicates, validation failures)
  - Species variations detected (list unique species names)
  - Date coverage gaps (if any dates failed)

- **FR-013**: System MUST provide rollback capability
  - Backup script to export new trips before deletion
  - Deletion script to remove all trips from new landings
  - Deletion script to remove new boat records
  - Deletion script to remove new landing records
  - Validation that rollback restored database to pre-expansion state

### Performance Requirements

- **NFR-001**: Scraper MUST maintain ethical delay standards
  - 2-5 second delays between requests (existing configuration)
  - No more than 1 request per second average
  - Respect source website's servers (no aggressive scraping)

- **NFR-002**: Initial regional expansion MUST complete within reasonable timeframe
  - Target: Process 30 days of data in < 3 hours
  - Allow for network failures and retries
  - Progress logging every 5 dates processed

### Key Entities

- **Landing**: Represents a fishing landing/dock operation
  - Attributes: landing_id (PK), name (unique)
  - New entities: 5 landings (Avila Beach, Santa Barbara, Oxnard, Marina Del Rey, Newport Beach)
  - Relationships: has many Boats

- **Boat**: Represents individual fishing vessel
  - Attributes: boat_id (PK), name, landing_id (FK)
  - New entities: 10-15 boats across 5 new landings
  - Relationships: belongs to one Landing, has many Trips

- **Trip**: Represents single fishing trip
  - Attributes: trip_id (PK), boat_id (FK), trip_date, trip_duration, anglers
  - New entities: 150-300 trips (30 days × 5-10 trips/day estimated)
  - Relationships: belongs to one Boat, has many Catches

- **Catch**: Represents fish caught during trip
  - Attributes: catch_id (PK), trip_id (FK), species, count
  - New entities: 500-1500 catches (estimate 3-5 species per trip)
  - Relationships: belongs to one Trip

### Success Criteria

1. **Data Completeness**: All 5 new landing regions represented in database
   - Patriot Sportfishing: ✅ trips present
   - Santa Barbara Landing: ✅ trips present
   - Channel Islands Sportfishing: ✅ trips present
   - Marina Del Rey Sportfishing: ✅ trips present
   - Newport Landing: ✅ trips present

2. **Data Accuracy**: Boat-landing associations correct
   - All Channel Islands boats → Channel Islands Sportfishing landing
   - All Marina Del Rey boats → Marina Del Rey Sportfishing landing
   - No San Diego boats mixed with new regions

3. **Data Integrity**: No corruption of existing data
   - Original 8,000 San Diego trips unchanged
   - Original boat/landing associations preserved
   - No duplicate trips within dataset

4. **Dashboard Functionality**: Users can filter by new regions
   - Landing filter dropdown shows all 5+ new landings
   - Boat filter shows boats from new regions
   - Trip data displays correctly for new regions
   - Metrics aggregate correctly across all regions

5. **Validation Reports**: Complete audit trail
   - Pre-scraping report shows baseline state
   - Post-scraping report shows all insertions
   - Species variation report highlights regional differences
   - Rollback documentation ready if needed

---

## Assumptions

1. **Source Structure Consistency**
   - socalfishreports.com uses identical HTML structure to sandiegofishreports.com
   - "XXX Fish Counts" header pattern consistent across regions
   - Boat/trip/catch data format matches existing parser expectations

2. **Data Availability**
   - All 5 expected landings actively reporting on socalfishreports.com
   - Historical data available for at least last 30 days
   - Data quality similar to San Diego source (complete species/count info)

3. **Database Capacity**
   - Supabase can handle 150-300 additional trips + catches without performance impact
   - Foreign key relationships scale appropriately
   - No table size limits reached

4. **No Manual Data Entry Required**
   - All data extractable via existing parsing logic
   - No special handling needed for any landing
   - Trip type variations handled by existing normalization

5. **Existing Scraper Compatibility**
   - boats_scraper.py parse_boats_page() function works with new source
   - get_or_create_landing() handles new landing names correctly
   - No code changes needed beyond URL configuration

---

## Dependencies

### External Dependencies
- **socalfishreports.com availability**: Website must be accessible
- **HTML structure stability**: Structure must match sandiegofishreports.com pattern
- **Supabase connectivity**: Production database must be online

### Internal Dependencies
- **boats_scraper.py**: Validated scraper (v3.0) with correct parsing logic
- **Database schema**: Existing landings/boats/trips/catches tables with proper constraints
- **Validation scripts**: check_scraper_status.py, validate_data.py

### Documentation Dependencies
- **SCRAPER_DOCS.md**: Will need update to reflect SoCal source
- **README.md**: Will need update with new regional coverage
- **Dashboard documentation**: Update to mention expanded regional coverage

---

## Scope Boundaries

### In Scope
- Switching scraper to socalfishreports.com source
- Scraping 5 new landing regions (Avila Beach through Newport Beach)
- Creating new landing/boat/trip/catch records
- Validating data quality and generating reports
- Updating dashboard filters to show new regions
- Providing rollback capability

### Out of Scope
- Re-scraping San Diego data from new source (keep existing sandiegofishreports.com data)
- Species name standardization across regions (future enhancement)
- Historical data beyond last 30 days (initial expansion only)
- Landing regions outside Southern California (no Northern California, Mexico, etc.)
- Boat scheduling or availability data (only catch reports)
- Weather data integration (separate feature)

---

## Review & Acceptance Checklist
*Quality validation for this specification*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs) - only references existing validated tools
- [x] Focused on data expansion and business value
- [x] Written for non-technical stakeholders (anglers, data managers)
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable (5 landings, boat counts, data integrity checks)
- [x] Scope is clearly bounded (5 specific regions, 30 days initial, no species standardization)
- [x] Dependencies and assumptions identified (source structure, database capacity, scraper compatibility)
- [x] Data fidelity, performance, and rollback expectations captured

---

## Execution Status
*Updated during spec creation*

- [x] User description parsed
- [x] Key concepts extracted (regional expansion, 5 new landings, source migration)
- [x] Ambiguities identified and resolved (same boat names at different landings = different boats)
- [x] User scenarios defined (angler choosing best location, regional filtering)
- [x] Requirements generated (13 functional, 2 non-functional with validation criteria)
- [x] Entities identified (Landing, Boat, Trip, Catch with new counts)
- [x] Review checklist passed

**Status**: ✅ READY FOR PLANNING (`/plan` workflow)
