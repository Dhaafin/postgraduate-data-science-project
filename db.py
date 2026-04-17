import os
import re
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()

# Setup Engine
DATABASE_URL = os.getenv('DATABASE_URL')
# Konversi URL ke format async psycopg
ASYNC_DB_URL = re.sub(r'^postgresql:', 'postgresql+psycopg:', DATABASE_URL)
engine = create_async_engine(ASYNC_DB_URL)

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS spotify_data (
                id SERIAL PRIMARY KEY,
                artist_id TEXT,
                raw_content JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

async def insert_artist_data(artist_id, data):
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO spotify_data (artist_id, raw_content) VALUES (:id, :content)"),
            {"id": artist_id, "content": json.dumps(data)}
        )