// Vercel serverless function for trips endpoint
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const SUPABASE_URL = process.env.SUPABASE_URL;
    const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

    if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
      throw new Error('Missing Supabase configuration');
    }

    // Parse query parameters
    const { landing_id, limit = 1000, offset = 0 } = req.query;

    // Build query
    let query = `${SUPABASE_URL}/rest/v1/trips?select=*,boat:boats(name,landing:landings(name)),catches(*)&order=trip_date.desc&limit=${limit}&offset=${offset}`;

    if (landing_id && landing_id !== 'all') {
      query += `&landing_id=eq.${landing_id}`;
    }

    const response = await fetch(query, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.statusText}`);
    }

    const trips = await response.json();

    res.status(200).json({
      success: true,
      data: trips
    });

  } catch (error) {
    console.error('Trips API error:', error);
    res.status(500).json({ error: error.message });
  }
}