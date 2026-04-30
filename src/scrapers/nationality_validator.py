"""
Nationality Validator (Enhanced)
Automated flagging of Indonesian vs Foreign/Corporate records using Wikipedia NLP.
Improved with deeper keyword scanning and error handling.
"""

import os
import sys
import requests
import re
import time
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connection import sync_engine, update_nationality_sync

class NationalityValidator:
    def __init__(self):
        self.headers = {
            "User-Agent": "NationalityValidator/2.0 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        
        # Comprehensive Indonesian Identifiers
        self.GREEN_KEYWORDS = [
            "indonesia", "jakarta", "bandung", "surabaya", "medan", "semarang", 
            "makassar", "palembang", "yogyakarta", "denpasar", "malang", "bali",
            "jawa", "sumatera", "kalimantan", "sulawesi", "papua", "ntb", "ntt",
            "grup musik indonesia", "penyanyi indonesia", "musisi indonesia",
            "dangdut", "koplo", "campursari", "pop indonesia", "rock indonesia",
            "aceh", "lampung", "riau", "banten", "jawa barat", "jawa tengah", "jawa timur",
            "warga negara indonesia", "keturunan indonesia", "asal indonesia"
        ]
        
        # Strong Foreign Identifiers (to avoid false positives like Astrid)
        # We look for "berkebangsaan [Country]" or "asal [Country]" specifically
        self.FOREIGN_MARKERS = [
            "berkebangsaan amerika serikat", "berkebangsaan korea selatan", "berkebangsaan inggris",
            "berkebangsaan britania raya", "berkebangsaan kanada", "berkebangsaan jepang",
            "penyanyi amerika serikat", "penyanyi korea selatan", "penyanyi inggris",
            "asal amerika serikat", "asal korea selatan", "asal inggris"
        ]
        
        # Corporate Identifiers
        self.CORPORATE_KEYWORDS = [
            "saluran youtube", "merek", "perusahaan", "karakter fiksi", 
            "acara televisi", "label rekaman", "produk", "aplikasi"
        ]

    def check_wikipedia(self, artist_name):
        """Searches Wikipedia and analyzes the first few paragraphs for deep context."""
        search_queries = [
            artist_name,
            f"{artist_name} (penyanyi)",
            f"{artist_name} (grup musik)",
            f"{artist_name} (musisi)"
        ]
        
        best_intro = ""
        
        for query in search_queries:
            params = {
                "action": "parse",
                "page": query,
                "prop": "text",
                "format": "json",
                "redirects": "true"
            }
            
            try:
                response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
                
                # Robust JSON handling
                if response.status_code != 200:
                    continue
                
                try:
                    data = response.json()
                except ValueError:
                    continue # Not JSON
                    
                if "parse" not in data:
                    continue

                html_content = data["parse"]["text"]["*"]
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Get the first 2 paragraphs for more context
                paragraphs = soup.find_all("p")
                full_text = " ".join([p.get_text().lower() for p in paragraphs[:2]])
                
                if len(full_text) > len(best_intro):
                    best_intro = full_text
                
                # If we found a good match, no need to try other search queries
                if "indonesia" in full_text:
                    break
                    
            except Exception:
                continue

        if not best_intro:
            return "NOT_FOUND", "No Wikipedia page found."

        # Logic 1: Corporate Check (High Priority)
        for corp in self.CORPORATE_KEYWORDS:
            if corp in best_intro:
                return "FOREIGN", f"Corporate/IP detected: {corp}"

        # Logic 2: Strong Foreign Marker Check
        for marker in self.FOREIGN_MARKERS:
            if marker in best_intro:
                # If it mentions Indonesia in a "collaboration" context, keep it uncertain
                if "kolaborasi dengan indonesia" not in best_intro:
                    return "FOREIGN", f"Strong foreign marker: {marker}"

        # Logic 3: Green Flag Check (Deep Scan)
        has_green = any(green in best_intro for green in self.GREEN_KEYWORDS)
        if has_green:
            return "INDONESIAN", "Indonesian context confirmed."
        
        # Logic 4: Weak Foreign Check (only if no green flags at all)
        weak_foreign = ["amerika serikat", "korea selatan", "inggris", "jepang", "kanada"]
        if any(f in best_intro for f in weak_foreign) and "indonesia" not in best_intro:
            return "FOREIGN", "Likely foreign (no Indonesian ties found)."

        return "UNCERTAIN", "Insufficient data for classification."

    def run_validation(self):
        print("\n" + "="*50)
        print("      NATIONALITY VALIDATOR V2.0")
        print("==================================================\n")
        
        if not sync_engine:
            print("Error: Database engine not initialized.")
            return

        with sync_engine.begin() as conn:
            result = conn.execute(text("SELECT id, artist_name FROM music_data WHERE is_indonesian IS NULL LIMIT 100"))
            artists = [{"id": row[0], "name": row[1]} for row in result.fetchall()]

        print(f"Auditing {len(artists)} unflagged records...\n")
        
        indo = 0
        foreign = 0
        uncertain = 0
        
        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            
            status, reason = self.check_wikipedia(name)
            
            if status == "INDONESIAN":
                print(f"🇮🇩 [INDO ] {name:<30} | {reason}")
                update_nationality_sync(db_id, True)
                indo += 1
            elif status == "FOREIGN":
                print(f"🌎 [NON-ID] {name:<30} | {reason}")
                update_nationality_sync(db_id, False)
                foreign += 1
            else:
                print(f"❓ [UNCRTN] {name:<30} | {reason}")
                # Don't update the flag, leave it NULL for manual review or geo-processing
                uncertain += 1
            
            # Rate limiting safety
            time.sleep(0.2)
        
        print("\n" + "="*50)
        print(f"VALIDATION SUMMARY")
        print(f"  - Indonesian: {indo}")
        print(f"  - Non-Indo:   {foreign}")
        print(f"  - Uncertain:  {uncertain}")
        print("="*50)

if __name__ == "__main__":
    validator = NationalityValidator()
    validator.run_validation()
