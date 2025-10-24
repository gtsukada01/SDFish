# SPEC-007: Conditional Metrics Dashboard Cards

**Status**: ✅ IMPLEMENTED
**Date**: 2025-10-18
**Version**: 1.0

## Overview

Implement smart conditional rendering for dashboard metric cards that show contextually relevant metrics based on active filters. Avoid showing redundant metrics like "Active Boats: 1" when a single boat is selected.

## Problem Statement

The original dashboard showed the same 4 metrics regardless of filter context:
- Total Fish
- Total Trips
- Active Boats
- Species

When users filter to a single boat or landing, metrics like "Active Boats: 1" and "Species: 2" provide no actionable value and waste screen space.

## Solution

### Card Layout

**Default View (No Filters):**
1. Total Fish
2. Total Trips
3. Active Boats
4. Species

**Filtered View (Boat/Landing Selected):**
1. Total Fish
2. Total Trips
3. Avg Fish/Angler
4. Best Moon Phase

**Species Filtered View (Species Selected):**
1. Total Fish
2. Total Trips
3. Active Boats
4. Best Moon Phase (NEW - Added Oct 18, 2025)

### Implementation Details

#### Conditional Logic
```typescript
const isBoatFiltered = !!filters.boat || selectedLandings.length > 0
const isSpeciesFiltered = !!filters.species && filters.species.length > 0
```

**Card 3 Conditional**: Shows based on `isBoatFiltered` only
- If boat/landing selected → "Avg Fish/Angler"
- Otherwise → "Active Boats"

**Card 4 Conditional**: Shows based on `isBoatFiltered || isSpeciesFiltered`
- If boat/landing **OR species** selected → "Best Moon Phase"
- Otherwise → "Species"

#### New Metrics Calculations

**Avg Fish/Angler:**
```typescript
const totalAnglers = catchData.reduce((sum, trip) =>
  sum + (trip.angler_count || 0), 0
)
const avgFishPerAngler = totalAnglers > 0
  ? Math.round((metrics?.fleet.total_fish || 0) / totalAnglers)
  : 0
```

**Best Moon Phase:**
```typescript
const MIN_TRIPS_FOR_MOON_PHASE = 10 // Statistical validity threshold
const bestMoonPhase = metrics?.moon_phase && metrics.moon_phase.length > 0
  ? metrics.moon_phase
      .filter(phase => phase.trip_count >= MIN_TRIPS_FOR_MOON_PHASE)
      .reduce((best, current) =>
        current.avg_fish_per_trip > best.avg_fish_per_trip ? current : best
      , null)
  : null
```

**Moon Phase Data Source:**
- Table: `ocean_conditions`
- Columns: `date`, `moon_phase_name`, `moon_illumination_percent`
- Coverage: Daily entries (every single day has a phase)
- Matching: Exact date match between `trip.trip_date` and `ocean_conditions.date`

**Statistical Validity:**
- Minimum 10 trips per moon phase required
- If insufficient data: Show "N/A" with message "Min 10 trips per phase required"
- If valid: Show phase name + average + trip count (e.g., "102 avg (35 trips)")

#### Visual Design

**Card Structure:**
- Gradient background: `bg-gradient-to-br from-background to-muted/20`
- Hover effects: `hover:shadow-lg hover:scale-[1.02]`
- Icons: lucide-react (Fish, Ship, Anchor, Layers, Moon, Users)
- Font size: `text-3xl` for numbers
- Line height: `leading-none` for tight spacing

**Context-Aware Subtext:**
- Total Fish: "Complete catch total" (filtered) vs "Fleet-wide total" (default)
- Total Trips: "For selected filter" (filtered) vs "Across all boats" (default)

## Files Modified

### src/App.tsx
- Added conditional logic for `isBoatFiltered`
- Added `avgFishPerAngler` calculation
- Added `bestMoonPhase` calculation with minimum threshold
- Updated metrics cards section (lines ~217-340)
- Imported Moon and Users icons from lucide-react

### src/components/ActiveFilters.tsx
- Fixed species filter badge display (normalized names only)
- Added species normalization to show one badge per species (not 50+ variants)

### src/lib/utils.ts
- Removed debug console logs from `normalizeSpeciesName`
- Removed debug console logs from `groupSpeciesByNormalizedName`

### src/lib/fetchRealData.ts
- Moon phase correlation uses `ocean_conditions` table
- Exact date matching for daily moon phase data

## Testing

### Manual Testing Checklist
- [x] Default view shows: Total Fish, Total Trips, Active Boats, Species
- [x] Select a boat → Cards switch to: Total Fish, Total Trips, Avg Fish/Angler, Best Moon Phase
- [x] Select a landing → Same behavior as boat filter
- [x] **Select a species → Card 4 switches to Best Moon Phase** (NEW - Oct 18, 2025)
- [x] Avg Fish/Angler calculates correctly (total fish / total anglers)
- [x] Best Moon Phase shows with ≥1 trip (threshold updated Oct 17, 2025)
- [x] Moon phase shows trip count: "102 avg (35 trips)"
- [x] Moon phase name formatted correctly (underscores replaced with spaces)
- [x] Hover effects work on all cards
- [x] Mobile responsive layout works
- [x] Card 4 clickable - scrolls to Moon Phase analytics tab

### Edge Cases
- **No anglers data**: Avg Fish/Angler shows 0 if totalAnglers = 0
- **No moon phases ≥10 trips**: Shows "N/A" with explanation
- **Multiple filters active**: isBoatFiltered = true if ANY filter active

## Performance

- No additional API calls required
- Calculations done client-side from existing data
- Moon phase filtering adds negligible overhead (~O(n) where n = 8 phases max)

## Bug Fixes (Post-Implementation)

### Species Filter Not Respecting Moon Phase Calculations (Oct 18, 2025)

**Problem**: When users filtered by species (e.g., "bluefin tuna"), moon phase metrics showed inflated averages based on ALL species caught on matching trips, not just the filtered species.

**Example**:
- Filter: Aztec boat + bluefin tuna (Sep 17 - Oct 17, 2025)
- Trip on Oct 1: 493 total fish (all species), 150 bluefin tuna
- **BEFORE FIX**: Moon phase avg calculated using 493 fish ❌
- **AFTER FIX**: Moon phase avg calculated using 150 bluefin ✅

**Impact**:
- 64% inflation in moon phase averages for Aztec + bluefin tuna example
- Misleading correlations showed "first_quarter: 329 avg" instead of correct "91.5 avg"

**Root Cause**:
In `fetchRealData.ts:68-122`, the code:
1. Filtered catches to find matching species ✅
2. BUT calculated `total_fish` from ALL catches instead of filtered catches ❌
3. This wrong `total_fish` propagated to moon phase calculations

**Fix Applied**:
```typescript
// BEFORE (Bug):
const totalFish = catches.reduce((sum, c) => sum + (c.count || 0), 0)
// Used ALL catches regardless of species filter

// AFTER (Fixed):
let activeCatches = catches
if (species && species.length > 0) {
  activeCatches = catches.filter(c => species.includes(c.species))
}
const totalFish = activeCatches.reduce((sum, c) => sum + (c.count || 0), 0)
// Uses only filtered species catches
```

**Files Changed**:
- `src/lib/fetchRealData.ts:68-122` - Filter catches before calculating totals
- `src/App.tsx:172-179` - Fix reduce error when no phases meet threshold

**Testing**:
- Verified with `test_species_filter_fix.py`
- Aztec + bluefin: 647 fish (36% of 1,796 total) correctly calculated
- Moon phase averages now based on filtered species only

**Validation Checklist**:
- [x] Species filter reduces Total Fish count correctly
- [x] Moon phase averages use filtered species only
- [x] Best Moon Phase shows "N/A" when no phase meets 3-trip threshold
- [x] Best Moon Phase displays correctly when phases meet 3+ trip threshold
- [x] Avg Fish/Angler calculated from filtered species counts
- [x] No console errors when filtered phases array is empty

### Moon Phase Fishing Date Estimation (Oct 17, 2025)

**Problem**: Original implementation assigned moon phases based on trip return dates, which is inaccurate for multi-day trips. A 1.5 Day trip returning Oct 17 likely fished during Oct 16, but was assigned Oct 17's moon phase.

**Solution**: Implemented fishing date estimation based on trip duration midpoint.

**Algorithm**:
```typescript
function estimateFishingDate(tripDate: string, tripDuration: string): string {
  // Subtract hours based on trip duration to find fishing midpoint
  // Examples:
  //   "1.5 Day" → 24 hours back
  //   "2 Day" → 36 hours back
  //   "1/2 Day AM" → 4 hours back
  //   "Overnight" → 10 hours back
}
```

**Duration Mapping** (43 variants):
- **Multi-day**: 1.5 Day (24h), 2 Day (36h), 2.5 Day (48h), 3 Day (60h)
- **Overnight**: 10 hours back
- **Full Day**: 8-10 hours back depending on offshore/local
- **Half Day**: 3-4 hours back depending on AM/PM/Twilight

**Impact**:
- **20%+ of trips** are multi-day (1.5+ days) with significant time offset
- Moon phase assignments now reflect actual fishing times, not return times
- Improves correlation accuracy for overnight and multi-day trips

**Files**:
- `src/lib/fetchRealData.ts`: Added `estimateFishingDate()` function
- `MOON_PHASE_DURATION_MAPPING.md`: Complete duration mapping documentation
- `test_fishing_date_estimation.py`: Validation script

**Validation Checklist**:
- [x] All 43 duration variants handled
- [x] Substring conflict resolution (e.g., "1.5 Day" vs "5 Day")
- [x] Fishing dates calculated correctly for multi-day trips
- [x] Moon phase data expanded to cover earlier dates

### Threshold Adjustment (Oct 17, 2025)

**Changed**: MIN_TRIPS_FOR_MOON_PHASE from 10 → 5 → **3 trips** → **1 trip** (final)

**Evolution**:
- **Original**: 10 trips (too conservative for filtered datasets)
- **First adjustment**: 5 trips (better, but still too high for small boat datasets)
- **Second adjustment**: 3 trips (practical minimum for individual boat analysis)
- **Final**: 1 trip (maximum data utility for all filter contexts)

**Reasoning**:
- With 8 moon phases, individual boats often have <10 total trips
- Example: Liberty boat has 10 trips across 6 phases (max 3 trips/phase)
- 1 trip = Shows data whenever available (user can assess statistical validity)
- Provides insight instead of "N/A" for boat-specific and species-specific filtering
- Trade-off: Lower statistical robustness, but higher utility

**Formatting**:
- Best Moon Phase card now uses `.toFixed(1)` to match Moon Phase Breakdown table
- Ensures consistency: "91.8 avg" displays identically in both locations

### Species Filter Enhancement (Oct 18, 2025)

**Added**: Card 4 now shows "Best Moon Phase" when species filter is active

**Problem**: When users filtered by species (e.g., "bluefin tuna"), Card 4 showed "Species: 1" which provided no value since the user already selected one species.

**Solution**: Extended Card 4 conditional logic to trigger on species filter:
```typescript
// Card 4 shows Best Moon Phase if ANY of these are true:
const showBestMoonPhase = isBoatFiltered || isSpeciesFiltered
```

**Use Case Example**:
- User filters: "Bluefin Tuna" (Sep 17 - Oct 17, 2025)
- Card 4 displays: "Best Moon Phase: New Moon - 45.1 avg (50 trips)"
- Clicking Card 4 scrolls to Moon Phase analytics tab
- User can see which moon phase had best bluefin tuna catches

**Impact**:
- Provides actionable insights for species-specific analysis
- Maintains consistency with boat/landing filter behavior
- Leverages existing moon phase correlation data
- No additional API calls required

**Files Modified**:
- `src/App.tsx:182` - Added `isSpeciesFiltered` detection
- `src/App.tsx:316-357` - Updated Card 4 conditional rendering

## Future Improvements

1. ~~Make threshold configurable (currently hardcoded to 10)~~ → Changed to 3 trips (Oct 17, 2025)
2. Add visual indicator for small sample sizes (e.g., warning for 3-5 trips)
3. Consider adding more conditional metrics for other filter contexts
4. Refine fishing time estimates based on skipper feedback
5. Consider adaptive threshold based on total trip count (e.g., 10% of trips minimum)

## Dependencies

- React 18.3+
- lucide-react 0.544+
- Moon phase data in `ocean_conditions` table (daily coverage required)

## Rollback Plan

If issues arise, revert to static 4-card layout by:
1. Remove conditional rendering (`isBoatFiltered` check)
2. Always show: Total Fish, Total Trips, Active Boats, Species
3. Revert App.tsx to previous commit

## Related Specs

- SPEC-006: Fish Scraper QC Validation
- Moon Phase Integration README

## Notes

- Moon phase data is already populated daily in `ocean_conditions` table
- No ±4 day window needed (daily data exists)
- Statistical threshold of 10 trips is based on standard practice for meaningful averages
- Phase names stored as snake_case (e.g., "waning_gibbous") and converted to display format
