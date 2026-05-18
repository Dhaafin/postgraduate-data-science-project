import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def check_schema():
    if not sync_engine:
        print("Database connection failed.")
        return
        
    print("\n--- [AUDITING MUSIC_DATA_STAGING COLUMNS] ---")
    
    with sync_engine.begin() as conn:
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'staging' 
              AND table_name = 'music_data_staging'
            ORDER BY ordinal_position
        """)
        columns = conn.execute(query).fetchall()
        for c in columns:
            print(f"- {c[0]}: {c[1]}")
            
    print("=" * 60 + "\n")

if __name__ == "__main__":
    check_schema()
