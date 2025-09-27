## Landing Reset Notes
**Last updated:** 2025-09-27 10:06 PDT (RESET-20250927-1006)

### Current State
- Dashboard markup and `styles/realdata.css` remain intact so the layout renders exactly as before.
- All JavaScript modules and backend integrations have been removed; the landing page is now static HTML.
- The project root is trimmed to essentials (`index.html`, `styles/realdata.css`, `landing.md`, `README.md`) so we can rebuild integrations systematically.

### Removed During Reset
- `api/` serverless functions and every script under `scripts/` (legacy API client, state, debug overlay, etc.).
- Node tooling (`package.json`, `node_modules`, lint/test configs) and former deployment helpers.
- Historical recovery scripts, reports, data dumps, and monitoring artifacts cluttering the repository root.

### Next Steps (suggested)
1. Define the new data contract for the landing experience (endpoint shape, fields, cadence).
2. Re-introduce client logic incrementally—start with a single vanilla JS module once the API contract is clear.
3. Add lightweight integration tests as the new pipeline stabilizes.
4. Document each milestone here so future resets stay controlled.

### Immediate To-Dos
- Confirm the static page loads via `index.html` without missing asset errors.
- Decide whether to keep the existing markup sections or simplify further before wiring new data sources.
