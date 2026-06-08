import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

load_dotenv()
engine = sqlalchemy.create_engine(os.getenv('DATABASE_URL'))
with engine.begin() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'music_data_staging' 
        AND table_schema = 'staging'
        ORDER BY ordinal_position
    """)).fetchall()
    
    print("Columns in staging.music_data_staging:")
    for c in cols:
        print(f"  - {c[0]}: {c[1]}")
