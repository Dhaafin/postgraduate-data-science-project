import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def check_empty():
    if not sync_engine:
        print("Sync engine not initialized")
        return
        
    print("\n--- [AUDITING EMPTY ORIGINS IN STAGING TABLE] ---")
    
    with sync_engine.begin() as conn:
        # 1. Total records
        total = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging")).scalar()
        
        # 2. Total with both city and province null
        both_null = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging WHERE origin_city IS NULL AND origin_province IS NULL")).scalar()
        
        # 3. Total with only city null but province populated (standard promoted province)
        prov_only = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging WHERE origin_city IS NULL AND origin_province IS NOT NULL")).scalar()
        
        # 4. Total with both populated
        both_populated = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging WHERE origin_city IS NOT NULL AND origin_province IS NOT NULL")).scalar()
        
        print(f"Total Staging Records           : {total}")
        print(f"Both City & Province are NULL   : {both_null}")
        print(f"Province Only (City is NULL)    : {prov_only}")
        print(f"Both City & Province Populated  : {both_populated}")
        
        # List a few examples of both_null
        query = text("""
            SELECT id, artist_name, origin_city, origin_province, is_indonesian, wikipedia_url 
            FROM staging.music_data_staging 
            WHERE origin_city IS NULL AND origin_province IS NULL 
            LIMIT 30
        """)
        rows = conn.execute(query).fetchall()
        
        print("\nExamples of records where BOTH City & Province are NULL:")
        print(f"{'ID':<5} | {'Artist Name':<30} | {'Is Indo':<8} | {'Wikipedia URL':<50}")
        print("-" * 105)
        for r in rows:
            print(f"{r[0]:<5} | {r[1][:30]:<30} | {str(r[4]):<8} | {str(r[5]):<50}")
            
    print("=" * 80 + "\n")

if __name__ == "__main__":
    check_empty()
