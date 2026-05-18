import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def audit_genres():
    if not sync_engine:
        print("Database connection failed.")
        return
        
    print("\n--- [AUDITING RAW GENRES IN DATABASE] ---")
    
    with sync_engine.begin() as conn:
        sample_query = text("SELECT id, artist_name, genre FROM staging.music_data_staging LIMIT 10")
        samples = conn.execute(sample_query).fetchall()
        print("Sample genres format:")
        for r in samples:
            print(f"- {r[1]}: {r[2]} (type: {type(r[2])})")
            
        # Get all non-null genres
        all_query = text("SELECT genre FROM staging.music_data_staging WHERE genre IS NOT NULL")
        records = conn.execute(all_query).fetchall()
        
        # Aggregate unique tags
        genre_counts = {}
        for r in records:
            genre_list = r[0]
            if isinstance(genre_list, list):
                for g in genre_list:
                    genre_counts[g] = genre_counts.get(g, 0) + 1
            elif isinstance(genre_list, str):
                clean_str = genre_list.strip('{}[]()""\'\'')
                if clean_str:
                    tags = [t.strip().strip('"\'') for t in clean_str.split(',') if t.strip()]
                    for t in tags:
                        genre_counts[t] = genre_counts.get(t, 0) + 1
            else:
                g_str = str(genre_list)
                genre_counts[g_str] = genre_counts.get(g_str, 0) + 1
                
        # Sort and display top 50 genres
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        print(f"\nTotal Unique Genre Tags Found: {len(sorted_genres)}")
        print("\nTop 50 Most Common Raw Spotify Genre Tags:")
        print(f"{'No.':<4} | {'Raw Genre Tag':<40} | {'Count':<5}")
        print("-" * 55)
        for idx, (g, count) in enumerate(sorted_genres[:50], start=1):
            print(f"{idx:<4} | {g:<40} | {count:<5}")
            
    print("=" * 60 + "\n")

if __name__ == "__main__":
    audit_genres()
