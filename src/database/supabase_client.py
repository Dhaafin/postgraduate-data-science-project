import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from root
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

def get_supabase_client() -> Client:
    """Returns an initialized Supabase client."""
    if not url or not key:
        print("Warning: Supabase URL or Key missing in environment.")
        return None
    return create_client(url, key)

# Singleton instance
supabase: Client = get_supabase_client()

if __name__ == "__main__":
    if supabase:
        print(f"Supabase client initialized for: {url}")
        # Test connection by fetching 1 row from music_data
        try:
            # Targeting the staging schema and table
            res = supabase.schema("staging").table("music_data_staging").select("*").limit(1).execute()
            print("Successfully connected to Supabase API.")
            print(f"Sample data: {res.data}")
        except Exception as e:
            print(f"Error connecting to Supabase API: {e}")
    else:
        print("Failed to initialize Supabase client.")
