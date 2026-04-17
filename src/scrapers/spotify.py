"""
Spotify API Documentation Scraper

This script automates the process of extracting API response data from the Spotify 
for Developers documentation page.
"""

import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# Add root to sys.path to allow imports from src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

async def run_spotify_scraper(artist_id="0tB33cNAVw1H2enMHpgFiP"):
    """
    Main execution logic for the Spotify API documentation scraper.
    """
    async with async_playwright() as p:
        # Move user_data to data/ folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(base_dir, "../../")
        user_data_dir = os.path.join(project_root, "data/user_data")
        output_file = os.path.join(project_root, "data/raw/spotify_response.json")
        
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir, exist_ok=True)

        print(f"Launching browser (User data: {user_data_dir})...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            url = "https://developer.spotify.com/documentation/web-api/reference/get-an-artist"
            print(f"Navigating to {url}...")
            
            await page.goto(url, wait_until="load", timeout=60000)

            input_selector = 'input.e-10202-form-input.hUEbal'
            
            print("Waiting for documentation console...")
            await page.wait_for_selector(input_selector, timeout=300000) # Long timeout for manual login if needed

            await page.fill(input_selector, "")
            await page.fill(input_selector, artist_id)
            print(f"Filled Artist ID: {artist_id}")

            button_selector = 'button:has-text("Try it")'
            response_selector = 'pre.sc-dcdedfe6-0.ePqgwR'

            await page.click(button_selector)
            print("Clicked 'Try it' button. Waiting for response...")

            await page.wait_for_selector(response_selector, state='visible', timeout=15000)
            response_text = await page.inner_text(response_selector)
            
            # Save to raw data
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            
            print(f"Successfully saved response to {output_file}")
            
            try:
                return json.loads(response_text)
            except:
                return response_text

        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(run_spotify_scraper())
