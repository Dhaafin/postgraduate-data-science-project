import sys
sys.path.append('c:\\[Dhaafin]\\Projects\\Personal Projects\\data-scraping')
from src.database.connection import sync_engine
from sqlalchemy import text

with sync_engine.begin() as conn:
    res = conn.execute(text("SELECT artist_type, COUNT(*) FROM staging.music_data_staging GROUP BY artist_type")).fetchall()
    print('DB counts:')
    for row in res:
        print(f'{row[0]}: {row[1]}')
    
    # Fix the data
    conn.execute(text("UPDATE staging.music_data_staging SET artist_type = 'Person' WHERE artist_type = 'Solo'"))
    conn.execute(text("UPDATE staging.music_data_staging SET artist_type = 'Group' WHERE artist_type = 'Band'"))
    print("Database patched!")
