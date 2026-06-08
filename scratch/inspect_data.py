import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def inspect():
    if not sync_engine:
        print("Engine not initialized")
        return
    with sync_engine.begin() as conn:
        print("--- Records with 'Gresik' ---")
        q1 = text("""
            SELECT id, artist_name, origin_city, origin_province 
            FROM staging.music_data_staging 
            WHERE origin_city ILIKE '%gresik%' OR origin_province ILIKE '%gresik%'
        """)
        rows = conn.execute(q1).fetchall()
        for r in rows:
            print(f"ID: {r.id} | Name: {r.artist_name} | City: '{r.origin_city}' | Prov: '{r.origin_province}'")

        print("\n--- Records where Province is NOT in INDO_PROVINCES list (excluding Null) ---")
        from src.utils.geo_constants import INDO_PROVINCES
        q2 = text("""
            SELECT id, artist_name, origin_city, origin_province 
            FROM staging.music_data_staging 
            WHERE origin_province IS NOT NULL
        """)
        rows2 = conn.execute(q2).fetchall()
        for r in rows2:
            if r.origin_province not in INDO_PROVINCES:
                print(f"ID: {r.id} | Name: {r.artist_name} | City: '{r.origin_city}' | Prov: '{r.origin_province}'")

if __name__ == "__main__":
    inspect()
