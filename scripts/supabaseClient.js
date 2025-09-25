/**
 * Direct Supabase Client for Production Deployment
 * Connects directly to Supabase database for live data
 */

// Supabase configuration
const SUPABASE_URL = 'https://ulsbtwqhwnrpkourphiq.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY1OTk2MDIsImV4cCI6MjA0MjE3NTYwMn0.MiGiAOUWKPOJ7SpgcRdEYMHf8RYrSKNEMaQGiZUcB8g';

/**
 * Direct Supabase query function
 * @param {string} query - SQL query string
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Query result
 */
async function querySupabase(query, params = {}) {
  const url = `${SUPABASE_URL}/rest/v1/rpc/${query}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Prefer': 'return=representation'
    },
    body: JSON.stringify(params)
  });

  if (!response.ok) {
    throw new Error(`Supabase query failed: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get fishing trips with filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise<Array>} Array of fishing trips
 */
async function getFishingTrips(filters = {}) {
  let query = `${SUPABASE_URL}/rest/v1/trips?select=*,boat_landings(*),catches(*)`;

  // Add filters
  const params = [];
  if (filters.landing_id && filters.landing_id !== 'all') {
    params.push(`landing_id=eq.${filters.landing_id}`);
  }
  if (filters.boat_id) {
    params.push(`boat_id=eq.${filters.boat_id}`);
  }
  if (filters.start_date) {
    params.push(`trip_date=gte.${filters.start_date}`);
  }
  if (filters.end_date) {
    params.push(`trip_date=lte.${filters.end_date}`);
  }

  if (params.length > 0) {
    query += '&' + params.join('&');
  }

  // Add ordering and limit
  query += '&order=trip_date.desc&limit=100';

  const response = await fetch(query, {
    headers: {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch trips: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Get summary statistics
 * @returns {Promise<Object>} Statistics object
 */
async function getStats() {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/get_dashboard_stats`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
    }
  });

  if (!response.ok) {
    // Fallback: calculate basic stats
    const trips = await getFishingTrips();
    return {
      total_trips: trips.length,
      total_anglers: trips.reduce((sum, trip) => sum + (trip.anglers || 0), 0),
      total_fish: trips.reduce((sum, trip) => sum + trip.catches.reduce((catchSum, c) => catchSum + c.count, 0), 0),
      unique_species: new Set(trips.flatMap(trip => trip.catches.map(c => c.species_name))).size
    };
  }

  const result = await response.json();
  return result[0] || {};
}

/**
 * Get boat landings for navigation
 * @returns {Promise<Array>} Array of boat landings
 */
async function getBoatLandings() {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/boat_landings?select=*&order=landing_name`, {
    headers: {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch landings: ${response.statusText}`);
  }

  return await response.json();
}

export default {
  getFishingTrips,
  getStats,
  getBoatLandings,
  querySupabase
};