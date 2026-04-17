"""
Spotify API Documentation Scraper

This script automates the process of extracting API response data from the Spotify 
for Developers documentation page.

It pulls the top 3 artist IDs from the database, runs each one through the 
Spotify docs console, collects metadata, then saves it back to the database.

Architecture note (Windows):
  - DB fetch + save  → SelectorEventLoop  (required by psycopg)
  - Playwright       → ProactorEventLoop  (required for subprocess spawning)
  These two loops run sequentially, never mixed.
"""

import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# Add root to sys.path to allow imports from src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.database.connection import engine, update_spotify_id
from sqlalchemy import text

# ─── Database helpers (run in SelectorEventLoop) ─────────────────────────────

async def get_top_artists_with_id(limit=3):
    """Fetch top N artists from the database that already have a spotify_id."""
    if not engine:
        return []
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT id, artist_name, spotify_id FROM music_data WHERE spotify_id IS NOT NULL AND spotify_id != '' LIMIT :limit"),
            {"limit": limit}
        )
        return [{"db_id": row[0], "artist_name": row[1], "spotify_id": row[2]} for row in result.fetchall()]

async def save_results_to_db(results):
    """Save the scraped results list back to the database."""
    for r in results:
        print(f"  -> Saving '{r['artist_name']}' to database...")
        await update_spotify_id(
            db_id=r["db_id"],
            spotify_id=r["spotify_id"],
            spotify_link=r["spotify_link"],
            genre=r["genres"],
            followers=r["followers"],
            popularity=r["popularity"]
        )
        print(f"  -> Done.")

# ─── Playwright scraper (run in ProactorEventLoop) ────────────────────────────

async def run_spotify_scraper(artists):
    """
    Opens Firefox, navigates to the Spotify docs console, loops through
    each artist, clicks 'Try it', and collects the response.
    Returns a list of result dicts. Does NOT touch the database.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../")
    user_data_dir = os.path.join(project_root, "data/user_data")
    output_file = os.path.join(project_root, "data/raw/spotify_response.json")

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
        url = "https://developer.spotify.com/documentation/web-api/reference/get-an-artist"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="load", timeout=60000)

        input_selector  = 'input.e-10202-form-input.hUEbal'
        button_selector = 'button:has-text("Try it")'
        response_selector = 'pre.sc-dcdedfe6-0.ePqgwR'

        print("\nBrowser is open. Please log in to Spotify if prompted.")
        print("(Press Ctrl+C at any time to cancel.)\n")
        try:
            input("Press Enter here once you're logged in and the page is ready...")
        except KeyboardInterrupt:
            print("\nCanceled.")
            # Keep browser open, just stop processing
            print("(Browser is still open. Close it manually.)")
            await asyncio.sleep(float('inf'))  # keep loop alive so browser stays

        await page.wait_for_selector(input_selector, timeout=30000)
        print("Console detected! Starting to process artists...\n")

        for artist in artists:
            db_id       = artist["db_id"]
            artist_name = artist["artist_name"]
            spotify_id  = artist["spotify_id"]

            print(f"Processing: '{artist_name}' (ID: {spotify_id})")

            await page.fill(input_selector, "")
            await page.fill(input_selector, spotify_id)
            print(f"  -> Filled ID into console.")

            await page.wait_for_selector(button_selector)
            await page.evaluate("el => el.click()", await page.query_selector(button_selector))
            print(f"  -> Clicked 'Try it'. Waiting for response...")

            await page.wait_for_selector(response_selector, state='visible', timeout=15000)
            await asyncio.sleep(1)  # let response fully render
            response_text = await page.inner_text(response_selector)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)

            try:
                data = json.loads(response_text)
                spotify_link = data.get("external_urls", {}).get("spotify")
                followers    = data.get("followers", {}).get("total", 0)
                genres       = data.get("genres", [])
                popularity   = data.get("popularity", 0)

                print(f"  -> Spotify Link : {spotify_link}")
                print(f"  -> Followers    : {followers:,}")
                print(f"  -> Genres       : {', '.join(genres) if genres else 'N/A'}")
                print(f"  -> Popularity   : {popularity}")

                results.append({
                    "db_id":       db_id,
                    "artist_name": artist_name,
                    "spotify_id":  spotify_id,
                    "spotify_link": spotify_link,
                    "followers":   followers,
                    "genres":      genres,
                    "popularity":  popularity
                })

            except json.JSONDecodeError:
                print(f"  -> Could not parse response. Raw: {response_text[:200]}")

            await asyncio.sleep(1)

    except Exception as e:
        print(f"\nError: {e}")

    print("\n--- Scraping done. Browser is still open. Close it when you're ready. ---")
    # Keep the event loop alive so the browser doesn't close
    try:
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        pass

    return results

# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.platform != 'win32':
        asyncio.run(run_spotify_scraper([]))
        sys.exit(0)

    # Step 1: Fetch artists in SelectorEventLoop (psycopg-compatible)
    print("Fetching top 3 artists from the database...")
    sel_loop = asyncio.SelectorEventLoop()
    artists = sel_loop.run_until_complete(get_top_artists_with_id(limit=3))
    sel_loop.close()

    if not artists:
        print("No artists with a Spotify ID found. Run the Search API extractor first.")
        sys.exit(0)

    print(f"Found {len(artists)} artists.\n")

    # Step 2: Scrape with Playwright in ProactorEventLoop (no DB calls inside)
    results = asyncio.run(run_spotify_scraper(artists))

    if results:
        # Step 3: Save results in a fresh SelectorEventLoop
        print(f"\nSaving {len(results)} results to the database...")
        sel_loop2 = asyncio.SelectorEventLoop()
        sel_loop2.run_until_complete(save_results_to_db(results))
        sel_loop2.close()
        print(f"All done!")
    else:
        print("No results to save.")
