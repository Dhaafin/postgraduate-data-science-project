import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import text
from src.database.connection import sync_engine

with sync_engine.begin() as conn:
    query = """
    SELECT unnest(genre) as g, count(*) 
    FROM music_data 
    WHERE NOT (
       array_to_string(genre, ',') ILIKE '%indonesian%'
       OR array_to_string(genre, ',') ILIKE '%indo %'
       OR array_to_string(genre, ',') ILIKE '%jawa%'
       OR array_to_string(genre, ',') ILIKE '%dangdut%'
       OR array_to_string(genre, ',') ILIKE '%koplo%'
       OR array_to_string(genre, ',') ILIKE '%sunda%'
       OR array_to_string(genre, ',') ILIKE '%minang%'
       OR array_to_string(genre, ',') ILIKE '%batak%'
       OR array_to_string(genre, ',') ILIKE '%maluku%'
       OR array_to_string(genre, ',') ILIKE '%timur%'
    )
    GROUP BY g ORDER BY count(*) DESC LIMIT 20
    """
    result = conn.execute(text(query))
    for row in result:
        print(f'{row[0]}: {row[1]}')
