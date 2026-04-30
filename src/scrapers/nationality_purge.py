"""
Nationality Purge Batch Auditor
Automated cleanup of non-Indonesian and Corporate records using Wikipedia NLP.
"""

import os
import sys
import requests
import re
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connection import sync_engine, delete_artist_sync

class NationalityPurge:
    def __init__(self):
        self.headers = {
            "User-Agent": "NationalityPurgeAuditor/1.0 (Research Project; contact via github)"
        }
        self.api_url = "https://id.wikipedia.org/w/api.php"
        
        # Keywords that confirm Indonesian origin
        self.GREEN_KEYWORDS = [
            "indonesia", "jakarta", "bandung", "surabaya", "medan", "semarang", 
            "makassar", "palembang", "yogyakarta", "denpasar", "malang", "bali",
            "jawa", "sumatera", "kalimantan", "sulawesi", "papua", "ntb", "ntt",
            "grup musik indonesia", "penyanyi indonesia", "musisi indonesia"
        ]
        
        # Keywords that trigger immediate purge (Non-Indonesian or Corporate)
        self.RED_KEYWORDS = [
            "amerika serikat", "korea selatan", "inggris", "britania raya", 
            "kanada", "jepang", "australia", "perancis", "jerman",
            "saluran youtube", "merek", "perusahaan", "karakter fiksi", "acara televisi"
        ]

    def check_wikipedia(self, artist_name):
        """Searches Wikipedia and analyzes the first paragraph."""
        params = {
            "action": "parse",
            "page": artist_name,
            "prop": "text",
            "format": "json",
            "redirects": "true"
        }
        
        try:
            # First try standard search
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if "parse" not in data:
                # Try with (penyanyi) suffix if first attempt fails
                params["page"] = f"{artist_name} (penyanyi)"
                response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
                data = response.json()
                
            if "parse" not in data:
                return "NOT_FOUND", None

            html_content = data["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract first paragraph
            first_p = soup.find("p")
            if not first_p:
                return "EMPTY_CONTENT", None
            
            intro_text = first_p.get_text().lower()
            
            # Logic 1: Immediate Red Flag (Corporate or International)
            for red in self.RED_KEYWORDS:
                if red in intro_text:
                    # Double check if 'indonesia' is also there (e.g. "Inggris yang berkarir di Indonesia")
                    if "indonesia" not in intro_text:
                        return "PURGE", f"Red flag found: {red}"
            
            # Logic 2: Green Flag Check
            has_green = any(green in intro_text for green in self.GREEN_KEYWORDS)
            if has_green:
                return "KEEP", "Indonesian keywords found."
            
            # Logic 3: Fallback - if it mentions other countries but not Indonesia
            other_countries = ["amerika", "korea", "inggris", "kanada", "jepang"]
            if any(country in intro_text for country in other_countries) and "indonesia" not in intro_text:
                return "PURGE", "Identified as foreign without Indonesian ties."

            return "UNCERTAIN", "No strong signals found."

        except Exception as e:
            return "ERROR", str(e)

    def run_purge(self):
        print("\n" + "="*50)
        print("      NATIONALITY PURGE BATCH AUDITOR")
        print("="*50 + "\n")
        
        if not sync_engine:
            print("Error: Database engine not initialized.")
            return

        with sync_engine.begin() as conn:
            result = conn.execute(text("SELECT id, artist_name FROM music_data"))
            artists = [{"id": row[0], "name": row[1]} for row in result.fetchall()]

        print(f"Total artists to audit: {len(artists)}\n")
        
        kept = 0
        purged = 0
        uncertain = 0
        
        for artist in artists:
            name = artist["name"]
            db_id = artist["id"]
            
            status, reason = self.check_wikipedia(name)
            
            if status == "PURGE":
                print(f"❌ [PURGE] {name:<30} | {reason}")
                delete_artist_sync(db_id)
                purged += 1
            elif status == "KEEP":
                print(f"✅ [KEEP ] {name:<30} | {reason}")
                kept += 1
            elif status == "NOT_FOUND":
                print(f"❓ [SKIP ] {name:<30} | Wikipedia page not found.")
                uncertain += 1
            else:
                print(f"⚠️ [CHECK] {name:<30} | {reason}")
                uncertain += 1
        
        print("\n" + "="*50)
        print(f"AUDIT COMPLETE")
        print(f"  - Kept:      {kept}")
        print(f"  - Purged:    {purged}")
        print(f"  - Uncertain: {uncertain}")
        print("="*50)

if __name__ == "__main__":
    auditor = NationalityPurge()
    auditor.run_purge()
