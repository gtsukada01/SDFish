import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://ulsbtwqhwnrpkourphiq.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1ODkyMjksImV4cCI6MjA3MjE2NTIyOX0.neoabBKdVpngZpRkYTxp7Z5WhTXX4uwCnb78N81s_Vk'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
