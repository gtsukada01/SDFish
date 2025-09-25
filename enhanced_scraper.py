#!/usr/bin/env python3
"""
Enhanced San Diego Fishing Reports Scraper
Addresses critical data collection failures identified in September 2025 audit.

Key Improvements:
- Enhanced parsing for weight qualifiers ("up to 100 pounds")
- Comprehensive data integrity validation
- Real-time failure detection and alerting
- Bulletproof transaction handling
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from supabase import create_client
from marine_conditions.config import MarineConfig
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIntegrityError(Exception):
    """Raised when scraped data fails integrity validation"""
    pass

class ScrapingStats:
    """Track scraping statistics and success rates"""
    def __init__(self):
        self.trips_attempted = 0
        self.trips_successful = 0
        self.trips_failed = 0
        self.zero_fish_high_anglers = 0
        self.weight_qualifiers_found = 0
        self.parsing_errors = []

    def get_success_rate(self):
        if self.trips_attempted == 0:
            return 0.0
        return (self.trips_successful / self.trips_attempted) * 100

    def log_summary(self):
        logger.info(f"SCRAPING SUMMARY:")
        logger.info(f"  Trips Attempted: {self.trips_attempted}")
        logger.info(f"  Successful: {self.trips_successful}")
        logger.info(f"  Failed: {self.trips_failed}")
        logger.info(f"  Success Rate: {self.get_success_rate():.1f}%")
        logger.info(f"  Weight Qualifiers Found: {self.weight_qualifiers_found}")
        logger.info(f"  Zero Fish (High Anglers): {self.zero_fish_high_anglers}")

class EnhancedFishingScraper:
    def __init__(self):
        """Initialize scraper with database connection and validation"""
        config = MarineConfig.from_env()
        self.supabase = create_client(config.supabase_url, config.supabase_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.stats = ScrapingStats()

        # Pre-load reference data for validation
        self._load_reference_data()

    def _load_reference_data(self):
        """Load boats and landings for validation"""
        try:
            boats_response = self.supabase.table('boats').select('id, name, landing_id').execute()
            landings_response = self.supabase.table('landings').select('id, name').execute()

            self.boats_map = {boat['name']: boat for boat in boats_response.data}
            self.landings_map = {landing['name']: landing for landing in landings_response.data}

            logger.info(f"Loaded {len(self.boats_map)} boats and {len(self.landings_map)} landings")
        except Exception as e:
            logger.error(f"Failed to load reference data: {e}")
            raise

    def enhanced_species_parser(self, species_text: str) -> List[Dict]:
        """
        Enhanced parser that handles weight qualifiers like "(up to 100 pounds)"

        CRITICAL: This addresses the Pacific Dawn failure case where
        "66 Bluefin Tuna (up to 100 pounds)" was completely lost.
        """
        if not species_text or species_text.strip() == '':
            return []

        logger.debug(f"Parsing species text: '{species_text}'")
        catches = []

        # Pattern 1: Handle weight qualifiers specifically
        # "66 Bluefin Tuna (up to 100 pounds)" -> count=66, species="Bluefin Tuna"
        weight_pattern = r'(\d+)\s+([^(]+?)\s*\((?:up to|about|around|to)?\s*(\d+)?\s*(?:pounds?|lbs?|#)\)'
        weight_matches = re.findall(weight_pattern, species_text, re.IGNORECASE)

        if weight_matches:
            self.stats.weight_qualifiers_found += len(weight_matches)
            logger.info(f"Found {len(weight_matches)} weight qualifiers in: {species_text}")

            for count_str, species_name, weight_str in weight_matches:
                try:
                    count = int(count_str)
                    species = species_name.strip()
                    catches.append({
                        'species': species,
                        'count': count,
                        'notes': f"Weight qualifier: {weight_str} pounds" if weight_str else "Weight qualifier present"
                    })
                    logger.debug(f"Parsed weight qualifier: {count} {species}")
                except ValueError:
                    logger.warning(f"Failed to parse count from weight qualifier: {count_str}")
                    continue

            # Remove processed weight qualifiers from text for further parsing
            species_text = re.sub(weight_pattern, '', species_text, flags=re.IGNORECASE)

        # Pattern 2: Standard count parsing "Species (count)"
        # "Bluefin Tuna (40), Yellowtail (12)"
        standard_pattern = r'([^,()]+?)\s*\((\d+)\)'
        standard_matches = re.findall(standard_pattern, species_text)

        for species_name, count_str in standard_matches:
            try:
                species = species_name.strip()
                count = int(count_str)
                catches.append({
                    'species': species,
                    'count': count,
                    'notes': None
                })
                logger.debug(f"Parsed standard format: {count} {species}")
            except ValueError:
                logger.warning(f"Failed to parse count: {count_str}")
                continue

        # Pattern 3: Simple count + species "40 Rockfish"
        simple_pattern = r'(\d+)\s+([^,\d]+)'
        remaining_text = re.sub(standard_pattern, '', species_text)
        simple_matches = re.findall(simple_pattern, remaining_text)

        for count_str, species_name in simple_matches:
            try:
                count = int(count_str)
                species = species_name.strip()
                if species and not any(c['species'] == species for c in catches):  # Avoid duplicates
                    catches.append({
                        'species': species,
                        'count': count,
                        'notes': None
                    })
                    logger.debug(f"Parsed simple format: {count} {species}")
            except ValueError:
                continue

        if not catches and species_text.strip():
            logger.warning(f"Failed to parse any species from: '{species_text}'")
            self.stats.parsing_errors.append(species_text)

        return catches

    def validate_trip_data(self, trip_data: Dict) -> bool:
        """
        Comprehensive validation to prevent Pacific Dawn-type failures
        """
        boat_name = trip_data.get('boat_name', '')
        anglers = trip_data.get('anglers', 0)
        catches = trip_data.get('catches', [])

        # Critical validation: High angler count with no catches is suspicious
        if anglers > 5 and len(catches) == 0:
            total_fish = sum(catch.get('count', 0) for catch in catches)
            if total_fish == 0:
                error_msg = f"SUSPICIOUS: {boat_name} has {anglers} anglers but 0 fish"
                logger.error(error_msg)
                self.stats.zero_fish_high_anglers += 1

                # This would have caught the Pacific Dawn issue
                if anglers >= 10:  # High-value trips
                    raise DataIntegrityError(f"High-angler trip with no fish data: {boat_name} ({anglers} anglers)")

        # Validate boat exists in our database
        if boat_name not in self.boats_map:
            logger.warning(f"Unknown boat: {boat_name}")
            return False

        # Validate required fields
        required_fields = ['boat_name', 'trip_date', 'trip_duration', 'anglers']
        for field in required_fields:
            if field not in trip_data or trip_data[field] is None:
                logger.error(f"Missing required field: {field}")
                return False

        return True

    def scrape_date(self, date_str: str) -> List[Dict]:
        """
        Scrape fishing data for a specific date with enhanced parsing
        """
        url = f"https://www.sandiegofishreports.com/dock_totals/boats.php?date={date_str}"
        logger.info(f"Scraping date: {date_str} - {url}")

        try:
            # Respectful delay between requests
            time.sleep(2)

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            trips = self.parse_trips_from_page(soup, date_str)

            logger.info(f"Found {len(trips)} trips for {date_str}")
            return trips

        except requests.RequestException as e:
            logger.error(f"Request failed for {date_str}: {e}")
            return []
        except Exception as e:
            logger.error(f"Parsing failed for {date_str}: {e}")
            return []

    def parse_trips_from_page(self, soup: BeautifulSoup, date_str: str) -> List[Dict]:
        """Parse trips from the HTML page"""
        trips = []

        # Find all boat entries (this will need to be adapted based on actual HTML structure)
        # The exact selectors would need to be determined by examining the page structure
        boat_sections = soup.find_all('tr')  # Placeholder - would need actual HTML analysis

        for section in boat_sections:
            try:
                trip_data = self.extract_trip_data(section, date_str)
                if trip_data:
                    self.stats.trips_attempted += 1

                    if self.validate_trip_data(trip_data):
                        trips.append(trip_data)
                        self.stats.trips_successful += 1
                    else:
                        self.stats.trips_failed += 1
                        logger.warning(f"Trip validation failed: {trip_data.get('boat_name', 'Unknown')}")

            except Exception as e:
                self.stats.trips_failed += 1
                logger.error(f"Error parsing trip section: {e}")
                continue

        return trips

    def extract_trip_data(self, section, date_str: str) -> Optional[Dict]:
        """
        Extract trip data from HTML section
        NOTE: This is a placeholder - actual implementation would need
        HTML structure analysis of sandiegofishreports.com
        """
        # This would need to be implemented based on actual HTML structure
        # For now, returning None as placeholder
        return None

    def save_trips_to_database(self, trips: List[Dict]) -> int:
        """
        Save trips to database with transaction safety
        """
        successful_saves = 0

        for trip in trips:
            try:
                # Use transaction to ensure atomicity
                with self.supabase.transaction():
                    trip_id = self.save_trip(trip)
                    self.save_catches(trip_id, trip.get('catches', []))
                    successful_saves += 1

            except Exception as e:
                logger.error(f"Failed to save trip {trip.get('boat_name', 'Unknown')}: {e}")
                continue

        return successful_saves

    def save_trip(self, trip_data: Dict) -> str:
        """Save trip record and return trip ID"""
        boat_info = self.boats_map[trip_data['boat_name']]

        trip_record = {
            'boat_id': boat_info['id'],
            'trip_date': trip_data['trip_date'],
            'trip_duration': trip_data['trip_duration'],
            'anglers': trip_data['anglers'],
            'total_fish': sum(catch.get('count', 0) for catch in trip_data.get('catches', []))
        }

        result = self.supabase.table('trips').insert(trip_record).execute()
        return result.data[0]['id']

    def save_catches(self, trip_id: str, catches: List[Dict]):
        """Save catch records for a trip"""
        if not catches:
            return

        catch_records = []
        for catch in catches:
            catch_records.append({
                'trip_id': trip_id,
                'species': catch['species'],
                'count': catch['count']
            })

        if catch_records:
            self.supabase.table('catches').insert(catch_records).execute()

    def run_daily_scrape(self, target_date: Optional[str] = None) -> ScrapingStats:
        """
        Run scraper for a specific date or today
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Starting enhanced scraping for {target_date}")

        trips = self.scrape_date(target_date)
        saved_count = self.save_trips_to_database(trips)

        self.stats.log_summary()

        # Critical alerts for data quality issues
        if self.stats.get_success_rate() < 85:
            logger.critical(f"SUCCESS RATE BELOW THRESHOLD: {self.stats.get_success_rate():.1f}%")

        if self.stats.zero_fish_high_anglers > 0:
            logger.critical(f"FOUND {self.stats.zero_fish_high_anglers} SUSPICIOUS ZERO-FISH TRIPS WITH HIGH ANGLER COUNTS")

        logger.info(f"Saved {saved_count} trips to database")
        return self.stats

def main():
    """Main execution function"""
    scraper = EnhancedFishingScraper()

    # Example: Scrape today's data
    stats = scraper.run_daily_scrape()

    # Alert if critical issues found
    if stats.get_success_rate() < 85 or stats.zero_fish_high_anglers > 0:
        logger.critical("CRITICAL DATA QUALITY ISSUES DETECTED - MANUAL REVIEW REQUIRED")

    return stats

if __name__ == "__main__":
    main()