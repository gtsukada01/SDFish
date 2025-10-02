-- ============================================
-- Supabase Row Level Security (RLS) Setup
-- Fish Scraper Dashboard - Read-Only Access
-- ============================================
--
-- Run this SQL in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/ulsbtwqhwnrpkourphiq/editor
--
-- This enables anonymous users to READ fishing data
-- but prevents any WRITE/UPDATE/DELETE operations.
-- ============================================

-- Enable RLS on all tables
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE boats ENABLE ROW LEVEL SECURITY;
ALTER TABLE catches ENABLE ROW LEVEL SECURITY;
ALTER TABLE landings ENABLE ROW LEVEL SECURITY;

-- Create read-only policies for anonymous users
-- These allow SELECT but block INSERT/UPDATE/DELETE

CREATE POLICY "Allow anonymous read trips"
ON trips FOR SELECT
TO anon
USING (true);

CREATE POLICY "Allow anonymous read boats"
ON boats FOR SELECT
TO anon
USING (true);

CREATE POLICY "Allow anonymous read catches"
ON catches FOR SELECT
TO anon
USING (true);

CREATE POLICY "Allow anonymous read landings"
ON landings FOR SELECT
TO anon
USING (true);

-- Verification queries (run these to confirm setup)
-- Should return policy details:
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE tablename IN ('trips', 'boats', 'catches', 'landings')
ORDER BY tablename, policyname;
