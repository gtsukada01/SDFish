# SPEC-011: Analytics & Insights Drilldown

**Status**: ✅ COMPLETE - All Phases Implemented
**Created**: October 20, 2025
**Completed (Phase 1)**: October 20, 2025
**Completed (Phase 2)**: October 20, 2025
**Owner**: Product Team
**Priority**: P1 - High Impact User Experience

## Problem Statement

Users viewing the Analytics & Insights section cannot easily drill down into specific data segments. When they see interesting patterns in the bar charts (e.g., "Dolphin caught 150 fish"), they must manually configure filters in the header to investigate those trips. This creates friction in data exploration and reduces analytical efficiency.

## Goals

1. **Direct Navigation**: Click any bar in Boats or Species tabs → Table filters to show only those trips
2. **Filter Integration**: Drilldown works seamlessly with existing header filter system
3. **Visual Feedback**: Clear indication when bar chart selections are active
4. **Progressive Enhancement**: Phase 1 focuses on Boats + Species (defer Moon phase for backend API development)

## Non-Goals

- **Moon Phase Drilldown**: Deferred to Phase 2 (requires backend moon_phase filter support)
- **Multi-Select from Charts**: Single-select only (use dropdown filters for multi-select)
- **Chart Toggle Behavior**: No toggle-off on re-click (use Active Filters badges to clear)

## User Stories

### Story 1: Boat Drilldown
**As a** fishing analytics user
**I want to** click a boat name in the Boats breakdown chart
**So that** I can immediately see all trips for that specific boat

**Acceptance Criteria:**
- Click "Dolphin" bar → Table shows only Dolphin trips
- Active Filters shows "Boat: Dolphin" badge with (x) to clear
- Works alongside existing landing/species/date filters
- Replaces any existing boat filter (single-select behavior)

### Story 2: Species Drilldown
**As a** fishing analytics user
**I want to** click a species name in the Species breakdown chart
**So that** I can see all trips that caught that species

**Acceptance Criteria:**
- Click "Yellowtail" bar → Table shows all trips with Yellowtail catches
- Active Filters shows "Species: Yellowtail" badge
- Normalizes species names (e.g., "Bluefin Tuna (up to 50 pounds)" → "Bluefin Tuna")
- Replaces existing species filter (single-select for simplicity)

### Story 3: Visual Feedback
**As a** user
**I want to** see which bars I've clicked
**So that** I understand my current drilldown state

**Acceptance Criteria:**
- Selected bars have distinct visual styling (highlight/border)
- Hover states remain functional on non-selected bars
- Clear visual hierarchy: selected > hover > default

## Technical Design

### Architecture Overview

```
User Click (Bar Chart)
    ↓
onClick Handler (MetricsBreakdown.tsx)
    ↓
Callback to Parent (App.tsx)
    ↓
Update Filters State
    ↓
useEffect Triggers (filters dependency)
    ↓
loadData() Fetches New Results
    ↓
Table Updates (CatchTable.tsx)
    ↓
Active Filters Badge Appears (ActiveFilters.tsx)
```

### Component Changes

#### 1. **MetricsBreakdown.tsx** - Add Click Handlers

**Current Structure:**
```tsx
interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
  mode?: 'boats' | 'species'
}
```

**Updated Structure:**
```tsx
interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
  mode?: 'boats' | 'species'
  selectedValue?: string | null  // Currently selected boat/species
  onBarClick?: (value: string) => void  // Callback when bar clicked
}

// Boats mode - render bar with click handler
<div
  key={boat.boat}
  className="space-y-1 cursor-pointer"
  onClick={() => onBarClick?.(boat.boat)}
>
  {/* Visual: Add ring-2 border if selectedValue === boat.boat */}
</div>

// Species mode - render bar with click handler
<div
  key={species.species}
  className="space-y-1 cursor-pointer"
  onClick={() => onBarClick?.(species.species)}
>
  {/* Visual: Add ring-2 border if selectedValue === species.species */}
</div>
```

#### 2. **App.tsx** - Wire Up Handlers

**New Handler Functions:**
```tsx
const handleBoatBarClick = (boatName: string) => {
  // Replace boat filter (single-select)
  setFilters(prev => ({ ...prev, boat: boatName }))

  // Scroll to table (smooth user experience)
  setTimeout(() => {
    document.querySelector('.catch-table')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}

const handleSpeciesBarClick = (speciesName: string) => {
  // Normalize species name (e.g., "bluefin tuna (up to 50 pounds)" → "bluefin tuna")
  const normalized = normalizeSpeciesName(speciesName)

  // Replace species filter (single-select, wrapped in array for API compatibility)
  setFilters(prev => ({ ...prev, species: [normalized] }))

  // Scroll to table
  setTimeout(() => {
    document.querySelector('.catch-table')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}
```

**Pass to MetricsBreakdown:**
```tsx
<TabsContent value="boats" className="mt-6">
  <MetricsBreakdown
    metrics={metrics}
    mode="boats"
    selectedValue={filters.boat || null}
    onBarClick={handleBoatBarClick}
  />
</TabsContent>

<TabsContent value="species" className="mt-6">
  <MetricsBreakdown
    metrics={metrics}
    mode="species"
    selectedValue={filters.species?.[0] || null}  // First species if array
    onBarClick={handleSpeciesBarClick}
  />
</TabsContent>
```

#### 3. **Visual Design** - Selected State Styling

**Tailwind Classes for Selected Bar:**
```tsx
// Container hover + cursor
className={`
  space-y-1 cursor-pointer rounded-md p-2
  hover:bg-accent/50 transition-colors
  ${selectedValue === value ? 'bg-accent/30' : ''}
`}

// Bar selected state
className={`
  relative h-7 bg-muted rounded-md overflow-hidden flex items-center
  ${selectedValue === value ? 'ring-2 ring-primary ring-offset-2' : ''}
  transition-all duration-300
`}
```

### Data Flow

**Initial State:**
```tsx
filters = {
  start_date: "2025-09-01",
  end_date: "2025-09-30",
  species: undefined,
  boat: undefined
}
```

**User Clicks "Dolphin" Bar:**
```tsx
handleBoatBarClick("Dolphin")
  ↓
setFilters({ ...prev, boat: "Dolphin" })
  ↓
filters = {
  start_date: "2025-09-01",
  end_date: "2025-09-30",
  boat: "Dolphin"  // ← NEW
}
  ↓
useEffect([filters]) triggers
  ↓
loadData() with boat="Dolphin"
  ↓
fetchRealCatchData({ ..., boat: "Dolphin" })
  ↓
Table shows only Dolphin trips
```

**User Clicks (x) on "Boat: Dolphin" Badge:**
```tsx
handleRemoveBoat("Dolphin")
  ↓
setFilters({ ...prev, boat: undefined })
  ↓
loadData() with boat=undefined
  ↓
Table shows all boats again
```

## Implementation Plan

### Phase 1: Core Drilldown (Current)

**Files to Modify:**
1. `src/components/MetricsBreakdown.tsx`
   - Add `selectedValue` and `onBarClick` props
   - Add click handlers to boat/species bars
   - Add visual styling for selected state
   - Add cursor-pointer and hover states

2. `src/App.tsx`
   - Add `handleBoatBarClick(boatName: string)` function
   - Add `handleSpeciesBarClick(speciesName: string)` function
   - Pass handlers to `<MetricsBreakdown />` component
   - Pass selected state for visual feedback

**Files NOT Modified:**
- `ActiveFilters.tsx` - Already handles badge display/removal ✅
- `MoonPhaseBreakdown.tsx` - No changes in Phase 1 ✅
- `types.ts` - Existing `Filters` interface already supports this ✅
- `fetchRealData.ts` - Backend API already supports boat/species filters ✅

### Phase 2: Moon Phase Drilldown (Future)

**Prerequisites:**
1. Backend API must add `moon_phase` filter parameter
2. Database query must support moon phase filtering
3. Update `Filters` interface with optional `moon_phase?: string`

**Implementation:**
1. Update `MoonPhaseBreakdown.tsx` with click handlers
2. Add `handleMoonPhaseBarClick()` in `App.tsx`
3. Update `fetchRealData.ts` to pass moon_phase filter
4. Add moon phase badge to `ActiveFilters.tsx`

## Testing Strategy

### Manual Testing Checklist

**Boats Tab Drilldown:**
- [ ] Click "Dolphin" → Table shows only Dolphin trips
- [ ] "Boat: Dolphin" badge appears in Active Filters
- [ ] Click (x) on badge → Clears boat filter, table shows all boats
- [ ] Click "Polaris Supreme" while "Dolphin" selected → Replaces with "Polaris Supreme"
- [ ] Selected bar has ring-2 border styling
- [ ] Non-selected bars still have hover effect

**Species Tab Drilldown:**
- [ ] Click "Yellowtail" → Table shows all trips with Yellowtail
- [ ] "Species: Yellowtail" badge appears
- [ ] Species normalization works ("Bluefin Tuna (up to 50 pounds)" → "Bluefin Tuna")
- [ ] Click different species → Replaces previous selection
- [ ] Selected bar visual feedback appears

**Filter Combinations:**
- [ ] Landing filter + boat drilldown → Both filters active
- [ ] Date range + species drilldown → Both filters active
- [ ] Boat dropdown selection + bar click → Bar click replaces dropdown selection
- [ ] Multiple filters + clear all → Drilldown selections cleared

**Edge Cases:**
- [ ] Click bar with 0 trips → Table shows "No results" (graceful empty state)
- [ ] Click bar while table is loading → Debounced correctly
- [ ] Mobile responsive: Bar click works on touch devices
- [ ] Keyboard accessibility: Can tab to bars and press Enter

## Success Metrics

**User Experience:**
- ✅ One-click drilldown (no manual filter configuration)
- ✅ <100ms UI response (synchronous filter update)
- ✅ Smooth scroll to table (visual feedback)
- ✅ Clear selected state (ring-2 border styling)

**Technical Quality:**
- ✅ Type-safe implementation (TypeScript strict mode)
- ✅ No API changes required (uses existing backend filters)
- ✅ Backwards compatible (non-breaking changes to components)
- ✅ Mobile responsive (touch-friendly click targets)

## Open Questions

1. **Keyboard Accessibility**: Should bars be keyboard-navigable (tabindex + Enter key)?
   - **Decision**: Yes, add in implementation for WCAG compliance

2. **Analytics Tracking**: Should we track bar click events?
   - **Decision**: Add console.log for Phase 1

3. **Deep Linking**: Should drilldown state be in URL query params?
   - **Decision**: Defer to Phase 3

---

**Implementation Estimate:** 2-3 hours
**User Impact:** High - Reduces 3-4 clicks to 1 click
**Technical Risk:** Low - Builds on existing filter system
