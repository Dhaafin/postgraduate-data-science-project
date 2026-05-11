"""
Wikipedia Discovery Script V3 (Sprint 4.1.2) - "Expert Resilience"
Features: Substring matching, Randomized Jitter, and Multi-Category Fallbacks.
"""

import os
import sys
import time
import random
import requests
from sqlalchemy import text
from difflib import SequenceMatcher

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connection import sync_engine

class WikiDiscovery:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.wiki_api_url = "https://id.wikipedia.org/w/api.php"

    def is_match(self, name, title):
        """Advanced matching: check similarity OR substring relationship."""
        name_l = name.lower()
        title_l = title.lower().split(" (")[0] # Strip (penyanyi)
        
        # 1. High similarity
        if SequenceMatcher(None, name_l, title_l).ratio() > 0.8:
            return True
        
        # 2. Substring match (e.g., 'Andmesh' in 'Andmesh Kamaleng')
        if name_l in title_l or title_l in name_l:
            return True
            
        return False

    def get_api(self, params):
        """Wrapper with retries and backoff for 429 errors."""
        for attempt in range(3):
            try:
                response = requests.get(self.wiki_api_url, params=params, headers=self.headers, timeout=15)
                if response.status_code == 429:
                    wait = 30 * (attempt + 1)
                    print(f" [429] Rate limit. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f" [Network Error] {e}")
                time.sleep(5)
        return None

    def find_via_wikidata(self, spotify_id):
        """Tier 1: 100% ID Match."""
        query = f"""
        SELECT ?sitelink WHERE {{
          ?item wdt:P1902 "{spotify_id}".
          ?sitelink schema:about ?item;
                    schema:isPartOf <https://id.wikipedia.org/>.
        }}
        """
        try:
            response = requests.get(self.sparql_url, params={'query': query, 'format': 'json'}, headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {}).get("bindings", [])
                if results: return results[0]["sitelink"]["value"]
        except: pass
        return None

    def find_via_search(self, artist_name):
        """Tier 2: Multi-Pass Search Logic."""
        # Pass 1: Opensearch (Titles)
        data = self.get_api({"action": "opensearch", "search": artist_name, "limit": 5, "format": "json"})
        if data and data[1]:
            for i, title in enumerate(data[1]):
                if self.is_match(artist_name, title):
                    return data[3][i]

        # Pass 2: Full-text search with Music context (Anchored)
        data = self.get_api({
            "action": "query", "list": "search", 
            "srsearch": f'"{artist_name}" (musisi OR penyanyi OR "grup musik")',
            "srlimit": 1, "format": "json"
        })
        if data and data.get("query", {}).get("search"):
            match = data["query"]["search"][0]
            if self.is_match(artist_name, match["title"]):
                return f"https://id.wikipedia.org/wiki/{match['title'].replace(' ', '_')}"

        return None

    def run(self):
        print("\n" + "="*50)
        print("      WIKIPEDIA DISCOVERY V3 (EXPERT MODE)")
        print("==================================================\n")
        
        if not sync_engine: return

        with sync_engine.begin() as conn:
            query = text("SELECT id, artist_name, spotify_id FROM music_data WHERE is_indonesian = TRUE AND wikipedia_url IS NULL")
            artists = [{"id": row[0], "name": row[1], "sid": row[2]} for row in conn.execute(query).fetchall()]

        print(f"Targeting {len(artists)} records...\n")
        
        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            spotify_id = artist["sid"]
            
            print(f"🔍 {name:<30}", end="", flush=True)
            
            # Tier 1: Wikidata
            url = self.find_via_wikidata(spotify_id)
            source = "✅ WD"
            
            # Tier 2: Smart Search
            if not url:
                url = self.find_via_search(name)
                source = "🔗 Search"
            
            if url:
                print(f" | {source:<10} | {url}")
                with sync_engine.begin() as conn:
                    conn.execute(text("UPDATE music_data SET wikipedia_url = :url WHERE id = :id"), {"url": url, "id": db_id})
            else:
                print(" | ❌ NO MATCH")
            
            # Randomized Jitter (1.5s to 4s) to mimic human browsing
            time.sleep(random.uniform(2.0, 5.0))

if __name__ == "__main__":
    WikiDiscovery().run()
