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
    const { landing_id, boat_id, limit = 1000, offset = 0, startDate, endDate } = req.query;

    // Build query with date range filtering to avoid September windowing
    let query = `${SUPABASE_URL}/rest/v1/trips?select=*,boat:boats(name,landing:landings(name)),catches(*)`;

    // Add date range filters FIRST to limit dataset before sorting
    if (startDate) {
      query += `&trip_date=gte.${startDate}`;
    }
    if (endDate) {
      query += `&trip_date=lte.${endDate}`;
    }

    // Add landing filter to further narrow results
    if (landing_id && landing_id !== 'all') {
      query += `&landing_id=eq.${landing_id}`;
    }

    // Add boat filter for specific boat filtering (like Liberty)
    if (boat_id && boat_id !== 'all') {
      query += `&boat_id=eq.${boat_id}`;
    }

    // Apply ordering and pagination after filtering
    query += `&order=trip_date.desc&limit=${limit}&offset=${offset}`;

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