import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def find_duplicates():
    if not sync_engine:
        print("DB connection error.")
        return
        
    print("\n--- [ANALYSIS: ARTIST NAME DUPLICATIONS] ---")
    
    with sync_engine.begin() as conn:
        # We find duplicate names by normalizing to lowercase and trimming whitespaces
        query = text("""
            SELECT LOWER(TRIM(artist_name)) as normalized_name, COUNT(*), ARRAY_AGG(id) as ids, ARRAY_AGG(artist_name) as original_names
            FROM staging.music_data_staging
            GROUP BY normalized_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        results = conn.execute(query).fetchall()
        
        if not results:
            print("No duplicate artist names found in the database!")
            return
            
        print(f"Found {len(results)} duplicate artist names.\n")
        print(f"{'Normalized Name':<30} | {'Count':<5} | {'IDs':<15} | {'Original Names'}")
        print("-" * 90)
        for r in results:
            ids_str = ", ".join(map(str, r[2]))
            orig_names = ", ".join(set(r[3]))
            print(f"{r[0]:<30} | {r[1]:<5} | {ids_str:<15} | {orig_names}")
        print("-" * 90)

if __name__ == "__main__":
    find_duplicates()
