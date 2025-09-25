"""API server for fishing dashboard data"""

from flask import Flask, jsonify
from flask_cors import CORS
from marine_conditions.config import MarineConfig
from supabase import create_client
from datetime import datetime, timedelta
from collections import defaultdict
import os
import math

app = Flask(__name__)
CORS(app)

# Initialize Supabase client
os.environ['SUPABASE_URL'] = "https://ulsbtwqhwnrpkourphiq.supabase.co"
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"

config = MarineConfig.from_env()
supabase = create_client(config.supabase_url, config.supabase_key)

def get_moon_phase(date):
    """Calculate moon phase for a given date using lunar cycle approximation"""
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')

    # Known new moon: January 11, 2025
    new_moon_reference = datetime(2025, 1, 11)
    lunar_cycle = 29.53059  # Average lunar cycle in days

    # Calculate days since reference new moon
    days_since = (date - new_moon_reference).days

    # Calculate position in current lunar cycle (0-29.53)
    cycle_position = days_since % lunar_cycle

    # Determine moon phase based on cycle position
    if cycle_position < 1.84566:
        return "New Moon"
    elif cycle_position < 7.38264:
        return "Waxing Crescent"
    elif cycle_position < 9.22830:
        return "First Quarter"
    elif cycle_position < 14.76530:
        return "Waxing Gibbous"
    elif cycle_position < 16.61095:
        return "Full Moon"
    elif cycle_position < 22.14794:
        return "Waning Gibbous"
    elif cycle_position < 23.99359:
        return "Last Quarter"
    else:
        return "Waning Crescent"

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    try:
        # Get total trips
        trips = supabase.table('trips').select('*', count='exact').execute()
        total_trips = trips.count

        # Get total fish
        catches = supabase.table('catches').select('count').execute()
        total_fish = sum(catch['count'] for catch in catches.data if catch['count'])

        # Calculate average
        avg_per_trip = total_fish / total_trips if total_trips > 0 else 0

        # Get boat count
        boats = supabase.table('boats').select('*', count='exact').execute()
        total_boats = boats.count

        return jsonify({
            'trips': total_trips,
            'fish': total_fish,
            'avgPerTrip': round(avg_per_trip, 1),
            'boats': total_boats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<period>')
def get_period_stats(period):
    """Get statistics for a specific period with optional filters"""
    try:
        from flask import request

        # Get filter parameters
        species_filter = request.args.get('species')
        duration_filter = request.args.get('duration')
        boat_filter = request.args.get('boat')
        landing_id = request.args.get('landing', type=int)

        # Calculate date range
        end_date = datetime.now()
        if period == 'last-30-days':
            start_date = end_date - timedelta(days=30)
        elif period == 'last-7-days':
            start_date = end_date - timedelta(days=7)
        elif period == 'year-to-date':
            start_date = datetime(end_date.year, 1, 1)
        elif period == 'all-time':
            start_date = datetime(2000, 1, 1)  # Effectively all time
        else:
            return jsonify({'error': 'Invalid period'}), 400

        # Get trips in period with boat info - use !inner when filtering by landing
        if landing_id:
            trips_query = supabase.table('trips').select('*, boat:boats!inner(name)', count='exact')
            trips_query = trips_query.gte('trip_date', start_date.strftime('%Y-%m-%d'))
            trips_query = trips_query.lte('trip_date', end_date.strftime('%Y-%m-%d'))
            trips_query = trips_query.eq('boat.landing_id', landing_id)
        else:
            trips_query = supabase.table('trips').select('*, boat:boats(name)', count='exact')
            trips_query = trips_query.gte('trip_date', start_date.strftime('%Y-%m-%d'))
            trips_query = trips_query.lte('trip_date', end_date.strftime('%Y-%m-%d'))

        # Apply duration filter
        if duration_filter:
            trips_query = trips_query.eq('trip_duration', duration_filter)

        # Apply boat filter at database level
        if boat_filter:
            boat_result = supabase.table('boats').select('id').eq('name', boat_filter).execute()
            if boat_result.data:
                boat_id = boat_result.data[0]['id']
                trips_query = trips_query.eq('boat_id', boat_id)

        trips = trips_query.execute()
        trip_ids = [t['id'] for t in trips.data]
        trips_count = trips.count

        # Get fish caught in those trips
        total_fish = 0
        if trip_ids:
            catches_query = supabase.table('catches').select('count, species').in_('trip_id', trip_ids)

            # Apply species filter
            if species_filter:
                catches_query = catches_query.eq('species', species_filter)

            catches = catches_query.execute()
            catch_sum = sum(catch['count'] for catch in catches.data if catch['count'])

            # Also get sum of total_fish from trips as fallback
            trips_total = sum(t.get('total_fish', 0) or 0 for t in trips.data)

            # Use maximum of both sources for reliability
            total_fish = max(catch_sum, trips_total) if not species_filter else catch_sum

        # Calculate average
        avg_per_trip = total_fish / trips_count if trips_count > 0 else 0

        # Get unique boats
        if boat_filter:
            unique_boats = 1 if trips_count > 0 else 0
        elif trip_ids:
            boat_trips = supabase.table('trips').select('boat_id').in_('id', trip_ids).execute()
            unique_boats = len(set(t['boat_id'] for t in boat_trips.data))
        else:
            unique_boats = 0

        return jsonify({
            'trips': trips_count,
            'fish': total_fish,
            'avgPerTrip': round(avg_per_trip, 1),
            'boats': unique_boats,
            'period': period
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-catches/<int:days>')
def get_daily_catches(days):
    """Get daily catch data for charts with optional filters"""
    try:
        from flask import request

        # Get filter parameters
        species_filter = request.args.get('species')
        duration_filter = request.args.get('duration')
        boat_filter = request.args.get('boat')
        landing_id = request.args.get('landing', type=int)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get trips with boat info - use !inner when filtering by landing
        if landing_id:
            trips_query = supabase.table('trips').select('*, boat:boats!inner(name)')
            trips_query = trips_query.gte('trip_date', start_date.strftime('%Y-%m-%d'))
            trips_query = trips_query.eq('boat.landing_id', landing_id)
        else:
            trips_query = supabase.table('trips').select('*, boat:boats(name)')
            trips_query = trips_query.gte('trip_date', start_date.strftime('%Y-%m-%d'))

        # Apply duration filter
        if duration_filter:
            trips_query = trips_query.eq('trip_duration', duration_filter)

        # Apply boat filter at database level
        if boat_filter:
            boat_result = supabase.table('boats').select('id').eq('name', boat_filter).execute()
            if boat_result.data:
                boat_id = boat_result.data[0]['id']
                trips_query = trips_query.eq('boat_id', boat_id)

        trips = trips_query.execute()
        filtered_trips = trips.data

        # Get all catches for these trips
        trip_ids = [t['id'] for t in filtered_trips]
        catches_data = []
        if trip_ids:
            catches_query = supabase.table('catches').select('trip_id, count, species').in_('trip_id', trip_ids)

            # Apply species filter if requested
            if species_filter:
                catches_query = catches_query.eq('species', species_filter)

            catches_result = catches_query.execute()
            catches_data = catches_result.data or []

        # Build trip to fish count map from BOTH sources
        trip_fish = defaultdict(int)

        # First get catch details
        for catch in catches_data:
            trip_fish[catch['trip_id']] += catch['count']

        # Then use total_fish as fallback for trips without catches
        for trip in filtered_trips:
            trip_id = trip['id']
            if trip_id not in trip_fish or trip_fish[trip_id] == 0:
                # Use total_fish if no catch data available
                total_fish = trip.get('total_fish', 0) or 0
                if total_fish > 0:
                    trip_fish[trip_id] = total_fish

        # Group by date (use filtered trips)
        daily_data = defaultdict(lambda: {'trips': 0, 'fish': 0})
        for trip in filtered_trips:
            date = trip['trip_date']
            daily_data[date]['trips'] += 1
            daily_data[date]['fish'] += trip_fish.get(trip['id'], 0)

        # Format for chart
        labels = []
        fish_values = []
        trip_values = []

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            labels.append(current_date.strftime('%m/%d'))
            fish_values.append(daily_data[date_str]['fish'])
            trip_values.append(daily_data[date_str]['trips'])
            current_date += timedelta(days=1)

        # Calculate moon phases for each date
        moon_phases = []
        current_date = start_date
        while current_date <= end_date:
            moon_phase = get_moon_phase(current_date.strftime('%Y-%m-%d'))
            moon_phases.append(moon_phase)
            current_date += timedelta(days=1)

        return jsonify({
            'labels': labels,
            'fish': fish_values,
            'trips': trip_values,
            'moonPhases': moon_phases
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-boats/<int:limit>')
def get_top_boats(limit):
    """Get top boats by fish caught with optional filters"""
    try:
        # Check for filters in query params
        from flask import request
        landing_id = request.args.get('landing', type=int)
        species_filter = request.args.get('species')
        duration_filter = request.args.get('duration')
        boat_filter = request.args.get('boat')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        # Build base query - use !inner when filtering by landing
        if landing_id:
            trips_query = supabase.table('trips').select('*, boat:boats!inner(name)')
            trips_query = trips_query.eq('boat.landing_id', landing_id)
        else:
            trips_query = supabase.table('trips').select('*, boat:boats(name)')

        # Apply optional date bounds
        if start_date:
            trips_query = trips_query.gte('trip_date', start_date)
        if end_date:
            trips_query = trips_query.lte('trip_date', end_date)

        # Apply duration filter
        if duration_filter:
            trips_query = trips_query.eq('trip_duration', duration_filter)

        # Apply boat filter at database level
        if boat_filter:
            boat_result = supabase.table('boats').select('id').eq('name', boat_filter).execute()
            if boat_result.data:
                boat_id = boat_result.data[0]['id']
                trips_query = trips_query.eq('boat_id', boat_id)

        trips = trips_query.execute()
        filtered_trips = trips.data

        # Get trip IDs for downstream lookups
        trip_ids = [t['id'] for t in filtered_trips]

        # Helper to keep Supabase "in" queries within a safe batch size
        def fetch_catches_for_ids(ids):
            if not ids:
                return []

            batch_size = 200
            results = []
            for i in range(0, len(ids), batch_size):
                batch = ids[i : i + batch_size]
                query = supabase.table('catches').select('trip_id, count, species').in_('trip_id', batch)
                if species_filter:
                    query = query.eq('species', species_filter)
                batch_result = query.execute()
                results.extend(batch_result.data or [])
            return results

        # Build trip to fish map
        trip_fish = defaultdict(int)

        if species_filter:
            # When filtering by species we must rely on catch records only
            catches_data = fetch_catches_for_ids(trip_ids)
            for catch in catches_data:
                trip_fish[catch['trip_id']] += catch['count']
        else:
            # Default to total_fish when available to avoid pulling massive catch datasets
            missing_totals = []
            for trip in filtered_trips:
                total_fish = trip.get('total_fish', 0) or 0
                if total_fish > 0:
                    trip_fish[trip['id']] = total_fish
                else:
                    missing_totals.append(trip['id'])

            # Only fetch catches for trips missing total_fish
            if missing_totals:
                catches_data = fetch_catches_for_ids(missing_totals)
                for catch in catches_data:
                    trip_fish[catch['trip_id']] += catch['count']

        # Aggregate by boat (use filtered trips)
        boat_totals = defaultdict(lambda: {'name': '', 'fish': 0, 'trips': 0})
        for trip in filtered_trips:
            if trip['boat']:
                boat_id = trip['boat_id']
                boat_totals[boat_id]['name'] = trip['boat']['name']
                boat_totals[boat_id]['trips'] += 1
                boat_totals[boat_id]['fish'] += trip_fish.get(trip['id'], 0)

        # Sort by fish count
        sorted_boats = sorted(boat_totals.values(), key=lambda x: x['fish'], reverse=True)[:limit]

        return jsonify({
            'labels': [b['name'] for b in sorted_boats],
            'fish': [b['fish'] for b in sorted_boats],
            'trips': [b['trips'] for b in sorted_boats]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/species-breakdown')
def get_species_breakdown():
    """Get species breakdown"""
    try:
        # Get all catches
        catches = supabase.table('catches').select('species, count').execute()

        # Aggregate by species
        species_totals = defaultdict(int)
        for catch in catches.data:
            species_totals[catch['species']] += catch['count']

        # Sort by count
        sorted_species = sorted(species_totals.items(), key=lambda x: x[1], reverse=True)[:10]

        return jsonify({
            'labels': [s[0] for s in sorted_species],
            'values': [s[1] for s in sorted_species]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters')
def get_filters():
    """Get all available filter options from real data, optionally filtered by landing"""
    try:
        # Check for landing filter in query params
        from flask import request
        landing_id = request.args.get('landing', type=int)

        if landing_id:
            # Get trips filtered by landing (including duration data)
            trips = supabase.table('trips').select('id, trip_duration, boat:boats!inner(name, landing_id)').eq('boats.landing_id', landing_id).execute()
            trip_ids = [t['id'] for t in trips.data]

            # Get species from catches for these trips
            if trip_ids:
                catches = supabase.table('catches').select('species').in_('trip_id', trip_ids).execute()
            else:
                catches = {'data': []}

            # Get boats for this landing
            boats = supabase.table('boats').select('name').eq('landing_id', landing_id).execute()
        else:
            # Get all data (no landing filter)
            catches = supabase.table('catches').select('species').execute()
            boats = supabase.table('boats').select('name').execute()
            trips = supabase.table('trips').select('trip_duration').execute()

        # Process species
        species_counts = {}
        for catch in catches.data:
            species = catch['species']
            species_counts[species] = species_counts.get(species, 0) + 1

        # Sort species alphabetically
        species_list = sorted(species_counts.keys())

        # Process boats
        boat_list = sorted(set(b['name'] for b in boats.data))

        # Process durations
        duration_counts = {}
        for trip in trips.data:
            if trip['trip_duration']:
                duration = trip['trip_duration']
                duration_counts[duration] = duration_counts.get(duration, 0) + 1

        # Sort durations in logical order (matching index.html)
        duration_order = [
            '1/2 Day AM', '1/2 Day PM', '1/2 Day Twilight',
            '3/4 Day',
            'Full Day', 'Full Day (Local)', 'Full Day Offshore', 'Full Day Coronado Islands',
            'Overnight',
            '1.5 Day', '1.75 Day', '2 Day', '2.5 Day', '3 Day', '3.5 Day', '4 Day', '4.5 Day', '5 Day', '5.5 Day'
        ]

        # Sort durations according to the predefined order, with any unknown ones at the end
        duration_list = []
        for duration in duration_order:
            if duration in duration_counts:
                duration_list.append(duration)

        # Add any durations not in the predefined order
        for duration in sorted(duration_counts.keys()):
            if duration not in duration_list:
                duration_list.append(duration)

        # Get landings (San Diego only)
        landings = supabase.table('landings').select('id, name').execute()
        landing_list = [{'id': l['id'], 'name': l['name']} for l in landings.data if l['name'] != 'Unknown']

        return jsonify({
            'species': species_list,
            'boats': boat_list,
            'durations': duration_list,
            'landings': landing_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/date-range/<start>/<end>')
def get_date_range_stats(start, end):
    """Get statistics for a custom date range with optional filters"""
    try:
        from flask import request

        # Get filter parameters
        species_filter = request.args.get('species')
        duration_filter = request.args.get('duration')
        boat_filter = request.args.get('boat')
        landing_id = request.args.get('landing', type=int)

        # Get trips in date range with boat info - use !inner when filtering by landing
        if landing_id:
            trips_query = supabase.table('trips').select('*, boat:boats!inner(name)', count='exact')
            trips_query = trips_query.gte('trip_date', start).lte('trip_date', end)
            trips_query = trips_query.eq('boat.landing_id', landing_id)
        else:
            trips_query = supabase.table('trips').select('*, boat:boats(name)', count='exact')
            trips_query = trips_query.gte('trip_date', start).lte('trip_date', end)

        # Apply duration filter
        if duration_filter:
            trips_query = trips_query.eq('trip_duration', duration_filter)

        # Apply boat filter at database level
        if boat_filter:
            boat_result = supabase.table('boats').select('id').eq('name', boat_filter).execute()
            if boat_result.data:
                boat_id = boat_result.data[0]['id']
                trips_query = trips_query.eq('boat_id', boat_id)

        trips = trips_query.execute()
        trip_ids = [t['id'] for t in trips.data]
        trips_count = trips.count

        # Get fish caught in those trips
        total_fish = 0
        if trip_ids:
            catches_query = supabase.table('catches').select('count, species').in_('trip_id', trip_ids)

            # Apply species filter
            if species_filter:
                catches_query = catches_query.eq('species', species_filter)

            catches = catches_query.execute()
            catch_sum = sum(catch['count'] for catch in catches.data if catch['count'])

            # Also get sum of total_fish from trips as fallback
            trips_total = sum(t.get('total_fish', 0) or 0 for t in trips.data)

            # Use maximum of both sources for reliability
            total_fish = max(catch_sum, trips_total) if not species_filter else catch_sum

        # Calculate average
        avg_per_trip = total_fish / trips_count if trips_count > 0 else 0

        # Get unique boats
        if boat_filter:
            unique_boats = 1 if trips_count > 0 else 0
        elif trip_ids:
            boat_trips = supabase.table('trips').select('boat_id').in_('id', trip_ids).execute()
            unique_boats = len(set(t['boat_id'] for t in boat_trips.data))
        else:
            unique_boats = 0

        return jsonify({
            'trips': trips_count,
            'fish': total_fish,
            'avgPerTrip': round(avg_per_trip, 1),
            'boats': unique_boats,
            'startDate': start,
            'endDate': end
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-trips/<int:limit>')
def get_recent_trips(limit):
    """Get most recent fishing trips with details with optional filters"""
    try:
        # Check for filters in query params
        from flask import request
        landing_id = request.args.get('landing', type=int)
        species_filter = request.args.get('species')
        duration_filter = request.args.get('duration')
        boat_filter = request.args.get('boat')

        # Build base query - use !inner when filtering by landing
        if landing_id:
            trips_query = supabase.table('trips').select('*, boat:boats!inner(name, landing:landings(name))')
            trips_query = trips_query.eq('boat.landing_id', landing_id)
        else:
            trips_query = supabase.table('trips').select('*, boat:boats(name, landing:landings(name))')

        # Apply duration filter
        if duration_filter:
            trips_query = trips_query.eq('trip_duration', duration_filter)

        # For boat filter, first get the boat_id
        if boat_filter:
            boat_result = supabase.table('boats').select('id').eq('name', boat_filter).execute()
            if boat_result.data:
                boat_id = boat_result.data[0]['id']
                trips_query = trips_query.eq('boat_id', boat_id)

        # Get trips (fetch extra only for species filter now)
        fetch_limit = limit * 5 if species_filter else limit
        trips_query = trips_query.order('trip_date', desc=True).limit(fetch_limit)
        trips = trips_query.execute()

        # No need to filter by boat after fetching since we already filtered at DB level
        filtered_trips = trips.data

        # Get catches for these trips
        trip_ids = [t['id'] for t in filtered_trips]
        catches = supabase.table('catches').select('trip_id, species, count').in_('trip_id', trip_ids).execute() if trip_ids else []

        # Group catches by trip
        catches_by_trip = defaultdict(list)
        for catch in catches.data if catches else []:
            catches_by_trip[catch['trip_id']].append(catch)

        # Format trips data
        formatted_trips = []
        for trip in filtered_trips:
            trip_catches = catches_by_trip.get(trip['id'], [])

            # Apply species filter if specified
            if species_filter:
                # Only include trips that caught the specified species
                has_species = any(c['species'] == species_filter for c in trip_catches)
                if not has_species:
                    continue

            # Calculate fish count using BOTH sources for reliability
            catch_sum = sum(c['count'] for c in trip_catches) if trip_catches else 0
            trip_total_fish = trip.get('total_fish', 0) or 0
            # Use the maximum of both sources for most reliable count
            reliable_fish_count = max(catch_sum, trip_total_fish)

            # Find top species by count
            top_species = ''
            if trip_catches:
                species_counts = defaultdict(int)
                for c in trip_catches:
                    species_counts[c['species']] += c['count']
                top_species_list = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)[:2]
                top_species = ', '.join([f"{s[0]} ({s[1]})" for s in top_species_list])
            elif trip_total_fish > 0:
                # If we have total_fish but no catch details, indicate this
                top_species = f'Mixed Species ({trip_total_fish})'

            formatted_trips.append({
                'date': trip['trip_date'],
                'boat': trip['boat']['name'] if trip['boat'] else 'Unknown',
                'landing': trip['boat']['landing']['name'] if trip['boat'] and trip['boat']['landing'] else 'Unknown',
                'duration': trip['trip_duration'] or 'Unknown',
                'anglers': trip['anglers'] or 0,
                'fishCount': reliable_fish_count,
                'topSpecies': top_species or 'N/A'
            })

        # Limit to requested number of trips
        formatted_trips = formatted_trips[:limit]

        return jsonify(formatted_trips)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/moon-phase-data')
def get_moon_phase_data():
    """Get fishing data aggregated by moon phase"""
    try:
        # Get all trips with catches
        response = supabase.table('trips').select(
            'trip_date, catches(count)'
        ).execute()

        trips = response.data

        # Aggregate data by moon phase
        moon_phase_data = defaultdict(lambda: {'trips': 0, 'fish': 0})

        for trip in trips:
            trip_date = trip['trip_date']
            moon_phase = get_moon_phase(trip_date)

            moon_phase_data[moon_phase]['trips'] += 1

            # Sum up fish caught
            if trip.get('catches'):
                total_fish = sum(catch['count'] for catch in trip['catches'] if catch.get('count'))
                moon_phase_data[moon_phase]['fish'] += total_fish

        # Format for Chart.js
        moon_phases = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                      "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]

        chart_data = {
            'labels': moon_phases,
            'fish': [moon_phase_data[phase]['fish'] for phase in moon_phases],
            'trips': [moon_phase_data[phase]['trips'] for phase in moon_phases],
            'avgPerTrip': [
                round(moon_phase_data[phase]['fish'] / moon_phase_data[phase]['trips'], 1)
                if moon_phase_data[phase]['trips'] > 0 else 0
                for phase in moon_phases
            ]
        }

        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting API server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
