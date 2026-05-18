import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import engine

async def check_duplicates():
    if not engine:
        print("Engine not initialized")
        return
        
    try:
        async with engine.connect() as conn:
            # 1. Total count
            total = await conn.execute(text("SELECT COUNT(*) FROM staging.music_data_staging"))
            total_count = total.scalar()
            print(f"Total rows in staging.music_data_staging: {total_count}")
            
            # 2. Check duplicates by artist_name
            dup_names_query = text("""
                SELECT artist_name, COUNT(*), ARRAY_AGG(id) as ids, ARRAY_AGG(spotify_id) as spotify_ids
                FROM staging.music_data_staging
                GROUP BY artist_name
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT 20
            """)
            result = await conn.execute(dup_names_query)
            rows = result.fetchall()
            print(f"\n--- [DUPLICATES BY artist_name (Top 20)] ---")
            for row in rows:
                print(f"Artist: {row[0]:<30} | Count: {row[1]} | IDs: {row[2]} | Spotify IDs: {row[3]}")
                
            # 3. Check duplicates by spotify_id
            dup_spotify_query = text("""
                SELECT spotify_id, COUNT(*), ARRAY_AGG(id) as ids, ARRAY_AGG(artist_name) as names
                FROM staging.music_data_staging
                WHERE spotify_id IS NOT NULL AND spotify_id != ''
                GROUP BY spotify_id
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT 20
            """)
            result = await conn.execute(dup_spotify_query)
            rows = result.fetchall()
            print(f"\n--- [DUPLICATES BY spotify_id (Top 20)] ---")
            for row in rows:
                print(f"Spotify ID: {row[0]:<25} | Count: {row[1]} | IDs: {row[2]} | Names: {row[3]}")
                
            # 4. Check if public.music_data exists and has duplicates
            try:
                public_total = await conn.execute(text("SELECT COUNT(*) FROM public.music_data"))
                public_count = public_total.scalar()
                print(f"\nTotal rows in public.music_data: {public_count}")
                
                dup_public_query = text("""
                    SELECT artist_name, COUNT(*)
                    FROM public.music_data
                    GROUP BY artist_name
                    HAVING COUNT(*) > 1
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                res_public = await conn.execute(dup_public_query)
                p_rows = res_public.fetchall()
                print("Duplicates in public.music_data:")
                for r in p_rows:
                    print(f"  Artist: {r[0]:<30} | Count: {r[1]}")
            except Exception as e:
                print(f"\npublic.music_data check failed or does not exist: {e}")
                
    except Exception as e:
        print(f"Error checking duplicates: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_duplicates())
