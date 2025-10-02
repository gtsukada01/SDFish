# SD Fishing Dashboard - React + shadcn/ui

**Status**: ✅ Production Ready (All Features Complete)
**Stack**: React 18 + shadcn/ui + Tailwind CSS + TanStack React Table + Supabase Direct Client
**Branch**: `001-offshore-analytics-table`
**Last Updated**: October 2, 2025

This dashboard provides Southern California offshore fishing analytics with production-ready React + shadcn/ui architecture and **real-time Supabase data integration** (7,746+ trips). Direct client queries ensure reliable deployment without API layer failures.

## What's Inside

### React Components (shadcn/ui)
- `src/App.tsx` – Main application with filters, metrics, and data table
- `src/components/Sidebar.tsx` – Hierarchical regional navigation with collapsible sections and pin functionality
- `src/components/Header.tsx` – Application header
- `src/components/FilterPanel.tsx` – Real Supabase data: 7 landings, 74 boats, 66 species with searchable dropdowns
- `src/components/MetricsBreakdown.tsx` – Collapsible boat/species breakdowns
- `src/components/CatchTable.tsx` – Data table with TanStack React Table
- `src/components/ui/` – shadcn component library (Button, Card, Table, Collapsible, etc.)

### Build & Config
- `index.html` – Single React mount point (`<div id="root"></div>`)
- `package.json` – React 18, shadcn/ui, Tailwind CSS, TanStack Table
- `tsconfig.json` – TypeScript config with path aliases (@/*)
- `tailwind.config.js` – Tailwind with HSL color tokens
- `components.json` – shadcn CLI configuration

### Specifications & Tests
- `specs/` – Feature spec, migration plan, tasks, contracts
- `tests/` – Playwright UI scenarios (desktop + mobile)
- `scripts/api/` – Generated TypeScript types and mocks
- `MIGRATION_STATUS.md` – Detailed migration progress report

## Getting Started

### Quick Start
```bash
# Install dependencies
npm install

# Build the application
npm run build

# Start development server
npm start
# → http://localhost:8081
```

### Data Mode Toggle

The dashboard supports two data modes (configured in `index.html`):

**Real Data Mode** (Production - Current):
```javascript
window.USE_REAL_DATA = true;  // Direct Supabase queries
```
- 🟢 Green badge in UI
- Real-time data from 7,746+ trips
- Filters work on live database
- Last 30 days: ~272 trips, 54 boats, 29 species

**Mock Data Mode** (Development/Testing):
```javascript
window.USE_REAL_DATA = false;  // Uses mocks.ts
```
- 🟡 Yellow badge in UI
- 2 sample trips for UI testing
- Faster for component development
- Auto-fallback if Supabase fails

### Development Workflow
```bash
# Regenerate TypeScript types from schemas
npm run generate:types

# Watch mode (auto-rebuild on changes)
npm run dev

# Build for production
npm run build
# Output: assets/main.js (1.6MB), assets/styles.css (1.6KB)
```

### Adding shadcn Components
```bash
# Add new shadcn component
npx shadcn@latest add [component-name]

# Example: Add dialog component
npx shadcn@latest add dialog
```

## Testing & Validation

```bash
# Contract validation (TypeScript types match JSON schemas)
npm run test:contracts

# Playwright UI tests (desktop + mobile)
npm run test:ui

# Performance benchmarks
npm run bench
```

### Playwright Browser Automation
```bash
# Install Playwright browsers
npx playwright install

# Run specific test file
npx playwright test tests/responsive.spec.ts
```

## Implementation Status

### ✅ Phase 2b: shadcn/ui Migration (T021-T028)
- ✅ T021: React 18 + shadcn/ui foundation
- ✅ T022: Build system (esbuild + Tailwind)
- ✅ T023: Sidebar navigation (shadcn Button + Separator)
- ✅ T024: Filter panel (Calendar, Select, Badge)
- ✅ T025: Metrics breakdowns (Collapsible)
- ✅ T026: Data table (shadcn Table + TanStack React Table)
- ✅ T027: CSS cleanup (deleted 430 lines)
- ✅ T028: Documentation updates

### ✅ Phase 3: Real Data Integration (T029-T034)
- ✅ T029: Supabase Row Level Security (RLS) enabled
- ✅ T030: Direct Supabase client with schema transformation
- ✅ T031: Real/mock data toggle with fallback
- ✅ T032: Local testing verified (272 trips/30 days)
- ✅ T033: Data quality validation (100/100 passed)
- ✅ T034: Documentation complete

### ✅ Phase 4: Navigation & Filter Enhancements (Complete)
- ✅ Real filter data from Supabase (7 landings, 74 boats, 66 species)
- ✅ Hierarchical regional navigation (San Diego, Orange County, Los Angeles, Channel Islands)
- ✅ Collapsible sidebar sections with expand/collapse functionality
- ✅ Pin/unpin functionality with right-aligned icons
- ✅ Sidebar collapse to minimal width (288px → 48px)
- ✅ Active state highlighting and filter synchronization

**Current Mode**: 🟢 Real Data (7,746+ trips from Supabase)
**Verification**: All features tested with Playwright, real data integration working
**See MIGRATION_STATUS.md and specs/001-offshore-analytics-table/landing.md for detailed reports.**

## Project Structure

```
fish-scraper/
├── src/
│   ├── main.tsx                 # React entry point
│   ├── App.tsx                  # Main application
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── FilterPanel.tsx
│   │   ├── MetricsBreakdown.tsx
│   │   ├── CatchTable.tsx
│   │   └── ui/                  # shadcn components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── table.tsx
│   │       ├── select.tsx
│   │       ├── popover.tsx
│   │       ├── calendar.tsx
│   │       ├── collapsible.tsx
│   │       └── ...
│   └── lib/
│       └── utils.ts             # cn() utility
├── scripts/api/
│   ├── types.ts                 # Generated TypeScript types
│   └── mocks.ts                 # Mock API responses
├── specs/
│   └── 001-offshore-analytics-table/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       └── contracts/
├── assets/
│   ├── main.js                  # Compiled React bundle (1.6MB)
│   └── styles.css               # Tailwind output (1.6KB)
├── index.html                   # Single page app entry
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── components.json              # shadcn config
└── MIGRATION_STATUS.md          # Detailed migration report
```

## Tech Stack

- **React**: 18.3.1 with TypeScript
- **UI Framework**: shadcn/ui (Radix UI + Tailwind CSS)
- **Styling**: Tailwind CSS 3.4.1 with HSL color tokens
- **Data Table**: TanStack React Table v8
- **Date Picker**: react-day-picker
- **Icons**: lucide-react
- **Build**: esbuild + PostCSS
- **Testing**: Playwright

## shadcn Components Used

- Button, Card, Table, Select, Popover, Calendar
- Collapsible, Separator, Label, Input, Badge

## What's Next

**Migration is complete!** The application is ready for:

1. **API Integration**: Wire Supabase client into React components (currently using mocks)
2. **Loading States**: Add shadcn Alert/Toast for loading/error feedback
3. **Progressive Loading**: Implement cursor pagination with "Load More" button
4. **Test Updates**: Rewrite legacy Playwright tests for React component selectors
5. **Accessibility**: Add ARIA announcements and enhanced keyboard navigation

**Commands**:
```bash
npm start                        # Start dev server → http://localhost:8081
npm run build                    # Production build
npx playwright test tests/ui/shadcn-table.spec.ts  # Verify components (✅ 4/4 passing)
```

See **MIGRATION_STATUS.md** and **specs/001-offshore-analytics-table/landing.md** for complete details.
