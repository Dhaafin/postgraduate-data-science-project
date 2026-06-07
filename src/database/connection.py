"""
Database configuration and operations for the Spotify data scraper.
Handles connection setup, table initialization, and data refactoring using SQLAlchemy and PostgreSQL.
"""

import os
import re
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load env from root
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
# Convert to async psycopg
ASYNC_DB_URL = None
if DATABASE_URL:
    ASYNC_DB_URL = re.sub(r'^postgresql:', 'postgresql+psycopg:', DATABASE_URL)

def get_db_engine():
    """Creates a fresh async engine."""
    if not ASYNC_DB_URL:
        return None
    return create_async_engine(ASYNC_DB_URL)

def get_sync_engine():
    """Creates a fresh synchronous engine for thread-safe operations on Windows."""
    if not DATABASE_URL:
        return None
    # Ensure it uses the standard psycopg driver for sync calls
    sync_url = re.sub(r'^postgresql\+psycopg:', 'postgresql:', DATABASE_URL)
    return create_engine(sync_url)

# Global engines
engine = get_db_engine()
sync_engine = get_sync_engine()
if not engine:
    print("Warning: DATABASE_URL not found in environment.")

async def init_db():
    """
    Initializes/Refactors the database schema.
    Desired order: id, needs_review, spotify_id, spotify_link, artist_name, genre, followers, popularity, geo fields, is_indonesian
    """
    if not engine:
        return
        
    async with engine.begin() as conn:
        # Robust check for table existence using information_schema
        check_table = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'music_data_staging' AND table_schema = 'staging')"
        ))
        exists = check_table.scalar()
        
        if not exists:
            print("Creating new music_data table...")
            await conn.execute(text("""
                CREATE TABLE staging.music_data_staging (
                    id SERIAL PRIMARY KEY,
                    needs_review BOOLEAN DEFAULT FALSE,
                    spotify_id TEXT,
                    spotify_link TEXT,
                    artist_name TEXT,
                    profile_picture TEXT,
                    genre TEXT[],
                    primary_genre TEXT,
                    followers INTEGER,
                    popularity INTEGER,
                    artist_type TEXT,
                    origin_city TEXT,
                    origin_province TEXT,
                    latitude DECIMAL,
                    longitude DECIMAL,
                    is_indonesian BOOLEAN DEFAULT NULL,
                    wikipedia_url TEXT
                );
            """))
            print("Table created successfully.")
        else:
            # Check current columns strictly within public schema
            cols_query = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'music_data_staging' 
                AND table_schema = 'staging' 
                ORDER BY ordinal_position
            """))
            current_cols = [row[0] for row in cols_query.fetchall()]
            
            desired_order = [
                "id", "needs_review", "spotify_id", "spotify_link", "artist_name", 
                "profile_picture", "genre", "primary_genre", "followers", "popularity", "artist_type",
                "origin_city", "origin_province", "latitude", "longitude", "is_indonesian", "wikipedia_url"
            ]
            
            # Trigger refactor if columns are missing or out of order
            if current_cols != desired_order:
                print(f"Schema mismatch detected.")
                print(f"Current: {current_cols}")
                print(f"Desired: {desired_order}")
                print("Refactoring table to maintain desired structure...")
                
                # 1. Create the new table structure
                await conn.execute(text("""
                    CREATE TABLE staging.music_data_staging_new (
                        id SERIAL PRIMARY KEY,
                        needs_review BOOLEAN DEFAULT FALSE,
                        spotify_id TEXT,
                        spotify_link TEXT,
                        artist_name TEXT,
                        profile_picture TEXT,
                        genre TEXT[],
                        primary_genre TEXT,
                        followers INTEGER,
                        popularity INTEGER,
                        artist_type TEXT,
                        origin_city TEXT,
                        origin_province TEXT,
                        latitude DECIMAL,
                        longitude DECIMAL,
                        is_indonesian BOOLEAN DEFAULT NULL,
                        wikipedia_url TEXT
                    );
                """))
                
                # 2. Map existing columns to the new table
                # Only include columns that actually exist in the current table
                insert_cols = [c for c in desired_order if c in current_cols]
                
                # Special case: id must always be included to preserve PKs
                if "id" not in insert_cols:
                    insert_cols.insert(0, "id")

                cols_str = ", ".join(insert_cols)
                await conn.execute(text(f"INSERT INTO staging.music_data_staging_new ({cols_str}) SELECT {cols_str} FROM staging.music_data_staging"))
                
                # 3. Swap the tables
                await conn.execute(text("DROP TABLE staging.music_data_staging"))
                await conn.execute(text("ALTER TABLE staging.music_data_staging_new RENAME TO music_data_staging"))
                
                # 4. Fix the ID sequence
                await conn.execute(text("SELECT setval(pg_get_serial_sequence('staging.music_data_staging', 'id'), (SELECT MAX(id) FROM staging.music_data_staging))"))
                print("Database refactor and migration complete.")
            else:
                print("Database schema is already up to date.")



if __name__ == "__main__":
    import asyncio
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("--- Database Initialization/Refactor ---")
    if engine:
        asyncio.run(init_db())
        print("Success: Database is ready.")
    else:
        print("Error: Could not initialize database.")
