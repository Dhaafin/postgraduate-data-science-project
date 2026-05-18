import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import engine

async def inspect_clashes():
    if not engine:
        print("Engine not initialized")
        return
        
    try:
        async with engine.connect() as conn:
            query = text("""
                SELECT id, artist_name, spotify_id, spotify_link, profile_picture, genre, followers, popularity, is_indonesian
                FROM staging.music_data_staging
                WHERE id IN (290, 55, 333, 450, 217, 387, 296, 336)
            """)
            result = await conn.execute(query)
            rows = result.fetchall()
            print("\n--- [INSPECTING SPECIFIC CLASHING ROWS] ---")
            for r in rows:
                print(f"ID: {r[0]:<4} | Name: {r[1]:<25} | Spotify ID: {r[2]:<22} | Pop: {r[7]} | Gen: {r[5][:2] if r[5] else 'None'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect_clashes())
