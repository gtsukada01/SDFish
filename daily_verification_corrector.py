#!/usr/bin/env python3
"""
Daily September 2025 Verification and Correction Tool
Systematically verify each day against source and make real-time corrections
"""

from supabase import create_client
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json

class DailyVerificationCorrector:
    def __init__(self):
        self.supabase = create_client(
            "https://ulsbtwqhwnrpkourphiq.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Load boat and landing mappings
        self.load_mappings()

        # Track corrections made
        self.corrections_made = []

    def load_mappings(self):
        """Load boat and landing mappings from database"""
        try:
            boats_response = self.supabase.table('boats').select('id, name, landing_id').execute()
            landings_response = self.supabase.table('landings').select('id, name').execute()

            self.boats_map = {boat['name']: boat for boat in boats_response.data}
            self.landings_map = {landing['name']: landing for landing in landings_response.data}

            print(f"Loaded {len(self.boats_map)} boats and {len(self.landings_map)} landings")
        except Exception as e:
            print(f"❌ Error loading mappings: {e}")
            self.boats_map = {}
            self.landings_map = {}

    def get_database_trips_for_date(self, date):
        """Get all trips from database for specific date"""
        try:
            response = self.supabase.table('trips').select(
                'id, boat_id, anglers, total_fish, trip_duration, boats(name), catches(species, count)'
            ).eq('trip_date', date).execute()

            return response.data
        except Exception as e:
            print(f"❌ Error fetching database trips for {date}: {e}")
            return []

    def extract_source_data_from_text(self, text):
        """Extract fishing data from webpage text using pattern matching"""
        boats_found = {}

        # Common patterns for fishing data
        # Pattern 1: "Boat Name: X fish species" or "Boat Name - X fish species"
        boat_pattern = r'([A-Za-z][A-Za-z0-9\s\-\.]{2,25})[\:\-]\s*(.+)'

        # Pattern 2: Weight qualifiers like "(up to X pounds)" or "(X lbs)"
        weight_pattern = r'(\d+)\s+([^(]+?)\s*\((?:up to|about|around|to)?\s*(\d+)?\s*(?:pounds?|lbs?|#)\)'

        # Pattern 3: Simple fish counts like "15 Bluefin Tuna"
        fish_pattern = r'(\d+)\s+([A-Za-z\s]+(?:Tuna|Bass|Rockfish|Yellowtail|Dorado|Bonito|Calico|Sand Bass|Sculpin|Sheephead|Whitefish|Lingcod|Cabezon))'

        lines = text.split('\n')
        current_boat = None

        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Check for boat names (usually followed by colon or dash)
            boat_match = re.search(boat_pattern, line)
            if boat_match:
                potential_boat = boat_match.group(1).strip()
                catch_info = boat_match.group(2).strip()

                # Validate this looks like a boat name (not a fish species)
                if (len(potential_boat) > 3 and
                    not any(word in potential_boat.lower() for word in ['bluefin', 'yellowtail', 'bass', 'rockfish', 'tuna', 'fish', 'caught', 'angler'])):

                    current_boat = potential_boat
                    boats_found[current_boat] = {'catches': [], 'raw_text': catch_info}

                    # Parse the catch info
                    self.parse_catch_data(catch_info, boats_found[current_boat])

            # Look for weight qualifiers specifically
            weight_matches = re.findall(weight_pattern, line, re.IGNORECASE)
            for match in weight_matches:
                count = int(match[0])
                species = match[1].strip()
                weight = match[2] if match[2] else 'N/A'

                if current_boat:
                    boats_found[current_boat]['catches'].append({
                        'species': species,
                        'count': count,
                        'weight_qualifier': f"up to {weight} pounds" if weight != 'N/A' else None
                    })

        return boats_found

    def parse_catch_data(self, catch_text, boat_data):
        """Parse catch data from text"""
        # Look for fish counts
        fish_pattern = r'(\d+)\s+([A-Za-z\s]+(?:Tuna|Bass|Rockfish|Yellowtail|Dorado|Bonito|Calico|Sand Bass|Sculpin|Sheephead|Whitefish|Lingcod|Cabezon))'

        matches = re.findall(fish_pattern, catch_text, re.IGNORECASE)

        for match in matches:
            count = int(match[0])
            species = match[1].strip()

            boat_data['catches'].append({
                'species': species,
                'count': count,
                'weight_qualifier': None
            })

    def verify_and_correct_date(self, date):
        """Verify a single date and make corrections"""
        print(f"\n🔍 VERIFYING {date}")
        print("=" * 50)

        # Get database trips
        db_trips = self.get_database_trips_for_date(date)

        # Fetch source data using WebFetch tool approach
        try:
            url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={date}"
            response = self.session.get(url)

            if response.status_code == 403:
                print(f"⚠️  Source blocked direct access for {date} - skipping")
                return
            elif response.status_code != 200:
                print(f"❌ Error fetching source for {date}: HTTP {response.status_code}")
                return

            # Parse source data
            source_data = self.extract_source_data_from_text(response.text)

            print(f"📊 Database: {len(db_trips)} trips | Source: {len(source_data)} boats found")

            # Compare and identify issues
            self.compare_and_correct(date, db_trips, source_data)

        except Exception as e:
            print(f"❌ Error processing {date}: {e}")

    def compare_and_correct(self, date, db_trips, source_data):
        """Compare database trips with source data and make corrections"""

        # Group database trips by boat name
        db_by_boat = {}
        for trip in db_trips:
            boat_name = trip['boats']['name']
            db_by_boat[boat_name] = trip

        corrections_this_date = []

        # Check each database trip
        for boat_name, db_trip in db_by_boat.items():
            db_anglers = db_trip['anglers']
            db_fish = db_trip['total_fish']
            trip_id = db_trip['id']

            # Check if this boat exists in source
            if boat_name not in source_data:
                if db_fish == 0 and db_anglers >= 5:
                    print(f"  ⚠️  {boat_name}: {db_anglers} anglers, 0 fish - NOT FOUND in source")
                    # This might be a phantom trip, but we need manual verification
                continue

            source_boat = source_data[boat_name]
            source_fish_count = sum(catch['count'] for catch in source_boat['catches'])

            # Check for mismatches
            if db_fish != source_fish_count:
                print(f"  🔧 MISMATCH FOUND: {boat_name}")
                print(f"      Database: {db_fish} fish | Source: {source_fish_count} fish")
                print(f"      Source catches: {source_boat['catches']}")

                # Prepare correction
                correction = {
                    'date': date,
                    'boat': boat_name,
                    'trip_id': trip_id,
                    'old_fish_count': db_fish,
                    'new_fish_count': source_fish_count,
                    'source_catches': source_boat['catches']
                }

                corrections_this_date.append(correction)

        # Check for missing boats in database
        for boat_name, source_boat in source_data.items():
            if boat_name not in db_by_boat:
                source_fish_count = sum(catch['count'] for catch in source_boat['catches'])
                if source_fish_count > 0:
                    print(f"  ➕ MISSING BOAT: {boat_name} ({source_fish_count} fish) not in database")

        # Apply corrections
        if corrections_this_date:
            print(f"  🔧 Applying {len(corrections_this_date)} corrections...")
            self.apply_corrections(corrections_this_date)
            self.corrections_made.extend(corrections_this_date)

    def apply_corrections(self, corrections):
        """Apply database corrections"""
        for correction in corrections:
            try:
                trip_id = correction['trip_id']
                new_fish_count = correction['new_fish_count']

                # Update the trip record
                update_response = self.supabase.table('trips').update({
                    'total_fish': new_fish_count
                }).eq('id', trip_id).execute()

                if update_response.data:
                    print(f"    ✅ Updated trip {trip_id}: {correction['old_fish_count']} → {new_fish_count} fish")
                else:
                    print(f"    ❌ Failed to update trip {trip_id}")

            except Exception as e:
                print(f"    ❌ Error updating trip {correction['trip_id']}: {e}")

    def generate_september_dates(self):
        """Generate all September 2025 dates"""
        dates = []
        start_date = datetime(2025, 9, 1)

        for i in range(30):  # September has 30 days
            date = start_date + timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))

        return dates

    def run_full_september_verification(self):
        """Run verification for all of September 2025"""
        print("🚨 SEPTEMBER 2025 DAILY VERIFICATION & CORRECTION")
        print("=" * 70)
        print("This will verify each day against source and make real-time corrections")
        print("")

        dates = self.generate_september_dates()

        for date in dates:
            self.verify_and_correct_date(date)

        # Generate summary
        print(f"\n" + "=" * 70)
        print(f"🎯 VERIFICATION COMPLETE")
        print(f"=" * 70)
        print(f"Total Corrections Made: {len(self.corrections_made)}")

        if self.corrections_made:
            print(f"\n📊 CORRECTIONS SUMMARY:")
            for correction in self.corrections_made:
                print(f"  {correction['date']} - {correction['boat']}: {correction['old_fish_count']} → {correction['new_fish_count']} fish")

        # Save corrections log
        with open('september_corrections_log.json', 'w') as f:
            json.dump(self.corrections_made, f, indent=2, default=str)

        print(f"\n✅ Corrections log saved to: september_corrections_log.json")

def main():
    corrector = DailyVerificationCorrector()
    corrector.run_full_september_verification()

if __name__ == "__main__":
    main()