# Moon Phase Duration Mapping Analysis

**Date**: 2025-10-18 (Updated after normalization)
**Purpose**: Map trip durations to estimated fishing midpoint times for accurate moon phase correlation

## Database Analysis Results

**Total Trips**: 7,841
**Unique Duration Strings**: 20 (normalized from 43 on Oct 18, 2025)

**Normalization Summary**:
- Removed geographic qualifiers (Local, Coronado Islands, Mexican Waters, Offshore, Islands)
- Consolidated duplicate trip types (e.g., "Reverse Overnight" → "Overnight")
- Consolidated "Extended 1.5 Day" → "1.75 Day"
- 311 trips updated with standardized duration values
- Zero data loss - all trips retain original meaning

## Top 10 Duration Types (87.8% of all trips)

| Duration | Count | % | Estimated Hours Back | Reasoning |
|----------|-------|---|---------------------|-----------|
| 1/2 Day AM | 2,248 | 28.67% | **4 hours** | 6am-12pm, midpoint ~9am (4 hrs before noon return) |
| Full Day | 1,246 | 15.89% | **8 hours** | 6am-6pm, midpoint ~noon (8 hrs before 8pm return) |
| 1/2 Day PM | 1,180 | 15.05% | **4 hours** | 12pm-6pm, midpoint ~3pm (4 hrs before 7pm return) |
| 1.5 Day | 705 | 8.99% | **24 hours** | Depart AM day 1, fish all day, return AM day 2 |
| 2 Day | 600 | 7.65% | **36 hours** | Depart AM day 1, fish 2 days, return evening day 2 |
| Overnight | 501 | 6.39% | **10 hours** | Depart evening, fish overnight, return morning |
| 1/2 Day Twilight | 365 | 4.66% | **3 hours** | 4pm-9pm, midpoint ~6:30pm (3 hrs before 9:30pm return) |
| 3/4 Day | 313 | 3.99% | **6 hours** | Extended day trip, 6am-4pm |
| 2.5 Day | 301 | 3.84% | **48 hours** | Depart AM, fish 2.5 days, return evening |
| 3 Day | 290 | 3.70% | **60 hours** | Depart AM, fish 3 days, return evening |

**Note**: After normalization (Oct 18, 2025), all geographic variants are consolidated into base categories.

## Complete Duration Mapping (All 20 Standardized Categories)

### Multi-Day Trips (2+ days)

```typescript
'5 Day': 96,           // 4 days before return (1 trip)
'4 Day': 84,           // 3.5 days before return (23 trips)
'3.5 Day': 72,         // 3 days before return (54 trips)
'3 Day': 60,           // 2.5 days before return (290 trips)
'2.5 Day': 48,         // 2 days before return (301 trips)
'2 Day': 36,           // 1.5 days before return (600 trips)
'1.75 Day': 30,        // ~1.25 days before return (2 trips)
'1.5 Day': 24,         // 1 day before return (705 trips)
```

### Overnight Trips

```typescript
'Overnight': 10,       // Evening depart, morning return (~10 hrs) (501 trips)
                       // Includes former "Reverse Overnight" (same duration)
```

### Full Day Trips

```typescript
'Full Day': 8,         // 6am-6pm, midpoint noon (1,246 trips)
                       // All geographic variants consolidated
```

### 3/4 Day Trips

```typescript
'3/4 Day': 6,          // 6am-4pm, midpoint 11am (313 trips)
                       // All geographic variants consolidated
```

### Half Day Trips

```typescript
'1/2 Day AM': 4,       // 6am-12pm, midpoint 9am (2,248 trips)
'1/2 Day PM': 4,       // 12pm-6pm, midpoint 3pm (1,180 trips)
'1/2 Day Twilight': 3, // 4pm-9pm, midpoint 6:30pm (365 trips)
```

### Hour-Based Trips

```typescript
'12 Hour': 6,          // Midpoint 6 hrs back (3 trips)
'10 Hour': 5,          // Midpoint 5 hrs back (1 trip)
'6 Hour': 3,           // Midpoint 3 hrs back (2 trips)
'4 Hour': 2,           // Midpoint 2 hrs back (4 trips)
'2 Hour': 1,           // Midpoint 1 hr back (1 trip)
```

### Special Cases

```typescript
'Lobster': 3,          // Crustacean fishing trip (1 trip)
```

**Total**: 20 standardized categories covering 7,841 trips

## Implementation Notes

### Pattern Matching Strategy (Post-Normalization)

After normalization (Oct 18, 2025), pattern matching is greatly simplified:

```typescript
// CRITICAL: Check fractional/decimal days FIRST to avoid substring conflicts
if (duration.includes('1/2 Day Twilight')) return 3
else if (duration.includes('1/2 Day AM')) return 4
else if (duration.includes('1/2 Day PM')) return 4
else if (duration.includes('3/4 Day')) return 6
else if (duration.includes('1.5 Day')) return 24
else if (duration.includes('1.75 Day')) return 30
else if (duration.includes('2.5 Day')) return 48
else if (duration.includes('3.5 Day')) return 72
else if (duration.includes('5 Day')) return 96
else if (duration.includes('4 Day')) return 84
else if (duration.includes('3 Day')) return 60
else if (duration.includes('2 Day')) return 36
else if (duration.includes('Overnight')) return 10
else if (duration.includes('Full Day')) return 8
else if (duration.includes('12 Hour')) return 6
else if (duration.includes('10 Hour')) return 5
else if (duration.includes('6 Hour')) return 3
else if (duration.includes('4 Hour')) return 2
else if (duration.includes('2 Hour')) return 1
else if (duration.includes('Lobster')) return 3
else return 6 // Default fallback
```

**Benefits of Normalization**:
- No need to handle geographic variants (already removed)
- No duplicate logic for similar trip types
- Cleaner codebase with 20 cases instead of 43
- Improved maintainability

### Edge Cases

1. **Unknown durations**
   - Default to **6 hours** (conservative mid-range estimate)
   - Should rarely occur after normalization

2. **Order matters**
   - Check decimal days (1.5, 1.75, etc.) before whole numbers to avoid substring conflicts

## Validation Metrics

After implementing this mapping, validate:

1. **Coverage**: % of trips with matched duration (target: >99%)
2. **Accuracy**: Spot-check sample trips for reasonable fishing time estimates
3. **Moon Phase Distribution**: Ensure phases are more evenly distributed across trip types

## Transparency Messaging

Add to UI:
```
"Moon phase based on estimated fishing midpoint
(calculated from trip duration, not return date)"
```

Add tooltip:
```
"Since fishing often occurs hours or days before returning to dock,
we estimate the actual fishing time based on trip duration.
Example: A 1.5 Day trip returning Oct 17 likely fished during Oct 16."
```

## Next Steps

1. ✅ Verify duration strings (COMPLETE - Oct 17, 2025)
2. ✅ **Normalize trip durations** (COMPLETE - Oct 18, 2025)
   - 43 variants → 20 standardized categories
   - 311 trips updated with zero data loss
   - See `normalize_trip_durations.py` for migration script
3. ✅ Update fishing date estimation logic (COMPLETE - Oct 18, 2025)
   - Updated `fetchRealData.ts` with simplified pattern matching
4. ⏳ Add transparency messaging to UI
5. ⏳ Test correlation improvements with normalized durations
6. ⏳ Update SPEC-007 documentation
