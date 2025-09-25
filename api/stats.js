// Vercel serverless function for stats endpoint
export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Direct Supabase query using service role key (environment variable)
    const SUPABASE_URL = process.env.SUPABASE_URL;
    const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

    if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
      throw new Error('Missing Supabase configuration');
    }

    // Query trips for statistics
    const response = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=*,catches(*)`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.statusText}`);
    }

    const trips = await response.json();

    // Calculate real statistics from actual data
    const stats = {
      trips: trips.length,
      boats: new Set(trips.map(t => t.boat_id)).size,
      fish: trips.reduce((sum, trip) => {
        return sum + (trip.catches?.reduce((catchSum, c) => catchSum + (c.count || 0), 0) || 0);
      }, 0),
      avgPerTrip: trips.length > 0 ?
        Math.round((trips.reduce((sum, trip) => {
          return sum + (trip.catches?.reduce((catchSum, c) => catchSum + (c.count || 0), 0) || 0);
        }, 0) / trips.length) * 10) / 10 : 0
    };

    res.status(200).json(stats);

  } catch (error) {
    console.error('Stats API error:', error);
    res.status(500).json({ error: error.message });
  }
}