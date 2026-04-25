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
from src.database.connection import engine, update_spotify_id

async def scrape_single_artist(page, query_name, selectors, output_file):
    """
    Scrapes metadata for a single artist using an existing browser page.
    """
    query_input_selector = selectors['query_input']
    button_selector = selectors['button']
    response_selector = selectors['response']

    print(f"Processing: '{query_name}'")

    try:
        # Clear and fill the search query
        await page.fill(query_input_selector, "")
        await page.fill(query_input_selector, query_name)
        
        await page.wait_for_selector(button_selector)
        await page.click(button_selector)
        
        # Wait for JSON response in the console
        await page.wait_for_selector(response_selector, state='visible', timeout=15000)
        await asyncio.sleep(1.5)  # Let response fully render
        response_text = await page.inner_text(response_selector)

        # Save the raw JSON for sanity check
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response_text)

        data = json.loads(response_text)
        artists_data = data.get("artists", {}).get("items", [])
        
        if not artists_data:
            print(f"  -> No artists found for '{query_name}'.")
            return None

        # Logic: Filter results for meaningful name overlap
        query_clean = query_name.lower().strip()
        query_words = set(re.findall(r'\w+', query_clean))
        stop_words = {"the", "and", "feat", "ft", "v", "vs"}
        significant_query_words = query_words - stop_words or query_words

        candidates = []
        for artist in artists_data:
            name_clean = artist.get("name", "").lower().strip()
            name_words = set(re.findall(r'\w+', name_clean))
            if significant_query_words & name_words:
                candidates.append(artist)
        
        if not candidates:
            print(f"  -> No valid matches found with common words for '{query_name}'.")
            return None

        # Best match is the most popular among candidates
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
        print(f"  -> Error scraping '{query_name}': {e}")
        return None

async def run_spotify_search_scraper():
    """
    Main orchestration for the continuous scraping loop.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")
    user_data_dir = os.path.join(project_root, "data/user_data")
    output_file = os.path.join(project_root, "data/raw/spotify_search_response.json")

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
        print(f"Launching browser (user data: {user_data_dir})...")
        context = await playwright.firefox.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        url = "https://developer.spotify.com/documentation/web-api/reference/search"
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="load", timeout=60000)

        print("\nBrowser is open. Please log in to Spotify if prompted.")
        input("Press Enter here once you're logged in and the page is ready to search...")

        # Setup filters (remove 'album', add 'artist')
        await page.wait_for_selector(selectors['query_input'], timeout=30000)
        try:
            if await page.locator(selectors['remove_album']).count() > 0:
                await page.click(selectors['remove_album'])
                await asyncio.sleep(0.5)
            await page.fill(selectors['type_input'], "artist")
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            print("Console filters configured (Artist only).\n")
        except Exception as e:
            print(f"Warning: Could not setup filters: {e}")

        while True:
            # Step 1: Fetch the next artist missing data
            target = await get_next_target_from_db()
            if not target:
                print("\nNo more artists to process. Finished!")
                break

            # Step 2: Scrape metadata
            result = await scrape_single_artist(page, target['artist_name'], selectors, output_file)
            
            # Step 3: Save results immediately
            if result:
                print(f"  -> Match found: {result['artist_name']}. Saving...")
                await update_spotify_id(
                    db_id=target['db_id'],
                    spotify_id=result["spotify_id"],
                    spotify_link=result["spotify_link"],
                    genre=result["genres"],
                    followers=result["followers"],
                    popularity=result["popularity"],
                    needs_review=False
                )
            else:
                print(f"  -> No results for '{target['artist_name']}'. Marking for review.")
                # Mark it so we don't try it again next time
                await update_spotify_id(
                    db_id=target['db_id'],
                    spotify_id="", # Empty but not NULL
                    needs_review=True
                )

            print("-" * 30)
            await asyncio.sleep(2) # Modest jitter/delay 

        await context.close()


# ─── Database Helpers ─────────────────────────────────────────────────────────

async def get_next_target_from_db():
    """Fetch the next artist who is missing a spotify_id and hasn't failed review."""
    if not engine:
        return None
    async with engine.begin() as conn:
        result = await conn.execute(
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
    # Playwright requires ProactorEventLoop on Windows. 
    # SQLAlchemy/psycopg also works fine with it.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("--- Continuous Spotify Artist Scraper ---")
    try:
        asyncio.run(run_spotify_search_scraper())
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
