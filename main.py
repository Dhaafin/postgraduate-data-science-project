"""
Main Entry Point for the Data Scraping Project.
Supports both Command-Line Arguments (for automation) and 
an Interactive Menu (for manual usage).
"""

import asyncio
import sys
import argparse
from src.scrapers.spotify_artist_scraper import run_spotify_scraper
from src.scrapers.viberate import fetch_viberate_artists
from src.scrapers.spotify_search_scraper import run_spotify_search_scraper
from src.scrapers.nationality_validator import NationalityValidator
from src.database.connection import init_db, insert_artist_data

async def run_viberate():
    """Logic for the Viberate scraper task."""
    print("\n--- Running Viberate Scraper ---")
    viberate_artists = fetch_viberate_artists()
    print(f"Found {len(viberate_artists)} artists from Viberate.")

    for artist_name in viberate_artists:
        print(f"Saving to Database (Viberate): {artist_name}")
        await insert_artist_data(spotify_id=None, artist_name=artist_name)
    print("Viberate data saved successfully.")

async def run_spotify_search_workflow():
    """Workflow for the Browser-based Spotify Search Scraper."""
    print("\n--- Running Spotify Search Scraper (Browser) ---")
    
    def scraper_thread_runner():
        import asyncio
        if sys.platform == 'win32':
             # Now that we use sync DB calls, we can use Proactor for Playwright stability.
             asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return asyncio.run(run_spotify_search_scraper())

    print("Launching the robust browser-based scraper...")
    await asyncio.to_thread(scraper_thread_runner)
    print("Spotify search process completed.")

async def run_nationality_validation():
    """Workflow for the Hybrid Nationality Validator."""
    print("\n--- Running Nationality Validator (Hybrid) ---")
    validator = NationalityValidator()
    # The validator is synchronous, so we wrap it in a thread
    await asyncio.to_thread(validator.run_validation)
    print("Nationality validation process completed.")

async def interactive_menu():
    """Displays an interactive console menu with categories."""
    while True:
        print("\n" + "="*40)
        print("      MUSIC SCRAPER MAIN MENU")
        print("="*40)
        
        print("\n [SCRAPING & ENRICHMENT]")
        print(" 1. Run Viberate Scraper (Charts)")
        print(" 2. Run Spotify Search Scraper (Browser Console)")
        print(" 3. Run Nationality Validator (Hybrid)")
        
        print("\n [UTILS]")
        print(" 4. Update Database (Run Migrations/Add Columns)")
        
        print("\n 5. Exit")
        print("-" * 40)
        
        choice = input("Select an option (1-4): ").strip()

        if choice == '1':
            await run_viberate()
        elif choice == '2':
            await run_spotify_search_workflow()
        elif choice == '3':
            await run_nationality_validation()
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
    parser.add_argument('--validate', action='store_true', help='Run Nationality validator')
    parser.add_argument('--all', action='store_true', help='Run all scrapers')
    
    args = parser.parse_args()

    # Always ensure DB is ready
    await init_db()

    # If any specific argument is passed, run non-interactively
    if args.all:
        await run_viberate()
        await run_spotify_search_workflow()
        await run_nationality_validation()
    elif args.viberate:
        await run_viberate()
    elif args.spotify:
        await run_spotify_search_workflow()
    elif args.validate:
        await run_nationality_validation()
    else:
        # No arguments? Show the menu
        await interactive_menu()

if __name__ == "__main__":
    # Windows-specific fix: Psycopg requires SelectorEventLoop for async operations.
    # We use this as the primary loop for DB and Menu interaction.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
