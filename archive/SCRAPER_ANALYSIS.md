# SD Fish Scraper - Deep Analysis & Implementation Plan

**Date**: October 15, 2025
**Status**: Research Complete - Ready for Team Review
**Database Status**: 7,746 trips | Latest: 2025-09-23 | **22 days behind**

---

## 🎯 Executive Summary

### Current Situation
- **Database**: 7,746 trips through Sept 23, 2025
- **Missing Data**: Sept 24 - Oct 15 (22 days)
- **Estimated Work**: ~220 trips to scrape

### Data Source Options

#### Option 1: Dock Totals (Aggregate Data) ❌ NOT COMPATIBLE
**URL**: `https://www.sandiegofishreports.com/dock_totals/index.php?date=YYYY-MM-DD`

**Structure**:
```
Landing: Fisherman's Landing
Boats: 3 Boats / 4 Trips
Anglers: 102 Anglers
Dock Totals: 165 Rockfish, 76 Bluefin Tuna (up to 180 pounds), 46 Sculpin...
```

**Problem**: This is **aggregated by landing**, but our database needs **individual trips by boat**.

**Database Schema Requires**:
- Individual boat ID
- Individual trip date + duration
- Individual angler count per trip
- Individual catches per trip

**Conclusion**: ❌ **Cannot use** - data granularity mismatch

#### Option 2: Individual Fish Reports (Trip-Level Data) ✅ REQUIRED
**URL**: `https://www.sandiegofishreports.com/fish_reports/saltwater.php`

**Structure**: Individual trip reports with:
- Specific boat name
- Trip date
- Trip duration (1.5-day, 2-day, etc.)
- Angler count
- Detailed catches by species

**Status**: Initial scraper written but **HTML parsing needs fixing**

---

## 🔍 Technical Analysis

### Database Schema (Validated)
```sql
landings (id, name)
    ↓
boats (id, name, landing_id)
    ↓
trips (id, boat_id, trip_date, trip_duration, anglers)
    ↓
catches (id, trip_id, species, count)
```

### Data Requirements
1. ✅ **Boat identification** - Individual boat name
2. ✅ **Landing association** - Which landing the boat operates from
3. ✅ **Trip specifics** - Date, duration (in days), angler count
4. ✅ **Catch details** - Species name + count per trip

### Current Scraper Status

**Files Created**:
- ✅ `sd_fish_scraper.py` - Main scraper (needs HTML parser fix)
- ✅ `check_scraper_status.py` - Database status checker (working)
- ✅ `validate_data.py` - Data integrity validator (working)
- ✅ `requirements.txt` - Python dependencies (installed)
- ✅ `SCRAPER_DOCS.md` - Comprehensive documentation

**Test Results**:
```
2025-10-15 19:24:56 - INFO - ✅ Successfully fetched 52508 bytes
2025-10-15 19:24:56 - INFO - ✅ Parsed 0 reports from page
2025-10-15 19:24:56 - WARNING - ⚠️  No reports found on page 1, stopping
```

**Issue**: HTML parser found 0 reports - need to investigate actual page structure

---

## 🛠️ Next Steps (Priority Order)

### CRITICAL PATH

#### Step 1: Debug HTML Parser (30 min)
**Task**: Use Chrome DevTools to inspect actual saltwater reports page structure

**Commands**:
```bash
# Inspect live page
python3 inspect_page.py

# Or manually test parsing
python3 -c "
import requests
from bs4 import BeautifulSoup
html = requests.get('https://www.sandiegofishreports.com/fish_reports/saltwater.php').text
soup = BeautifulSoup(html, 'lxml')
print(soup.prettify()[:5000])
"
```

**Expected Fix**: Update `parse_report_page()` function with correct CSS selectors

#### Step 2: Test Scraper (15 min)
```bash
# Dry run test (2 pages)
python3 sd_fish_scraper.py --start-date 2025-09-22 --dry-run --max-pages 2

# Verify parsing works
tail -50 scraper.log
```

**Success Criteria**: Should see "Parsed X reports from page"

#### Step 3: Small Production Run (10 min)
```bash
# Scrape 1 week of data
python3 sd_fish_scraper.py --start-date 2025-10-08 --max-pages 10

# Verify insertions
python3 check_scraper_status.py
```

**Success Criteria**: Database shows new trips after 2025-09-23

#### Step 4: Full Update (25 min)
```bash
# Scrape all missing dates (Sept 22 - Oct 15)
python3 sd_fish_scraper.py --start-date 2025-09-22

# Validate data quality
python3 validate_data.py
```

**Estimated Time**: ~22 minutes at 10 trips/min (220 trips × 2-5 sec delays)

---

## 📊 Performance Metrics

### Current Configuration
- **Delays**: 2-5 seconds between requests (optimized for speed + quality)
- **Retry Logic**: 3 attempts with exponential backoff (5s, 10s, 15s)
- **Timeout**: 30 seconds per request
- **Expected Speed**: ~10-15 trips per minute

### Estimated Scraping Times
| Trips | Time Estimate |
|-------|---------------|
| 10    | ~1 minute     |
| 50    | ~5 minutes    |
| 100   | ~10 minutes   |
| 220   | ~22 minutes   |

---

## 🚨 Risk Assessment

### Technical Risks

#### Risk 1: HTML Structure Changes ⚠️ MEDIUM
**Impact**: Parser fails to extract data
**Mitigation**:
- Comprehensive error logging
- Dry-run testing before production
- Fallback to manual inspection

#### Risk 2: IP Blocking 🟢 LOW
**Impact**: Server blocks our IP
**Mitigation**:
- 2-5 second delays (respectful)
- Browser-like User-Agent
- Automatic retry with backoff

#### Risk 3: Duplicate Data 🟢 LOW
**Impact**: Same trip inserted twice
**Mitigation**:
- Database unique constraint on (boat_id, trip_date, trip_duration)
- Scraper checks for existing trips before insertion
- Logs all skipped duplicates

#### Risk 4: Data Quality Issues ⚠️ MEDIUM
**Impact**: Incorrect species names, counts, dates
**Mitigation**:
- Regex validation for species/counts
- Date parsing with multiple formats
- `validate_data.py` catches anomalies post-scrape

---

## 🧪 Testing Strategy

### Phase 1: Parser Validation
```bash
# Test HTML parsing
python3 -c "
from sd_fish_scraper import fetch_page, parse_report_page
import requests
session = requests.Session()
html = fetch_page('https://www.sandiegofishreports.com/fish_reports/saltwater.php', session)
reports = parse_report_page(html)
print(f'Found {len(reports)} reports')
print(reports[0] if reports else 'No reports found')
"
```

### Phase 2: Dry Run
```bash
python3 sd_fish_scraper.py --start-date 2025-10-10 --dry-run --max-pages 1
```

**Check Logs**:
- ✅ Reports parsed correctly
- ✅ Species names extracted
- ✅ Counts are numeric
- ✅ Dates parsed correctly
- ✅ Landing/boat names normalized

### Phase 3: Small Production Test
```bash
# Insert 10-20 trips
python3 sd_fish_scraper.py --start-date 2025-10-12 --max-pages 2

# Verify in database
python3 -c "
from sd_fish_scraper import init_supabase
supabase = init_supabase()
trips = supabase.table('trips').select('*').gte('trip_date', '2025-10-12').execute()
print(f'Inserted {len(trips.data)} trips')
for trip in trips.data[:3]:
    print(f'  - Trip {trip[\"id\"]}: {trip[\"trip_date\"]}')
"
```

### Phase 4: Data Validation
```bash
python3 validate_data.py
```

**Expected Output**:
- ✅ All foreign keys valid
- ✅ No orphaned records
- ✅ All catches have counts > 0
- ✅ All trips have valid dates

---

## 📋 Team Review Checklist

### Before Proceeding
- [ ] Review scraper code (`sd_fish_scraper.py`)
- [ ] Understand database schema and constraints
- [ ] Verify dock_totals incompatibility reasoning
- [ ] Approve 2-5 second delay configuration
- [ ] Review error handling strategy

### Implementation Sign-Off
- [ ] HTML parser debugged and tested
- [ ] Dry run successful (logs reviewed)
- [ ] Small production test passed
- [ ] Data validation clean
- [ ] Ready for full 22-day backfill

### Post-Scrape Validation
- [ ] `check_scraper_status.py` shows current date
- [ ] `validate_data.py` passes all tests
- [ ] Dashboard shows new data (`npm start`)
- [ ] No duplicate trips in database

---

## 💡 Alternative Approaches (For Discussion)

### Alternative 1: Hybrid Approach
**Idea**: Use dock_totals for date validation, then scrape individual reports

**Pros**:
- Quickly identify which dates have data
- Reduce unnecessary scraping

**Cons**:
- More complex workflow
- Still need individual report parsing

**Recommendation**: ⚠️ Nice-to-have but not critical

### Alternative 2: Manual Data Entry
**Idea**: Manually enter the 22 days of missing data

**Pros**:
- No scraping needed
- Complete control over data quality

**Cons**:
- Time-consuming (~2-3 hours)
- Error-prone
- Not sustainable for ongoing updates

**Recommendation**: ❌ Not recommended

### Alternative 3: Use Different Data Source
**Idea**: Find API or structured data feed

**Pros**:
- More reliable than web scraping
- Easier to maintain

**Cons**:
- No known API for sandiegofishreports.com
- May not have historical data

**Recommendation**: ⚠️ Investigate for future, but not viable now

---

## 📞 Questions for Team

1. **Scraping Strategy**: Approve proceeding with individual fish reports scraping?
2. **Delay Configuration**: Is 2-5 seconds acceptable, or should we be more/less aggressive?
3. **Data Quality**: What's the acceptable error rate for species/count parsing?
4. **Ongoing Updates**: Should we set up automated weekly/daily scraping?
5. **Monitoring**: Do we need alerts when scraper fails or data is stale?

---

## 🎓 Key Learnings

### What We Know
1. **Database is 22 days behind** - significant but manageable gap
2. **Dock totals are not usable** - wrong data granularity
3. **Individual reports are required** - only source with trip-level data
4. **HTML structure needs fixing** - parser currently fails
5. **Infrastructure is ready** - database, helpers, docs all complete

### What We Need
1. **30 minutes of debugging** - fix HTML parser
2. **Team approval** - proceed with scraping strategy
3. **20-30 minutes of runtime** - to backfill 22 days

### Success Criteria
- ✅ Database shows trips through Oct 15, 2025
- ✅ No data quality issues in validation
- ✅ Dashboard displays updated data
- ✅ Documentation reflects final approach

---

**Ready for team review and sign-off!** 🚀

*Last Updated: October 15, 2025*
