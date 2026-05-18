"""
MusicBrainz Geo-Enrichment Pipeline

Queries MusicBrainz for artist origins and types.
Generates reports for manual review if origin is missing or foreign-born.
Delegates all database updates to operations.py.
"""

import os
import sys
import time
import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.database.operations import get_artists_without_origin_sync, update_artist_type_sync, update_origin_city_sync
from src.utils.geo_constants import is_indonesian_location

class MusicBrainzEnrichment:
    def __init__(self):
        self.headers = {
            "User-Agent": "IndoMusicSpatialAnalytics/1.1 ( data.research@localhost )"
        }
        self.url = "https://musicbrainz.org/ws/2/artist/"
        self.foreign_born = []
        self.manual_queue = []
        self.successful_updates = 0

    def query_musicbrainz(self, artist_name):
        params = {
            "query": f'"{artist_name}"', 
            "fmt": "json"
        }
        try:
            response = requests.get(self.url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if not data.get("artists"):
                return None
            artist = data["artists"][0]
            if artist.get("score", 0) < 80:
                return None
            return {
                "name": artist.get("name"),
                "score": artist.get("score"),
                "type": artist.get("type", "Unknown"),
                "country": artist.get("country", "Unknown"),
                "begin_area": artist.get("begin-area", {}).get("name", None)
            }
        except Exception as e:
            print(f"  [!] Network Error for {artist_name}: {e}")
            return None

    def generate_reports(self):
        docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../docs/musicbrainz'))
        os.makedirs(docs_dir, exist_ok=True)
        
        foreign_path = os.path.join(docs_dir, "FOREIGN_BORN_REPORT.md")
        with open(foreign_path, "w", encoding="utf-8") as f:
            f.write("# Foreign-Born Artist Report\n\n")
            f.write("Artists successfully matched on MusicBrainz, but flagged as non-Indonesian.\n\n")
            f.write("| Database ID | Artist Name | MB Country | Begin Area |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in self.foreign_born:
                f.write(f"| {item['id']} | {item['name']} | {item['country']} | {item['begin_area']} |\n")
                
        manual_path = os.path.join(docs_dir, "MANUAL_ORIGIN_QUEUE.md")
        with open(manual_path, "w", encoding="utf-8") as f:
            f.write("# Manual Origin Queue\n\n")
            f.write("Artists that MusicBrainz could not identify with high confidence.\n\n")
            f.write("| Database ID | Artist Name | Manual Origin City | Manual Artist Type |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in self.manual_queue:
                f.write(f"| {item['id']} | {item['name']} |  |  |\n")

        print(f"\n[+] Generated {foreign_path}")
        print(f"[+] Generated {manual_path}")

    def run(self):
        print("\n" + "="*60)
        print(" MUSICBRAINZ GEO-ENRICHMENT PIPELINE")
        print("="*60)
        
        artists = get_artists_without_origin_sync()
        print(f"Targeting {len(artists)} records without origin data...\n")
        
        for idx, artist in enumerate(artists, start=1):
            db_id = artist["id"]
            name = artist["name"]
            
            print(f"\rProgress: [{idx}/{len(artists)}] 🔍 {name:<25}", end="", flush=True)
            
            mb_data = self.query_musicbrainz(name)
            
            if not mb_data:
                self.manual_queue.append({"id": db_id, "name": name})
            else:
                artist_type = mb_data["type"]
                country = mb_data["country"]
                begin_area = mb_data["begin_area"]
                
                if country != 'ID' and not is_indonesian_location(begin_area):
                    self.foreign_born.append({
                        "id": db_id, 
                        "name": name, 
                        "country": country, 
                        "begin_area": begin_area or "Unknown"
                    })
                
                update_artist_type_sync(db_id, artist_type)
                if begin_area:
                    update_origin_city_sync(db_id, begin_area)
                self.successful_updates += 1

            time.sleep(2.0)
            
        print("\r" + " "*60 + "\r", end="")
        print("="*60)
        print(" ENRICHMENT COMPLETE")
        print(f"Successful Updates : {self.successful_updates}")
        print(f"Foreign Born Flags : {len(self.foreign_born)}")
        print(f"Manual Queue Sent  : {len(self.manual_queue)}")
        self.generate_reports()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    MusicBrainzEnrichment().run()
