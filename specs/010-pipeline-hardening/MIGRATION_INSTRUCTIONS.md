# Database Migration Instructions - SPEC-010

## Manual Migration via Supabase SQL Editor

**Requirement**: Apply `migration_010_scrape_jobs.sql` to production database

### Steps:

1. **Open Supabase SQL Editor**:
   - Navigate to: https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq
   - Click "SQL Editor" in left sidebar

2. **Create New Query**:
   - Click "New query" button
   - Name it: "SPEC-010 Migration - Scrape Jobs Audit Trail"

3. **Copy Migration SQL**:
   - Open: `specs/010-pipeline-hardening/migration_010_scrape_jobs.sql`
   - Copy entire contents

4. **Execute Migration**:
   - Paste SQL into query editor
   - Review the SQL (creates scrape_jobs table, adds scrape_job_id to trips)
   - Click "Run" button
   - Verify success messages

5. **Verify Migration**:
   - Run verification queries at bottom of migration file:
     ```sql
     -- Verify scrape_jobs table exists
     SELECT table_name, table_type
     FROM information_schema.tables
     WHERE table_name = 'scrape_jobs';

     -- Verify indexes created
     SELECT indexname, indexdef
     FROM pg_indexes
     WHERE tablename = 'scrape_jobs';

     -- Verify scrape_job_id column added
     SELECT column_name, data_type, is_nullable
     FROM information_schema.columns
     WHERE table_name = 'trips' AND column_name = 'scrape_job_id';
     ```

6. **Expected Results**:
   - ✅ scrape_jobs table created with 18 columns
   - ✅ 4 indexes on scrape_jobs (status, operator, dates, started)
   - ✅ scrape_job_id column added to trips table
   - ✅ 1 index on trips(scrape_job_id)

### Rollback (if needed):

If migration fails or needs to be reverted:
```sql
BEGIN;
DROP INDEX IF EXISTS idx_trips_scrape_job;
ALTER TABLE trips DROP COLUMN IF EXISTS scrape_job_id;
DROP TABLE IF EXISTS scrape_jobs CASCADE;
COMMIT;
```

---

## Alternative: Supabase CLI (if installed)

```bash
# Login to Supabase
supabase login

# Link project
supabase link --project-ref ulsbtwqhwnrpkourphiq

# Run migration
supabase db execute -f specs/010-pipeline-hardening/migration_010_scrape_jobs.sql
```

---

## Status

- [ ] Migration executed
- [ ] Verification queries passed
- [ ] scrape_jobs table confirmed in database
- [ ] scrape_job_id column confirmed in trips table

**After migration is complete**, update IMPLEMENTATION_LOG.md to mark database tasks as done.
