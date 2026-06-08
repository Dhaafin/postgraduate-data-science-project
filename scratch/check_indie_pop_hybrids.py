import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def check():
    if not sync_engine:
        print("DB connection error.")
        return
    with sync_engine.begin() as conn:
        query = text("""
            SELECT artist_name, genre, popularity, followers, primary_genre 
            FROM staging.music_data_staging 
            WHERE array_to_string(genre, ',') ILIKE '%indonesian pop%'
              AND array_to_string(genre, ',') ILIKE '%indonesian indie%'
            ORDER BY popularity DESC
        """)
        results = conn.execute(query).fetchall()
        print(f"\n--- INDIE-POP HYBRIDS ({len(results)} rows) ---")
        for r in results:
            print(f"Artist: {r[0]:<25} | Popularity: {r[2]:<4} | Followers: {r[3]:<8} | Primary: {r[4]}")
            
if __name__ == "__main__":
    check()
