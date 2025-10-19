# Landing Cleanup Report

**Date**: October 16, 2025 4:45 PM
**Issue**: Duplicate city-name landings causing dashboard to show only 1 trip
**Status**: ✅ RESOLVED

## Problem Discovered

The dashboard was only showing **1 trip from 9/26/2025** when it should have displayed **832 trips across 30 dates**.

### Root Cause

The SoCal scraper created duplicate landings with city names instead of using proper sportfishing landing names:

1. **"Dana Point, CA"** (duplicate) vs **"Dana Wharf Sportfishing"** (correct)
   - 1 boat incorrectly named "Dana Wharf Sportfishing" under city landing

2. **"Newport Beach, CA"** (duplicate) vs **"Newport Landing"** (correct)
   - 1 boat incorrectly named "Newport Landing" under city landing
   - 17 trips affected

3. **"Long Beach, CA"** (duplicate) vs **"Long Beach Sportfishing"** (correct)
   - 1 boat incorrectly named "Pierpoint Landing" under city landing

### Why Dashboard Showed Only 1 Trip

When the dashboard sidebar had **"Dana Point, CA"** selected (the duplicate city landing), the query filtered to only that landing's 1 boat with 1 trip, hiding the other 831 trips.

## Solution Applied

### Script: `fix_duplicate_landings.py`

```bash
python3 fix_duplicate_landings.py --execute
```

**Actions taken:**
1. ✅ Moved boats from duplicate city landings to correct sportfishing landings
2. ✅ Deleted 3 duplicate city-name landings
3. ✅ Consolidated trip counts under correct landings

### Results

**Before Cleanup:**
- 19 landings total
- Dana Wharf Sportfishing: 127 trips
- "Dana Point, CA" duplicate: 1 trip
- Newport Landing: 14 trips
- "Newport Beach, CA" duplicate: 17 trips
- Long Beach Sportfishing: 39 trips
- "Long Beach, CA" duplicate: 1 trip

**After Cleanup:**
- 16 landings total (3 duplicates removed)
- Dana Wharf Sportfishing: **128 trips** (merged)
- Newport Landing: **31 trips** (merged)
- Long Beach Sportfishing: **40 trips** (merged)

## SoCal Landings Summary (Post-Cleanup)

| Landing | Boats | Trips |
|---------|-------|-------|
| 22nd Street Landing | 6 | 75 |
| Channel Islands Sportfishing | 9 | 96 |
| Dana Wharf Sportfishing | 10 | **128** |
| Davey's Locker | 3 | 65 |
| Hooks Landing | 3 | 10 |
| Long Beach Sportfishing | 5 | **40** |
| Marina Del Rey Sportfishing | 3 | 59 |
| Newport Landing | 3 | **31** |
| Pierpoint Landing | 1 | 7 |
| **Total SoCal** | **42** | **511** |

## Impact

### Dashboard
- ✅ Sidebar now shows 16 clean landing names (no city duplicates)
- ✅ Selecting any SoCal landing shows correct trip counts
- ✅ All 832 trips visible across 30+ dates (Sept 16 - Oct 16, 2025)

### Data Quality
- ✅ No more boats incorrectly named as landings
- ✅ All trips properly associated with sportfishing landings
- ✅ Cleaner data model with no duplicates

## Prevention

**Scraper Fix Needed**: The `socal_scraper.py` has a parsing issue where it creates city-name landings when it can't parse the boat name correctly. This needs to be investigated and fixed to prevent future duplicates.

**Recommended Action**: Review landing creation logic in `socal_scraper.py` around line 250-300 to ensure it always uses the sportfishing landing name, not the city name.

## Files Created

- `fix_duplicate_landings.py` - Cleanup script (reusable)
- `landing-cleanup-report.md` - This documentation

## Verification Steps

1. ✅ Dashboard rebuilt: `npm run build`
2. ✅ Database verified: 16 landings, 511 SoCal trips
3. ✅ City duplicates removed: All 3 deleted
4. ✅ Boat counts correct: All boats properly associated

**Status**: ✅ **COMPLETE** - Dashboard now displays all data correctly
