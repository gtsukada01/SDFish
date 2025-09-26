export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const version = process.env.VERCEL_GIT_COMMIT_SHA || 'unknown';
  const env = process.env.VERCEL_ENV || 'unknown';

  return res.status(200).json({
    ok: true,
    timestamp: new Date().toISOString(),
    version,
    env
  });
}

