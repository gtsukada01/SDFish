#!/usr/bin/env python3
"""
Phase 2: Systematic 2024 Weight Qualifier Verification
Verify all 294 weight qualifier suspects using proven 2025 methodology
"""

from supabase import create_client
import re
from collections import defaultdict

class Phase2SystematicVerification:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.verified_failures = []
        self.confirmed_zeros = []
        self.total_fish_recovered = 0

    def get_high_priority_suspects(self):
        """Get the 5 highest priority 2024 weight qualifier suspects"""
        print("🎯 PHASE 2: HIGH-PRIORITY 2024 WEIGHT QUALIFIER VERIFICATION")
        print("=" * 70)

        # High-priority suspects from Phase 1 analysis
        high_priority_suspects = [
            {'date': '2024-05-13', 'boat': 'Excel', 'anglers': 33, 'duration': '3 Day', 'priority': 'CRITICAL'},
            {'date': '2024-08-04', 'boat': 'Oceanside 95', 'anglers': 32, 'duration': '1.5 Day', 'priority': 'CRITICAL'},
            {'date': '2024-05-11', 'boat': 'Pacific Queen', 'anglers': 32, 'duration': '1.5 Day', 'priority': 'CRITICAL'},
            {'date': '2024-09-06', 'boat': 'Condor', 'anglers': 32, 'duration': '2 Day', 'priority': 'CRITICAL'},
            {'date': '2024-05-19', 'boat': 'Tribute', 'anglers': 30, 'duration': '1.5 Day', 'priority': 'HIGH'},
        ]

        # Verify these trips exist in database with 0 fish
        validated_suspects = []

        for suspect in high_priority_suspects:
            try:
                response = self.supabase.table('trips').select(
                    'id, total_fish, boats(name)'
                ).eq('trip_date', suspect['date']).execute()

                target_trip = None
                for trip in response.data:
                    if trip['boats']['name'] == suspect['boat']:
                        target_trip = trip
                        break

                if target_trip and target_trip['total_fish'] == 0:
                    suspect['trip_id'] = target_trip['id']
                    suspect['current_fish'] = target_trip['total_fish']
                    validated_suspects.append(suspect)
                    print(f"✅ CONFIRMED SUSPECT: {suspect['boat']} on {suspect['date']} ({suspect['anglers']} anglers, {suspect['duration']})")
                elif target_trip:
                    print(f"⚠️  ALREADY FIXED: {suspect['boat']} on {suspect['date']} has {target_trip['total_fish']} fish")
                else:
                    print(f"❌ NOT FOUND: {suspect['boat']} on {suspect['date']}")

            except Exception as e:
                print(f"❌ Error checking {suspect['boat']} on {suspect['date']}: {e}")

        print(f"\n🎯 HIGH-PRIORITY SUSPECTS TO VERIFY: {len(validated_suspects)}")
        return validated_suspects

    def verify_suspect_with_webfetch(self, suspect):
        """Verify individual suspect using WebFetch (placeholder for actual implementation)"""
        print(f"\n🔍 VERIFYING: {suspect['boat']} - {suspect['date']}")
        print("=" * 50)

        url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={suspect['date']}"
        print(f"URL: {url}")

        # This is where WebFetch would be called in actual implementation
        # For now, return structure for manual verification
        verification_result = {
            'suspect': suspect,
            'url': url,
            'needs_manual_verification': True,
            'expected_pattern': f"Look for: {suspect['boat']} with '(up to X pounds)' pattern"
        }

        return verification_result

    def apply_weight_qualifier_fix(self, fix_data):
        """Apply weight qualifier fix to database"""
        try:
            trip_id = fix_data['trip_id']
            fish_count = fix_data['fish_count']
            species = fix_data['species']

            # Update trip
            self.supabase.table('trips').update({
                'total_fish': fish_count
            }).eq('id', trip_id).execute()

            # Add catch record
            self.supabase.table('catches').insert({
                'trip_id': trip_id,
                'species': species,
                'count': fish_count
            }).execute()

            self.verified_failures.append(fix_data)
            self.total_fish_recovered += fish_count

            print(f"✅ FIXED: {fix_data['boat']} +{fish_count} {species}")
            return True

        except Exception as e:
            print(f"❌ Error fixing {fix_data['boat']}: {e}")
            return False

    def get_all_2024_weight_qualifier_suspects(self):
        """Get all 294 weight qualifier suspects from 2024 analysis"""
        print("\n🔍 LOADING ALL 2024 WEIGHT QUALIFIER SUSPECTS")
        print("=" * 60)

        # Get all 2024 trips for analysis
        try:
            response = self.supabase.table('trips').select(
                'id, trip_date, boat_id, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
            ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

            trips = response.data
            weight_qualifier_suspects = []

            for trip in trips:
                boat_name = trip['boats']['name']
                anglers = trip.get('anglers', 0)
                fish_count = trip.get('total_fish', 0)
                date = trip['trip_date']
                duration = trip.get('trip_duration', '')

                # Apply 2025 pattern: High-angler, multi-day trips with 0 fish
                if (anglers >= 10 and
                    fish_count == 0 and
                    ('Day' in duration and duration not in ['Full Day', '1/2 Day AM', '1/2 Day PM', '3/4 Day', '1/2 Day Twilight'])):

                    priority = 'CRITICAL' if anglers >= 20 else 'HIGH' if anglers >= 15 else 'MEDIUM'

                    weight_qualifier_suspects.append({
                        'date': date,
                        'boat': boat_name,
                        'anglers': anglers,
                        'duration': duration,
                        'trip_id': trip['id'],
                        'priority': priority
                    })

            # Sort by priority and angler count
            weight_qualifier_suspects.sort(key=lambda x: (x['priority'] == 'CRITICAL', x['priority'] == 'HIGH', x['anglers']), reverse=True)

            print(f"Total 2024 weight qualifier suspects: {len(weight_qualifier_suspects)}")
            return weight_qualifier_suspects

        except Exception as e:
            print(f"❌ Error loading 2024 suspects: {e}")
            return []

    def generate_verification_batch_plan(self, all_suspects):
        """Generate systematic verification plan for all suspects"""
        print(f"\n📋 PHASE 2 VERIFICATION BATCH PLAN")
        print("=" * 60)

        # Group by priority
        priority_groups = defaultdict(list)
        for suspect in all_suspects:
            priority_groups[suspect['priority']].append(suspect)

        print(f"CRITICAL Priority: {len(priority_groups['CRITICAL'])} suspects")
        print(f"HIGH Priority: {len(priority_groups['HIGH'])} suspects")
        print(f"MEDIUM Priority: {len(priority_groups['MEDIUM'])} suspects")

        # Create verification batches
        verification_plan = {
            'batch_1_critical': priority_groups['CRITICAL'][:20],  # Top 20 critical
            'batch_2_high': priority_groups['HIGH'][:30],          # Top 30 high
            'batch_3_medium': priority_groups['MEDIUM'][:50],      # Top 50 medium
            'remaining': all_suspects[100:]                        # Rest for systematic sweep
        }

        print(f"\nBATCH PLAN:")
        print(f"Batch 1 (CRITICAL): {len(verification_plan['batch_1_critical'])} suspects - Immediate verification")
        print(f"Batch 2 (HIGH): {len(verification_plan['batch_2_high'])} suspects - Priority verification")
        print(f"Batch 3 (MEDIUM): {len(verification_plan['batch_3_medium'])} suspects - Systematic verification")
        print(f"Remaining: {len(verification_plan['remaining'])} suspects - Complete sweep")

        return verification_plan

    def run_high_priority_verification_round(self):
        """Run verification of high-priority suspects"""
        print("🚨 PHASE 2: HIGH-PRIORITY WEIGHT QUALIFIER VERIFICATION ROUND")
        print("=" * 80)
        print("Starting with 5 highest priority suspects from Phase 1 analysis")
        print()

        # Get high-priority suspects
        high_priority_suspects = self.get_high_priority_suspects()

        if not high_priority_suspects:
            print("❌ No high-priority suspects found for verification")
            return

        print(f"\n🔍 VERIFICATION TARGETS:")
        verification_results = []

        for i, suspect in enumerate(high_priority_suspects, 1):
            print(f"\n{i}. {suspect['date']} - {suspect['boat']} ({suspect['anglers']} anglers, {suspect['duration']})")

            # Verify with WebFetch (structure for manual verification)
            verification_result = self.verify_suspect_with_webfetch(suspect)
            verification_results.append(verification_result)

        # Generate summary of verification targets
        print(f"\n📊 HIGH-PRIORITY VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Suspects requiring manual WebFetch verification: {len(verification_results)}")

        print(f"\n🎯 MANUAL VERIFICATION REQUIRED:")
        for i, result in enumerate(verification_results, 1):
            suspect = result['suspect']
            print(f"{i}. {suspect['date']} - {suspect['boat']}")
            print(f"   URL: {result['url']}")
            print(f"   Pattern: Look for '(up to X pounds)' in {suspect['boat']} entry")
            print(f"   Expected: High fish count due to {suspect['anglers']} anglers on {suspect['duration']} trip")

        print(f"\n🚨 CRITICAL NEXT STEPS:")
        print("1. Manually verify each URL above for weight qualifier patterns")
        print("2. Record actual fish counts and species found")
        print("3. Apply database fixes for confirmed weight qualifier failures")
        print("4. Continue with systematic verification of remaining 289 suspects")

        return verification_results

def main():
    verifier = Phase2SystematicVerification()
    verifier.run_high_priority_verification_round()

if __name__ == "__main__":
    main()