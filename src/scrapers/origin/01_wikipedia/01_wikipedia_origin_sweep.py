import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from src.database.connection import sync_engine
from src.utils.geo_constants import is_indonesian_location

class WikipediaOriginSweep:
    def __init__(self):
        self.headers = {
            "User-Agent": "IndoMusicSpatialAnalytics/1.1 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        self.queue_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../docs/musicbrainz/FINAL_GEO_ENRICHMENT_QUEUE.md'))
        self.successful_discoveries = 0
        self.skipped_count = 0

    def parse_queue(self):
        """Parse the FINAL_GEO_ENRICHMENT_QUEUE.md for MANUAL_PENDING entries."""
        if not os.path.exists(self.queue_path):
            print(f"[!] Queue file not found: {self.queue_path}")
            return []

        with open(self.queue_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        pending_artists = []
        for line in lines:
            if "| MANUAL_PENDING |" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    pending_artists.append({"id": parts[0], "name": parts[1]})
        return pending_artists

    def clean_location_string(self, raw_text):
        """Clean Wikipedia garbage (dates, ages, citations) to get the city."""
        # 1. Remove references [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', raw_text)
        
        # 2. Extract location after date/age patterns
        # Matches '17 Juli 2000 (umur 25)Jakarta' or 'Padang, 20 Maret 1981'
        # Strategy: Look for the last comma-separated part or the part after the closing parenthesis
        if ')' in text:
            text = text.split(')')[-1]
        
        # 3. Final cleanup: strip common noise
        text = text.strip()
        # Remove "Indonesia" suffix if redundant for geocoding but keep for validation
        return text

    def fetch_wikipedia_origin(self, artist_name):
        """Search and extract origin from Wikipedia Infobox or Lead Paragraph."""
        # Step A: Search for the best page
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": artist_name,
            "format": "json"
        }
        try:
            r = requests.get(self.api_url, params=search_params, headers=self.headers, timeout=10)
            data = r.json()
            if not data.get("query", {}).get("search"):
                return None
            
            title = data["query"]["search"][0]["title"]
            
            # Step B: Parse the page content
            parse_params = {
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": "true"
            }
            r = requests.get(self.api_url, params=parse_params, headers=self.headers, timeout=10)
            html = r.json()["parse"]["text"]["*"]
            soup = BeautifulSoup(html, "html.parser")
            
            # Step C: Check Infobox
            infobox = soup.find("table", {"class": "infobox"})
            if infobox:
                rows = infobox.find_all("tr")
                for row in rows:
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        header = th.get_text().lower()
                        if "lahir" in header or "asal" in header:
                            return self.clean_location_string(td.get_text())

            # Step D: Fallback to first paragraph regex
            paragraphs = soup.find_all("p")
            for p in paragraphs[:2]:
                text_content = p.get_text()
                match = re.search(r"lahir (?:di|pada) ([\w\s,]+)", text_content, re.I)
                if match:
                    return self.clean_location_string(match.group(1))

        except Exception as e:
            print(f"  [!] Error processing {artist_name}: {e}")
        
        return None

    def run(self):
        print("\n" + "="*60)
        print(" WIKIPEDIA ORIGIN SWEEP PIPELINE (M4)")
        print("="*60)
        
        artists = self.parse_queue()
        print(f"Targeting {len(artists)} artists with MANUAL_PENDING status...\n")

        for idx, artist in enumerate(artists, start=1):
            name = artist["name"]
            db_id = artist["id"]
            
            print(f"[{idx}/{len(artists)}] 🔍 {name:<30}", end="", flush=True)
            
            origin = self.fetch_wikipedia_origin(name)
            
            if origin and is_indonesian_location(origin):
                print(f" | ✅ Found: {origin}")
                
                # Update Supabase Staging
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE staging.music_data_staging SET origin_city = :city, is_indonesian = TRUE WHERE id = :id"),
                        {"city": origin, "id": db_id}
                    )
                self.successful_discoveries += 1
            else:
                print(" | ❌ Not found")
                self.skipped_count += 1
            
            # Respect Wikipedia rate limits
            time.sleep(1.5)

        print("\n" + "="*60)
        print(" SWEEP COMPLETE")
        print("="*60)
        print(f"Successfully Discovered : {self.successful_discoveries}")
        print(f"Skipped / Not Found     : {self.skipped_count}")
        print("="*60)

if __name__ == "__main__":
    WikipediaOriginSweep().run()
