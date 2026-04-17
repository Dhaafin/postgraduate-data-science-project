"""
Main Entry Point for the Data Scraping Project.
Supports both Command-Line Arguments (for automation) and 
an Interactive Menu (for manual usage).
"""

import asyncio
import sys
import argparse
from src.scrapers.spotify import run_spotify_scraper
from src.scrapers.viberate import fetch_viberate_artists
from src.database.connection import init_db, insert_artist_data

async def run_viberate():
    """Logic for the Viberate scraper task."""
    print("\n--- Running Viberate Scraper ---")
    viberate_artists = fetch_viberate_artists()
    print(f"Found {len(viberate_artists)} artists from Viberate.")

    for artist_name in viberate_artists:
        print(f"Saving to Database (Viberate): {artist_name}")
        await insert_artist_data(None, artist_name)
    print("Viberate data saved successfully.")

async def run_spotify():
    """Logic for the Spotify scraper task."""
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
    else:
        print("Spotify scraper failed or was interrupted.")

async def interactive_menu():
    """Displays an interactive console menu."""
    while True:
        print("\n" + "="*30)
        print("   MUSIC SCRAPER MAIN MENU")
        print("="*30)
        print("1. Run Viberate Scraper (Charts)")
        print("2. Run Spotify Scraper (API Docs)")
        print("3. Run Both Scrapers")
        print("4. Exit")
        print("-" * 30)
        
        choice = input("Select an option (1-4): ").strip()

        if choice == '1':
            await run_viberate()
        elif choice == '2':
            await run_spotify()
        elif choice == '3':
            await run_viberate()
            await run_spotify()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to return to the menu...")

async def main():
    """Main orchestrator with Argument Parsing."""
    parser = argparse.ArgumentParser(description="Professional Music Data Scraper")
    parser.add_argument('--viberate', action='store_true', help='Run Viberate scraper')
    parser.add_argument('--spotify', action='store_true', help='Run Spotify scraper')
    parser.add_argument('--all', action='store_true', help='Run all scrapers')
    
    args = parser.parse_args()

    # Always ensure DB is ready
    await init_db()

    # If any specific argument is passed, run non-interactively
    if args.all:
        await run_viberate()
        await run_spotify()
    elif args.viberate:
        await run_viberate()
    elif args.spotify:
        await run_spotify()
    else:
        # No arguments? Show the menu
        await interactive_menu()

if __name__ == "__main__":
    # Windows-specific fix for psycopg
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
