## Landing Filters Diagnostic Notes
**Last updated:** 2025-09-27 09:37 PDT (CRID-20250927-0937)

### Current Status
- `state.getApiFilters()` now emits `startDate`, `endDate`, `landing_id`, and resolved `boat_id` while keeping client-only keys for UI filtering.
- Dashboard initialization hydrates `boatNameToIdMap` and `landingIdToNameMap` before the first data load, then stores them in state and exposes them for the debug overlay.
- Relative `/api/...` calls remain intact for both legacy fetches and the API client.
- Added `tests/state-getApiFilters.test.js` to assert the server-ready payload stays intact (Node run: `All state.getApiFilters diagnostics passed`).
- Reviewed `USE_NEW_API_CLIENT` branches in `dashboard.entry.js` to confirm they reuse state-derived payloads and stay on the relative `/api` surface for debug parity.
- `github-deployment/scripts/apiClient.js` now emits request/response telemetry (request IDs, row counts, errors) into the debug overlay so `USE_NEW_API_CLIENT` produces the same diagnostics as the wrapped `fetch` path.

### Verification Checklist
- Enable debug overlay (`localStorage.setItem('debug','1')`) and reload: mapping panel should show ✅ for boats and landings.
- Select Liberty: network request to `/api/trips` should include `boat_id=71`, `landing_id=<liberty landing>`, `startDate`, and `endDate`.
- Change date range: subsequent requests should retain both IDs and updated dates; overlay history should reflect the new payloads.
- Reload after landing switch to confirm mappings persist (no warning about empty boat map).
- Toggle `USE_NEW_API_CLIENT` on and reload: verify overlay `requestHistory` records the API client fetches with matching params and `X-Client-Request-Id` headers.

### Follow-Ups
- Run the full Liberty regression flow in production and capture overlay/screenshots for the recovery log.
