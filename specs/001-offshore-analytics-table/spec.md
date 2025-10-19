# Feature Specification: Southern California Offshore Analytics Table

**Feature Branch**: `[001-offshore-analytics-table]`  
**Created**: 2025-09-27  
**Status**: Draft  
**Input**: Stakeholder brief: "Fishing analytics site must show Southern California offshore catch data from Supabase in a best-in-class filterable table so anglers can plan trips."

## User Scenarios & Testing

### Primary User Story
A Southern California angler planning an offshore trip visits the dashboard to review recent catch activity, applies filters for species and date range, and sees an updated table that reflects the latest offshore bite intel for those criteria.

### Acceptance Scenarios
1. **Given** the user loads the dashboard, **When** no filters are applied, **Then** the table shows all available records for the most recent 36 months in chronological order with the latest day visible first.
2. **Given** the user selects a custom date range (defaulting to the last 30 days) and one or more target species, **When** the filters are applied, **Then** the table refreshes within two seconds and displays only rows that match all selected criteria.
3. **Given** the user applies filters that produce no matching rows, **When** the dataset is empty, **Then** the UI communicates that no results are available and suggests clearing or adjusting filters.
4. **Given** the Supabase service is unreachable or returns an error, **When** the user attempts to load data, **Then** the UI displays an actionable error message and does not show stale or partial results.

### Edge Cases
- Records with missing or inconsistent location/species/boat data MUST still appear in the table with a blank cell and an internal data-quality flag so the issue can be tracked for cleanup.
- When a query would return more than 10k rows, the UI SHOULD fall back to progressive loading (virtualized scrolling plus optional pagination) to protect performance and messaging should coach the user toward tighter filters.
- Historical data older than 36 months SHOULD remain accessible via archived views or exports but is out of scope for the primary table.

## Requirements

- **FR-001**: The system MUST display the Southern California offshore catch dataset spanning the latest 36 months in a table with the required fields: trip date, boat, landing, trip duration, number of anglers, total fish caught, and top species caught. Rows with missing required fields MUST render blank placeholders and be logged for data-quality review.
- **FR-002**: The system MUST provide filter controls for date range (default last 30 days), landing zone, boat, and target species, with multi-select support where applicable.
- **FR-003**: The system MUST apply filters without requiring a full page reload, visually reflect the active filter state, and maintain scroll position.
- **FR-004**: The system MUST show a clearly worded empty-state when no rows match the selected filters and provide a one-click option to reset filters.
- **FR-005**: The system MUST surface error messaging when data retrieval fails and avoid displaying outdated or partial information.
- **FR-006**: The system MUST provide summary metrics aligned with the current filter context, including total fish caught (fleet-wide and per boat), catch totals by species (fleet-wide and per boat), number of trips overall, and number of trips per boat.
- **FR-007**: The system MUST incorporate best-in-class data table affordances: sticky header, sortable columns, resizable columns, responsive layout, and virtualized row rendering beyond the initial viewport.

### Non-Functional Requirements
- **NFR-001**: Table refresh after filter changes MUST complete within two seconds under normal load (dataset ≤5k rows) and degrade gracefully when progressive loading activates.
- **NFR-002**: The experience MUST be responsive across desktop (≥1280px width) and modern mobile breakpoints, specifically Google Pixel 10 and iPhone 17 viewports when accessed via @web preview tooling.
- **NFR-003**: Data presented MUST reflect the latest successful sync with Supabase and indicate the last updated timestamp.

### Key Entities
- **Catch Record**: Represents a single offshore trip observation with attributes: trip date (ISO date), boat name, landing/port, trip duration (hours), number of anglers, total fish caught, top species caught (species name plus count), optional notes for additional species or conditions.
- **Filter Criteria**: User-selected parameters (date range defaulting to last 30 days, landing zone list, boat list, species multi-select) that determine which records appear in the table.
- **Summary Metrics**: Aggregated values scoped to the current filter (total fish across all boats, fish by boat, fish by species, trips overall, trips per boat) surfaced above or alongside the table.
- **Data Refresh Status**: Metadata describing when the dataset was last synced from Supabase, including success/failure state and timestamp, so the UI can communicate data freshness.

## Review & Acceptance Checklist

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Assumptions & Dependencies
- Offshore catch data is sourced from the existing Supabase project and may expand to cover at least 36 months of history.
- Data-quality logging for blank/mismatched fields will feed a cleanup backlog managed outside the UI.
- Supabase access keys and Vercel environment variables will be configured ahead of frontend integration work.
- Reference-only assets `[backup] index-realdata.html` and `@index` remain local and excluded from GitHub; they inform styling and legacy data hooks but are not deployed.
