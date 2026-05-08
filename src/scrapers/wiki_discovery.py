"""
Wikipedia Discovery Script (Sprint 4.1)
Connects Spotify IDs to Wikipedia URLs using Wikidata SPARQL and Anchored Search.
"""

import os
import sys
import time
import requests
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connection import sync_engine

class WikiDiscovery:
    def __init__(self):
        self.headers = {
            "User-Agent": "WikiDiscoveryBot/1.0 (Research Project; contact via github)"
        }
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.wiki_api_url = "https://id.wikipedia.org/w/api.php"

    def find_via_wikidata(self, spotify_id):
        """Uses SPARQL to find the Wikipedia sitelink for a Spotify Artist ID."""
        query = f"""
        SELECT ?sitelink WHERE {{
          ?item wdt:P1902 "{spotify_id}".
          ?sitelink schema:about ?item;
                    schema:isPartOf <https://id.wikipedia.org/>.
        }}
        """
        try:
            response = requests.get(
                self.sparql_url, 
                params={'query': query, 'format': 'json'}, 
                headers=self.headers,
                timeout=15
            )
            data = response.json()
            results = data.get("results", {}).get("bindings", [])
            if results:
                return results[0]["sitelink"]["value"]
        except Exception as e:
            print(f"  [Wikidata Error] {e}")
        return None

    def find_via_search(self, artist_name):
        """Fallback: Performs an anchored search on id.wikipedia.org."""
        # Try with music-specific anchors
        search_query = f'"{artist_name}" (musisi OR penyanyi OR "grup musik") indonesia'
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_query,
            "format": "json",
            "srlimit": 1
        }
        try:
            response = requests.get(self.wiki_api_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                title = search_results[0]["title"]
                return f"https://id.wikipedia.org/wiki/{title.replace(' ', '_')}"
        except Exception as e:
            print(f"  [Search Error] {e}")
        return None

    def run(self):
        print("\n" + "="*50)
        print("      WIKIPEDIA URL DISCOVERY (SPRINT 4.1)")
        print("==================================================\n")
        
        if not sync_engine:
            print("Error: Database engine not initialized.")
            return

        with sync_engine.begin() as conn:
            # Only process validated Indonesian artists missing a Wiki URL
            query = text("""
                SELECT id, artist_name, spotify_id 
                FROM music_data 
                WHERE is_indonesian = TRUE 
                AND wikipedia_url IS NULL
            """)
            result = conn.execute(query)
            artists = [{"id": row[0], "name": row[1], "sid": row[2]} for row in result.fetchall()]

        print(f"Targeting {len(artists)} artists for discovery...\n")
        
        found_wd = 0
        found_search = 0
        failed = 0

        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            spotify_id = artist["sid"]
            
            print(f"🔍 Processing: {name}...")
            
            # Tier 1: Wikidata
            wiki_url = self.find_via_wikidata(spotify_id)
            if wiki_url:
                print(f"  ✅ Found via Wikidata: {wiki_url}")
                found_wd += 1
            else:
                # Tier 2: Anchored Search
                wiki_url = self.find_via_search(name)
                if wiki_url:
                    print(f"  🔗 Found via Search:   {wiki_url}")
                    found_search += 1
                else:
                    print(f"  ❌ No match found.")
                    failed += 1
            
            if wiki_url:
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE music_data SET wikipedia_url = :url WHERE id = :id"),
                        {"url": wiki_url, "id": db_id}
                    )
            
            # Be gentle with APIs
            time.sleep(1)

        print("\n" + "="*50)
        print(f"DISCOVERY SUMMARY")
        print(f"  - Total Processed: {len(artists)}")
        print(f"  - Wikidata Hits:   {found_wd}")
        print(f"  - Search Hits:     {found_search}")
        print(f"  - Failed:          {failed}")
        print("="*50)

if __name__ == "__main__":
    discovery = WikiDiscovery()
    discovery.run()
