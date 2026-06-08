import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine
from sqlalchemy import text

def check():
    with sync_engine.begin() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging")).scalar()
        null_types = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging WHERE artist_type IS NULL")).scalar()
        null_indonesian_types = conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging WHERE artist_type IS NULL AND is_indonesian = TRUE")).scalar()
        types_dist = conn.execute(text("SELECT artist_type, COUNT(*) FROM staging.music_data_staging GROUP BY artist_type")).fetchall()
        
        print(f"Total artists in DB: {total}")
        print(f"Artists with NULL artist_type: {null_types}")
        print(f"Indonesian artists with NULL artist_type: {null_indonesian_types}")
        print("Artist type distribution:")
        for t, count in types_dist:
            print(f"  - {t or 'NULL'}: {count}")

if __name__ == "__main__":
    check()
