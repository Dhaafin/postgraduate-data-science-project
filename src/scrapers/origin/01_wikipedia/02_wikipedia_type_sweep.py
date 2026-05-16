import os
import sys
import time
import random
import re
import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from src.database.connection import sync_engine

class WikipediaTypeSweep:
    def __init__(self):
        self.headers = {
            "User-Agent": "IndoMusicTypeAnalytics/1.0 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        self.successful_updates = 0
        self.skipped_count = 0

    def _safe_get_json(self, params, artist_name):
        """Wrapper for requests to handle rate limits and non-JSON responses."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = requests.get(self.api_url, params=params, headers=self.headers, timeout=15)
                
                if r.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    print(f" [!] Rate limited. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                r.raise_for_status()
                return r.json()
            except requests.exceptions.JSONDecodeError:
                print(f" [!] Invalid JSON for {artist_name} (Attempt {attempt+1})")
                time.sleep(5)
            except Exception as e:
                print(f" [!] Request failed: {e}")
                time.sleep(5)
        return None

    def fetch_wikipedia_type(self, artist_name):
        """Determine if artist is a 'Person' or 'Group' via Wikipedia."""
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": artist_name,
            "format": "json"
        }
        
        data = self._safe_get_json(search_params, artist_name)
        if not data or not data.get("query", {}).get("search"):
            return None
        
        title = data["query"]["search"][0]["title"]
        
        parse_params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "redirects": "true"
        }
        
        data = self._safe_get_json(parse_params, artist_name)
        if not data or "parse" not in data:
            return None
            
        html = data["parse"]["text"]["*"]
        soup = BeautifulSoup(html, "html.parser")
        
        # Method 1: Check Infobox for 'Anggota' (Members) or 'Lahir' (Birth)
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            infobox_text = infobox.get_text().lower()
            if "anggota" in infobox_text or "mantan anggota" in infobox_text:
                return "Group"
            if "lahir" in infobox_text or "nama lahir" in infobox_text:
                return "Person"

        # Method 2: Check Lead Paragraph for keywords
        paragraphs = soup.find_all("p")
        for p in paragraphs[:2]:
            text_content = p.get_text().lower()
            if "grup musik" in text_content or "kelompok musik" in text_content or "band asal" in text_content:
                return "Group"
            if "adalah seorang" in text_content or "penyanyi indonesia" in text_content or "aktris" in text_content:
                return "Person"
        
        return None

    def run(self):
        print("\n" + "="*60)
        print(" WIKIPEDIA ARTIST-TYPE SWEEP (M4)")
        print("="*60)
        
        if not sync_engine:
            print("Database connection failed.")
            return

        with sync_engine.begin() as conn:
            query = text("SELECT id, artist_name FROM staging.music_data_staging WHERE artist_type IS NULL")
            artists = [{"id": row[0], "name": row[1]} for row in conn.execute(query).fetchall()]

        print(f"Targeting {len(artists)} records with NULL artist_type...\n")

        for idx, artist in enumerate(artists, start=1):
            name = artist["name"]
            db_id = artist["id"]
            
            print(f"[{idx}/{len(artists)}] 🔍 {name:<30}", end="", flush=True)
            
            a_type = self.fetch_wikipedia_type(name)
            
            if a_type:
                print(f" | ✅ Type: {a_type}")
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE staging.music_data_staging SET artist_type = :type WHERE id = :id"),
                        {"type": a_type, "id": db_id}
                    )
                self.successful_updates += 1
            else:
                print(" | ❌ Uncertain")
                self.skipped_count += 1
            
            time.sleep(random.uniform(2.0, 5.0))

        print("\n" + "="*60)
        print(" TYPE SWEEP COMPLETE")
        print("="*60)
        print(f"Successfully Updated : {self.successful_updates}")
        print(f"Skipped / Uncertain  : {self.skipped_count}")
        print("="*60)

if __name__ == "__main__":
    WikipediaTypeSweep().run()
