# 2024 SoCal Complete Backfill Project

**Status**: 🟡 IN PROGRESS
**Objective**: Scrape and validate ALL 2024 SoCal fishing data (366 dates)
**Expected**: ~6,000 trips based on 2025 patterns

## 📊 Current Progress

| Quarter | Dates | Status | Trips | QC Pass Rate |
|---------|-------|--------|-------|--------------|
| Q1 (Jan-Mar) | 91 days | ⬜ Not Started | - | - |
| Q2 (Apr-Jun) | 91 days | ⬜ Not Started | - | - |
| Q3 (Jul-Sep) | 92 days | ⬜ Not Started | - | - |
| Q4 (Oct-Dec) | 92 days | ⬜ Not Started | - | - |
| **Total** | **366 days** | **⬜ 0%** | **0** | **-** |

## 🚀 Execution Instructions

### Phase 1: Q1 2024 (Jan-Mar)
```bash
cd /Users/btsukada/Desktop/Fishing/fish-scraper
./2024-socal-backfill/scripts/scrape_q1.sh
```

**QC Validation**:
```bash
python3 scripts/python/socal_qc_validator.py \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --output 2024-socal-backfill/logs/qc_q1.json
```

**Expected**: ~800 trips | **Runtime**: ~3 hours

---

### Phase 2: Q2 2024 (Apr-Jun)
```bash
./2024-socal-backfill/scripts/scrape_q2.sh
```

**QC Validation**:
```bash
python3 scripts/python/socal_qc_validator.py \
  --start-date 2024-04-01 \
  --end-date 2024-06-30 \
  --output 2024-socal-backfill/logs/qc_q2.json
```

**Expected**: ~1,800 trips (PEAK SEASON) | **Runtime**: ~3.5 hours

---

### Phase 3: Q3 2024 (Jul-Sep)
```bash
./2024-socal-backfill/scripts/scrape_q3.sh
```

**QC Validation**:
```bash
python3 scripts/python/socal_qc_validator.py \
  --start-date 2024-07-01 \
  --end-date 2024-09-30 \
  --output 2024-socal-backfill/logs/qc_q3.json
```

**Expected**: ~1,900 trips (PEAK SEASON) | **Runtime**: ~3.5 hours

---

### Phase 4: Q4 2024 (Oct-Dec)
```bash
./2024-socal-backfill/scripts/scrape_q4.sh
```

**QC Validation**:
```bash
python3 scripts/python/socal_qc_validator.py \
  --start-date 2024-10-01 \
  --end-date 2024-12-31 \
  --output 2024-socal-backfill/logs/qc_q4.json
```

**Expected**: ~1,500 trips | **Runtime**: ~3.5 hours

---

### Phase 5: Final Validation
```bash
./2024-socal-backfill/scripts/qc_validate_all.sh
```

**Validates all 366 dates** end-to-end | **Target**: 100% pass rate

## 🔧 Error Recovery

If QC validation shows failures:

1. **Check which dates failed**:
   ```bash
   cat 2024-socal-backfill/logs/qc_q1.json | jq '.failed_dates[]'
   ```

2. **Delete trips for failed dates**:
   ```sql
   -- Example for 2024-05-15
   DELETE FROM trips
   WHERE trip_date = '2024-05-15'
   AND boat_id IN (
     SELECT id FROM boats
     WHERE landing_id IN (
       SELECT id FROM landings WHERE source = 'socalfishreports'
     )
   );
   ```

3. **Re-scrape specific dates**:
   ```bash
   python3 socal_scraper.py --date 2024-05-15
   ```

4. **Re-validate**:
   ```bash
   python3 scripts/python/socal_qc_validator.py \
     --date 2024-05-15 \
     --output 2024-socal-backfill/logs/qc_retest.json
   ```

## ✅ Success Criteria

- ✅ All 366 dates scraped
- ✅ 100% QC pass rate (366/366 validated)
- ✅ ~6,000 total trips in database
- ✅ Zero data loss or corruption
- ✅ All weight label data properly captured

## 📝 Completion Checklist

When 100% QC validation achieved:

- [ ] Save final QC report: `cp logs/qc_2024_full.json ../../logs/`
- [ ] Update main README.md with 2024 SoCal completion
- [ ] Create COMPLETE.md with final statistics
- [ ] Optional: Archive project: `tar -czf ../../archive/2024-socal-backfill-COMPLETE.tar.gz .`
- [ ] Delete project directory: `cd ../.. && rm -rf 2024-socal-backfill/`

## 📁 Directory Structure

```
2024-socal-backfill/
├── scripts/
│   ├── scrape_q1.sh        ✅ Ready
│   ├── scrape_q2.sh        ✅ Ready
│   ├── scrape_q3.sh        ✅ Ready
│   ├── scrape_q4.sh        ✅ Ready
│   └── qc_validate_all.sh  ✅ Ready
├── logs/
│   ├── q1_jan.log
│   ├── q1_feb.log
│   ├── q1_mar.log
│   ├── qc_q1.json
│   └── ... (generated during execution)
└── README.md               ✅ This file
```

## ⏱️ Timeline Estimate

| Phase | Runtime | QC Time | Total |
|-------|---------|---------|-------|
| Q1 | ~3 hours | ~5 min | ~3.1 hours |
| Q2 | ~3.5 hours | ~5 min | ~3.6 hours |
| Q3 | ~3.5 hours | ~5 min | ~3.6 hours |
| Q4 | ~3.5 hours | ~5 min | ~3.6 hours |
| Final QC | - | ~10 min | ~10 min |
| **Total** | **~14 hours** | **~30 min** | **~14.5 hours** |

**Recommended**: Run one quarter per day/night to allow monitoring.

## 🎯 Data Quality Standards

This project uses the same proven standards as the 2025 SoCal backfill:

- ✅ **Weight label deduplication**: Prefers detailed rows with size info
- ✅ **Field-level validation**: Every field matches source 1:1
- ✅ **Composite key matching**: Boat + Trip Type + Anglers
- ✅ **Ethical scraping**: 2-5 second delays between requests
- ✅ **100% accuracy mandate**: Zero tolerance for data drift

---

**Last Updated**: October 24, 2025
**Created By**: Claude Code (automated backfill project)
