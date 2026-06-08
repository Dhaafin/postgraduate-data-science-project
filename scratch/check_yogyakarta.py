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
            SELECT id, artist_name, origin_city, origin_province 
            FROM staging.music_data_staging 
            WHERE origin_city ILIKE '%yogyakarta%' 
               OR origin_province ILIKE '%yogyakarta%'
               OR origin_city ILIKE '%jogja%'
               OR origin_province ILIKE '%jogja%'
        """)
        results = conn.execute(query).fetchall()
        print(f"\n--- YOGYAKARTA/JOGJA RECORDS IN DB ({len(results)} rows) ---")
        for r in results:
            print(f"ID: {r[0]:<4} | Artist: {r[1]:<25} | City: {r[2]:<15} | Province: {r[3]}")
            
if __name__ == "__main__":
    check()
