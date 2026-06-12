import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import text
from src.database.connection import sync_engine

with sync_engine.begin() as conn:
    result = conn.execute(text("SELECT artist_name, genre FROM music_data WHERE artist_name IN ('Mahalini Raharja', 'Mahalini', 'Young Lex', 'Idgitaf', 'Astrid', 'Sarwendah', 'NDX A.K.A', 'Baba Lili Tata')"))
    for row in result:
        print(f"{row[0]}: {row[1]}")
