# Quickstart: Southern California Offshore Analytics Table

**Status**: ✅ Production Ready (React 18 + shadcn/ui + Real Supabase Data + Navigation)
**Last Updated**: October 2, 2025, 12:00 AM PST

## Prerequisites
- Node 18+ with `npm`
- Playwright browsers installed locally (run `npx playwright install` after dependencies)
- Supabase account (for production data - optional for mock mode)

## 1. Install project dependencies
```bash
npm install
npx playwright install  # required for UI + performance suites
```

## 2. Regenerate Spec Kit artifacts
```bash
npm run generate:types
```
This command rebuilds `scripts/api/types.ts` and `scripts/api/mocks.ts` from the JSON Schemas in `specs/001-offshore-analytics-table/contracts/`.

## 3. Build the React application
```bash
# Production build (esbuild + Tailwind CSS)
npm run build

# Watch mode during development
npm run dev

# Start development server
npm start  # → http://localhost:8081
```

**Build Output**:
- `assets/main.js` (1.6MB React bundle with source maps)
- `assets/styles.css` (1.6KB Tailwind CSS output)

**Architecture**: React 18 + shadcn/ui components + TanStack React Table

## 4. Run contract tests
```
npm run test:contracts
```

## 5. Configure data mode (index.html)

### Real Data Mode (Production - Current)
```javascript
window.USE_REAL_DATA = true;  // ✅ ENABLED
```
- Uses direct Supabase client queries
- No API layer (avoids Vercel deployment issues)
- 7,746+ real trips from database
- Credentials in `src/lib/supabase.ts` (public anon key is safe)

### Mock Data Mode (Development)
```javascript
window.USE_REAL_DATA = false;
```
- Uses `scripts/api/mocks.ts` (2 sample trips)
- Faster for UI development
- Auto-fallback if Supabase connection fails

### Supabase Row Level Security (RLS)
**Already configured** - run this SQL if deploying to new Supabase instance:
```sql
-- Enable read-only access for anonymous users
-- See scripts/setup-rls.sql for full script
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read trips" ON trips FOR SELECT TO anon USING (true);
```

### Telemetry configuration (optional)
```javascript
window.FISH_TELEMETRY_ENDPOINT = "https://your-telemetry-service.com/events";
```
If unset, telemetry events log to console only. The instrumentation helper:
- Queues events while offline and replays on reconnect
- Attaches filter payload hashes for correlation
- Emits `fetch_start`, `fetch_success`, `fetch_error`, and `state_render` events

## 6. Preview the React application
1. Start the development server:
   ```bash
   npm start  # → http://localhost:8081
   ```
2. Browse to `http://localhost:8081`
3. **Features**:
   - Hierarchical regional navigation (San Diego, Orange County, Los Angeles, Channel Islands)
   - Collapsible sidebar with pin/unpin functionality
   - Real Supabase filter data: 7 landings, 74 boats, 66 species
   - Date range filters with shadcn Calendar + Popover
   - Landing, Boat, and Species dropdowns (shadcn Select with real data)
   - Summary metrics cards (Total Trips, Total Fish, Active Boats, Species)
   - Collapsible boat/species breakdowns
   - Data table with sorting and pagination (TanStack React Table)
4. All UI components use shadcn/ui design system with Tailwind CSS

## 7. Test command matrix

### Contract tests (Vitest)
```bash
npm run test:contracts              # Validates schemas, mocks, and API client adapters
```

### UI tests (Playwright)
```bash
npm run test:ui                     # Legacy vanilla tests (pending update for React)
npx playwright test tests/ui/shadcn-table.spec.ts  # shadcn component verification (✅ 4/4 passing)
```
**shadcn Verification Tests**:
- ✅ Table renders with 2 mock data rows
- ✅ 8 column headers present (Date, Boat, Landing, Duration, Anglers, Total Fish, Top Species, Weather)
- ✅ Pagination controls functional
- ✅ Summary metrics cards display correctly
- ✅ Sortable columns have icons

**Note**: Legacy tests in `tests/ui/table.desktop.spec.ts` require updating for React component selectors.

### Performance benchmarks
```bash
npm run bench                       # Filter response timing (≤2s median, ≤2.5s P95)
```

### Type checking
```bash
npm run typecheck                   # Validates TypeScript across all modules
```

Document all testing outcomes, data-quality findings (blank fields), and anomalies in `landing.md` with RESET timestamps after each validation run.
