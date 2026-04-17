"""
Spotify Search API Scraper.
Retrieves artist names from the database, searches Spotify, and updates the Spotify IDs.
"""

import os
import sys
import asyncio
import urllib.parse
import requests

# Ensure the root directory is in the path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import get_all_artists, update_spotify_id

async def run_spotify_search():
    print("\n" + "="*40)
    print(" Spotify API Data Extractor (Search)")
    print("="*40)
    
    # Ask the user for the bearer token
    token = input("\nPlease enter your Spotify Bearer Token: ").strip()
    if not token:
        print("Error: No token provided.")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Fetch all artists that are missing a Spotify ID
    print("\nFetching artists from the database...")
    artists = await get_all_artists()
    
    if not artists:
        print("No artists without a Spotify ID found in the database. Every artist is already linked!")
        return

    print(f"Found {len(artists)} artists to search for on Spotify.\n")

    for artist in artists:
        db_id = artist["id"]
        artist_name = artist["artist_name"]
        
        print(f"Searching for: '{artist_name}'...")
        
        # URI encode the artist name for the search query
        encoded_name = urllib.parse.quote(artist_name)
        url = f"https://api.spotify.com/v1/search?q={encoded_name}&type=artist&limit=1"
        
        try:
            response = requests.get(url, headers=headers)
            
            # Stop if the token is invalid or expired
            if response.status_code == 401:
                print("Error: Unauthorized. Your token might be expired or invalid.")
                break
                
            response.raise_for_status()
            data = response.json()
            
            items = data.get("artists", {}).get("items", [])
            
            if items:
                # Get the first result (usually the most relevant)
                spotify_id = items[0].get("id")
                spotify_name = items[0].get("name")
                
                print(f"  -> Found match: {spotify_name} (ID: {spotify_id})")
                
                # Update the ID in our database
                await update_spotify_id(db_id, spotify_id)
                print(f"  -> Successfully updated database.")
            else:
                print(f"  -> No results found on Spotify for '{artist_name}'.")
                
        except Exception as e:
            print(f"  -> Error searching for '{artist_name}': {e}")
            
    print("\n--- Process Finished ---")

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy with psycopg
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(run_spotify_search())
    except KeyboardInterrupt:
        print("\nProcess canceled by user.")
