// Debug API endpoint to check Liberty trips directly from database
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

    // Get total trip count
    const totalResponse = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=*&limit=0`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Prefer': 'count=exact'
      }
    });

    const totalCount = totalResponse.headers.get('content-range')?.split('/')[1] || 0;

    // Get date range
    const oldestResponse = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=trip_date&order=trip_date.asc&limit=5`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });
    const oldest = await oldestResponse.json();

    const newestResponse = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=trip_date&order=trip_date.desc&limit=5`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });
    const newest = await newestResponse.json();

    // Get Liberty boat ID
    const boatResponse = await fetch(`${SUPABASE_URL}/rest/v1/boats?select=id,name&name=eq.Liberty`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });
    const libertyBoats = await boatResponse.json();

    let libertyData = { found: false, trips: 0, dates: [] };

    if (libertyBoats.length > 0) {
      const libertyBoatId = libertyBoats[0].id;

      // Get Liberty trip count
      const libertyCountResponse = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=*&boat_id=eq.${libertyBoatId}&limit=0`, {
        headers: {
          'apikey': SUPABASE_SERVICE_KEY,
          'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
          'Prefer': 'count=exact'
        }
      });

      const libertyCount = libertyCountResponse.headers.get('content-range')?.split('/')[1] || 0;

      // Get Liberty trip dates
      const libertyTripsResponse = await fetch(`${SUPABASE_URL}/rest/v1/trips?select=trip_date&boat_id=eq.${libertyBoatId}&order=trip_date.asc`, {
        headers: {
          'apikey': SUPABASE_SERVICE_KEY,
          'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
        }
      });
      const libertyTrips = await libertyTripsResponse.json();

      libertyData = {
        found: true,
        boatId: libertyBoatId,
        trips: parseInt(libertyCount),
        dates: libertyTrips.map(t => t.trip_date),
        firstDate: libertyTrips[0]?.trip_date,
        lastDate: libertyTrips[libertyTrips.length - 1]?.trip_date
      };
    }

    res.status(200).json({
      success: true,
      database: {
        totalTrips: parseInt(totalCount),
        oldestDates: oldest.map(t => t.trip_date),
        newestDates: newest.map(t => t.trip_date),
        dateRange: {
          oldest: oldest[0]?.trip_date,
          newest: newest[0]?.trip_date
        }
      },
      liberty: libertyData
    });

  } catch (error) {
    console.error('Debug API error:', error);
    res.status(500).json({ error: error.message });
  }
}