"""
Wikipedia Origin & Type Sweeper

Extracts origin city and artist type (Person/Group) from Wikipedia infoboxes and lead paragraphs.
Delegates all database updates to operations.py.
"""

import os
import sys
import time
import random
import re
import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.database.operations import get_artists_without_origin_sync, get_artists_without_type_sync, update_origin_city_sync, update_artist_type_sync
from src.utils.geo_constants import is_indonesian_location

class WikipediaSweeper:
    def __init__(self):
        self.headers = {
            "User-Agent": "IndoMusicSpatialAnalytics/1.2 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        
    def _safe_get_json(self, params, artist_name):
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

    def search_wikipedia_title(self, artist_name):
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": artist_name,
            "format": "json"
        }
        data = self._safe_get_json(search_params, artist_name)
        if not data or not data.get("query", {}).get("search"):
            return None
        return data["query"]["search"][0]["title"]
        
    def parse_wikipedia_page(self, title, artist_name):
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
        return BeautifulSoup(html, "html.parser")

    def clean_location_string(self, raw_text):
        text = re.sub(r'\[\d+\]', '', raw_text)
        if ')' in text:
            text = text.split(')')[-1]
        return text.strip()

    def fetch_wikipedia_origin(self, artist_name):
        title = self.search_wikipedia_title(artist_name)
        if not title: return None
        soup = self.parse_wikipedia_page(title, artist_name)
        if not soup: return None
        
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            for row in infobox.find_all("tr"):
                th, td = row.find("th"), row.find("td")
                if th and td:
                    header = th.get_text().lower()
                    if "lahir" in header or "asal" in header:
                        return self.clean_location_string(td.get_text())

        paragraphs = soup.find_all("p")
        for p in paragraphs[:2]:
            match = re.search(r"lahir (?:di|pada) ([\w\s,]+)", p.get_text(), re.I)
            if match:
                return self.clean_location_string(match.group(1))
        
        return None

    def fetch_wikipedia_type(self, artist_name):
        title = self.search_wikipedia_title(artist_name)
        if not title: return None
        soup = self.parse_wikipedia_page(title, artist_name)
        if not soup: return None
        
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            infobox_text = infobox.get_text().lower()
            if "anggota" in infobox_text or "mantan anggota" in infobox_text:
                return "Group"
            if "lahir" in infobox_text or "nama lahir" in infobox_text:
                return "Person"

        paragraphs = soup.find_all("p")
        for p in paragraphs[:2]:
            text_content = p.get_text().lower()
            if "grup musik" in text_content or "kelompok musik" in text_content or "band asal" in text_content:
                return "Group"
            if "adalah seorang" in text_content or "penyanyi indonesia" in text_content or "aktris" in text_content:
                return "Person"
        return None

    def run_origin_sweep(self):
        print("\n" + "="*60)
        print(" WIKIPEDIA ORIGIN SWEEP PIPELINE")
        print("="*60)
        
        artists = get_artists_without_origin_sync()
        print(f"Targeting {len(artists)} artists for origin sweep...\n")

        successful, skipped = 0, 0
        for idx, artist in enumerate(artists, start=1):
            name, db_id = artist["name"], artist["id"]
            print(f"[{idx}/{len(artists)}] SEARCH {name:<30}", end="", flush=True)
            
            origin = self.fetch_wikipedia_origin(name)
            if origin and is_indonesian_location(origin):
                print(f" | FOUND: {origin}")
                update_origin_city_sync(db_id, origin)
                successful += 1
            else:
                print(" | NOT FOUND")
                skipped += 1
            
            time.sleep(random.uniform(2.0, 5.0))

        print(f"\nSuccessfully Discovered: {successful} | Skipped: {skipped}\n")

    def run_type_sweep(self):
        print("\n" + "="*60)
        print(" WIKIPEDIA ARTIST-TYPE SWEEP")
        print("="*60)
        
        artists = get_artists_without_type_sync()
        print(f"Targeting {len(artists)} records with NULL artist_type...\n")

        successful, skipped = 0, 0
        for idx, artist in enumerate(artists, start=1):
            name, db_id = artist["name"], artist["id"]
            print(f"[{idx}/{len(artists)}] 🔍 {name:<30}", end="", flush=True)
            
            a_type = self.fetch_wikipedia_type(name)
            if a_type:
                print(f" | ✅ Type: {a_type}")
                update_artist_type_sync(db_id, a_type)
                successful += 1
            else:
                print(" | ❌ Uncertain")
                skipped += 1
            
            time.sleep(random.uniform(2.0, 5.0))

        print(f"\nSuccessfully Updated: {successful} | Skipped: {skipped}\n")

if __name__ == "__main__":
    sweeper = WikipediaSweeper()
    sweeper.run_origin_sweep()
    sweeper.run_type_sweep()
