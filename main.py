"""
Main Entry Point for the Data Scraping Project.
Orchestrates the scrapers and saves data to the database.
"""

import asyncio
from src.scrapers.spotify import run_spotify_scraper
from src.scrapers.viberate import fetch_viberate_artists
from src.database.connection import init_db, insert_artist_data

async def main():
    print("--- Initializing Database ---")
    await init_db()

    print("\n--- Running Viberate Scraper ---")
    viberate_artists = fetch_viberate_artists()
    print(f"Found {len(viberate_artists)} artists from Viberate.")

    # Example: Processing top 5 artists from Viberate
    # For now, let's just show how it would work
    for artist in viberate_artists[:5]:
        print(f"Scrapped from Viberate: {artist}")

    print("\n--- Running Spotify Scraper ---")
    # Using a sample artist ID for now (can be dynamic later)
    spotify_data = await run_spotify_scraper("0tB33cNAVw1H2enMHpgFiP")
    
    if spotify_data and isinstance(spotify_data, dict):
        artist_name = spotify_data.get("name")
        spotify_id = spotify_data.get("id")
        
        if artist_name and spotify_id:
            print(f"Saving to Database: {artist_name} ({spotify_id})")
            await insert_artist_data(spotify_id, artist_name)
            print("Successfully saved to database.")
    
    print("\n--- Scraping Task Completed ---")

if __name__ == "__main__":
    import sys
    # Fix for Windows: psycopg requires SelectorEventLoop
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
