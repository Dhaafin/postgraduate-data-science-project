"""
Database configuration and operations for the Spotify data scraper.
Handles connection setup, table initialization, and data insertion using SQLAlchemy and PostgreSQL.
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
    Initializes the database schema.
    Creates the 'music_data' table if it does not already exist.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS music_data (
                id SERIAL PRIMARY KEY,
                spotify_id TEXT,
                artist_name TEXT,
                genre TEXT[],
                followers INTEGER,
                popularity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        # Migration: Add columns if they don't exist in the current table
        await conn.execute(text("ALTER TABLE music_data ADD COLUMN IF NOT EXISTS genre TEXT[]"))
        # Ensure genre is an array if it was previously created as TEXT
        await conn.execute(text("ALTER TABLE music_data ALTER COLUMN genre TYPE TEXT[] USING CASE WHEN genre IS NULL THEN NULL ELSE ARRAY[genre] END"))
        await conn.execute(text("ALTER TABLE music_data ADD COLUMN IF NOT EXISTS followers INTEGER"))
        await conn.execute(text("ALTER TABLE music_data ADD COLUMN IF NOT EXISTS popularity INTEGER"))


async def insert_artist_data(spotify_id, artist_name, genre=None, followers=None, popularity=None):
    """
    Inserts a new artist record into the music_data table.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO music_data (spotify_id, artist_name, genre, followers, popularity) 
                VALUES (:id, :name, :genre, :followers, :popularity)
            """),
            {
                "id": spotify_id, 
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
        # Using IS NULL or spotify_id = '' so it matches empty IDs
        result = await conn.execute(text("SELECT id, artist_name FROM music_data WHERE spotify_id IS NULL OR spotify_id = ''"))
        # Fetching rows safely using mapping to dict
        return [{"id": row[0], "artist_name": row[1]} for row in result.fetchall()]

async def update_spotify_id(db_id, spotify_id, genre=None, followers=None, popularity=None):
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
                    genre = :genre, 
                    followers = :followers, 
                    popularity = :popularity 
                WHERE id = :id
            """),
            {
                "spotify_id": spotify_id, 
                "genre": genre, 
                "followers": followers, 
                "popularity": popularity,
                "id": db_id
            }
        )


if __name__ == "__main__":
    import asyncio
    import sys
    
    # Fix for Windows: psycopg requires SelectorEventLoop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("--- Database Initialization ---")
    if engine:
        asyncio.run(init_db())
        print("Success: Database initialized and table 'music_data' is ready.")
    else:
        print("Error: Could not initialize database. Check your .env file.")

