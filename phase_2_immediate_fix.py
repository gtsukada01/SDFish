#!/usr/bin/env python3
"""
Phase 2: Immediate Weight Qualifier Fixes
Apply verified corrections as they are confirmed
"""

from supabase import create_client

class Phase2ImmediateFix:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.fixes_applied = []

    def apply_condor_sep_6_fix(self):
        """Apply Condor September 6, 2024 weight qualifier fix"""
        print("🔧 APPLYING CONDOR SEPTEMBER 6, 2024 WEIGHT QUALIFIER FIX")
        print("=" * 60)
        print("Source: 34 Bluefin Tuna (up to 220 pounds)")
        print("Database: 0 fish (WEIGHT QUALIFIER FAILURE CONFIRMED)")

        try:
            # Find the Condor trip on 2024-09-06
            response = self.supabase.table('trips').select(
                'id, total_fish, boats(name)'
            ).eq('trip_date', '2024-09-06').execute()

            condor_trip = None
            for trip in response.data:
                if trip['boats']['name'] == 'Condor':
                    condor_trip = trip
                    break

            if not condor_trip:
                print("❌ Condor trip not found for 2024-09-06")
                return False

            trip_id = condor_trip['id']
            current_fish = condor_trip['total_fish']

            if current_fish > 0:
                print(f"⚠️  Condor already has {current_fish} fish - skipping")
                return False

            print(f"Trip ID: {trip_id}")
            print(f"Current fish: {current_fish}")
            print(f"Applying fix: +34 Bluefin Tuna")

            # Update trip
            self.supabase.table('trips').update({
                'total_fish': 34
            }).eq('id', trip_id).execute()

            # Add catch record
            self.supabase.table('catches').insert({
                'trip_id': trip_id,
                'species': 'Bluefin Tuna',
                'count': 34
            }).execute()

            fix_record = {
                'date': '2024-09-06',
                'boat': 'Condor',
                'trip_id': trip_id,
                'fish_recovered': 34,
                'species': 'Bluefin Tuna',
                'weight_info': 'up to 220 pounds',
                'source': '34 Bluefin Tuna (up to 220 pounds)'
            }

            self.fixes_applied.append(fix_record)

            print("✅ CONDOR WEIGHT QUALIFIER FIX APPLIED")
            print(f"   +34 Bluefin Tuna recovered")
            print(f"   Weight qualifier: (up to 220 pounds)")

            return True

        except Exception as e:
            print(f"❌ Error applying Condor fix: {e}")
            return False

    def run_immediate_fixes(self):
        """Run all confirmed immediate fixes"""
        print("🚨 PHASE 2: IMMEDIATE WEIGHT QUALIFIER FIXES")
        print("=" * 70)

        # Apply Condor fix
        condor_success = self.apply_condor_sep_6_fix()

        # Summary
        print(f"\n📊 IMMEDIATE FIXES SUMMARY")
        print("=" * 50)

        total_fish_recovered = sum(fix['fish_recovered'] for fix in self.fixes_applied)

        print(f"Fixes applied: {len(self.fixes_applied)}")
        print(f"Total fish recovered: +{total_fish_recovered}")

        if self.fixes_applied:
            print(f"\n🎯 FIXES APPLIED:")
            for fix in self.fixes_applied:
                print(f"  {fix['date']} - {fix['boat']}: +{fix['fish_recovered']} {fix['species']}")
                print(f"    Source: {fix['source']}")

        return self.fixes_applied

def main():
    fixer = Phase2ImmediateFix()
    fixer.run_immediate_fixes()

if __name__ == "__main__":
    main()