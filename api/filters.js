// Vercel serverless function for filters endpoint
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

    // Get landings for filters
    const landingsResponse = await fetch(`${SUPABASE_URL}/rest/v1/landings?select=*&order=name`, {
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
      }
    });

    if (!landingsResponse.ok) {
      throw new Error(`Supabase error: ${landingsResponse.statusText}`);
    }

    const landings = await landingsResponse.json();
    const landingList = landings
      .filter(l => l.name && l.name !== 'Unknown')
      .map(l => ({ id: l.id, name: l.name }));

    res.status(200).json({
      success: true,
      data: {
        landings: landingList
      }
    });

  } catch (error) {
    console.error('Filters API error:', error);
    res.status(500).json({ error: error.message });
  }
}