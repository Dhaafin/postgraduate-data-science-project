"""
Spotify Search Console Scraper

This script automates the process of extracting artist metadata from the Spotify 
for Developers Search endpoint console. 

It uses Playwright to simulate browser interaction, allowing for data extraction
without requiring direct API credential management for every run, by leveraging
the interactive 'Try it' console.
"""

import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# Add the project root to sys.path so we can import internal modules (src.*)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import engine, update_spotify_id

async def run_spotify_search_scraper(artists_to_search):
    """
    Orchestrates the browser automation for the Spotify Search console.

    Args:
        artists_to_search (list): A list of artist names (strings) to query.

    Returns:
        list: A list of dictionaries containing extracted artist metadata 
              (ID, followers, genres, popularity, etc.).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")
    user_data_dir = os.path.join(project_root, "data/user_data")
    output_file = os.path.join(project_root, "data/raw/spotify_search_response.json")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(user_data_dir, exist_ok=True)

    results = []

    playwright = await async_playwright().start()
    print(f"Launching browser (user data: {user_data_dir})...")
    context = await playwright.firefox.launch_persistent_context(
        user_data_dir,
        headless=False,
        args=["--start-maximized"]
    )

    try:
        page = context.pages[0] if context.pages else await context.new_page()
        url = "https://developer.spotify.com/documentation/web-api/reference/search"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="load", timeout=60000)

        # DOM Selectors for the Spotify Developer Console
        remove_album_selector  = 'div[aria-label="Remove album"]'
        type_input_selector    = 'input#react-select-2-input'
        query_input_selector   = 'input[data-encore-id="formInput"]'
        button_selector        = 'button:has-text("Try it")'
        response_selector      = 'pre.sc-dcdedfe6-0.ePqgwR'

        print("\nBrowser is open. Please log in to Spotify if prompted.")
        print("(Press Ctrl+C at any time to cancel.)\n")
        try:
            input("Press Enter here once you're logged in and the page is ready...")
        except KeyboardInterrupt:
            print("\nCanceled.")
            print("(Browser is still open. Close it manually.)")
            await asyncio.sleep(float('inf'))

        await page.wait_for_selector(query_input_selector, timeout=30000)
        print("Console detected! Setting up filters...\n")

        # Setup filters (remove 'album', add 'artist')
        try:
            if await page.locator(remove_album_selector).count() > 0:
                await page.click(remove_album_selector)
                print("  -> Removed default 'album' filter.")
                await asyncio.sleep(0.5)
            
            await page.fill(type_input_selector, "artist")
            await page.keyboard.press("Enter")
            print("  -> Added 'artist' filter.")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Warning: Could not setup filters automatically: {e}")

        print("\nStarting to process queries...\n")

        for query_name in artists_to_search:
            print(f"Processing: '{query_name}'")

            # Empties the input using filling with empty string, but sometimes needs double check
            await page.fill(query_input_selector, "")
            await page.fill(query_input_selector, query_name)
            print(f"  -> Filled search query.")

            await page.wait_for_selector(button_selector)
            await page.click(button_selector)
            print(f"  -> Clicked 'Try it'. Waiting for response...")

            await page.wait_for_selector(response_selector, state='visible', timeout=15000)
            await asyncio.sleep(1.5)  # let response fully render/update
            response_text = await page.inner_text(response_selector)

            # Save the raw JSON
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)

            try:
                data = json.loads(response_text)
                
                artists_data = data.get("artists", {}).get("items", [])
                if artists_data:
                    # Just picking the first result for this test
                    first_artist = artists_data[0]
                    spotify_id   = first_artist.get("id")
                    spotify_link = first_artist.get("external_urls", {}).get("spotify")
                    followers    = first_artist.get("followers", {}).get("total", 0)
                    genres       = first_artist.get("genres", [])
                    popularity   = first_artist.get("popularity", 0)
                    actual_name  = first_artist.get("name")

                    print(f"  -> Best Match : {actual_name}")
                    print(f"  -> Spotify ID : {spotify_id}")
                    print(f"  -> Followers  : {followers:,}")
                    print(f"  -> Genres     : {', '.join(genres) if genres else 'N/A'}")
                    print(f"  -> Popularity : {popularity}")

                    results.append({
                        "query_name":   query_name,
                        "artist_name":  actual_name,
                        "spotify_id":   spotify_id,
                        "spotify_link": spotify_link,
                        "followers":    followers,
                        "genres":       genres,
                        "popularity":   popularity
                    })
                else:
                    print("  -> No artists found in the JSON response.")

            except json.JSONDecodeError:
                print(f"  -> Could not parse response. Raw: {response_text[:200]}")

            await asyncio.sleep(1.5)
            print("-" * 40)

    except Exception as e:
        print(f"\nError: {e}")

    print("\n--- Scraping done. ---")
    try:
        input("Press Enter to close browser and exit...")
    except KeyboardInterrupt:
        pass
        
    await context.close()
    await playwright.stop()

    return results

# ─── Database Helpers ─────────────────────────────────────────────────────────

async def get_search_targets_from_db(limit=3):
    """Fetch the top N artists from the database who are missing a spotify_id."""
    if not engine:
        return []
    async with engine.begin() as conn:
        # We target the lowest IDs first as requested
        result = await conn.execute(
            text("SELECT id, artist_name FROM music_data WHERE spotify_id IS NULL OR spotify_id = '' ORDER BY id ASC LIMIT :limit"),
            {"limit": limit}
        )
        return [{"db_id": row[0], "artist_name": row[1]} for row in result.fetchall()]

async def save_results_to_db(results):
    """Persist the scraped metadata back to the PostgreSQL database."""
    for r in results:
        # Avoid saving if no match was found (query_name is always present, but others might not be)
        if not r.get("spotify_id"):
            continue

        print(f"  -> Saving '{r['artist_name']}' (ID: {r['db_id']}) to database...")
        await update_spotify_id(
            db_id=r["db_id"],
            spotify_id=r["spotify_id"],
            spotify_link=r["spotify_link"],
            genre=r["genres"],
            followers=r["followers"],
            popularity=r["popularity"]
        )
    print("Database update complete.")

# ─── Execution Logic ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    from sqlalchemy import text
    
    # Requirement: Test with 3 artists with the lowest IDs
    LIMIT = 3

    # Step 1: Fetch targets (Requires SelectorEventLoop on Windows for psycopg)
    print(f"Fetching artists with the lowest IDs missing Spotify data (Limit: {LIMIT})...")
    
    # Setup loop policy for DB operations
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    db_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(db_loop)
    targets = db_loop.run_until_complete(get_search_targets_from_db(limit=LIMIT))
    db_loop.close()

    if not targets:
        print("No artists without a Spotify ID found in the database. Process complete!")
        sys.exit(0)

    print(f"Found {len(targets)} artists to process: {[t['artist_name'] for t in targets]}\n")

    # Step 2: Scrape metadata (Requires ProactorEventLoop on Windows for Playwright)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Map database records to a simple list of names for the scraper logic
    artist_names = [t['artist_name'] for t in targets]
    results = asyncio.run(run_spotify_search_scraper(artist_names))

    # Re-attach database IDs to the results so we can save them
    for i, res in enumerate(results):
        res["db_id"] = targets[i]["db_id"]

    # Step 3: Save results (Switch back to SelectorEventLoop)
    if results:
        print(f"\nSaving {len(results)} results back to the database...")
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        save_loop = asyncio.new_event_loop()
        save_loop.run_until_complete(save_results_to_db(results))
        save_loop.close()
        print("Success: All artists processed.")
    else:
        print("No matches were found to save.")
