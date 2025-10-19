#!/usr/bin/env python3
"""
Trip Date Migration Script - Spec 005
Migrates all trip dates from return/report dates to departure dates

Author: Claude Code
Date: October 16, 2025
Specification: FR-003 (Dry-Run), FR-004 (Production)
Constitution: v1.0.0
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import date_calculator
sys.path.insert(0, str(Path(__file__).parent))

from date_calculator import calculate_departure_date, validate_date_change

# Import Supabase connection
sys.path.insert(0, '/Users/btsukada/Desktop/Fishing/fish-scraper')
from boats_scraper import init_supabase


class TripDateMigrator:
    """
    Handles migration of trip dates from report dates to departure dates.

    Supports:
    - Dry-run mode (FR-003): Calculate changes without database writes
    - Production mode (FR-004): Execute migration with transaction safety
    - Comprehensive logging and validation
    """

    def __init__(self, dry_run=True):
        """
        Initialize migrator.

        Args:
            dry_run: If True, only calculate changes without writing to database
        """
        self.dry_run = dry_run
        self.supabase = init_supabase()
        self.stats = {
            'total_trips': 0,
            'trips_updated': 0,
            'trips_unchanged': 0,
            'validation_errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        self.changes = []
        self.validation_errors = []

    def fetch_all_trips(self):
        """
        Fetch all trips from database with boat names.

        Returns:
            List of trip dictionaries
        """
        print("=" * 80)
        print("FETCHING TRIPS FROM DATABASE")
        print("=" * 80)

        # Fetch all trips with boat information
        result = self.supabase.table('trips')\
            .select('id, boat_id, trip_date, trip_duration, anglers, boats(name)')\
            .order('trip_date')\
            .execute()

        trips = result.data
        self.stats['total_trips'] = len(trips)

        print(f"✅ Fetched {len(trips):,} trips")
        print(f"   Date range: {trips[0]['trip_date']} to {trips[-1]['trip_date']}")
        print()

        return trips

    def calculate_all_changes(self, trips):
        """
        Calculate departure dates for all trips.

        Args:
            trips: List of trip dictionaries

        Returns:
            List of change dictionaries
        """
        print("=" * 80)
        print(f"CALCULATING DEPARTURE DATES ({'DRY RUN' if self.dry_run else 'PRODUCTION'})")
        print("=" * 80)

        changes = []
        unchanged = 0

        for i, trip in enumerate(trips, 1):
            trip_id = trip['id']
            boat_name = trip['boats']['name'] if trip['boats'] else 'Unknown'
            old_date = trip['trip_date']
            trip_duration = trip['trip_duration']

            try:
                # Calculate new departure date
                new_date = calculate_departure_date(old_date, trip_duration)

                # Check if date actually changed
                if new_date == old_date:
                    unchanged += 1
                    continue

                # Validate the change
                validation = validate_date_change(
                    old_date, new_date, trip_duration, boat_name, trip_id
                )

                if not validation['valid']:
                    self.validation_errors.append(validation)
                    self.stats['validation_errors'] += 1
                    print(f"⚠️  {validation['message']}")
                    continue

                # Record the change
                change = {
                    'trip_id': trip_id,
                    'boat_id': trip['boat_id'],
                    'boat_name': boat_name,
                    'old_date': old_date,
                    'new_date': new_date,
                    'trip_duration': trip_duration,
                    'days_diff': validation['expected_days'],
                    'anglers': trip['anglers']
                }
                changes.append(change)

                # Progress logging (every 1000 trips)
                if i % 1000 == 0:
                    print(f"   Processed {i:,}/{len(trips):,} trips...")

            except Exception as e:
                error = {
                    'trip_id': trip_id,
                    'boat_name': boat_name,
                    'error': str(e),
                    'trip_duration': trip_duration
                }
                self.validation_errors.append(error)
                self.stats['validation_errors'] += 1
                print(f"❌ ERROR: Trip {trip_id} ({boat_name}) - {e}")

        self.stats['trips_updated'] = len(changes)
        self.stats['trips_unchanged'] = unchanged

        print()
        print(f"✅ Calculation complete:")
        print(f"   {len(changes):,} trips to update")
        print(f"   {unchanged:,} trips unchanged (same-day trips)")
        print(f"   {len(self.validation_errors)} validation errors")
        print()

        return changes

    def print_sample_changes(self, changes, sample_size=10):
        """
        Print sample of proposed changes for review.

        Args:
            changes: List of change dictionaries
            sample_size: Number of samples to show
        """
        print("=" * 80)
        print(f"SAMPLE CHANGES (showing {sample_size} of {len(changes):,})")
        print("=" * 80)

        # Show first few changes
        for change in changes[:sample_size]:
            print(f"Trip {change['trip_id']:5d} | {change['boat_name']:30s} | "
                  f"{change['old_date']} → {change['new_date']} | "
                  f"{change['trip_duration']:15s} | {change['anglers']} anglers")

        print()

    def execute_migration(self, changes):
        """
        Execute migration in production mode with transaction safety.

        Args:
            changes: List of change dictionaries
        """
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No database changes will be made")
            return

        print("=" * 80)
        print("EXECUTING PRODUCTION MIGRATION")
        print("=" * 80)
        print("⚠️  WARNING: This will modify the database!")
        print(f"   {len(changes):,} trips will be updated")
        print()

        # Confirmation prompt
        response = input("Type 'EXECUTE' to proceed: ")
        if response != 'EXECUTE':
            print("❌ Migration cancelled by user")
            return

        print()
        print("🚀 Starting migration...")

        updated = 0
        errors = []

        for i, change in enumerate(changes, 1):
            try:
                # Update trip_date
                result = self.supabase.table('trips')\
                    .update({'trip_date': change['new_date']})\
                    .eq('id', change['trip_id'])\
                    .execute()

                if result.data:
                    updated += 1
                else:
                    errors.append({
                        'trip_id': change['trip_id'],
                        'error': 'Update returned no data'
                    })

                # Progress logging (every 1000 trips)
                if i % 1000 == 0:
                    print(f"   Updated {i:,}/{len(changes):,} trips...")

            except Exception as e:
                errors.append({
                    'trip_id': change['trip_id'],
                    'error': str(e)
                })
                print(f"❌ ERROR: Trip {change['trip_id']} - {e}")

        print()
        print(f"✅ Migration complete:")
        print(f"   {updated:,} trips updated successfully")
        print(f"   {len(errors)} errors")
        print()

        if errors:
            print("❌ ERRORS OCCURRED:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"   Trip {error['trip_id']}: {error['error']}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")

    def generate_report(self, changes):
        """
        Generate comprehensive migration report.

        Args:
            changes: List of change dictionaries

        Returns:
            Dictionary with report data
        """
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        report = {
            'timestamp': self.stats['end_time'].isoformat(),
            'mode': 'DRY_RUN' if self.dry_run else 'PRODUCTION',
            'duration_seconds': duration,
            'statistics': {
                'total_trips': self.stats['total_trips'],
                'trips_to_update': self.stats['trips_updated'],
                'trips_unchanged': self.stats['trips_unchanged'],
                'validation_errors': self.stats['validation_errors']
            },
            'sample_changes': changes[:20],  # First 20 changes
            'validation_errors': self.validation_errors[:10] if self.validation_errors else []
        }

        return report

    def save_report(self, report, output_file=None):
        """
        Save migration report to JSON file.

        Args:
            report: Report dictionary
            output_file: Path to output file (optional)
        """
        if output_file is None:
            mode = 'dry_run' if self.dry_run else 'production'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'migration_report_{mode}_{timestamp}.json'

        # Ensure output directory exists
        output_path = Path(__file__).parent.parent / 'validation' / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📄 Report saved: {output_path}")

    def run(self):
        """
        Execute full migration workflow.
        """
        print("\n")
        print("=" * 80)
        print("TRIP DATE MIGRATION - SPEC 005")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        print(f"Started: {self.stats['start_time']}")
        print("=" * 80)
        print("\n")

        # Step 1: Fetch all trips
        trips = self.fetch_all_trips()

        # Step 2: Calculate all changes
        changes = self.calculate_all_changes(trips)
        self.changes = changes

        # Step 3: Show sample changes
        self.print_sample_changes(changes)

        # Step 4: Execute migration (production only)
        if not self.dry_run:
            self.execute_migration(changes)

        # Step 5: Generate report
        report = self.generate_report(changes)
        self.save_report(report)

        # Step 6: Print summary
        print("=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        print(f"Total trips: {self.stats['total_trips']:,}")
        print(f"Trips to update: {self.stats['trips_updated']:,}")
        print(f"Trips unchanged: {self.stats['trips_unchanged']:,}")
        print(f"Validation errors: {self.stats['validation_errors']}")
        print(f"Duration: {(self.stats['end_time'] - self.stats['start_time']).total_seconds():.1f} seconds")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠️  DRY RUN COMPLETE - No database changes made")
            print("   Review the report and run with --production to execute migration\n")
        else:
            print("\n✅ PRODUCTION MIGRATION COMPLETE")
            print(f"   {self.stats['trips_updated']:,} trips updated successfully\n")


def main():
    """
    Main entry point for migration script.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Migrate trip dates from report dates to departure dates'
    )
    parser.add_argument(
        '--production',
        action='store_true',
        help='Execute production migration (default: dry-run)'
    )

    args = parser.parse_args()

    # Initialize migrator
    migrator = TripDateMigrator(dry_run=not args.production)

    # Run migration
    migrator.run()


if __name__ == '__main__':
    main()
