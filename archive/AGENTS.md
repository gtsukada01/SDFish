# fish-scraper Development Guidelines

Auto-generated summary of active plans. Last updated: 2025-09-27

## Active Technologies
- TypeScript 5.x targeting ES2022 (browser bundles via esbuild)
- Spec Kit generated contracts, types, and mock payloads
- Supabase REST/edge endpoints backed by Postgres views
- `@tanstack/virtual-core` (or equivalent) for table virtualization

## Project Structure
```
index.html
scripts/
  api/
  ui/
styles/
specs/
tests/
```

## Commands
- `npm run generate:types`
- `npm run generate:all` (types + contract tests)
- `npx vitest run tests/contracts --run`
- `npx playwright test`
- `node --loader ts-node/esm tests/performance/filter.bench.ts`

## Code Style
- Prefer explicit types; no `any` without justification
- Keep generated files (`scripts/api/types.ts`, `scripts/api/mocks.ts`) read-only and regenerate from Spec Kit contracts
- Update `scripts/api/validators.ts` manually whenever schema semantics change so runtime checks stay aligned
- Preserve raw Supabase values; blank/partial data must surface as empty cells + logged events

## Recent Changes
- 2025-09-27: Bootstrapped Spec Kit artifacts and contract tests for feature `001-offshore-analytics-table`

<!-- MANUAL ADDITIONS START -->
- T010 complete: `scripts/api/client.ts` now targets Supabase edge routes. Set `window.FISH_SUPABASE_URL` (or bundle-time env) and optional `window.FISH_SUPABASE_ANON_KEY` before bootstrapping. Fallback reads `window.FISH_API_BASE_URL` or `/api`.
- Tests added: `tests/api/client.spec.ts` validates Supabase URL/header composition, cursor streaming, and mock pagination guard. Run with `npx vitest run tests/api --run`.
- T011 complete: `scripts/api/instrumentation.ts` queues telemetry while offline, stamps filter hashes (`hashFilters`), and flushes after `configureTelemetry` sees a webhook endpoint. Spec coverage lives in `tests/api/instrumentation.spec.ts`.
- T012–T013 complete: `scripts/ui/filters.ts` mounts header controls (date, landing, boat, multi-species) emitting `filters:change`. `scripts/main.ts` now debounces filter updates, aborts inflight fetches, derives option lists from data, and keeps `mock-filter` events working for tests.
<!-- MANUAL ADDITIONS END -->
