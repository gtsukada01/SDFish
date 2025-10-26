# Task Breakdown: Frontend Modernization & Deployment Hardening

**Spec**: `specs/012-modernize-frontend/spec.md`  
**Plan**: `specs/012-modernize-frontend/plan.md`  
**Owner**: Dashboard Engineering  
**Status**: Draft

---

## Phase 1 – Tooling Baseline & CI Guardrails
- [x] Add lint/type/unit/e2e/build scripts to `package.json`.
- [x] Capture bundle baseline (`docs/perf/bundle-baseline.json`, `docs/perf/bundle-baseline.md`).
- [x] Create `frontend/.env.example` and update `.gitignore`.
- [x] Update CI workflow to run full suite on PR (lint, typecheck, vitest, Playwright, build).
- [x] Draft action file `actions/012-01-tooling.md` with verification logs.

## Phase 2 – Data Layer Consolidation
- [x] Implement `src/services/catch-data.ts` with caching + abort logic.
- [x] Build `CatchDataProvider` and `useCatchData` hook for `App`.
- [x] Refactor summary metrics to reuse fetched records.
- [x] Add vitest coverage for cache hits/misses and error fallback.
- [x] Update Playwright tests to assert single Supabase call/filter change.
- [ ] Close `actions/012-02-data-layer.md` with telemetry evidence. *(owner to upload final logs)*

## Phase 3 – Filter & Sidebar Decomposition
- [x] Create `FilterOptionsProvider` with memoized cache + background refresh.
- [x] Split Header Filters into sub-components (date preset, landing/boat select, species multi-select, durations, apply/reset).
- [x] Rebuild Sidebar with shared provider, pinned landing controls, and region subcomponents.
- [x] Add component tests / visual diffs for new pieces.
- [x] Update accessibility checks (keyboard navigation, screen-reader labels).
- [ ] Finalize `actions/012-03-filters.md` with screenshots + test logs.

## Phase 4 – Legacy Cleanup & Build Pipeline
- [x] Archive or remove legacy DOM client assets; add README describing historical context.
- [x] Tighten Tailwind `content` glob and remove unused CSS artifacts.
- [x] Ignore build outputs and create `npm run build:prod` generating `dist/`.
- [x] Update Playwright static server to read from `dist/`.
- [x] Record before/after bundle metrics in `docs/perf/bundle-after.json`.
- [ ] Complete `actions/012-04-build.md` with artifact manifest.

## Phase 5 – Secrets, Docs & Launch
- [x] Switch Supabase client to env-driven config with runtime validation.
- [x] Remove legacy global flags from `index.html`; document new config loader.
- [x] Update README + onboarding docs; add ADR for modernization decision.
- [x] Execute manual QA checklist (attach to `notes/2025-11-launch-review.md`).
- [x] Run secret scan to confirm no hard-coded keys remain.
- [ ] Close `actions/012-05-launch.md` with QA evidence and go-live sign-off.

### Operational Follow-Through (completed 2025-10-23)
- [x] Apply Supabase migrations for telemetry/quarantine (`20251023_*` scripts).
- [x] Run `scripts/data/recover_collisions.py` across 23 historical dates to restore lost trips (backups stored in `backups/phase2/`).
- [x] Verify collisions logged in `trip_collisions` and `trips` new rows carry `trip_hash_version = 2`.
- [x] Confirm unit tests (`python3 -m unittest tests/python/test_collision_detection.py`) and spot-check trip counts per recovered day.

---

## Cross-Cutting Quality Checks
- [ ] Ensure each PR references the relevant action doc and includes test command output snippets.
- [ ] Maintain bundle-size guard (GitHub Action) and respond to alerts within 24 hours.
- [ ] Update project board weekly with action status.
