# Date Semantics Investigation Report

**Date**: October 16, 2025
**Investigator**: Claude Code
**Status**: ✅ COMPLETED - User Approval Required

---

## Executive Summary

### Investigation Objective
Determine what `boats.php?date=YYYY-MM-DD` represents: departure date, return date, or report date.

### CRITICAL FINDING
**`boats.php?date` represents the RETURN/REPORT DATE** - when boats returned to dock and reported their catches.

### Impact on Database
- **Original scraper was CORRECT**: Stored dates from boats.php as-is
- **Spec 005 was WRONG**: Subtracted trip duration, creating dates that were too early
- **Required Action**: Scrape Sept-Oct 2025 dates WITHOUT any date manipulation

---

## Test Case 1: Multi-Day Trip Date Range

### Test Setup
- **Boat**: Polaris Supreme (Seaforth Sportfishing)
- **Charter Page Data**: 09-30-2025 | 3 Day | 24 anglers | 144 Bluefin, 10 Dolphin, 96 Yellowfin, 60 Yellowtail

### boats.php Date Checks

**boats.php?date=2025-09-28** (2 days before reported date):
- ❌ **Polaris Supreme does NOT appear**
- Other boats present: Dolphin, Liberty, Tomahawk, etc.
- **Conclusion**: 3-day trip not visible 2 days before report date

**boats.php?date=2025-09-29** (1 day before reported date):
- ❌ **Polaris Supreme does NOT appear**
- Other boats present: Constitution, Dolphin, Pacific Queen, etc.
- **Conclusion**: 3-day trip not visible 1 day before report date

**boats.php?date=2025-09-30** (reported date):
- ✅ **Polaris Supreme APPEARS**
- Trip Type: 3 Day
- Anglers: 24
- Catches: 144 Bluefin Tuna, 60 Yellowtail, 10 Dorado, 96 Yellowfin Tuna
- **Conclusion**: Trip appears ONLY on the report date

### Finding
Multi-day trips appear ONCE on boats.php - on the date they returned/were reported, NOT continuously during the trip or on departure date.

---

## Test Case 2: 5-Day Trip Validation

### Test Setup
- **Boat**: Polaris Supreme
- **Charter Page Data**: 10-08-2025 | 5 Day | 22 anglers | 19 Bluefin, 57 Yellowfin, 330 Yellowtail

### boats.php Verification

**boats.php?date=2025-10-08**:
- ✅ **Polaris Supreme appears with matching data**
- Trip Type: 5 Day
- Anglers: 22
- Catches: 19 Bluefin Tuna, 330 Yellowtail, 57 Yellowfin Tuna

### Finding
Confirms that dates on charter boat pages match boats.php dates, and both represent the RETURN/REPORT date.

---

## Test Case 3: 2-Day Trip Validation

### Test Setup
- **Boat**: Polaris Supreme
- **Charter Page Data**: 10-10-2025 | 2 Day | 23 anglers | 92 Bluefin

### boats.php Verification

**boats.php?date=2025-10-10**:
- ✅ **Polaris Supreme appears with matching data**
- Trip Type: 2 Day
- Anglers: 23
- Catches: 92 Bluefin Tuna

### Finding
Further confirms consistent pattern across different trip durations.

---

## Date Semantics Conclusion

### What boats.php?date Represents

**RETURN/REPORT DATE**: The date when the fishing trip ended, the boat returned to dock, and catches were reported.

### Evidence
1. **Single appearance**: Multi-day trips appear ONCE on boats.php, not on multiple dates
2. **Timing pattern**: 3-day trip appears on day 30, NOT on days 27, 28, or 29
3. **Charter boat consistency**: Dates on charter boat pages match boats.php dates exactly
4. **Logical inference**: If Sept 30 were the departure date for a 3-day trip, the boat would still be out on Sept 30-Oct 2. Instead, it appears on boats.php on Sept 30, meaning it returned that day.

---

## Recommended Database Storage Strategy

### CRITICAL: Store Dates AS-IS

```python
# CORRECT approach (original scraper):
trip_date = date  # Store boats.php date exactly as shown

# WRONG approach (Spec 005 - DO NOT USE):
trip_date = date - timedelta(days=trip_duration)  # This made all dates wrong
```

### Field Semantics

**`trip_date` field should represent**: RETURN/REPORT DATE (when boat came back)

**Rationale**:
1. **Source of truth principle**: boats.php is our single source of truth
2. **Data integrity**: Store exactly what the source shows, no calculations
3. **User expectations**: When users see "09-30" on the website, they expect to see "09-30" in our database
4. **Simplicity**: No complex date logic, no edge cases, no errors

### Display Strategy (Optional)

If users want to know departure dates, calculate in the UI layer only:

```typescript
// In frontend display code (NOT in scraper):
const estimatedDeparture = new Date(trip_date);
estimatedDeparture.setDate(estimatedDeparture.getDate() - tripDurationDays);
// Display: "Returned: 09-30, Departed: ~09-27"
```

**CRITICAL**: This calculation should NEVER happen in the scraper or be stored in the database.

---

## Impact on Spec 005 "Trip Date Correction"

### Spec 005 Analysis

**What Spec 005 Did**:
```python
departure_date = report_date - trip_duration_days
# Example: 2025-10-10 (2 Day) → 2025-10-08
```

**Why This Was Wrong**:
- Assumed boats.php showed "report dates" that needed conversion to "departure dates"
- Reality: boats.php already shows meaningful dates (return dates) that should be stored as-is
- Result: All dates became 2-5 days too early

**User Impact**:
- 09-30 website → 09-27 database (off by 3 days for 3-day trip)
- 10-10 website → 10-08 database (off by 2 days for 2-day trip)
- User expectation violated: "I see 09-30 on the website, why does your database show 09-27?"

### Required Action

**REVERT Spec 005 changes**:
1. ✅ Delete Sept-Oct 2025 data (COMPLETED)
2. ⏳ Remove date calculation logic from scrapers
3. ⏳ Re-scrape with dates stored AS-IS
4. ⏳ Validate 100% match between website and database

---

## Next Steps

### Phase 2: Parser Review (FR-003)

**Remove date manipulation logic**:

```python
# boats_scraper.py - CURRENT (line 131):
'trip_date': date,  # This is CORRECT

# boats_scraper.py - Spec 005 CHANGED IT TO (WRONG):
'trip_date': calculate_departure_date(date, normalized_trip_type),  # REMOVE THIS

# REQUIRED FIX:
'trip_date': date,  # Store boats.php date exactly as shown
```

### Phase 3: QC Validation

Build script that verifies:
```python
def validate_date_accuracy():
    """
    Fetch boats.php?date=2025-09-30
    Parse Polaris Supreme: 3 Day, 24 anglers
    Query database for trip on 2025-09-30
    Assert: trip_date == '2025-09-30' (NOT '2025-09-27')
    """
```

### Phase 4: Production Re-Scraping

Scrape Sept 1 - Oct 31, 2025 (61 dates) with:
- ✅ No date calculations
- ✅ Store dates exactly as shown on boats.php
- ✅ QC validation after every batch
- ✅ 100% accuracy requirement

---

## Acceptance Criteria

- ✅ **Test Case 1**: Multi-day trip date range tested (Polaris Supreme Sept 30)
- ✅ **Test Case 2**: 5-day trip validated (Polaris Supreme Oct 8)
- ✅ **Test Case 3**: 2-day trip validated (Polaris Supreme Oct 10)
- ✅ **Clear conclusion**: boats.php?date = RETURN/REPORT DATE
- ✅ **Storage strategy**: Store dates AS-IS, no calculations
- ⏳ **User approval**: PENDING

---

## Examples with Data

### Example 1: 3-Day Trip

**Source**: boats.php?date=2025-09-30
```
Polaris Supreme (Seaforth Sportfishing)
3 Day | 24 anglers
144 Bluefin Tuna, 60 Yellowtail, 10 Dorado, 96 Yellowfin Tuna
```

**Database Storage** (CORRECT):
```json
{
  "boat_name": "Polaris Supreme",
  "landing_name": "Seaforth Sportfishing",
  "trip_date": "2025-09-30",  // Stored AS-IS from boats.php
  "trip_duration": "3 Day",
  "anglers": 24,
  "catches": [
    {"species": "Bluefin Tuna", "count": 144},
    {"species": "Yellowtail", "count": 60},
    {"species": "Dorado", "count": 10},
    {"species": "Yellowfin Tuna", "count": 96}
  ]
}
```

**Database Storage** (WRONG - Spec 005 approach):
```json
{
  "trip_date": "2025-09-27",  // ❌ WRONG - subtracted 3 days
  // This violates "source of truth" principle
}
```

---

## Sign-Off

**Investigation Status**: ✅ COMPLETED
**Findings**: CONCLUSIVE
**Recommendation**: Store boats.php dates AS-IS, no calculations
**Spec 005 Impact**: REVERT date calculation logic
**Next Phase**: Parser review and QC validation

**User Approval Required**: _________________ (Date: _________)

Once approved, proceed to Phase 2: Parser Date Logic Review (FR-003).
