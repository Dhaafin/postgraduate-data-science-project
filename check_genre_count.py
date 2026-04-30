import sys
import os
sys.path.append(os.path.abspath('.'))
from sqlalchemy import text
from src.database.connection import sync_engine

with sync_engine.begin() as conn:
    # Check how many artists have indonesian/indo/jawa/dangdut etc in genres
    query = """
    SELECT COUNT(*) FROM music_data 
    WHERE array_to_string(genre, ',') ILIKE '%indonesian%'
       OR array_to_string(genre, ',') ILIKE '%indo %'
       OR array_to_string(genre, ',') ILIKE '%jawa%'
       OR array_to_string(genre, ',') ILIKE '%dangdut%'
       OR array_to_string(genre, ',') ILIKE '%koplo%'
       OR array_to_string(genre, ',') ILIKE '%sunda%'
       OR array_to_string(genre, ',') ILIKE '%minang%'
       OR array_to_string(genre, ',') ILIKE '%batak%'
       OR array_to_string(genre, ',') ILIKE '%maluku%'
       OR array_to_string(genre, ',') ILIKE '%timur%'
    """
    result = conn.execute(text(query))
    count = result.scalar()
    
    total = conn.execute(text("SELECT COUNT(*) FROM music_data")).scalar()
    print(f"Artists with clear Indonesian genres: {count} out of {total}")
