import os
from supabase import create_client

# Use the connection from environment or hardcoded
url = "https://ulsbtwqhwnrpkourphiq.supabase.co"
key = os.environ.get('SUPABASE_ANON_KEY', '')  # Need anon key

supabase = create_client(url, key) if key else None

if not supabase:
    print("Need SUPABASE_ANON_KEY environment variable")
else:
    # Fetch species that contain "bluefin"  
    result = supabase.table('catches').select('species').ilike('species', '%bluefin%').limit(20).execute()
    
    print("Bluefin species in database:")
    species_set = set()
    for row in result.data:
        species_set.add(row['species'])
    
    for species in sorted(species_set):
        print(f"  - '{species}'")
