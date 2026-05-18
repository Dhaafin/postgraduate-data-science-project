"""
Nationality Validator V3.1 (Hybrid Metadata Strategy)

Automated flagging of Indonesian vs Foreign/Corporate records.
Prioritizes Spotify Genres for lightning-fast accuracy, falling back to Wikipedia search for edge cases.
"""

import os
import sys
import requests
import time
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.database.operations import get_unflagged_nationality_artists_sync, update_nationality_sync

class NationalityValidator:
    def __init__(self):
        self.headers = {
            "User-Agent": "NationalityValidator/3.1 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        self.report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../docs/validation/ARTIST_VALIDATION_REPORT.md'))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        
        # TIER 1: Spotify Indonesian Genres
        self.SPOTIFY_INDO_GENRES = [
            "indonesian", "indo", "jawa", "dangdut", "koplo", "sunda", 
            "minang", "batak", "maluku", "timur", "funkot", "hipdut",
            "sholawat"
        ]
        
        # TIER 2: Spotify Foreign/Corporate Genres
        self.SPOTIFY_FOREIGN_GENRES = [
            "k-pop", "k-ballad", "k-rock", "mollywood", "brazilian", 
            "norwegian", "children's music", "white noise", "lullaby"
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
        
        for indo in self.SPOTIFY_INDO_GENRES:
            if indo in genre_str or f"indo " in genre_str:
                return "INDONESIAN", f"Spotify Genre Match: {indo}"
                
        for foreign in self.SPOTIFY_FOREIGN_GENRES:
            if foreign in genre_str:
                return "FOREIGN", f"Spotify Foreign Genre: {foreign}"
                
        return None, None

    def search_wikipedia_title(self, artist_name):
        """Uses the Search API to find the closest actual page title."""
        time.sleep(0.5)
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
        page_title = self.search_wikipedia_title(artist_name)
        if not page_title:
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

            for marker in self.WIKI_FOREIGN_MARKERS:
                if marker in full_text:
                    return "FOREIGN", f"Wiki strong foreign marker: {marker}"

            has_green = any(green in full_text for green in self.WIKI_GREEN)
            if has_green:
                return "INDONESIAN", "Wiki Indonesian context confirmed."

            return "UNCERTAIN", "Wiki ambiguous."

        except Exception as e:
            return "ERROR", str(e)

    def run_validation(self):
        print("\n" + "="*50)
        print("      NATIONALITY VALIDATOR V3.1 (HYBRID)")
        print("==================================================\n")
        
        artists = get_unflagged_nationality_artists_sync()

        print(f"Auditing {len(artists)} unflagged records...\n")
        
        indo, foreign, uncertain = 0, 0, 0
        spotify_hits, wiki_hits = 0, 0
        results_log = []
        
        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            genres = artist["genre"]
            
            status, reason = self.validate_via_spotify(genres)
            
            if status:
                spotify_hits += 1
            else:
                status, reason = self.check_wikipedia(name)
                wiki_hits += 1
                time.sleep(0.1)
            
            if status == "INDONESIAN":
                print(f"🇮🇩 [INDO ] {name:<25} | {reason}")
                update_nationality_sync(db_id, True)
                indo += 1
                results_log.append({"name": name, "status": "✅ INDO", "reason": reason})
            elif status == "FOREIGN":
                print(f"🌎 [NON-ID] {name:<25} | {reason}")
                update_nationality_sync(db_id, False)
                foreign += 1
                results_log.append({"name": name, "status": "🌎 FOREIGN", "reason": reason})
            else:
                print(f"❓ [UNCRTN] {name:<25} | {reason}")
                uncertain += 1
                results_log.append({"name": name, "status": "❓ UNCERTAIN", "reason": reason})
                
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

        self.generate_markdown_report(len(artists), indo, foreign, uncertain, spotify_hits, wiki_hits, results_log)

    def generate_markdown_report(self, total, indo, foreign, uncertain, spotify_hits, wiki_hits, log):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        content = f"""# Artist Nationality Validation Report
Generated on: `{timestamp}`

## 📊 Summary Statistics
| Metric | Count |
| :--- | :--- |
| **Total Audited** | {total} |
| **Valid Indonesian** | {indo} |
| **Foreign / Noise** | {foreign} |
| **Uncertain** | {uncertain} |

## 🛠️ Pipeline Performance
- **Fast-Tracked via Spotify Genres**: {spotify_hits}
- **Fallbacks via Wikipedia Scan**: {wiki_hits}

## 📝 Detailed Audit Log
| Artist Name | Status | Reason / Marker |
| :--- | :--- | :--- |
"""
        for entry in log:
            content += f"| {entry['name']} | {entry['status']} | {entry['reason']} |\n"

        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[REPORT] Detailed validation results saved to: {self.report_path}")

if __name__ == "__main__":
    validator = NationalityValidator()
    validator.run_validation()
