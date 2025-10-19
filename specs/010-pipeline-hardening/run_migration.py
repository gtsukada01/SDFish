#!/usr/bin/env python3
"""
SPEC-010 Migration Runner
Executes migration_010_scrape_jobs.sql against Supabase database
"""

import sys
from pathlib import Path

# Add parent directory to path to import scraper modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client, Client

# Supabase credentials (from boats_scraper.py)
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

def run_migration():
    """Execute migration SQL against Supabase"""

    print("🔧 SPEC-010 Migration: Scrape Jobs Audit Trail")
    print("=" * 60)

    # Read migration SQL
    migration_file = Path(__file__).parent / "migration_010_scrape_jobs.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r') as f:
        sql_content = f.read()

    print(f"✅ Loaded migration SQL ({len(sql_content)} bytes)")
    print()

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
    print()

    # Parse SQL into executable statements
    # Split on semicolons but preserve comments and structure
    statements = []
    current_stmt = []

    for line in sql_content.split('\n'):
        line_stripped = line.strip()

        # Skip comment-only lines and separators
        if line_stripped.startswith('--') or line_stripped.startswith('=='):
            continue

        # Skip empty lines
        if not line_stripped:
            continue

        current_stmt.append(line)

        # If line ends with semicolon, complete the statement
        if line_stripped.endswith(';'):
            stmt = '\n'.join(current_stmt).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current_stmt = []

    print(f"📝 Parsed {len(statements)} SQL statements")
    print()

    # Execute statements using raw SQL
    # Note: Supabase client doesn't support raw SQL directly,
    # so we'll use psycopg2 through the connection string

    import psycopg2

    # Construct PostgreSQL connection string
    # Format: postgresql://[user[:password]@][host][:port][/dbname]
    # For Supabase: postgresql://postgres.[ref]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

    print("⚠️  Note: Using psycopg2 for raw SQL execution")
    print("    Supabase client requires PostgREST API, not suitable for DDL")
    print()

    # Extract reference from URL
    ref = SUPABASE_URL.split('//')[1].split('.')[0]

    # Prompt for database password (service key is for API, not direct DB access)
    print("🔐 Database connection required")
    print(f"   Host: aws-0-us-west-1.pooler.supabase.com")
    print(f"   Database: postgres")
    print(f"   User: postgres.{ref}")
    print()
    print("⚠️  This migration requires direct PostgreSQL access.")
    print("    Please run the SQL manually via Supabase SQL Editor:")
    print()
    print("    1. Go to: https://supabase.com/dashboard/project/" + ref)
    print("    2. Navigate to: SQL Editor")
    print("    3. Copy and paste the contents of migration_010_scrape_jobs.sql")
    print("    4. Execute the SQL")
    print()

    return False

if __name__ == "__main__":
    try:
        success = run_migration()
        if not success:
            print("⚠️  Migration requires manual execution via Supabase SQL Editor")
            print(f"📄 Migration file: {Path(__file__).parent / 'migration_010_scrape_jobs.sql'}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
