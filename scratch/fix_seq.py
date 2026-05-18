import sys
import os
sys.path.append('c:\\[Dhaafin]\\Projects\\Personal Projects\\data-scraping')
from src.database.connection import sync_engine
from sqlalchemy import text

with sync_engine.begin() as conn:
    try:
        conn.execute(text("SELECT setval(pg_get_serial_sequence('staging.music_data_staging', 'id'), (SELECT MAX(id) FROM staging.music_data_staging))"))
        print('Sequence synchronized with MAX(id)!')
    except Exception as e:
        print(f'Error: {e}')
