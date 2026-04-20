"""
Spotify Search API Scraper (Testing Version)

This script automates the process of extracting API response data from the Spotify 
for Developers documentation page (Search endpoint).

For testing purposes, this version uses a hardcoded list of artist names
instead of fetching from the database, and simply prints the results.
"""

import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

async def run_spotify_search_scraper(artists_to_search):
    """
    Opens Firefox, navigates to the Spotify docs console, sets up search filters,
    loops through each artist query, and collects the response.
    Returns a list of result dicts.
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

        # Selectors based on provided HTML
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

if __name__ == "__main__":
    import asyncio
    
    # Required for Playwright to spawn subprocesses correctly on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Hardcoded list of artists to test with
    test_artists = ["batas senja", "fourtwnty", "doxy"]
    
    print("--- Running Test Spotify Search Scraper ---\n")
    print(f"Artists to search: {test_artists}\n")
    
    results = asyncio.run(run_spotify_search_scraper(test_artists))
    
    print("\n--- Final Extracted Summary ---")
    for r in results:
        print(f"{r['query_name']} -> {r['artist_name']} ({r['spotify_id']})")
