# Implementation Plan: Frontend Modernization & Deployment Hardening

**Spec Link**: `specs/012-modernize-frontend/spec.md`  
**Owner**: Dashboard Engineering  
**Reviewers**: Data Platform, QA Automation, DevOps  
**Status**: Draft  
**Last Updated**: 2025-10-22

---

## Milestones & Deliverables

| Milestone | Target Date | Key Deliverables | Exit Criteria |
|-----------|-------------|------------------|---------------|
| M1. Tooling Baseline & CI Guardrails | 2025-10-25 | Added lint/type/test/build commands, baseline bundle metrics, `frontend/.env.example` | CI runs lint/type/unit/e2e/build on PRs; baseline metrics stored in `docs/perf/bundle-baseline.json` |
| M2. Data Layer Consolidation | 2025-11-01 | `CatchDataService`, `useCatchData` hook, cached summary reuse, updated App | Filter change triggers single Supabase fetch; vitest + Playwright coverage proves dedupe |
| M3. Filter & Sidebar Decomposition | 2025-11-08 | New filter provider/context, split components, provider caching | Header + sidebar share provider, files <200 LOC, Playwright regressions green |
| M4. Legacy Cleanup & Build Pipeline | 2025-11-15 | Archived DOM client, Tailwind glob reduction, `npm run build:prod` producing `dist/` | Tailwind bundle shrinks ≥30%, dist <10 MB, new build scripts documented |
| M5. Secrets, Docs & Launch Readiness | 2025-11-20 | Env-configured Supabase client, updated docs/ADR, QA evidence | No hard-coded keys, README onboarding updated, manual QA checklist signed off |

---

## Phase Breakdown

### Phase 1 – Tooling Baseline & CI Guardrails
- Create scripts: `npm run lint`, `npm run test:unit`, `npm run test:ui`, `npm run typecheck`, `npm run build:prod`.
- Capture bundle baseline via `esbuild --metafile` and `wc -c frontend/assets/styles.css`, store under `docs/perf/`.
- Generate `frontend/.env.example`, add `.env.local` to `.gitignore`.
- Update CI workflow to run full suite on PRs touching `src/`, `scripts/`, `specs/012-*`.
- Deliverable: `actions/012-01-tooling.md` closed with verification logs attached.

### Phase 2 – Data Layer Consolidation
- Introduce `src/services/catch-data.ts` encapsulating Supabase calls with AbortController + caching.
- Build `useCatchData` hook and `CatchDataProvider` context consumed by `App`.
- Refactor `fetchRealSummaryMetrics` to accept pre-fetched records when available; remove duplicate Promises.
- Add vitest specs covering cache hits/misses; update Playwright to assert single network call per filter change (using mocks).
- Deliverable: `actions/012-02-data-layer.md` with telemetry screenshot evidencing 1 call/filter change.

### Phase 3 – Filter & Sidebar Decomposition
- Create `src/providers/filter-options.tsx` returning cached landings/boats/species/durations.
- Split `HeaderFilters` into sub-components (`DatePresetSelector`, `BoatSelect`, `SpeciesMultiSelect`, etc.).
- Rebuild `Sidebar` with memoized section components and pinned landing manager.
- Add Storybook-lite snapshots or component tests (vitest + React Testing Library) for new units.
- Deliverable: `actions/012-03-filters.md` referencing LOC diff, Playwright visual diffs, accessibility notes.

### Phase 4 – Legacy Cleanup & Build Pipeline
- Move legacy DOM client (`scripts/main.ts`, `scripts/ui/*`) into `archive/legacy-dom-client/` with README, or delete after confirmation.
- Update Tailwind `content` array to `["./index.html", "./src/**/*.{ts,tsx}", "./tests/**/*.{ts,tsx}"]`.
- Stop tracking build artifacts; add `/dist` and `/assets/*.map` to `.gitignore`.
- Implement `npm run build:prod` that writes `dist/` with hashed assets; adjust Playwright static server to serve from `dist/`.
- Deliverable: `actions/012-04-build.md` containing before/after bundle stats and file manifests.

### Phase 5 – Secrets, Docs & Launch
- Refactor `src/lib/supabase.ts` to read from `import.meta.env.VITE_SUPABASE_*` with runtime guard + friendly error message.
- Update `frontend/index.html` (or new config loader) to eliminate legacy `window.FISH_*` flags in favor of provider config.
- Publish ADR `docs/architecture/decision-records/2025-10-frontend-modernization.md`.
- Complete manual QA checklist (responsive, keyboard nav, error states), attach to `notes/2025-11-launch-review.md`.
- Deliverable: `actions/012-05-launch.md` linking to QA evidence, docs PRs, and secret scan results.

---

## Dependencies & Resources
- Supabase staging credentials for testing new env loading.
- Access to CI configuration and Vercel deployment settings.
- QA automation time for Playwright updates.
- DevOps sign-off on dist-based deployments.

---

## Rollout & Backout

- **Rollout**: Feature branches merged sequentially into `main` behind feature flag `USE_REAL_DATA_PROVIDER`. Staging soak for 48 hours with telemetry monitoring before enabling flag in production.
- **Backout**: Revert individual feature branches if telemetry spikes (Supabase errors, bundle size). Keep legacy scripts archived for quick re-enable if needed.

---

## Monitoring & Quality Gates

- Supabase request count per session (via instrumentation) monitored daily.
- Bundle size GitHub Action alerts on >50 KB increase.
- CI gates: lint, unit, typecheck, Playwright, `npm run build:prod`.
- Manual QA checklist required before enabling production flag.

---

## Operational Runbook (Record of Work + Future Procedure)

**Latest execution**: 2025-10-23 by dashboard automation (spec-012). Follow this checklist for future recoveries or audits.

1. **Schema migrations** (run in Supabase SQL Editor):
   - `migrations/20251023_add_trip_collisions.sql`
   - `migrations/20251023_add_trip_slug_and_hash_v2.sql`
   - `migrations/20251023_create_trips_quarantine.sql`
2. **Re-scrape recovery**
   - Export credentials: `export SUPABASE_URL=...` and `export SUPABASE_SERVICE_ROLE_KEY=...`.
   - Execute `python3 scripts/data/recover_collisions.py --dates "YYYY-MM-DD,..."`.
   - The script automatically:
     * backs up trips to `trips_quarantine` and `backups/phase2/*.json`
     * deletes affected trips/catches
     * re-runs `socal_scraper.py` for each day with new hash logic
3. **Verification**
   - `python3 -m unittest tests/python/test_collision_detection.py`
   - `python3 scripts/sql/find_composite_collisions.sql` (via Supabase SQL editor) to confirm collisions logged not data loss.
   - Spot-check: `select count(*) from trips where trip_date = 'YYYY-MM-DD';`
   - Review `trip_collisions` for rows expected to be human differences (weight labels, etc.).
4. **QC follow-up**
   - Regenerate QC baselines for refreshed dates and archive prior snapshots under `logs/qc_baselines_pre_phase2/`.
   - Document any lingering collisions in `COMPREHENSIVE_QC_VERIFICATION.md`.
5. **Backout** (if re-scrape results are unacceptable)
   - Restore via `INSERT INTO trips SELECT * FROM trips_quarantine WHERE trip_date = 'YYYY-MM-DD' AND reason = 'phase2_rescrape_YYYY-MM-DD';`
   - Delete re-scraped rows and rerun QC.

All commands above were executed successfully on the dates listed in the primary spec; repeat the same procedure to recover future collision windows.

---

## Communication

- Weekly status note in `notes/` directory and posted to engineering Slack.
- Update project board with action status (To Do / In Progress / Review / Done).
- Notify stakeholders (Data Platform, Ops) before rollout and after completion with summary metrics.
