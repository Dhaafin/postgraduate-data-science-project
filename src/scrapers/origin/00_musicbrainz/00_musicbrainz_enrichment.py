import os
import sys
import time
import requests
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from src.database.connection import sync_engine
from src.utils.geo_constants import is_indonesian_location

class MusicBrainzEnrichment:
    def __init__(self):
        self.headers = {
            "User-Agent": "IndoMusicSpatialAnalytics/1.0 ( data.research@localhost )"
        }
        self.url = "https://musicbrainz.org/ws/2/artist/"
        self.foreign_born = []
        self.manual_queue = []
        self.successful_updates = 0

    def query_musicbrainz(self, artist_name):
        """Query the MusicBrainz API without country restriction to catch foreign-born artists."""
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
                
            # Get the top match
            artist = data["artists"][0]
            
            # Confidence threshold
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
        """Write the in-memory queues to Markdown reports."""
        docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../docs/musicbrainz'))
        os.makedirs(docs_dir, exist_ok=True)
        
        # 1. Foreign Born Report
        foreign_path = os.path.join(docs_dir, "FOREIGN_BORN_REPORT.md")
        with open(foreign_path, "w", encoding="utf-8") as f:
            f.write("# Foreign-Born Artist Report\n\n")
            f.write("Artists successfully matched on MusicBrainz, but flagged as non-Indonesian (either by country code or begin-area).\n\n")
            f.write("| Database ID | Artist Name | MB Country | Begin Area |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in self.foreign_born:
                f.write(f"| {item['id']} | {item['name']} | {item['country']} | {item['begin_area']} |\n")
                
        # 2. Manual Origin Queue
        manual_path = os.path.join(docs_dir, "MANUAL_ORIGIN_QUEUE.md")
        with open(manual_path, "w", encoding="utf-8") as f:
            f.write("# Manual Origin Queue\n\n")
            f.write("Artists that MusicBrainz could not identify with high confidence. Require manual research.\n\n")
            f.write("| Database ID | Artist Name | Manual Origin City | Manual Artist Type (Solo/Band) |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in self.manual_queue:
                f.write(f"| {item['id']} | {item['name']} |  |  |\n")

        print(f"\n[+] Generated {foreign_path}")
        print(f"[+] Generated {manual_path}")

    def run(self):
        print("\n" + "="*60)
        print(" MUSICBRAINZ GEO-ENRICHMENT PIPELINE (M4)")
        print("="*60)
        
        if not sync_engine:
            print("Database connection failed.")
            return

        with sync_engine.begin() as conn:
            query = text("SELECT id, artist_name FROM music_data WHERE is_indonesian = TRUE AND origin_city IS NULL")
            artists = [{"id": row[0], "name": row[1]} for row in conn.execute(query).fetchall()]

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
                
                # Report if Foreign Born (and not in an Indonesian city)
                if country != 'ID' and not is_indonesian_location(begin_area):
                    self.foreign_born.append({
                        "id": db_id, 
                        "name": name, 
                        "country": country, 
                        "begin_area": begin_area or "Unknown"
                    })
                
                # We still update the database even if foreign born, because they are structurally part of our dataset
                # The spatial analysis can filter them out later if needed
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE music_data SET artist_type = :type, origin_city = :city WHERE id = :id"),
                        {"type": artist_type, "city": begin_area, "id": db_id}
                    )
                self.successful_updates += 1

            # Strict Rate Limiting
            time.sleep(2.0)
            
        print("\r" + " "*60 + "\r", end="") # Clear progress line
        
        print("="*60)
        print(" ENRICHMENT COMPLETE")
        print("="*60)
        print(f"Total Processed    : {len(artists)}")
        print(f"Successful Updates : {self.successful_updates}")
        print(f"Foreign Born Flags : {len(self.foreign_born)}")
        print(f"Manual Queue Sent  : {len(self.manual_queue)}")
        
        self.generate_reports()
        print("="*60)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    MusicBrainzEnrichment().run()
