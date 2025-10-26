# Feature Specification: Frontend Modernization & Deployment Hardening

**Feature Branch**: `[012-frontend-modernization]`  
**Created**: 2025-10-22  
**Status**: Draft  
**Input**: User description: "Deeply analyze the structure of the web app and produce a spec-kit development plan to remove bloat, orphaned code, and oversized modules while preserving quality gates."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Data Fetching (Priority: P1)

Dashboard operators expect that adjusting filters (dates, boats, species, landings) uses a single, resilient Supabase query so the UI responds quickly without hammering the database.

**Why this priority**: Supabase API credits and dashboard latency are the most visible pain points today; hitting the database twice per filter change is unsustainable.

**Independent Test**: Mock Supabase client, trigger filter changes, and assert only one catch-record query fires per refresh while UI renders state transitions correctly.

**Acceptance Scenarios**:

1. **Given** the user loads the dashboard with valid Supabase credentials, **When** they change the date preset, **Then** catch data and summary metrics resolve using shared results from a single Supabase fetch.
2. **Given** Supabase returns an error once, **When** the user retries the same filter combination, **Then** the retry succeeds without residual caches interfering.

---

### User Story 2 - Unified Filter Experience (Priority: P1)

Analysts expect landing, boat, species, and duration options to stay in sync across Header Filters and Sidebar without redundant API traffic.

**Why this priority**: Current duplication causes inconsistent lists and fragmented UX when option data changes.

**Independent Test**: Mount the filter provider, render both components, simulate updates to landing selection, and verify both update instantly without additional network traffic.

**Acceptance Scenarios**:

1. **Given** the user pins a landing in the sidebar, **When** they open the Header Filters, **Then** the available boat list reflects that landing without extra Supabase calls.
2. **Given** filter options were loaded earlier in the session, **When** the sidebar remounts (mobile sheet open/close), **Then** cached options render immediately while a background refresh optionally revalidates.

---

### User Story 3 - Lean Production Deployments (Priority: P2)

DevOps wants every deployment to publish only the compiled dashboard assets in a `dist/` directory with secrets injected via environment variables, ensuring sensitive keys and historical logs never reach production.

**Why this priority**: Current deployments include hundreds of MB of logs/QC archives and a hard-coded Supabase anon key that breaches security policy.

**Independent Test**: Run the production build task, inspect the `dist/` output (size, file list), and confirm CI publishes only that directory with environment-provided config.

**Acceptance Scenarios**:

1. **Given** a clean working tree, **When** `npm run build:prod` executes, **Then** only compiled assets, `index.html`, and minimal config land in `dist/` under 10 MB.
2. **Given** environment variables `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set, **When** the built app loads, **Then** network calls authenticate using those values and no hard-coded keys appear in the bundle.

---

### Edge Cases

- What happens when Supabase throttles requests mid-refresh and cached data becomes stale?
- How does the system handle missing or malformed environment variables during build or runtime?
- What occurs when filter provider cache grows stale across sessions (e.g., landings added while user idle)?
- How do we surface errors if `dist/` is missing required files (e.g., bundle unexpectedly empty)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST consolidate catch-data and summary metric retrieval into a shared fetch pipeline that deduplicates Supabase requests per filter change.
- **FR-002**: System MUST expose a caching filter options provider that both Header Filters and Sidebar consume, guaranteeing consistency without duplicate queries.
- **FR-003**: System MUST decompose `App`, `HeaderFilters`, and `Sidebar` into composable units (hooks, providers, presentational components) so no single file exceeds 200 LOC.
- **FR-004**: System MUST emit production builds into an isolated `dist/` directory containing only necessary runtime assets (HTML, JS, CSS, static media).
- **FR-005**: System MUST load Supabase credentials and feature flags from environment variables, failing fast with actionable errors if missing.
- **FR-006**: System MUST remove or quarantine the legacy DOM client (`scripts/main.ts` and friends) from production dependencies while keeping historical references archived.
- **FR-007**: System MUST update CI to run linting, type-checking, unit tests, E2E tests, and bundle-size verification on every PR touching the dashboard.
- **FR-008**: System MUST document manual QA sweeps (accessibility, responsive checks) and tie them to release gating tasks.

### Key Entities

- **Catch Data Service**: Abstraction returning `{records, metrics, options}` and managing fetch dedupe, error states, and caching.
- **Filter Options Context**: React context providing normalized landings, boats, species, durations plus mutation utilities.
- **Build Artifact**: `dist/` output with checksum metadata for QA verification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reduce Supabase requests per filter change from 2→1 (50% drop), verified in staging telemetry logs.
- **SC-002**: Cut Tailwind CSS bundle size by ≥30% compared to baseline (`wc -c` of old vs new stylesheets).
- **SC-003**: Ensure production bundle (JS + CSS + HTML) remains <4 MB and the `dist/` directory stays <10 MB.
- **SC-004**: Achieve 100% automated test pass rate (unit, lint, typecheck, Playwright) in CI for every PR tied to this spec.
- **SC-005**: Remove all hard-coded Supabase credentials from the repository; static code analysis finds zero secrets post-migration.
- **SC-006**: Complete manual QA checklist (responsive layout, keyboard navigation, error fallbacks) with documented evidence before launch.
