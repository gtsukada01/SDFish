# Research: Southern California Offshore Analytics Table

## 1. Supabase Contract Strategy
- **Decision**: Define a dedicated Postgres view `public.offshore_catch_view` plus an edge function `offshore-catch` that returns paginated/tabular data and a companion `offshore-metrics` endpoint for summary aggregations. Both endpoints accept `start_date`, `end_date`, `species[]`, `landing`, and `boat` filters; defaults reflect the last 30 days. Responses include `data[]`, `total_rows`, `filters_applied`, and `last_synced_at` metadata.
- **Rationale**: A view lets us normalize the existing historical tables without duplicating data, while the edge function enforces consistent filtering logic and CORS headers for the static frontend. Splitting metrics keeps the table payload lean and allows independent caching strategies.
- **Alternatives**:
  - Query the base table directly from the browser via Supabase client (rejected: heavier client, exposes service key, harder to evolve contract).
  - Build a composite endpoint returning both table rows and metrics (rejected: payload size and cache granularity).
- **Follow-up**: Confirm column names in Supabase (`trip_date`, `boat`, `landing`, `trip_duration_hours`, `angler_count`, `total_fish`, `top_species`, `top_species_count`, `created_at`). Adjust view definition accordingly and document SQL in `contracts/` during Phase 1.

## 2. Virtualization & Progressive Loading
- **Decision**: Use `@tanstack/virtual-core` to manage row virtualization with a window size of 20 rows and overscan of 5. Enable progressive loading when `total_rows > 6000`, batching in 1000-row chunks with a load-more trigger or virtual-only fetch depending on filter combination.
- **Rationale**: `@tanstack/virtual-core` is framework-agnostic, lightweight (~5KB), and compatible with vanilla TypeScript. Setting a 6k threshold keeps initial render responsive while still allowing anglers to scroll large histories.
- **Alternatives**:
  - Build custom virtualization (rejected: more maintenance, fewer optimizations).
  - Adopt React/Table libraries (rejected: we’re staying framework-light per reset goals).
- **Follow-up**: Validate actual dataset sizes; tweak threshold if performance tests indicate higher/lower limits.

## 3. Telemetry & Data-Quality Logging
- **Decision**: Implement a small telemetry helper that logs events (`fetch_start`, `fetch_success`, `fetch_error`, `blank_field_detected`) to `console.info` in production and optionally posts to a Supabase `analytics_events` table when environment variable `ENABLE_TELEMETRY_WEBHOOK` is set. Blank-field events capture record ID, missing fields, and timestamp.
- **Rationale**: Console logging is zero-cost for browsers and supports quick debugging, while optional webhook keeps room for structured observability without forcing backend changes during rebuild.
- **Alternatives**:
  - Ship no telemetry (rejected: violates Observable Resilience principle).
  - Require server-side logging immediately (rejected: slows initial rebuild; we can enable later).
- **Follow-up**: Specify the webhook payload schema in Phase 1 contracts and add a toggle in `quickstart.md` for enabling the telemetry endpoint.

## 4. Responsive & Accessibility Testing
- **Decision**: Use Playwright with built-in device descriptors `Desktop Chrome`, `Pixel 7` (closest available) customized to Pixel 10 resolution, and `iPhone 14 Pro Max` customized to iPhone 17 specs via `viewport` and `userAgent` overrides. Run tests in headless mode locally and in CI (GitHub Actions or Vercel if needed).
- **Rationale**: Playwright’s device emulation integrates with our UI tests, enabling the acceptance scenarios to double as responsive checks. Customizing descriptors avoids waiting for official Pixel 10/iPhone 17 presets.
- **Alternatives**:
  - Manual @web-only verification (rejected: not automatable, brittle).
  - Cypress (rejected: heavier setup, less flexible device emulation for our use case).
- **Follow-up**: Capture exact viewport dimensions/User-Agent strings for Pixel 10/iPhone 17 once devices ship; update Playwright config accordingly.

## 5. Performance Harness
- **Decision**: Build a Node-based harness using Playwright’s trace API. The harness will: load the mock-backed page, trigger filter combinations, collect `performance.timing` differences, and fail if median response exceeds 2000ms or P95 exceeds 2500ms. Store scripts in `tests/performance/filter.bench.ts` with thresholds configurable via environment variables.
- **Rationale**: Playwright trace gives consistent metrics across desktop/mobile contexts and integrates with our existing tooling. Median/P95 thresholds align with constitution.
- **Alternatives**:
  - Custom browser benchmark (rejected: reinventing instrumentation).
  - Lighthouse CI (rejected: less granular for filter interactions).
- **Follow-up**: Decide whether to sample cold vs warm cache scenarios; document in quickstart.

## 6. Build Pipeline
- **Decision**: Use `esbuild` via a lightweight npm script to transpile `scripts/**/*.ts` into `public/assets/*.js` (ES2017 target). CSS handled via vanilla files (no build step). Bundle size target <100KB gzipped for initial load.
- **Rationale**: `esbuild` is fast, zero-config for our needs, and avoids complex bundlers. Aligns with static hosting on Vercel.
- **Alternatives**:
  - Plain `tsc` (rejected: emits unbundled modules; more work for browser compatibility).
  - Vite (rejected: heavier project footprint though could be reconsidered later).
- **Follow-up**: Add `esbuild` to tooling once we reintroduce package.json; verify Vercel deployment script.

## 7. Summary Metric Computation
- **Decision**: Compute metrics via Supabase edge function `offshore-metrics` returning totals per boat and species alongside overall totals. Keep aggregation server-side to ensure alignment with database truth.
- **Rationale**: Server-side aggregation avoids floating discrepancies and honors Data Fidelity First. We can reuse the view or call Postgres stored procedures.
- **Alternatives**:
  - Aggregate client-side (rejected: duplicates logic, risks drift).
  - Precompute nightly (rejected for now; we want live filtered metrics).
- **Follow-up**: Draft SQL for metrics (GROUP BY boat/species) and include in contracts.

## 8. Data Quality Workflow
- **Decision**: Collect blank-field logs into a JSON blob appended to `landing.md` (or a separate `data-quality.md`) during QA, and optionally forward to Supabase `data_quality_issues` table via webhook.
- **Rationale**: Keeps investigative trail without blocking release; stakeholders can triage mismatches later.
- **Alternatives**:
  - Ignore blanks (rejected per constitution).
  - Block UI rendering for blanks (rejected: hides data from anglers).
- **Follow-up**: Create CLI script (future task) that extracts log entries for manual review.

## 9. Outstanding Risks
- Need Supabase credentials and view/edge function deployment plan before implementation.
- Device emulation for future Pixel/iPhone may require updates as specs stabilize.
- Ensuring virtualization + summary metrics remain in sync when progressive loading kicks in; add integration test coverage.

All open questions now have a documented direction; implementation tasks will validate exact SQL, device parameters, and telemetry endpoints during Phase 1.
