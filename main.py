"""
Main Entry Point for the Data Scraping Project.
Supports both Command-Line Arguments (for automation) and 
an Interactive Menu (for manual usage).
"""

import asyncio
import sys
import argparse
from src.scrapers.spotify import run_spotify_scraper
from src.scrapers.spotify_search_api import run_spotify_search
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
    """Logic for the Spotify Search API task."""
    await run_spotify_search()

async def interactive_menu():
    """Displays an interactive console menu with categories."""
    while True:
        print("\n" + "="*40)
        print("      MUSIC SCRAPER MAIN MENU")
        print("="*40)
        
        print("\n [SCRAPING]")
        print(" 1. Run Viberate Scraper (Charts)")
        print(" 2. Run Spotify Scraper (Search API Extractor)")
        print(" 3. Run Both Scrapers")
        
        print("\n [UTILS]")
        print(" 4. Update Database (Run Migrations/Add Columns)")
        
        print("\n 5. Exit")
        print("-" * 40)
        
        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            await run_viberate()
        elif choice == '2':
            await run_spotify()
        elif choice == '3':
            await run_viberate()
            await run_spotify()
        elif choice == '4':
            print("\n--- Running Database Migrations ---")
            await init_db()
            print("Database checked and updated successfully.")
        elif choice == '5':
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
