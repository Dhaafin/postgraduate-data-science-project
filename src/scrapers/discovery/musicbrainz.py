"""
MusicBrainz Discovery Module (Pre-Validated Deep Search)

Discovers artists by leveraging MusicBrainz's Lucene query syntax (e.g. country:ID).
This bypasses downstream nationality validation and instantly seeds origin data.
"""

import requests
import time
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.database.operations import insert_musicbrainz_seed_sync

class MusicBrainzDiscovery:
    def __init__(self):
        self.base_url = "https://musicbrainz.org/ws/2/artist/"
        self.headers = {
            "User-Agent": "SpatialAnalytics/1.0 (Research Project - contact via github)",
            "Accept": "application/json"
        }
        self.rate_limit_delay = 1.2 # MusicBrainz allows 1 req/sec. Adding buffer.

    def run_discovery(self, query="country:ID", max_pages=5, dry_run=False):
        """
        Runs the discovery process up to max_pages (100 results per page).
        Default query finds all artists with country explicitly set to Indonesia.
        """
        mode = "DRY RUN (Preview Only)" if dry_run else "LIVE (Database Ingestion)"
        print("\n" + "="*60)
        print(" MUSICBRAINZ DEEP DISCOVERY PIPELINE")
        print(f" Query: '{query}' | Mode: {mode}")
        print("="*60)

        offset = 0
        limit = 100
        total_discovered = 0
        total_inserted = 0
        preview_list = []
        
        for page in range(1, max_pages + 1):
            print(f"\n[Page {page}/{max_pages}] Fetching offset {offset}...")
            
            params = {
                "query": query,
                "fmt": "json",
                "limit": limit,
                "offset": offset
            }
            
            try:
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=15)
                
                if response.status_code == 503:
                    print(" [!] Rate limited. Backing off for 5 seconds...")
                    time.sleep(5)
                    response = requests.get(self.base_url, params=params, headers=self.headers, timeout=15)
                    
                response.raise_for_status()
                data = response.json()
                
                artists = data.get("artists", [])
                if not artists:
                    print(" -> No more artists found. Ending pagination.")
                    break
                    
                print(f" -> Found {len(artists)} records in this batch.")
                
                for a in artists:
                    name = a.get("name")
                    if not name:
                        continue
                        
                    raw_type = a.get("type", "Unknown")
                    if raw_type == "Person":
                        artist_type = "Solo"
                    elif raw_type == "Group":
                        artist_type = "Band"
                    else:
                        artist_type = None
                        
                    origin_city = None
                    if "begin-area" in a and a["begin-area"]:
                        origin_city = a["begin-area"].get("name")
                        
                    total_discovered += 1
                    
                    if dry_run:
                        preview_list.append({"name": name, "type": artist_type, "city": origin_city})
                        print(f"   [PREVIEW] {name:<25} | Type: {str(artist_type):<5} | City: {str(origin_city)}")
                    else:
                        db_id = insert_musicbrainz_seed_sync(name, artist_type, origin_city)
                        if db_id:
                            total_inserted += 1
                            print(f"   [+] INSERTED: {name:<25} | Type: {str(artist_type):<5} | City: {str(origin_city)}")
                        
                offset += limit
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f" [!] Error during fetching: {e}")
                break

        print("\n" + "="*60)
        print(" MUSICBRAINZ DISCOVERY COMPLETE")
        print(f" Total Discovered: {total_discovered}")
        if not dry_run:
            print(f" Total New Seeds Inserted: {total_inserted}")
        print("="*60)
        
        return preview_list if dry_run else []

if __name__ == "__main__":
    discovery = MusicBrainzDiscovery()
    # Pull 200 records to start
    discovery.run_discovery(query="country:ID", max_pages=2)
