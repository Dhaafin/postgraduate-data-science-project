"""
Spotify Search API Scraper.

This script automates the process of matching artists in the local database with 
their official Spotify IDs using the Spotify Web API's search endpoint.

Workflow:
1. Prompts the user for a manual Spotify Bearer Token.
2. Queries the database for all artists missing a 'spotify_id'.
3. Searches Spotify for each artist name.
4. Updates the database record with the first (most relevant) Spotify ID found.
"""

import os
import sys
import asyncio
import urllib.parse
import requests

# Add the project root to sys.path so we can import internal modules (src.*)
# This allows running the script directly from the command line.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import get_all_artists, update_spotify_id

async def run_spotify_search():
    """
    Main orchestration function for searching and syncing Spotify IDs.
    
    Handles user input for authentication, database retrieval, 
    API requests, and database updates.
    """
    print("\n" + "="*40)
    print(" Spotify API Data Extractor (Search)")
    print("="*40)
    
    # We ask for the token manually as per user requirement to avoid 
    # reliance on the automated auth script for this specific tool.
    token = input("\nPlease enter your Spotify Bearer Token: ").strip()
    if not token:
        print("Error: No token provided.")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Pull only the records that actually need an ID update
    print("\nFetching artists from the database...")
    artists = await get_all_artists()
    
    if not artists:
        print("No artists without a Spotify ID found. Everything is already synced!")
        return

    print(f"Found {len(artists)} artists to search for on Spotify.\n")

    for artist in artists:
        db_id = artist["id"]
        artist_name = artist["artist_name"]
        
        print(f"Searching for: '{artist_name}'...")
        
        # URI encoding is critical to handle names with spaces or special characters
        encoded_name = urllib.parse.quote(artist_name)
        url = f"https://api.spotify.com/v1/search?q={encoded_name}&type=artist&limit=1"
        
        try:
            response = requests.get(url, headers=headers)
            
            # Auth check: Stop early if the token expires during a mid-run
            if response.status_code == 401:
                print("Error: Unauthorized. Your token might be expired or invalid.")
                break
                
            response.raise_for_status()
            data = response.json()
            
            # Navigate the JSON response to find result items
            items = data.get("artists", {}).get("items", [])
            
            if items:
                # We assume the first result is the best match
                spotify_id = items[0].get("id")
                spotify_name = items[0].get("name")
                
                print(f"  -> Found match: {spotify_name} (ID: {spotify_id})")
                
                # Perform the database update for this specific row
                await update_spotify_id(db_id, spotify_id)
                print(f"  -> Successfully updated database.")
            else:
                print(f"  -> No results found on Spotify for '{artist_name}'.")
                
        except Exception as e:
            print(f"  -> Error searching for '{artist_name}': {e}")
            
    print("\n--- Process Finished ---")

if __name__ == "__main__":
    # Windows fix: The default ProactorEventLoop doesn't work well 
    # with certain networking/async libraries on Windows.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_spotify_search())
    except KeyboardInterrupt:
        print("\nProcess canceled by user.")
