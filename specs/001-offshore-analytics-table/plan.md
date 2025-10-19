# Implementation Plan: Southern California Offshore Analytics Table

**Branch**: `[001-offshore-analytics-table]` | **Date**: 2025-09-27 | **Spec**: specs/001-offshore-analytics-table/spec.md
**Input**: Feature specification from `/specs/001-offshore-analytics-table/spec.md`

## Summary
Deliver a best-in-class, filterable offshore catch table that renders the most recent 36 months of Supabase data with responsive UX, rich summary metrics, and observable error handling. The feature hinges on Spec Kit–generated contracts, a type-safe data adapter layer, and a virtualized table UI that meets the ≤2s refresh budget on desktop and mobile (
@web Pixel 10 + iPhone 17).

## Technical Context
**Language/Version**: TypeScript 5.x targeting ES2022 (compiled to browser-safe JS)
**Primary Dependencies**: Spec Kit generated types & mocks; Supabase REST/edge endpoint (fetch-based); virtualization helper (evaluate `@tanstack/virtual-core` vs lightweight custom)
**Storage**: Supabase (PostgreSQL) via existing database + potential edge functions
**Testing**: Vitest for contract/unit tests; Playwright for desktop/mobile flows; custom perf harness (likely Node + Happy DOM or Playwright timing)
**Target Platform**: Desktop web, @web Google Pixel 10, @web iPhone 17 (Vercel preview)
**Project Type**: Static frontend with generated contracts and Supabase integration
**Performance Goals**: ≤2s filter response ≤5k rows; smooth virtual scroll at ≥60fps; summary metrics update within same frame as table change
**Constraints**: Preserve raw Supabase values; blank cells logged; responsive + accessible interactions; telemetry for loading/error states
**Scale/Scope**: 36 months history (~10–12k rows peak), fleet + per-boat metrics, progressive loading/pagination guardrails

## Constitution Check
- **Data Fidelity First**: Plan will mirror Supabase payloads through generated types, propagate blanks to UI, and emit data-quality logs (research to confirm logging transport).
- **Spec-Led Delivery**: Contracts, types, and mocks are generated from Spec Kit before any adapter/UI code; implementation tasks depend on those artifacts.
- **Observable Resilience**: Loading/error/empty flows plus telemetry (structured console logs + optional analytics hook) documented below; retries evaluated during research.
- **Responsive Clarity**: Layout targets desktop + @web Pixel 10/iPhone 17; accessibility checks (keyboard nav, ARIA) included in plan tasks.
- **Fast Progressive UX**: Virtualization/pagination thresholds defined during research; perf harness ensures ≤2s median refresh and flags degradations.

**Constitution Gate Status**: PASS (no violations identified; research tasks capture open decisions)

## Project Structure

### Documentation (this feature)
```
specs/001-offshore-analytics-table/
├── spec.md              # Stakeholder specification
├── plan.md              # This file
├── research.md          # Phase 0 findings (to be created)
├── data-model.md        # Contracts + type derivations (Phase 1)
├── quickstart.md        # Mock + verification instructions (Phase 1)
├── contracts/           # Generated schemas + mock payloads (Phase 1)
└── tasks.md             # /tasks output (Phase 2)
```

### Source, Assets, and Tests (repository root)
```
index.html               # Landing shell
scripts/
├── main.ts              # Entry module initializes filters + table
├── api/
│   ├── client.ts        # Supabase fetch + adapters
│   ├── types.ts         # Generated Spec Kit types (read-only)
│   ├── mocks.ts         # Generated mock data fixtures
│   └── instrumentation.ts # Data-quality logging + telemetry hooks
└── ui/
    ├── table.ts         # Rendering + virtualization helpers
    ├── progressive.ts   # Progressive loading + pagination guards
    ├── metrics.ts       # Summary metric tiles
    └── states.ts        # Loading/error/empty-state rendering
styles/
├── realdata.css         # Reference styles (read-only)
└── table.css            # New scoped styles
specs/                   # Feature specifications + plans
.tests/
├── contracts/           # Schema + mapping tests (Vitest)
├── ui/                  # Playwright scenarios (desktop + mobile)
└── performance/         # Filter-response timing harness
```

**Structure Decision**: Adopt the structure above; any runtime build artifacts (e.g., transpiled JS) will output to `public/` or `dist/` folders ignored from source control. Confirm final build pipeline (tsc vs esbuild) during research.

## Phase 0: Outline & Research
1. **Supabase Contract Validation**: Document existing tables/columns, confirm 36-month retention, and design REST/edge endpoint contract (auth, pagination, filtering semantics).
2. **Virtualization Strategy**: Compare lightweight custom virtualization vs `@tanstack/virtual-core` for our dataset size; decide on scroll container + sticky header approach.
3. **Telemetry & Logging**: Choose logging transport (console vs external), define data-quality logging schema, and determine how to surface incident notes in quickstart/landing docs.
4. **Responsive Testing Tooling**: Confirm Playwright device configs for @web Pixel 10/iPhone 17 and any headless constraints when running locally.
5. **Performance Harness Design**: Determine measurement approach (Playwright trace vs custom Node runner) to validate ≤2s filter response and virtualization thresholds.
6. **Build Pipeline**: Decide between vanilla `tsc`, `tsup`, or `esbuild` for bundling/compiling TypeScript into browser-ready JS without introducing heavy deps.

**Output**: `research.md` capturing decisions (Decision, Rationale, Alternatives) with all unknowns resolved before Phase 1.

## Phase 1: Design & Contracts
*Prerequisite: research.md complete*

1. **Data Model Extraction**: Populate `data-model.md` with catch record schema, summary metric models, filter criteria, telemetry events, and logging payloads.
2. **Contract Generation**: Use Spec Kit to author JSON schema/OpenAPI documents and example payloads in `specs/001-offshore-analytics-table/contracts/` (table data, summary metrics, status endpoint).
3. **Generated Artifacts**: Produce TypeScript types (`scripts/api/types.ts`) and mock data (`scripts/api/mocks.ts`) from contracts; ensure they remain read-only.
4. **Contract Tests**: Write failing Vitest suites (`tests/contracts/*.spec.ts`) verifying that mock payloads conform to schemas and adapters transform data correctly (including blank-field logging).
5. **UI Scenario Mapping**: Draft Playwright specs (desktop + Pixel 10 + iPhone 17) in `tests/ui/` that assert acceptance scenarios using mocks.
6. **Perf Harness Outline**: Scaffold timing harness (`tests/performance/filter.bench.ts`) referencing virtualization thresholds and expected budgets.
7. **Agent Context Refresh**: Run `.specify/scripts/bash/update-agent-context.sh codex` to capture new tech choices and latest milestones.

**Output**: `data-model.md`, `contracts/` artifacts, generated types/mocks, red tests in `tests/`, `quickstart.md` with mock usage instructions, updated agent context.

## Phase 2: Task Planning Approach
*Sets up inputs for `/tasks`; no task list is generated here.*

**Task Generation Strategy**:
- Leverage `.specify/templates/tasks-template.md` to translate contracts/designs into executable tasks grouped by constitutional principles.
- Ensure tasks cover spec sync, contract tests, adapters, UI rendering, telemetry, accessibility, performance verification, and documentation updates.
- Mark tasks touching independent files as `[P]` for parallel execution.

**Ordering Strategy**:
1. Environment + spec artifact sync
2. Contract and UI tests (fail-first)
3. Data adapter + instrumentation implementation
4. Table rendering + progressive loading
5. Summary metrics + telemetry wiring
6. Responsive styling and accessibility polish
7. Performance validation + documentation updates

### Supabase Integration Assumptions (Phase 2 Kickoff)
- Base project URL arrives via `SUPABASE_URL` (e.g., `https://<project>.supabase.co`); `scripts/api/client.ts` composes fetch targets from this value rather than hard-coded relatives.
- Catch rows, summary metrics, and status metadata ship through edge functions `offshore-catch`, `offshore-metrics`, and `offshore-status` under `${SUPABASE_URL}/functions/v1/*`, each accepting the filters defined in `data-model.md` and returning `filters_applied` metadata.
- We will not rely on the REST view directly in production; any Supabase PostgREST views (e.g., `offshore_status_view`) exist only to back the edge functions.
- All outbound calls include the public anon key via `SUPABASE_ANON_KEY` (`apikey` + `Authorization: Bearer` headers) and honor `USE_MOCKS` to short-circuit to Spec Kit fixtures during local testing.
- No proxy layer is expected in production; local development may optionally mount `/api/*` rewrites, but the default path uses direct Supabase URLs once credentials are present.

**Estimated Output**: 20–30 tasks enumerated in `/specs/001-offshore-analytics-table/tasks.md`.

### ⚠️ Phase 2b: Course Correction (Added 2025-10-01)
Tasks T014-T020 were completed using vanilla TypeScript with DOM manipulation instead of React + shadcn/ui components, violating the CLAUDE.md mandate: *"ALL user interface components MUST use the shadcn/ui design system exclusively."*

**Discovery Method**: Playwright visual inspection revealed gray native date inputs, scrollable native selects, custom CSS styling, and missing shadcn component usage. Screenshot analysis confirmed:
- Native HTML5 `<input type="date">` calendars (gray appearance)
- Native `<select>` dropdowns with scrollable lists
- 430 lines of custom CSS with manual rgba() colors
- Vanilla TypeScript .ts files using document.createElement()
- Empty table body (virtualization rendering issue)

**Resolution**: Added migration tasks T021-T028 to rebuild with proper React + shadcn/ui architecture while preserving:
- Left sidebar navigation (unchanged per user directive)
- Filter panel layout (converted to shadcn Calendar, Select components)
- Summary metrics functionality (converted to shadcn Cards)
- Table virtualization (converted to @tanstack/react-table with shadcn Table)
- Progressive loading (converted to shadcn Button)
- Collapsible breakdowns (converted to shadcn Collapsible)

**Technical Debt**: All UI code from T014-T020 will be replaced; API client (T010), instrumentation (T011), and contract tests (T003-T005) remain valid as they don't touch UI layer.

## Phase 3+: Future Implementation
- **Phase 3**: Execute `/tasks` to emit tasks.md from the updated template.
- **Phase 4**: Implement tasks respecting the constitution (tests first, telemetry, responsive checks).
- **Phase 5**: Validate end-to-end (contract tests, Playwright, performance harness) and log outcomes in `quickstart.md` + `landing.md`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Vanilla TypeScript + DOM manipulation used instead of React + shadcn/ui (T014-T020) | Tasks executed before CLAUDE.md design system mandate was checked; initial implementation prioritized speed over design system compliance | Discovered via Playwright visual inspection that components don't match shadcn standards (gray calendars, scrollable selects, custom CSS). Rebuild required with T021-T028 migration tasks to achieve production-quality UI matching CLAUDE.md requirements. |

## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [!] Phase 2: Task planning - COURSE CORRECTION REQUIRED
  - T014-T020 completed (2025-10-01) with vanilla TypeScript
  - CLAUDE.md violation discovered via Playwright inspection
  - T021-T028 migration tasks added for shadcn/ui rebuild
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v1.0.0 – See `/memory/constitution.md`*
