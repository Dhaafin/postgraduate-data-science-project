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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

async def insert_artist_data(spotify_id, artist_name):
    """
    Inserts a new artist record into the music_data table.

    Args:
        spotify_id (str): The unique Spotify ID for the artist.
        artist_name (str): The display name of the artist.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO music_data (spotify_id, artist_name) VALUES (:id, :name)"),
            {"id": spotify_id, "name": artist_name}
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

