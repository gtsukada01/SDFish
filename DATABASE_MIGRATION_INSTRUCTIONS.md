# Database Constraint Migration Instructions

## Problem
The database constraint `trips_unique_trip` is missing the `anglers` field, blocking multiple trips per boat/date/type with different angler counts.

**Example**: New Seaforth on 2025-04-12 had TWO "1/2 Day PM" trips:
- Trip 1: 53 anglers ✅ (in database)
- Trip 2: 20 anglers ❌ (blocked by constraint)

## Solution
Update the constraint to include the `anglers` field per SPEC 006 requirements.

## Steps to Fix

### Option 1: Supabase Dashboard (Recommended)

1. Go to: https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq
2. Navigate to: **SQL Editor**
3. Paste the contents of `migrate_constraint.sql`
4. Click **Run**
5. Verify you see: `ALTER TABLE` success message

### Option 2: Command Line (If you have database password)

```bash
# Install PostgreSQL client if needed
brew install postgresql

# Get your database password from Supabase dashboard:
# Settings → Database → Connection string

# Run migration
psql "postgresql://postgres.[YOUR-PASSWORD]@db.ulsbtwqhwnrpkourphiq.supabase.co:5432/postgres" \
  -f migrate_constraint.sql
```

### Option 3: Python Script (If you have database password)

```bash
# Install psycopg2
pip3 install psycopg2-binary

# Set environment variable
export DATABASE_URL="postgresql://postgres.[YOUR-PASSWORD]@db.ulsbtwqhwnrpkourphiq.supabase.co:5432/postgres"

# Run migration
python3 -c "
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()

# Drop old constraint
cursor.execute('ALTER TABLE trips DROP CONSTRAINT IF EXISTS trips_unique_trip')

# Add new constraint
cursor.execute('ALTER TABLE trips ADD CONSTRAINT trips_unique_trip UNIQUE (boat_id, trip_date, trip_duration, anglers)')

conn.commit()
print('✅ Migration complete!')
"
```

## Verification

After running the migration, verify the constraint:

```sql
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
JOIN pg_class cl ON cl.oid = c.conrelid
WHERE
    cl.relname = 'trips'
    AND conname = 'trips_unique_trip';
```

**Expected output**:
```
constraint_name: trips_unique_trip
constraint_definition: UNIQUE (boat_id, trip_date, trip_duration, anglers)
```

## Next Steps

Once migration is complete:
1. Re-scrape 2025-04-12 to insert the missing trip
2. QC validate to confirm 100% pass rate
3. Continue with April Batch 3 (04/13-04/15)
4. Proceed with remaining April batches (4-6)
