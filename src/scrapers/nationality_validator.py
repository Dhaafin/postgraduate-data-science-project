"""
Nationality Validator V3.0 (Hybrid Metadata Strategy)
Automated flagging of Indonesian vs Foreign/Corporate records.
Prioritizes Spotify Genres for lightning-fast accuracy, falling back to Wikipedia search for edge cases.
"""

import os
import sys
import requests
import time
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connection import sync_engine, update_nationality_sync

class NationalityValidator:
    def __init__(self):
        self.headers = {
            "User-Agent": "NationalityValidator/3.0 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        
        # TIER 1: Spotify Indonesian Genres
        self.SPOTIFY_INDO_GENRES = [
            "indonesian", "indo", "jawa", "dangdut", "koplo", "sunda", 
            "minang", "batak", "maluku", "timur", "funkot", "hipdut"
        ]
        
        # TIER 2: Spotify Foreign/Corporate Genres
        self.SPOTIFY_FOREIGN_GENRES = [
            "k-pop", "k-ballad", "k-rock", "mollywood", "brazilian", 
            "norwegian", "children's music", "white noise", "lullaby",
            "sholawat" # While common in ID, often not standard pop artists.
        ]
        
        # TIER 3: Wikipedia Fallback Keywords
        self.WIKI_GREEN = [
            "indonesia", "jakarta", "bandung", "surabaya", "medan", "semarang",
            "jawa", "sumatera", "kalimantan", "sulawesi", "papua", "bali",
            "grup musik indonesia", "penyanyi indonesia", "musisi indonesia"
        ]
        
        self.WIKI_FOREIGN_MARKERS = [
            "berkebangsaan amerika serikat", "berkebangsaan korea selatan", "berkebangsaan inggris",
            "berkebangsaan britania raya", "berkebangsaan kanada", "berkebangsaan jepang",
            "asal amerika serikat", "asal korea selatan", "asal inggris"
        ]

    def validate_via_spotify(self, genres):
        """Tier 1 & 2: Instant metadata validation."""
        if not genres:
            return None, None
            
        genre_str = ", ".join(genres).lower()
        
        # Check Tier 1 (Indonesian)
        for indo in self.SPOTIFY_INDO_GENRES:
            # Add spaces to avoid matching 'windows' with 'indo'
            if indo in genre_str or f"indo " in genre_str:
                return "INDONESIAN", f"Spotify Genre Match: {indo}"
                
        # Check Tier 2 (Foreign)
        for foreign in self.SPOTIFY_FOREIGN_GENRES:
            if foreign in genre_str:
                return "FOREIGN", f"Spotify Foreign Genre: {foreign}"
                
        return None, None

    def search_wikipedia_title(self, artist_name):
        """Uses the Search API to find the closest actual page title."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": artist_name,
            "utf8": "",
            "format": "json",
            "srlimit": 1
        }
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=5)
            data = response.json()
            if data.get("query", {}).get("search"):
                return data["query"]["search"][0]["title"]
        except Exception:
            pass
        return None

    def check_wikipedia(self, artist_name):
        """Tier 3: Wikipedia Fallback."""
        # Find the best title first
        page_title = self.search_wikipedia_title(artist_name)
        if not page_title:
            # Fallback to direct name if search fails
            page_title = artist_name
            
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "text",
            "format": "json",
            "redirects": "true"
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return "ERROR", f"HTTP {response.status_code}"
                
            try:
                data = response.json()
            except ValueError:
                return "ERROR", "Invalid JSON from Wikipedia"
                
            if "parse" not in data:
                return "NOT_FOUND", "No Wikipedia page found."

            html_content = data["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, "html.parser")
            
            paragraphs = soup.find_all("p")
            full_text = " ".join([p.get_text().lower() for p in paragraphs[:2]])
            
            if not full_text:
                return "EMPTY", "Wikipedia page has no text."

            # Strong Foreign Check
            for marker in self.WIKI_FOREIGN_MARKERS:
                if marker in full_text:
                    return "FOREIGN", f"Wiki strong foreign marker: {marker}"

            # Indonesian Check
            has_green = any(green in full_text for green in self.WIKI_GREEN)
            if has_green:
                return "INDONESIAN", "Wiki Indonesian context confirmed."

            return "UNCERTAIN", "Wiki ambiguous."

        except Exception as e:
            return "ERROR", str(e)

    def run_validation(self):
        print("\n" + "="*50)
        print("      NATIONALITY VALIDATOR V3.0 (HYBRID)")
        print("==================================================\n")
        
        if not sync_engine:
            print("Error: Database engine not initialized.")
            return

        with sync_engine.begin() as conn:
            # Process ALL unflagged records
            result = conn.execute(text("SELECT id, artist_name, genre FROM music_data WHERE is_indonesian IS NULL"))
            artists = [{"id": row[0], "name": row[1], "genre": row[2]} for row in result.fetchall()]

        print(f"Auditing {len(artists)} unflagged records...\n")
        
        indo = 0
        foreign = 0
        uncertain = 0
        spotify_hits = 0
        wiki_hits = 0
        
        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            genres = artist["genre"]
            
            # TIER 1 & 2: SPOTIFY METADATA
            status, reason = self.validate_via_spotify(genres)
            
            if status:
                spotify_hits += 1
            else:
                # TIER 3: WIKIPEDIA
                status, reason = self.check_wikipedia(name)
                wiki_hits += 1
                time.sleep(0.1) # Rate limit only for Wiki hits
            
            # Execution
            if status == "INDONESIAN":
                print(f"🇮🇩 [INDO ] {name:<25} | {reason}")
                update_nationality_sync(db_id, True)
                indo += 1
            elif status == "FOREIGN":
                print(f"🌎 [NON-ID] {name:<25} | {reason}")
                update_nationality_sync(db_id, False)
                foreign += 1
            else:
                print(f"❓ [UNCRTN] {name:<25} | {reason}")
                uncertain += 1
                
        print("\n" + "="*50)
        print(f"VALIDATION SUMMARY")
        print(f"  - Total Audited: {len(artists)}")
        print(f"  - Fast-Tracked via Spotify: {spotify_hits}")
        print(f"  - Fallbacks via Wikipedia:  {wiki_hits}")
        print(f"  -------------------------")
        print(f"  - Valid Indonesian: {indo}")
        print(f"  - Foreign/Noise:    {foreign}")
        print(f"  - Uncertain:        {uncertain}")
        print("="*50)

if __name__ == "__main__":
    validator = NationalityValidator()
    validator.run_validation()
