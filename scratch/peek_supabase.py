import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import engine
from sqlalchemy import text

async def peek_data():
    if not engine:
        print("Engine not initialized")
        return
        
    try:
        async with engine.connect() as conn:
            query = text("SELECT id, artist_name, origin_city, spotify_id FROM staging.music_data_staging LIMIT 5")
            result = await conn.execute(query)
            rows = result.fetchall()
            print("\n--- [PEEK: staging.music_data_staging] ---")
            for row in rows:
                print(f"ID: {row[0]} | Artist: {row[1]:<20} | Origin: {row[2] or 'None':<15} | Spotify: {row[3]}")
            print("--- [END PEEK] ---\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(peek_data())
