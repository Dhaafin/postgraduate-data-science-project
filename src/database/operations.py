"""
Centralized Database Operations

All database queries, inserts, and updates for the application are strictly confined to this module.
This enforces schema mapping to `staging.music_data_staging` and prevents scattered SQL queries.
"""

from sqlalchemy import text
from src.database.connection import engine, sync_engine

# --- ASYNC OPERATIONS (Used by Playwright/Async contexts) ---

async def insert_artist_data(spotify_id, artist_name, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=False):
    """Inserts a new artist record into the staging table asynchronously."""
    if not engine: return
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO staging.music_data_staging (spotify_id, spotify_link, artist_name, profile_picture, genre, followers, popularity, artist_type, needs_review) 
                VALUES (:id, :link, :name, :profile_picture, :genre, :followers, :popularity, :artist_type, :needs_review)
            """),
            {"id": spotify_id, "link": spotify_link, "name": artist_name, "profile_picture": profile_picture, "genre": genre, "followers": followers, "popularity": popularity, "artist_type": artist_type, "needs_review": needs_review}
        )

async def get_all_artists(db_engine=None):
    """Retrieves all artists that don't have a Spotify ID."""
    target_engine = db_engine or engine
    if not target_engine: return []
    async with target_engine.begin() as conn:
        result = await conn.execute(text("SELECT id, artist_name FROM staging.music_data_staging WHERE spotify_id IS NULL OR spotify_id = ''"))
        return [{"id": row[0], "artist_name": row[1]} for row in result.fetchall()]

async def update_spotify_id(db_id, spotify_id, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=None):
    """Asynchronously updates an artist's Spotify information."""
    if not engine: return
    async with engine.begin() as conn:
        set_clauses = [
            "spotify_id = :spotify_id", "spotify_link = :spotify_link", "profile_picture = :profile_picture", 
            "genre = :genre", "followers = :followers", "popularity = :popularity", "artist_type = :artist_type"
        ]
        params = {
            "spotify_id": spotify_id, "spotify_link": spotify_link, "profile_picture": profile_picture,
            "genre": genre, "followers": followers, "popularity": popularity, "artist_type": artist_type,
            "id": db_id
        }
        if needs_review is not None:
            set_clauses.append("needs_review = :needs_review")
            params["needs_review"] = needs_review
            
        set_str = ", ".join(set_clauses)
        await conn.execute(text(f"UPDATE staging.music_data_staging SET {set_str} WHERE id = :id"), params)


# --- SYNC OPERATIONS (Used by CLI, Wikipedia/MusicBrainz requests, etc.) ---

def get_next_target_for_enrichment_sync(db_engine=None):
    """Fetches the next un-enriched artist for Spotify search."""
    target_engine = db_engine or sync_engine
    if not target_engine: return None
    with target_engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT id, artist_name 
                FROM staging.music_data_staging 
                WHERE (spotify_id IS NULL OR spotify_id = '') 
                  AND (needs_review IS FALSE OR needs_review IS NULL)
                ORDER BY id ASC 
                LIMIT 1
            """)
        )
        row = result.fetchone()
        return {"db_id": row[0], "artist_name": row[1]} if row else None

def update_spotify_id_sync(db_id, spotify_id, spotify_link=None, profile_picture=None, genre=None, followers=None, popularity=None, artist_type=None, needs_review=None, db_engine=None):
    """Synchronous version of update_spotify_id."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        set_clauses = [
            "spotify_id = :spotify_id", "spotify_link = :spotify_link", "profile_picture = :profile_picture", 
            "genre = :genre", "followers = :followers", "popularity = :popularity", "artist_type = :artist_type"
        ]
        params = {
            "spotify_id": spotify_id, "spotify_link": spotify_link, "profile_picture": profile_picture,
            "genre": genre, "followers": followers, "popularity": popularity, "artist_type": artist_type,
            "id": db_id
        }
        if needs_review is not None:
            set_clauses.append("needs_review = :needs_review")
            params["needs_review"] = needs_review
            
        set_str = ", ".join(set_clauses)
        conn.execute(text(f"UPDATE staging.music_data_staging SET {set_str} WHERE id = :id"), params)

def get_unflagged_nationality_artists_sync(db_engine=None):
    """Retrieves all records that haven't been validated for nationality yet."""
    target_engine = db_engine or sync_engine
    if not target_engine: return []
    with target_engine.begin() as conn:
        result = conn.execute(text("SELECT id, artist_name, genre FROM staging.music_data_staging WHERE is_indonesian IS NULL"))
        return [{"id": row[0], "name": row[1], "genre": row[2]} for row in result.fetchall()]

def update_nationality_sync(db_id, is_indonesian, db_engine=None):
    """Synchronously updates the is_indonesian flag."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        conn.execute(
            text("UPDATE staging.music_data_staging SET is_indonesian = :is_indonesian WHERE id = :id"),
            {"is_indonesian": is_indonesian, "id": db_id}
        )

def get_artists_without_origin_sync(db_engine=None):
    """Fetches confirmed Indonesian artists missing origin data."""
    target_engine = db_engine or sync_engine
    if not target_engine: return []
    with target_engine.begin() as conn:
        query = text("""
            SELECT id, artist_name 
            FROM staging.music_data_staging 
            WHERE origin_city IS NULL 
              AND is_indonesian = TRUE
            ORDER BY id
        """)
        return [{"id": row[0], "name": row[1]} for row in conn.execute(query).fetchall()]

def update_origin_city_sync(db_id, origin_city, db_engine=None):
    """Updates the origin city and enforces the Indonesian flag."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        conn.execute(
            text("UPDATE staging.music_data_staging SET origin_city = :city, is_indonesian = TRUE WHERE id = :id"),
            {"city": origin_city, "id": db_id}
        )

def get_artists_without_type_sync(db_engine=None):
    """Fetches artists missing the artist_type field."""
    target_engine = db_engine or sync_engine
    if not target_engine: return []
    with target_engine.begin() as conn:
        query = text("SELECT id, artist_name FROM staging.music_data_staging WHERE artist_type IS NULL")
        return [{"id": row[0], "name": row[1]} for row in conn.execute(query).fetchall()]

def update_artist_type_sync(db_id, artist_type, db_engine=None):
    """Updates the artist_type (Person/Group)."""
    target_engine = db_engine or sync_engine
    if not target_engine: return
    with target_engine.begin() as conn:
        conn.execute(
            text("UPDATE staging.music_data_staging SET artist_type = :type WHERE id = :id"),
            {"type": artist_type, "id": db_id}
        )

def insert_seed_artist_sync(artist_name, db_engine=None):
    """Inserts a single raw seed artist synchronously. Returns the ID."""
    target_engine = db_engine or sync_engine
    if not target_engine: return None
    with target_engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO staging.music_data_staging (artist_name) VALUES (:name) RETURNING id"),
            {"name": artist_name}
        )
        return result.fetchone()[0]

def check_artist_exists_sync(artist_name, db_engine=None):
    """Checks if an artist already exists using strict alphanumeric matching."""
    target_engine = db_engine or sync_engine
    if not target_engine: return False
    with target_engine.begin() as conn:
        check = conn.execute(
            text("""
                SELECT id FROM staging.music_data_staging 
                WHERE LOWER(REGEXP_REPLACE(artist_name, '[^a-zA-Z0-9]', '', 'g')) = LOWER(REGEXP_REPLACE(:name, '[^a-zA-Z0-9]', '', 'g'))
            """),
            {"name": artist_name}
        ).fetchone()
        return bool(check)

def insert_musicbrainz_seed_sync(artist_name, artist_type, origin_city, origin_province, db_engine=None):
    """Inserts a pre-validated MusicBrainz artist directly into the staging table. Skips if exists."""
    target_engine = db_engine or sync_engine
    if not target_engine: return None
    
    if check_artist_exists_sync(artist_name, target_engine):
        return None
        
    with target_engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO staging.music_data_staging 
                (artist_name, artist_type, origin_city, origin_province, is_indonesian) 
                VALUES (:name, :type, :city, :prov, TRUE) 
                RETURNING id
            """),
            {"name": artist_name, "type": artist_type, "city": origin_city, "prov": origin_province}
        )
        return result.fetchone()[0]
