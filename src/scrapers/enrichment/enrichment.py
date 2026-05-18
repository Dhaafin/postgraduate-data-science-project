"""
Spotify Search Console Scraper (Enrichment)

Automates the process of extracting artist metadata from the Spotify for Developers Search endpoint console.
"""

import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.database.operations import get_next_target_for_enrichment_sync, update_spotify_id_sync
from src.utils.scoring import score_spotify_candidate

async def scrape_single_artist(page, query_name, selectors, output_file):
    query_input_selector = selectors['query_input']
    button_selector = selectors['button']
    response_selector = selectors['response']

    print(f"Processing: '{query_name}'")
    try:
        await page.fill(query_input_selector, "")
        await page.fill(query_input_selector, query_name)
        
        await page.wait_for_selector(button_selector)
        await page.click(button_selector)
        
        await page.wait_for_selector(response_selector, state='visible', timeout=15000)
        await asyncio.sleep(1.5)
        response_text = await page.inner_text(response_selector)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response_text)

        data = json.loads(response_text)
        artists_data = data.get("artists", {}).get("items", [])
        
        if not artists_data:
            print(f"  -> No luck. Spotify doesn't seem to have anyone for '{query_name}'.")
            return None

        scored_candidates = []
        for artist in artists_data:
            score_data = score_spotify_candidate(query_name, artist)
            scored_candidates.append(score_data)
        
        if not scored_candidates:
            return None

        scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)
        best = scored_candidates[0]
        
        if best["total_score"] < 0.7:
            print(f"  -> Low Confidence Match ({best['total_score']:.2f}) for '{query_name}'. Refusing to save.")
            return None

        best_match = best["data"]
        print(f"  -> Best Match: {best_match.get('name')} (Score: {best['total_score']:.2f})")

        return {
            "artist_name":  best_match.get("name"),
            "spotify_id":   best_match.get("id"),
            "spotify_link": best_match.get("external_urls", {}).get("spotify"),
            "profile_picture": best_match.get("images", [])[0].get("url") if best_match.get("images") else None,
            "followers":    best_match.get("followers", {}).get("total", 0),
            "genres":       best_match.get("genres", []),
            "popularity":   best_match.get("popularity", 0)
        }
    except Exception as e:
        print(f"  -> Oops! Something went wrong while scraping '{query_name}': {e}")
        return None

async def run_spotify_enrichment():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, "../../../")
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
        
        print(f"Heading over to {url}...")
        await page.goto(url, wait_until="load", timeout=60000)
        print("\nBrowser is open! Please log in to Spotify if you haven't already.")
        input("Press Enter here once you're logged in and ready to roll...")

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

        try:
            while True:
                target = get_next_target_for_enrichment_sync()
                if not target:
                    print("\nAll caught up! No more artists to process.")
                    break

                result = await scrape_single_artist(page, target['artist_name'], selectors, output_file)
                
                if result:
                    print(f"  -> Found {result['artist_name']}. Saving...")
                    update_spotify_id_sync(
                        db_id=target['db_id'],
                        spotify_id=result["spotify_id"],
                        spotify_link=result["spotify_link"],
                        profile_picture=result["profile_picture"],
                        genre=result["genres"],
                        followers=result["followers"],
                        popularity=result["popularity"],
                        needs_review=False
                    )
                else:
                    print(f"  -> Couldn't find a match. Marking for review.")
                    update_spotify_id_sync(
                        db_id=target['db_id'],
                        spotify_id="", 
                        needs_review=True
                    )
                print("-" * 30)
                await asyncio.sleep(2)
        finally:
            await context.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.run(run_spotify_enrichment())
    except KeyboardInterrupt:
        print("\nStopped by user.")
