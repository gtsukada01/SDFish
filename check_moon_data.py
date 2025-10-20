#!/usr/bin/env python3
"""
Quick script to check ocean_conditions table structure and data density
"""
from supabase import create_client

SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n🔍 Checking ocean_conditions table...")
print("=" * 60)

# Check October 2024 as a sample month
result = supabase.table('ocean_conditions')\
    .select('date, moon_phase_name')\
    .gte('date', '2024-10-01')\
    .lte('date', '2024-10-31')\
    .order('date')\
    .execute()

if result.data:
    print(f"\n✅ Found {len(result.data)} entries for October 2024")
    print(f"   Expected: 31 days (if daily data)")
    print(f"   Found: {len(result.data)} days")

    if len(result.data) == 31:
        print("   ✅ DAILY DATA - Every day has a moon phase entry")
    elif len(result.data) < 10:
        print("   ⚠️  ANCHOR-ONLY DATA - Only major phase transitions")
    else:
        print("   ⚠️  PARTIAL DATA - Some days missing")

    print("\n📅 First 10 days of October 2024:")
    for row in result.data[:10]:
        print(f"   {row['date']}: {row['moon_phase_name']}")

    # Count unique phases
    unique_phases = set(row['moon_phase_name'] for row in result.data)
    print(f"\n🌙 Unique moon phases in October: {len(unique_phases)}")
    for phase in sorted(unique_phases):
        count = sum(1 for row in result.data if row['moon_phase_name'] == phase)
        print(f"   {phase}: {count} days")
else:
    print("❌ No data found in ocean_conditions table for October 2024")

print("\n" + "=" * 60)
