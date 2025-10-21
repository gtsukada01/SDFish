# SPEC-011: Analytics Drilldown - Testing Checklist

**Status**: Ready for QA
**Build**: October 20, 2025
**Test URL**: http://localhost:3002

---

## Pre-Testing Setup

1. **Start Dashboard Server:**
   ```bash
   cd /Users/btsukada/Desktop/Fishing/fish-scraper
   python3 -m http.server 3002
   ```

2. **Verify Real Data Mode:**
   - Open http://localhost:3002
   - Confirm data loads (should see catch records in table)
   - Verify Analytics & Insights section appears below table

3. **Test Data:**
   - Use default date range (last 30 days)
   - Should have multiple boats and species to test drilldown

---

## Test Suite 1: Boats Tab Drilldown

### Test 1.1: Basic Boat Click
**Steps:**
1. Navigate to Analytics & Insights section
2. Click "Boats" tab (should be selected by default)
3. Identify a boat in the bar chart (e.g., "Dolphin")
4. Click the boat's bar

**Expected Results:**
- [ ] Table scrolls into view smoothly
- [ ] Table filters to show only trips for that boat
- [ ] Active Filters section shows "Boat: [BoatName]" badge
- [ ] Bar chart shows selected boat with ring-2 border
- [ ] Bar chart shows selected boat with light background (bg-accent/30)
- [ ] Console shows: `[Analytics Drilldown] Boat clicked: [BoatName]`

**Verify Data Accuracy:**
- [ ] All trips in table match the selected boat name
- [ ] Trip count in table matches bar chart trip count

### Test 1.2: Boat Visual Feedback
**Steps:**
1. With boat selected from Test 1.1
2. Hover over other (non-selected) boats

**Expected Results:**
- [ ] Selected boat maintains ring-2 border + background
- [ ] Non-selected boats show hover effect (bg-accent/50)
- [ ] Cursor shows pointer on all boats
- [ ] Visual hierarchy clear: selected > hover > default

### Test 1.3: Clear Boat Filter via Badge
**Steps:**
1. With boat selected, locate "Boat: [Name]" badge in Active Filters
2. Click the (x) button on the badge

**Expected Results:**
- [ ] Boat filter cleared
- [ ] Table shows all boats again
- [ ] Badge disappears from Active Filters
- [ ] Bar chart no longer shows selected state (no ring/background)

### Test 1.4: Switch Between Boats
**Steps:**
1. Click boat "Dolphin" bar
2. Click boat "Polaris Supreme" bar

**Expected Results:**
- [ ] Table updates to show only Polaris Supreme trips
- [ ] Active Filters updates: "Boat: Polaris Supreme"
- [ ] Only Polaris Supreme bar shows selected styling
- [ ] Dolphin bar loses selected styling

### Test 1.5: Keyboard Accessibility
**Steps:**
1. Click on page, then press Tab key repeatedly
2. Navigate to a boat bar in the breakdown
3. Press Enter or Space key

**Expected Results:**
- [ ] Can tab to boat bars (focus visible)
- [ ] Enter key triggers boat filter
- [ ] Space key triggers boat filter
- [ ] Same behavior as mouse click

---

## Test Suite 2: Species Tab Drilldown

### Test 2.1: Basic Species Click
**Steps:**
1. Navigate to Analytics & Insights section
2. Click "Species" tab
3. Identify a species in the bar chart (e.g., "Yellowtail")
4. Click the species bar

**Expected Results:**
- [ ] Table scrolls into view smoothly
- [ ] Table filters to show only trips that caught that species
- [ ] Active Filters shows "Species: [SpeciesName]" badge
- [ ] Bar chart shows selected species with ring-2 border
- [ ] Console shows: `[Analytics Drilldown] Species clicked: [Name] → [Normalized]`

**Verify Data Accuracy:**
- [ ] All trips in table contain the selected species
- [ ] Fish count in table matches bar chart count

### Test 2.2: Species Normalization
**Steps:**
1. Look for species with weight qualifiers in bar chart
   - Example: "Bluefin Tuna (up to 50 pounds)"
2. Click that species bar

**Expected Results:**
- [ ] Console shows normalized name: "Bluefin Tuna (up to 50 pounds)" → "Bluefin Tuna"
- [ ] Active Filters badge shows normalized name: "Species: Bluefin Tuna"
- [ ] Table shows all trips with any Bluefin Tuna variants
- [ ] Selected bar styling applies to clicked bar

### Test 2.3: Clear Species Filter via Badge
**Steps:**
1. With species selected, locate "Species: [Name]" badge
2. Click the (x) button

**Expected Results:**
- [ ] Species filter cleared
- [ ] Table shows all species again
- [ ] Badge disappears
- [ ] Bar chart no longer shows selected state

### Test 2.4: Switch Between Species
**Steps:**
1. Click "Yellowtail" bar
2. Click "Bluefin Tuna" bar

**Expected Results:**
- [ ] Table updates to show only Bluefin Tuna trips
- [ ] Active Filters updates: "Species: Bluefin Tuna"
- [ ] Only Bluefin Tuna bar shows selected styling
- [ ] Yellowtail bar loses selected styling

---

## Test Suite 3: Filter Combinations

### Test 3.1: Landing + Boat Drilldown
**Steps:**
1. Select a landing from sidebar (e.g., "H&M Landing")
2. Navigate to Boats tab in Analytics
3. Click a boat bar

**Expected Results:**
- [ ] Both filters active: Landing + Boat
- [ ] Active Filters shows both badges
- [ ] Table shows only trips matching BOTH filters
- [ ] Correct trip count (intersection, not union)

### Test 3.2: Date Range + Species Drilldown
**Steps:**
1. Change date range in header filters
2. Navigate to Species tab
3. Click a species bar

**Expected Results:**
- [ ] Both filters active
- [ ] Active Filters shows date range + species
- [ ] Table respects both filters

### Test 3.3: Boat Dropdown → Bar Click Override
**Steps:**
1. Use boat dropdown filter in header to select "Dolphin"
2. Navigate to Boats tab
3. Click "Polaris Supreme" bar

**Expected Results:**
- [ ] Bar click REPLACES dropdown selection
- [ ] Active Filters shows "Boat: Polaris Supreme" (not Dolphin)
- [ ] Table shows only Polaris Supreme trips

### Test 3.4: Species Dropdown → Bar Click Override
**Steps:**
1. Use species dropdown to select multiple species
2. Navigate to Species tab
3. Click a single species bar

**Expected Results:**
- [ ] Bar click REPLACES multi-select
- [ ] Active Filters shows only clicked species
- [ ] Table filtered to single species

### Test 3.5: Clear All Filters
**Steps:**
1. Set up multiple filters: landing, boat, species
2. Click drilldown bars to add more filters
3. Click "Clear All" in Active Filters

**Expected Results:**
- [ ] All filters cleared (including drilldown selections)
- [ ] Table shows all trips (reset to default)
- [ ] All badges disappear
- [ ] Bar charts show no selected state
- [ ] Date range resets to last 30 days

---

## Test Suite 4: Moon Phase Tab (No Drilldown - Phase 1)

### Test 4.1: Moon Tab Unchanged
**Steps:**
1. Navigate to Moon tab
2. Click moon phase bars

**Expected Results:**
- [ ] No click handler active (cursor remains default)
- [ ] No filter changes
- [ ] No hover effects
- [ ] Bars not interactive (expected for Phase 1)

---

## Test Suite 5: Edge Cases

### Test 5.1: Bar with 0 Trips
**Steps:**
1. Look for boat/species with very few trips
2. Click that bar
3. Apply additional filters to potentially reach 0 results

**Expected Results:**
- [ ] Filter applies correctly
- [ ] Table shows "No results." message (graceful empty state)
- [ ] Active filter badge still visible
- [ ] Can clear filter to restore data

### Test 5.2: Rapid Clicking
**Steps:**
1. Rapidly click different boat bars in succession

**Expected Results:**
- [ ] No UI freezing or errors
- [ ] Final clicked bar wins (shows correct filter)
- [ ] Table updates correctly to last clicked boat
- [ ] No duplicate API calls (useEffect debounce)

### Test 5.3: Mobile Touch Interaction
**Steps:**
1. Open dashboard on mobile device or resize browser to mobile width
2. Navigate to Analytics section
3. Tap boat/species bars

**Expected Results:**
- [ ] Tap triggers drilldown (not just hover)
- [ ] Touch targets adequate (bars easy to tap)
- [ ] Scroll behavior works on mobile
- [ ] No double-tap required

### Test 5.4: Metric Card Click + Bar Drilldown
**Steps:**
1. Click "Catch" metric card (navigates to Species tab)
2. Click a species bar

**Expected Results:**
- [ ] Smooth navigation: card → tab → drilldown
- [ ] No conflicts between navigation mechanisms
- [ ] Table scrolls correctly

---

## Test Suite 6: Console Logging (Debug Verification)

### Test 6.1: Boat Click Logging
**Steps:**
1. Open browser DevTools (F12) → Console tab
2. Click a boat bar

**Expected:**
```
[Analytics Drilldown] Boat clicked: Dolphin
```

### Test 6.2: Species Click Logging
**Steps:**
1. Console open
2. Click a species bar (preferably one with qualifiers)

**Expected:**
```
[Analytics Drilldown] Species clicked: Bluefin Tuna (up to 50 pounds) → Bluefin Tuna
```

---

## Browser Compatibility (Optional Smoke Test)

**Browsers to Test:**
- [ ] Chrome/Chromium (primary)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

**Per Browser:**
- [ ] Bar click works
- [ ] Visual styling renders correctly
- [ ] Keyboard navigation works (desktop)
- [ ] Touch interaction works (mobile)

---

## Performance Verification

### Test P1: Scroll Smoothness
**Steps:**
1. Click bar drilldown
2. Observe scroll to table

**Expected:**
- [ ] Smooth scroll animation (no jumps)
- [ ] Scroll completes in <500ms
- [ ] Table visible after scroll

### Test P2: Filter Update Speed
**Steps:**
1. Click bar
2. Measure time until table updates

**Expected:**
- [ ] Filter state update immediate (<100ms)
- [ ] Table data fetch/update <2s
- [ ] No visible lag in UI

---

## Regression Testing (Existing Features)

**Verify drilldown doesn't break existing functionality:**

- [ ] Header filters still work independently
- [ ] Active Filters badges work for all filter types
- [ ] Pagination still functions correctly
- [ ] Table sorting still works
- [ ] Mobile sidebar navigation unaffected
- [ ] Metric cards still navigate to tabs
- [ ] Date picker still functions

---

## Sign-Off Criteria

**Must Pass All:**
- ✅ All Test Suite 1 (Boats) tests pass
- ✅ All Test Suite 2 (Species) tests pass
- ✅ All Test Suite 3 (Filter Combinations) tests pass
- ✅ No console errors
- ✅ No broken existing features (regression tests pass)

**Nice to Have:**
- ✅ Browser compatibility confirmed
- ✅ Performance benchmarks met
- ✅ Mobile testing completed

---

## Known Limitations (Phase 1)

1. **Moon Phase**: No drilldown in Phase 1 (requires backend API update)
2. **Multi-Select**: Bar click = single-select only (use dropdowns for multi)
3. **Toggle Behavior**: Bar click doesn't toggle off (use badge (x) to clear)
4. **Deep Linking**: Drilldown state not in URL (Phase 3 feature)

---

**Testing Status**: [ ] Not Started | [ ] In Progress | [ ] Complete

**Tested By**: _______________

**Date**: _______________

**Issues Found**: (List below or link to issue tracker)
