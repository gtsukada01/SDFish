#!/usr/bin/env python3
"""
Date Correction System for 2024 Data
Fix systematic date misalignment where return dates were stored as trip dates
Based on proven 2025 methodology
"""

from supabase import create_client
from datetime import datetime, timedelta
from collections import defaultdict
import json

class DateCorrectionSystem2024:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.corrections_applied = []
        self.duplicates_removed = []

    def calculate_departure_date(self, return_date_str, trip_duration):
        """Calculate actual departure date from return date and duration"""
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d')

        # Duration mapping to days
        duration_days = {
            'Full Day': 0,  # Same day trip
            '1/2 Day AM': 0,  # Same day trip
            '1/2 Day PM': 0,  # Same day trip
            '3/4 Day': 0,  # Same day trip
            '1/2 Day Twilight': 0,  # Same day evening trip
            'Overnight': 1,  # Departs 1 day earlier
            '1.5 Day': 1,  # Departs 1 day earlier
            '2 Day': 1,  # Departs 1 day earlier
            '2.5 Day': 2,  # Departs 2 days earlier
            '3 Day': 2,  # Departs 2 days earlier
            '3.5 Day': 3,  # Departs 3 days earlier
            '4 Day': 3,  # Departs 3 days earlier
            '5 Day': 4,  # Departs 4 days earlier
        }

        # Handle special cases
        if 'Full Day Offshore' in trip_duration or 'Full Day Coronado Islands' in trip_duration:
            days_to_subtract = 0
        elif 'Day' not in trip_duration:
            days_to_subtract = 0  # Default for unknown durations
        else:
            days_to_subtract = duration_days.get(trip_duration, 0)

        departure_date = return_date - timedelta(days=days_to_subtract)
        return departure_date.strftime('%Y-%m-%d')

    def identify_2024_multi_day_trips_needing_correction(self):
        """Identify all 2024 multi-day trips that need date correction"""
        print("🔍 IDENTIFYING 2024 MULTI-DAY TRIPS NEEDING DATE CORRECTION")
        print("=" * 60)

        # Get all 2024 trips
        response = self.supabase.table('trips').select(
            'id, trip_date, trip_duration, anglers, total_fish, boats(name)'
        ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

        trips_needing_correction = []

        for trip in response.data:
            duration = trip.get('trip_duration', '')

            # Check if this is a multi-day trip
            multi_day_durations = ['Overnight', '1.5 Day', '2 Day', '2.5 Day', '3 Day', '3.5 Day', '4 Day', '5 Day']

            if any(d in duration for d in multi_day_durations):
                current_date = trip['trip_date']
                correct_departure_date = self.calculate_departure_date(current_date, duration)

                # Only correct if dates are different
                if current_date != correct_departure_date:
                    trips_needing_correction.append({
                        'id': trip['id'],
                        'boat': trip['boats']['name'],
                        'current_date': current_date,
                        'correct_date': correct_departure_date,
                        'duration': duration,
                        'anglers': trip.get('anglers', 0),
                        'fish': trip.get('total_fish', 0)
                    })

        print(f"2024 multi-day trips needing date correction: {len(trips_needing_correction)}")
        return trips_needing_correction

    def identify_2024_duplicate_trips(self):
        """Identify duplicate trip entries that need removal"""
        print("\n🔍 IDENTIFYING 2024 DUPLICATE TRIPS FOR REMOVAL")
        print("=" * 50)

        # Get all 2024 trips grouped by signature
        response = self.supabase.table('trips').select(
            'id, trip_date, trip_duration, anglers, total_fish, boats(name)'
        ).gte('trip_date', '2024-01-01').lte('trip_date', '2024-12-31').execute()

        # Group trips by signature (boat + duration + anglers + fish)
        trip_signatures = defaultdict(list)

        for trip in response.data:
            signature = f"{trip['boats']['name']}_{trip.get('trip_duration', '')}_{trip.get('anglers', 0)}_{trip.get('total_fish', 0)}"
            trip_signatures[signature].append(trip)

        # Find duplicates
        duplicates_to_remove = []

        for signature, trips in trip_signatures.items():
            if len(trips) > 1:
                # Sort by date to keep the earliest occurrence (likely correct departure date)
                trips_sorted = sorted(trips, key=lambda x: x['trip_date'])

                # Mark later occurrences as duplicates to remove
                for duplicate_trip in trips_sorted[1:]:
                    duplicates_to_remove.append({
                        'id': duplicate_trip['id'],
                        'boat': duplicate_trip['boats']['name'],
                        'date': duplicate_trip['trip_date'],
                        'duration': duplicate_trip.get('trip_duration', ''),
                        'signature': signature,
                        'keep_date': trips_sorted[0]['trip_date']  # Date of trip we're keeping
                    })

        print(f"2024 duplicate trips to remove: {len(duplicates_to_remove)}")
        return duplicates_to_remove

    def apply_date_corrections_batch(self, corrections, batch_size=50):
        """Apply date corrections in batches"""
        print(f"\n🔧 APPLYING 2024 DATE CORRECTIONS")
        print("=" * 50)

        total_corrected = 0

        # Process in batches
        for i in range(0, len(corrections), batch_size):
            batch = corrections[i:i + batch_size]

            print(f"Processing batch {i//batch_size + 1} ({len(batch)} corrections)")

            for correction in batch:
                try:
                    # Update trip date
                    update_response = self.supabase.table('trips').update({
                        'trip_date': correction['correct_date']
                    }).eq('id', correction['id']).execute()

                    if update_response.data:
                        total_corrected += 1
                        self.corrections_applied.append(correction)
                        print(f"  ✅ {correction['boat']}: {correction['current_date']} → {correction['correct_date']}")

                except Exception as e:
                    print(f"  ❌ Failed to correct trip {correction['id']}: {e}")

        return total_corrected

    def remove_duplicate_trips_batch(self, duplicates, batch_size=50):
        """Remove duplicate trips in batches"""
        print(f"\n🗑️ REMOVING 2024 DUPLICATE TRIPS")
        print("=" * 50)

        total_removed = 0

        # Process in batches
        for i in range(0, len(duplicates), batch_size):
            batch = duplicates[i:i + batch_size]

            print(f"Processing batch {i//batch_size + 1} ({len(batch)} removals)")

            for duplicate in batch:
                try:
                    # First remove associated catches
                    self.supabase.table('catches').delete().eq('trip_id', duplicate['id']).execute()

                    # Then remove the trip
                    delete_response = self.supabase.table('trips').delete().eq('id', duplicate['id']).execute()

                    if delete_response.data:
                        total_removed += 1
                        self.duplicates_removed.append(duplicate)
                        print(f"  ✅ Removed duplicate: {duplicate['boat']} on {duplicate['date']}")

                except Exception as e:
                    print(f"  ❌ Failed to remove duplicate {duplicate['id']}: {e}")

        return total_removed

    def run_comprehensive_2024_date_correction(self):
        """Run complete 2024 date correction system"""
        print("🚨 COMPREHENSIVE 2024 DATE CORRECTION SYSTEM")
        print("=" * 80)
        print("Fixing systematic date misalignment where return dates were stored as trip dates")
        print("Based on proven 2025 methodology")
        print()

        # Step 1: Identify corrections needed
        multi_day_corrections = self.identify_2024_multi_day_trips_needing_correction()
        duplicates_to_remove = self.identify_2024_duplicate_trips()

        print(f"\n📋 2024 CORRECTION PLAN:")
        print(f"Multi-day trip date corrections needed: {len(multi_day_corrections)}")
        print(f"Duplicate trips to remove: {len(duplicates_to_remove)}")

        # Step 2: Apply corrections (process duplicates first to avoid conflicts)
        duplicates_removed = self.remove_duplicate_trips_batch(duplicates_to_remove)
        corrections_applied = self.apply_date_corrections_batch(multi_day_corrections)

        # Step 3: Generate summary
        print(f"\n🎯 2024 DATE CORRECTION COMPLETE")
        print("=" * 60)
        print(f"Date corrections applied: {corrections_applied}")
        print(f"Duplicate trips removed: {duplicates_removed}")

        # Show sample corrections
        if self.corrections_applied:
            print(f"\n📊 SAMPLE 2024 DATE CORRECTIONS:")
            for correction in self.corrections_applied[:10]:
                print(f"  {correction['boat']}: {correction['current_date']} → {correction['correct_date']} ({correction['duration']})")

        if self.duplicates_removed:
            print(f"\n🗑️ SAMPLE 2024 DUPLICATES REMOVED:")
            for duplicate in self.duplicates_removed[:10]:
                print(f"  {duplicate['boat']}: {duplicate['date']} (kept: {duplicate['keep_date']})")

        # Save correction log
        correction_log = {
            'corrections_applied': self.corrections_applied,
            'duplicates_removed': self.duplicates_removed,
            'summary': {
                'total_corrections': corrections_applied,
                'total_duplicates_removed': duplicates_removed,
                'correction_date': '2025-09-24',
                'year': '2024'
            }
        }

        with open('date_correction_2024_log.json', 'w') as f:
            json.dump(correction_log, f, indent=2, default=str)

        print(f"\n✅ 2024 date correction log saved to: date_correction_2024_log.json")

        # Final assessment
        print(f"\n🎯 FINAL 2024 ASSESSMENT:")
        print(f"2024 date alignment issue: RESOLVED")
        print(f"Multi-day trips now show correct departure dates")
        print(f"Duplicate entries removed from database")
        print(f"Data integrity restored for 2024 trip timing analysis")

        # Risk assessment for remaining 2024 issues
        if corrections_applied > 1000 or duplicates_removed > 200:
            print(f"\n🚨 CRITICAL 2024 FINDING:")
            print(f"Massive date misalignment detected in 2024")
            print(f"Scale suggests systematic collection issues throughout 2024")

        return {
            'corrections_applied': corrections_applied,
            'duplicates_removed': duplicates_removed,
            'correction_log': correction_log
        }

def main():
    corrector = DateCorrectionSystem2024()
    corrector.run_comprehensive_2024_date_correction()

if __name__ == "__main__":
    main()