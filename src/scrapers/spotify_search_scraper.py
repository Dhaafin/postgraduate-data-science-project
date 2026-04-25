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
import re
from playwright.async_api import async_playwright

# Add the project root to sys.path so we can import internal modules (src.*)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import text
from src.database.connection import engine, update_spotify_id, get_db_engine, sync_engine, update_spotify_id_sync, get_sync_engine

async def scrape_single_artist(page, query_name, selectors, output_file):
    """
    Handles the actual browser interaction for a single artist search.

    This function fills the search box, clicks the 'Try it' button, waits for the
    Spotify console to spit out a JSON response, and then parses it to find 
    the best possible match.

    Args:
        page (Page): The Playwright page instance to use.
        query_name (str): The name of the artist we're looking for.
        selectors (dict): A map of CSS selectors for the Spotify console.
        output_file (str): Path to save the raw JSON response for debugging.

    Returns:
        dict | None: A dictionary of artist metadata if a match is found, else None.
    """
    query_input_selector = selectors['query_input']
    button_selector = selectors['button']
    response_selector = selectors['response']

    print(f"Processing: '{query_name}'")

    try:
        # First, clear the search box and type the artist name
        await page.fill(query_input_selector, "")
        await page.fill(query_input_selector, query_name)
        
        # Smash that 'Try it' button
        await page.wait_for_selector(button_selector)
        await page.click(button_selector)
        
        # Wait for the JSON response to appear in the code block
        await page.wait_for_selector(response_selector, state='visible', timeout=15000)
        await asyncio.sleep(1.5)  # Give the UI a second to finish rendering
        response_text = await page.inner_text(response_selector)

        # Better save a copy of the raw JSON just in case we need to debug later
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response_text)

        data = json.loads(response_text)
        artists_data = data.get("artists", {}).get("items", [])
        
        if not artists_data:
            print(f"  -> No luck. Spotify doesn't seem to have anyone for '{query_name}'.")
            return None

        # We need to be picky here. We only want results where the artist name 
        # actually makes sense given our search query to avoid grabbing the wrong person.
        query_clean = query_name.lower().strip()
        query_words = set(re.findall(r'\w+', query_clean))
        stop_words = {"the", "and", "feat", "ft", "v", "vs"}
        significant_query_words = query_words - stop_words or query_words

        candidates = []
        for artist in artists_data:
            name_clean = artist.get("name", "").lower().strip()
            name_words = set(re.findall(r'\w+', name_clean))
            # If they share at least one meaningful word, they're a candidate
            if significant_query_words & name_words:
                candidates.append(artist)
        
        if not candidates:
            print(f"  -> Found some names, but none of them look like a good enough match for '{query_name}'.")
            return None

        # If we have multiple candidates, we'll bet on the one with the highest popularity
        best_match = max(candidates, key=lambda x: x.get("popularity", 0))

        return {
            "artist_name":  best_match.get("name"),
            "spotify_id":   best_match.get("id"),
            "spotify_link": best_match.get("external_urls", {}).get("spotify"),
            "followers":    best_match.get("followers", {}).get("total", 0),
            "genres":       best_match.get("genres", []),
            "popularity":   best_match.get("popularity", 0)
        }

    except Exception as e:
        print(f"  -> Oops! Something went wrong while scraping '{query_name}': {e}")
        return None

async def run_spotify_search_scraper():
    """
    The main engine that drives the whole scraping process.

    It sets up the browser, navigates to the Spotify developer console, 
    and enters a loop that keeps pulling artists from the database and 
    processing them until there's nobody left to search for.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")
    user_data_dir = os.path.join(project_root, "data/user_data")
    output_file = os.path.join(project_root, "data/raw/spotify_search_response.json")

    # Make sure we have somewhere to put our data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(user_data_dir, exist_ok=True)

    selectors = {
        'remove_album': 'div[aria-label="Remove album"]',
        'type_input': 'input#react-select-2-input',
        'query_input': 'input[data-encore-id="formInput"]',
        'button': 'button:has-text("Try it")',
        'response': 'pre.sc-dcdedfe6-0.ePqgwR'
    }

    async with async_playwright() as playwright:
        # We use a persistent context so we don't have to log in every single time
        print(f"Launching browser (user data: {user_data_dir})...")
        context = await playwright.firefox.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        url = "https://developer.spotify.com/documentation/web-api/reference/search"
        
        print(f"Heading over to {url}...")
        await page.goto(url, wait_until="load", timeout=60000)

        # Give the user a moment to log in or get the page ready
        print("\nBrowser is open! Please log in to Spotify if you haven't already.")
        input("Press Enter here once you're logged in and ready to roll...")

        # Let's set up the filters first so we're only looking for 'artists'
        await page.wait_for_selector(selectors['query_input'], timeout=30000)
        try:
            if await page.locator(selectors['remove_album']).count() > 0:
                await page.click(selectors['remove_album'])
                await asyncio.sleep(0.5)
            await page.fill(selectors['type_input'], "artist")
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            print("Filters set to 'Artist' only. Starting the loop...\n")
        except Exception as e:
            print(f"Warning: Had some trouble setting the filters automatically: {e}")

        # Use a fresh synchronous engine for this thread
        scraper_engine = get_sync_engine()
        if not scraper_engine:
            print("Error: Could not create a database engine for the scraper.")
            return

        try:
            while True:
                # Step 1: Who's next? (Fetch synchronously to avoid Proactor conflict)
                target = get_next_target_from_db_sync(scraper_engine)
                if not target:
                    print("\nLooks like we're all caught up! No more artists to process.")
                    break

                # Step 2: Try to find them on Spotify (This remains async for Playwright)
                result = await scrape_single_artist(page, target['artist_name'], selectors, output_file)
                
                # Step 3: Write results back (Synchronously)
                if result:
                    print(f"  -> Score! Found {result['artist_name']}. Saving to database...")
                    update_spotify_id_sync(
                        db_id=target['db_id'],
                        spotify_id=result["spotify_id"],
                        spotify_link=result["spotify_link"],
                        genre=result["genres"],
                        followers=result["followers"],
                        popularity=result["popularity"],
                        needs_review=False,
                        db_engine=scraper_engine
                    )
                else:
                    print(f"  -> Couldn't find a match for '{target['artist_name']}'. Marking for review.")
                    update_spotify_id_sync(
                        db_id=target['db_id'],
                        spotify_id="", 
                        needs_review=True,
                        db_engine=scraper_engine
                    )

                print("-" * 30)
                await asyncio.sleep(2)
        finally:
            # Clean up the sync engine if needed
            scraper_engine.dispose()

        await context.close()


# ─── Database Helpers ─────────────────────────────────────────────────────────

def get_next_target_from_db_sync(db_engine):
    """
    Synchronous version of target fetching.
    """
    if not db_engine:
        return None
    with db_engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT id, artist_name 
                FROM music_data 
                WHERE (spotify_id IS NULL OR spotify_id = '') 
                  AND (needs_review IS FALSE OR needs_review IS NULL)
                ORDER BY id ASC 
                LIMIT 1
            """)
        )
        row = result.fetchone()
        return {"db_id": row[0], "artist_name": row[1]} if row else None

# Note: save_results_to_db is no longer needed as we save one-by-one inside run_spotify_search_scraper

# ─── Execution Logic ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # On Windows, Playwright REQUIRED the ProactorEventLoop to launch browsers.
    # Since we now use synchronous database calls, we can safely use Proactor 
    # without breaking any asynchronous DB drivers.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("--- Spotify Artist Metadata Scraper ---")
    try:
        asyncio.run(run_spotify_search_scraper())
    except KeyboardInterrupt:
        print("\nStopping... See ya later!")
    except Exception as e:
        print(f"\nFatal error crashed the scraper: {e}")
