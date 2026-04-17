"""
Database configuration and operations for the Spotify data scraper.
Handles connection setup, table initialization, and data refactoring using SQLAlchemy and PostgreSQL.
"""

import os
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load env from root
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
# Convert to async psycopg
if DATABASE_URL:
    ASYNC_DB_URL = re.sub(r'^postgresql:', 'postgresql+psycopg:', DATABASE_URL)
    engine = create_async_engine(ASYNC_DB_URL)
else:
    engine = None
    print("Warning: DATABASE_URL not found in environment.")

async def init_db():
    """
    Initializes/Refactors the database schema.
    Desired order: id, spotify_id, spotify_link, artist_name, genre, followers, popularity
    Removes: created_at
    """
    if not engine:
        return
        
    async with engine.begin() as conn:
        # Check if table exists
        check = await conn.execute(text("SELECT to_regclass('public.music_data')"))
        exists = check.fetchone()[0] is not None
        
        if not exists:
            # Fresh start
            print("Creating new music_data table...")
            await conn.execute(text("""
                CREATE TABLE music_data (
                    id SERIAL PRIMARY KEY,
                    spotify_id TEXT,
                    spotify_link TEXT,
                    artist_name TEXT,
                    genre TEXT[],
                    followers INTEGER,
                    popularity INTEGER
                );
            """))
        else:
            # Check current columns to see if we need to refactor
            cols_query = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'music_data'"))
            current_cols = [row[0] for row in cols_query.fetchall()]
            
            # If 'created_at' exists or 'spotify_link' is missing, we refactor
            if 'created_at' in current_cols or 'spotify_link' not in current_cols:
                print("Refactoring table to requested structure (reordering and removing created_at)...")
                
                # 1. Create the new table structure
                await conn.execute(text("""
                    CREATE TABLE music_data_new (
                        id SERIAL PRIMARY KEY,
                        spotify_id TEXT,
                        spotify_link TEXT,
                        artist_name TEXT,
                        genre TEXT[],
                        followers INTEGER,
                        popularity INTEGER
                    );
                """))
                
                # 2. Map existing columns to the new table
                # We handle columns that might be missing in older versions (like genre/followers)
                insert_cols = ["id", "spotify_id", "artist_name"]
                if 'genre' in current_cols: insert_cols.append("genre")
                if 'followers' in current_cols: insert_cols.append("followers")
                if 'popularity' in current_cols: insert_cols.append("popularity")
                
                cols_str = ", ".join(insert_cols)
                await conn.execute(text(f"INSERT INTO music_data_new ({cols_str}) SELECT {cols_str} FROM music_data"))
                
                # 3. Swap the tables
                await conn.execute(text("DROP TABLE music_data"))
                await conn.execute(text("ALTER TABLE music_data_new RENAME TO music_data"))
                
                # 4. Fix the ID sequence
                await conn.execute(text("SELECT setval(pg_get_serial_sequence('music_data', 'id'), (SELECT MAX(id) FROM music_data))"))
                print("Refactor complete.")

async def insert_artist_data(spotify_id, artist_name, spotify_link=None, genre=None, followers=None, popularity=None):
    """
    Inserts a new artist record into the music_data table.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO music_data (spotify_id, spotify_link, artist_name, genre, followers, popularity) 
                VALUES (:id, :link, :name, :genre, :followers, :popularity)
            """),
            {
                "id": spotify_id, 
                "link": spotify_link,
                "name": artist_name,
                "genre": genre,
                "followers": followers,
                "popularity": popularity
            }
        )

async def get_all_artists():
    """
    Retrieves all artists from the music_data table that don't have a Spotify ID.
    Returns a list of dicts with 'id' and 'artist_name'.
    """
    if not engine:
        return []
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id, artist_name FROM music_data WHERE spotify_id IS NULL OR spotify_id = ''"))
        return [{"id": row[0], "artist_name": row[1]} for row in result.fetchall()]

async def update_spotify_id(db_id, spotify_id, spotify_link=None, genre=None, followers=None, popularity=None):
    """
    Updates the spotify_id and extra metadata for a specific artist in the database.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE music_data 
                SET spotify_id = :spotify_id, 
                    spotify_link = :spotify_link,
                    genre = :genre, 
                    followers = :followers, 
                    popularity = :popularity 
                WHERE id = :id
            """),
            {
                "spotify_id": spotify_id, 
                "spotify_link": spotify_link,
                "genre": genre, 
                "followers": followers, 
                "popularity": popularity,
                "id": db_id
            }
        )

if __name__ == "__main__":
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("--- Database Initialization/Refactor ---")
    if engine:
        asyncio.run(init_db())
        print("Success: Database is ready and structure is verified.")
    else:
        print("Error: Could not initialize database. Check your .env file.")
