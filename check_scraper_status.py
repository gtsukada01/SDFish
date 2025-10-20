#!/usr/bin/env python3
"""
Check Scraper Status
====================

Analyzes the Supabase database to determine:
- Current data coverage (date ranges)
- Missing dates that need scraping
- Database statistics (trips, boats, species, landings)
- Recommended scraping parameters

Usage:
    python3 check_scraper_status.py
"""

import sys
from datetime import datetime, timedelta
from supabase import create_client
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Supabase configuration
SUPABASE_URL = "https://ulsbtwqhwnrpkourphiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk"

def main():
    """Main status check"""
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}📊 San Diego Fish Scraper - Database Status Check")
    print(f"{Fore.MAGENTA}{'='*80}\n")

    try:
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"{Fore.GREEN}✅ Connected to Supabase\n")

        # ===================================================================
        # SECTION 1: Database Statistics
        # ===================================================================
        print(f"{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}📈 Database Statistics")
        print(f"{Fore.CYAN}{'─'*80}")

        # Count landings
        landings = supabase.table('landings').select('id', count='exact').execute()
        landing_count = landings.count if hasattr(landings, 'count') else len(landings.data)
        print(f"{Fore.GREEN}✅ Landings: {landing_count}")

        # Count boats
        boats = supabase.table('boats').select('id', count='exact').execute()
        boat_count = boats.count if hasattr(boats, 'count') else len(boats.data)
        print(f"{Fore.GREEN}✅ Boats: {boat_count}")

        # Count trips
        trips = supabase.table('trips').select('id', count='exact').execute()
        trip_count = trips.count if hasattr(trips, 'count') else len(trips.data)
        print(f"{Fore.GREEN}✅ Trips: {trip_count:,}")

        # Count catches
        catches = supabase.table('catches').select('id', count='exact').execute()
        catch_count = catches.count if hasattr(catches, 'count') else len(catches.data)
        print(f"{Fore.GREEN}✅ Catches: {catch_count:,}")

        # ===================================================================
        # SECTION 2: Date Coverage
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}📅 Date Coverage Analysis")
        print(f"{Fore.CYAN}{'─'*80}")

        # Get earliest trip date
        earliest = supabase.table('trips').select('trip_date').order('trip_date', desc=False).limit(1).execute()
        if earliest.data:
            earliest_date = datetime.fromisoformat(earliest.data[0]['trip_date']).date()
            print(f"{Fore.GREEN}✅ Earliest trip: {earliest_date}")
        else:
            print(f"{Fore.RED}❌ No trips found in database")
            sys.exit(1)

        # Get latest trip date
        latest = supabase.table('trips').select('trip_date').order('trip_date', desc=True).limit(1).execute()
        if latest.data:
            latest_date = datetime.fromisoformat(latest.data[0]['trip_date']).date()
            print(f"{Fore.GREEN}✅ Latest trip: {latest_date}")
        else:
            print(f"{Fore.RED}❌ No trips found in database")
            sys.exit(1)

        # Calculate days covered
        days_covered = (latest_date - earliest_date).days + 1
        print(f"{Fore.GREEN}✅ Date range: {days_covered} days ({earliest_date} to {latest_date})")

        # ===================================================================
        # SECTION 3: Missing Dates Analysis
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}⚠️  Missing Dates Analysis")
        print(f"{Fore.CYAN}{'─'*80}")

        # Calculate how many days since latest trip
        today = datetime.now().date()
        days_behind = (today - latest_date).days

        if days_behind == 0:
            print(f"{Fore.GREEN}✅ Database is up-to-date! (latest trip is today)")
        elif days_behind == 1:
            print(f"{Fore.YELLOW}⚠️  Database is 1 day behind (latest trip: yesterday)")
            print(f"{Fore.CYAN}💡 Recommendation: Scrape from {latest_date}")
        else:
            print(f"{Fore.YELLOW}⚠️  Database is {days_behind} days behind")
            print(f"{Fore.YELLOW}   Latest trip: {latest_date}")
            print(f"{Fore.YELLOW}   Today: {today}")
            print(f"{Fore.YELLOW}   Missing dates: {latest_date + timedelta(days=1)} to {today}")

            # Calculate estimated scraping time
            avg_trips_per_day = 10  # Rough estimate
            estimated_trips = days_behind * avg_trips_per_day
            estimated_minutes = estimated_trips / 10  # ~10 trips per minute with 2-5s delays
            print(f"\n{Fore.CYAN}⏱️  Estimated scraping time:")
            print(f"{Fore.CYAN}   ~{estimated_trips} trips to scrape")
            print(f"{Fore.CYAN}   ~{estimated_minutes:.1f} minutes at 10 trips/min")

            # Recommended command
            recommended_date = latest_date - timedelta(days=1)  # Start 1 day before to catch any updates
            print(f"\n{Fore.GREEN}💡 Recommended command:")
            print(f"{Fore.WHITE}   python3 sd_fish_scraper.py --start-date {recommended_date}")

        # ===================================================================
        # SECTION 4: Recent Activity
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}📊 Recent Activity (Last 30 Days)")
        print(f"{Fore.CYAN}{'─'*80}")

        thirty_days_ago = (today - timedelta(days=30)).isoformat()

        # Trips in last 30 days
        recent_trips = supabase.table('trips').select('id', count='exact').gte('trip_date', thirty_days_ago).execute()
        recent_trip_count = recent_trips.count if hasattr(recent_trips, 'count') else len(recent_trips.data)
        print(f"{Fore.GREEN}✅ Trips in last 30 days: {recent_trip_count}")

        # Unique boats in last 30 days
        recent_boats = supabase.table('trips').select('boat_id').gte('trip_date', thirty_days_ago).execute()
        unique_boats = len(set(trip['boat_id'] for trip in recent_boats.data))
        print(f"{Fore.GREEN}✅ Active boats (last 30 days): {unique_boats}")

        # Total fish caught in last 30 days (query catches table directly)
        recent_trip_ids = [trip['id'] for trip in recent_trips.data]
        if recent_trip_ids:
            recent_catches = supabase.table('catches').select('count').in_('trip_id', recent_trip_ids).execute()
            total_fish = sum(catch['count'] for catch in recent_catches.data)
            print(f"{Fore.GREEN}✅ Total fish caught (last 30 days): {total_fish:,}")
        else:
            print(f"{Fore.YELLOW}⚠️  No trips in last 30 days")

        # ===================================================================
        # SECTION 5: Top Landings
        # ===================================================================
        print(f"\n{Fore.CYAN}{'─'*80}")
        print(f"{Fore.CYAN}🏆 Top Landings (by trip count)")
        print(f"{Fore.CYAN}{'─'*80}")

        # Get all boats with landing info
        boats_data = supabase.table('boats').select('id, name, landing_id, landings(name)').execute()

        # Count trips per landing
        landing_trips = {}
        for boat in boats_data.data:
            landing_name = boat['landings']['name'] if boat.get('landings') else 'Unknown'

            # Count trips for this boat
            boat_trips = supabase.table('trips').select('id', count='exact').eq('boat_id', boat['id']).execute()
            boat_trip_count = boat_trips.count if hasattr(boat_trips, 'count') else len(boat_trips.data)

            if landing_name not in landing_trips:
                landing_trips[landing_name] = 0
            landing_trips[landing_name] += boat_trip_count

        # Sort and display top 5
        sorted_landings = sorted(landing_trips.items(), key=lambda x: x[1], reverse=True)[:5]
        for idx, (landing, count) in enumerate(sorted_landings, 1):
            print(f"{Fore.GREEN}{idx}. {landing}: {count:,} trips")

        # ===================================================================
        # FINAL SUMMARY
        # ===================================================================
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}📋 Summary")
        print(f"{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.CYAN}Database: {trip_count:,} trips from {earliest_date} to {latest_date}")

        if days_behind > 0:
            print(f"{Fore.YELLOW}Status: ⚠️  {days_behind} days behind")
            print(f"{Fore.GREEN}\nNext steps:")
            print(f"{Fore.WHITE}1. Run: python3 sd_fish_scraper.py --start-date {latest_date - timedelta(days=1)}")
            print(f"{Fore.WHITE}2. Test first with: --dry-run --max-pages 2")
            print(f"{Fore.WHITE}3. Monitor: tail -f scraper.log")
        else:
            print(f"{Fore.GREEN}Status: ✅ Up-to-date!")

        print(f"{Fore.MAGENTA}{'='*80}\n")

    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
