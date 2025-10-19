# Tasks: Southern California Offshore Analytics Table

**Input**: specs/001-offshore-analytics-table/spec.md + plan.md + research.md + data-model.md + contracts/ + quickstart.md
**Prerequisites**: Node 18+, npm toolchain, Playwright browsers (see quickstart)

## Execution Flow (main)
1. Sync Spec Kit artifacts so generated types/mocks/validators reflect latest contracts.
2. Lock testing targets (Vitest, Playwright, perf harness) against current mocks and desired Supabase behaviour.
3. Implement adapters, UI state, and virtualization using Spec Kit guidance.
4. Wire telemetry, progressive loading, and responsive layout.
5. Re-run validation suites and document outcomes in quickstart + landing logs.

## Task List
- [x] T001 Sync Spec Kit artifacts via `npm run generate:types`, then verify `scripts/api/types.ts`, `scripts/api/mocks.ts`, and `scripts/api/validators.ts` match contracts; record RESET note in `landing.md`.
- [x] T002 [P] Update `specs/001-offshore-analytics-table/plan.md` Phase tracker (Phase 2 → in_progress) and capture Supabase endpoint/base URL assumptions before implementation begins.
- [x] T003 Expand `tests/contracts/catch-records.spec.ts` to assert pagination limits, cursor presence, and blank-field telemetry expectations using mock mutations.
- [x] T004 [P] Extend `tests/contracts/summary-metrics.spec.ts` to validate per-species + per-boat totals, unique counts, and filters_applied echo from mocks.
- [x] T005 [P] Harden `tests/contracts/status.spec.ts` with cases for null vs string `message`/`incident_id` and degraded/error status scenarios.
- [x] T006 Convert `tests/ui/table.desktop.spec.ts` from skipped to active: cover initial render, filter application, empty-state messaging, and progressive load trigger under mocks.
- [x] T007 [P] Mirror the desktop flow in `tests/ui/table.pixel10.spec.ts`, validating responsive breakpoints and touch interaction affordances.
- [x] T008 [P] Mirror acceptance scenarios in `tests/ui/table.iphone17.spec.ts`, ensuring accessible announcements for loading/error states on mobile.
- [x] T009 Replace placeholder waits in `tests/performance/filter.bench.ts` with Playwright trace-based timing (wait for network idle + table hydration) and assert ≤2s median/≤2.5s P95 budgets.
- [x] T010 Implement Supabase-backed fetching in `scripts/api/client.ts`: build query params, honor `USE_MOCKS`, stream paginated batches, and surface telemetry/logBlankFields per research decisions.
- [x] T011 [P] Enhance `scripts/api/instrumentation.ts` to queue telemetry when offline, include filter payload hashes, and respect optional webhook endpoint from quickstart instructions (see `tests/api/instrumentation.spec.ts`).
- [x] T012 Scaffold `scripts/ui/filters.ts` to render date range, landing, boat, and species controls (multi-select), emitting typed filter change events.
- [x] T013 Wire the new filter module into `scripts/main.ts`: manage filter state, debounce updates, trigger catch + metrics loads, and reset pagination when criteria change.
- [x] T014 [P] Integrate `@tanstack/virtual-core` virtualization within `scripts/ui/table.ts` (sticky header, row windowing, keyboard focus retention, blank-cell indicators).
- [x] T015 [P] Expand `scripts/ui/metrics.ts` to render fleet totals plus toggled per-boat/per-species panels with accessible summaries and number formatting.
- [x] T016 [P] Upgrade `scripts/ui/progressive.ts` to handle chunked fetches (cursor + limit), disable control when exhausted, and announce load completion for screen readers.
- [x] T017 Refine `scripts/ui/states.ts` to include ARIA live regions, retry hooks, and telemetry emission hooks for error/empty renders.
- [x] T018 Refresh `styles/table.css` (and companion rules in `styles/realdata.css` if needed) for responsive columns, resizable headers, focus outlines, and mobile-friendly spacing.
- [x] T019 [P] Update `specs/001-offshore-analytics-table/quickstart.md` with Supabase environment variables, telemetry toggle instructions, and the finalized test command matrix.
- [x] T020 [P] Document validation outcomes (contract/UI/perf runs, data-quality findings) in `landing.md` with a new RESET timestamp.

## ⚠️ Phase 2b: shadcn/ui Migration (CRITICAL)
**Discovery (2025-10-01)**: Tasks T014-T020 completed with vanilla TypeScript + DOM manipulation, violating CLAUDE.md mandate requiring shadcn/ui design system exclusively. Complete rebuild required.

**Issues Identified via Playwright inspection**:
- Gray native HTML5 date inputs (should be shadcn Calendar + Popover)
- Scrollable native select dropdowns (should be shadcn Select with full list display)
- Custom CSS (430 lines) instead of Tailwind utility classes with HSL color tokens
- Vanilla .ts files with document.createElement() instead of React .tsx components
- Empty table body (virtualization not rendering data rows)
- Custom buttons, cards, and collapsibles instead of shadcn components

**Migration Tasks**:
- [x] T021 Install React 18+, Tailwind CSS, and shadcn/ui foundation; run `npx shadcn@latest init` and install Button, Card, Table, Select, Calendar, Popover, Collapsible, Badge, Label, Input components.
- [x] T022 Configure build system for React: Update tsconfig.json with JSX support and path aliases, modify esbuild for .tsx loading and CSS bundling, create styles/globals.css with Tailwind directives and HSL color tokens.
- [ ] T023 Create React architecture: Add src/main.tsx entry point with ReactDOM.createRoot, create src/App.tsx main component, preserve left sidebar HTML structure (untouched), set up component tree for filters/metrics/table.
- [ ] T024 Convert FilterPanel to shadcn components: Replace native date inputs with Calendar + Popover (DatePicker pattern), replace native selects with shadcn Select, implement multi-select for species, use shadcn Button for reset action.
- [ ] T025 Convert MetricsCards and Collapsibles to shadcn: Use Card with CardHeader/CardContent for fleet summary, replace custom collapsible sections with shadcn Collapsible + CollapsibleTrigger/CollapsibleContent, use shadcn Table for per-boat/per-species breakdowns.
- [x] T026 Convert DataTable to shadcn with React virtualization: Use shadcn Table components (TableHeader, TableBody, TableRow, TableCell), integrate @tanstack/react-table for virtualization, debug and fix empty table body issue, implement sticky header with keyboard navigation.
- [x] T027 Replace custom CSS with Tailwind styling: Delete 430 lines from styles/table.css, apply Tailwind utility classes throughout (space-y-4, grid, gap-4, p-4), migrate all rgba() colors to HSL tokens (bg-card, border-border, text-foreground), implement responsive breakpoints (md:, lg:).
- [x] T028 Update tests and documentation: Update Playwright selectors for shadcn components, verify all acceptance scenarios pass, update quickstart.md with React build process, document migration in landing.md with RESET timestamp and bundle size comparison.

## Phase 3: Real Supabase Data Integration (T029-T034)

- [x] T029 Enable Supabase Row Level Security: Run SQL in Supabase dashboard to enable RLS on all tables (trips, boats, catches, landings), create read-only policies for anonymous users, verify anon key can read but not write.
- [x] T030 Create Supabase data fetcher: Implement src/lib/fetchRealData.ts with direct Supabase client queries, handle foreign key joins (trips → boats → landings, catches), transform database schema to CatchRecord format, support filter params (date range, boat, landing, species).
- [x] T031 Update App.tsx for real data: Add USE_REAL_DATA flag check, fetch from Supabase when enabled, fallback to mocks on error, display data source badge (green=real, yellow=mock), handle loading states.
- [x] T032 Local testing with real data: Enable USE_REAL_DATA=true in index.html, verify table shows real trips (~272 for last 30 days), test filters work, measure load time (<2s), compare metrics vs mocks.
- [x] T033 Create validation script: Implement scripts/validate-real-data.ts to check 100 real trips, validate schema compliance, detect null values, verify foreign keys resolve, log data quality metrics (100/100 passed).
- [x] T034 Update documentation: Document USE_REAL_DATA toggle in README.md and quickstart.md, add RLS setup instructions, note real vs mock data differences, update landing.md with Phase 3 completion.

## Dependencies
- T001 → prerequisite for all downstream work.
- T002 depends on T001 to ensure plan reflects synced artifacts.
- T003–T009 require T001; T006–T008 also depend on strengthened contract tests (T003–T005).
- T010 waits for T003–T005 to define expected payload behaviour.
- T011–T016 depend on T010 (API client ready) and relevant tests T006–T009 for guidance; `[P]` tasks in this band touch distinct modules.
- T017 relies on core UI wiring from T013–T016.
- T018 depends on UI structure from T013–T016.
- T019 waits for implementation + test updates (T010–T018).
- T020 is last, summarising completed validation.

## Migration Dependencies
- T021 → prerequisite for all migration work (foundation must be installed first).
- T022 depends on T021 (build system requires dependencies).
- T023 depends on T022 (React architecture requires build config).
- T024–T026 depend on T023 (components require React root); these can run in parallel after T023.
- T027 depends on T024–T026 (styling follows component conversion).
- T028 depends on T027 (testing validates complete migration).

## Parallel Execution Guidance
Once T010 completes:
- Run T014 [P] (virtualized table), T015 [P] (summary metrics cards), and T016 [P] (progressive loading control) in parallel—they touch separate UI modules.
- After UI modules settle, execute T011 [P] (telemetry enhancements) alongside T018 (responsive styling) while T017 finalises shared state messaging.
- Documentation tasks T019 [P] and T020 [P] can run concurrently once validation suites pass.
