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
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'music_data' AND table_schema = 'public')"
        ))
        exists = check_table.scalar()
        
        if not exists:
            print("Creating new music_data table...")
            await conn.execute(text("""
                CREATE TABLE music_data (
                    id SERIAL PRIMARY KEY,
                    needs_review BOOLEAN DEFAULT FALSE,
                    spotify_id TEXT,
                    spotify_link TEXT,
                    artist_name TEXT,
                    profile_picture TEXT,
                    genre TEXT[],
                    followers INTEGER,
                    popularity INTEGER,
                    artist_type TEXT,
                    origin_city TEXT,
                    origin_province TEXT,
                    latitude DECIMAL,
                    longitude DECIMAL,
                    is_indonesian BOOLEAN DEFAULT NULL
                );
            """))
            print("Table created successfully.")
        else:
            # Check current columns strictly within public schema
            cols_query = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'music_data' 
                AND table_schema = 'public' 
                ORDER BY ordinal_position
            """))
            current_cols = [row[0] for row in cols_query.fetchall()]
            
            desired_order = [
                "id", "needs_review", "spotify_id", "spotify_link", "artist_name", 
                "profile_picture", "genre", "followers", "popularity", "artist_type",
                "origin_city", "origin_province", "latitude", "longitude", "is_indonesian"
            ]
            
            # Trigger refactor if columns are missing or out of order
            if current_cols != desired_order:
                print(f"Schema mismatch detected.")
                print(f"Current: {current_cols}")
                print(f"Desired: {desired_order}")
                print("Refactoring table to maintain desired structure...")
                
                # 1. Create the new table structure
                await conn.execute(text("""
                    CREATE TABLE music_data_new (
                        id SERIAL PRIMARY KEY,
                        needs_review BOOLEAN DEFAULT FALSE,
                        spotify_id TEXT,
                        spotify_link TEXT,
                        artist_name TEXT,
                        profile_picture TEXT,
                        genre TEXT[],
                        followers INTEGER,
                        popularity INTEGER,
                        artist_type TEXT,
                        origin_city TEXT,
                        origin_province TEXT,
                        latitude DECIMAL,
                        longitude DECIMAL,
                        is_indonesian BOOLEAN DEFAULT NULL
                    );
                """))
                
                # 2. Map existing columns to the new table
                # Only include columns that actually exist in the current table
                insert_cols = [c for c in desired_order if c in current_cols]
                
                # Special case: id must always be included to preserve PKs
                if "id" not in insert_cols:
                    insert_cols.insert(0, "id")

                cols_str = ", ".join(insert_cols)
                await conn.execute(text(f"INSERT INTO music_data_new ({cols_str}) SELECT {cols_str} FROM music_data"))
                
                # 3. Swap the tables
                await conn.execute(text("DROP TABLE music_data"))
                await conn.execute(text("ALTER TABLE music_data_new RENAME TO music_data"))
                
                # 4. Fix the ID sequence
                await conn.execute(text("SELECT setval(pg_get_serial_sequence('music_data', 'id'), (SELECT MAX(id) FROM music_data))"))
                print("Database refactor and migration complete.")
            else:
                print("Database schema is already up to date.")

async def insert_artist_data(spotify_id, artist_name, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=False):
    """Inserts a new artist record into the music_data table."""
    if not engine: return
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO music_data (spotify_id, spotify_link, artist_name, profile_picture, genre, followers, popularity, artist_type, needs_review) 
                VALUES (:id, :link, :name, :profile_picture, :genre, :followers, :popularity, :artist_type, :needs_review)
            """),
            {"id": spotify_id, "link": spotify_link, "name": artist_name, "profile_picture": profile_picture, "genre": genre, "followers": followers, "popularity": popularity, "artist_type": artist_type, "needs_review": needs_review}
        )

async def get_all_artists(db_engine=None):
    """Retrieves all artists from the music_data table that don't have a Spotify ID."""
    target_engine = db_engine or engine
    if not target_engine: return []
    async with target_engine.begin() as conn:
        result = await conn.execute(text("SELECT id, artist_name FROM music_data WHERE spotify_id IS NULL OR spotify_id = ''"))
        return [{"id": row[0], "artist_name": row[1]} for row in result.fetchall()]

def update_nationality_sync(db_id, is_indonesian, db_engine=None):
    """Synchronously updates the is_indonesian flag for an artist."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        conn.execute(
            text("UPDATE music_data SET is_indonesian = :is_indonesian WHERE id = :id"),
            {"is_indonesian": is_indonesian, "id": db_id}
        )

def update_spotify_id_sync(db_id, spotify_id, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=None, db_engine=None):
    """Synchronous version of update_spotify_id."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        set_clauses = ["spotify_id = :spotify_id", "spotify_link = :spotify_link", "profile_picture = :profile_picture", "genre = :genre", "followers = :followers", "popularity = :popularity", "artist_type = :artist_type"]
        params = {"spotify_id": spotify_id, "spotify_link": spotify_link, "profile_picture": profile_picture, "genre": genre, "followers": followers, "popularity": popularity, "artist_type": artist_type, "id": db_id}
        if needs_review is not None:
            set_clauses.append("needs_review = :needs_review")
            params["needs_review"] = needs_review
        set_str = ", ".join(set_clauses)
        conn.execute(text(f"UPDATE music_data SET {set_str} WHERE id = :id"), params)

async def update_spotify_id(db_id, spotify_id, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=None):
    """
    Asynchronously updates an artist's Spotify information.
    """
    if not engine:
        return
    async with engine.begin() as conn:
        set_clauses = [
            "spotify_id = :spotify_id",
            "spotify_link = :spotify_link",
            "profile_picture = :profile_picture",
            "genre = :genre",
            "followers = :followers",
            "popularity = :popularity",
            "artist_type = :artist_type"
        ]
        params = {
            "spotify_id": spotify_id,
            "spotify_link": spotify_link,
            "profile_picture": profile_picture,
            "genre": genre,
            "followers": followers,
            "popularity": popularity,
            "artist_type": artist_type,
            "id": db_id
        }
        
        if needs_review is not None:
            set_clauses.append("needs_review = :needs_review")
            params["needs_review"] = needs_review
            
        set_str = ", ".join(set_clauses)
        await conn.execute(
            text(f"UPDATE music_data SET {set_str} WHERE id = :id"),
            params
        )

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
