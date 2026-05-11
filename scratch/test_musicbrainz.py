import os
import sys
import time
import requests
from sqlalchemy import text

# Add project root to path so we can import the db connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def fetch_test_artists(limit=50):
    if not sync_engine:
        print("Database connection failed.")
        return []
        
    with sync_engine.begin() as conn:
        # Fetch artists that are flagged as indonesian
        query = text("SELECT id, artist_name FROM music_data WHERE is_indonesian = TRUE LIMIT :limit")
        result = conn.execute(query, {"limit": limit}).fetchall()
        return [{"id": row[0], "name": row[1]} for row in result]

def query_musicbrainz(artist_name):
    url = "https://musicbrainz.org/ws/2/artist/"
    params = {
        "query": f'"{artist_name}" AND country:ID',
        "fmt": "json"
    }
    headers = {
        "User-Agent": "IndoMusicSpatialAnalytics/1.0 ( data.research@localhost )"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("artists"):
            return None
            
        artist = data["artists"][0]
        return {
            "name_mb": artist.get("name"),
            "score": artist.get("score"),
            "type": artist.get("type", "Unknown"),
            "begin_area": artist.get("begin-area", {}).get("name", "N/A")
        }
    except Exception as e:
        print(f"  [!] Error querying {artist_name}: {e}")
        return None

def run_test():
    artists = fetch_test_artists(50)
    if not artists:
        return
        
    hits = 0
    misses = 0
    results_summary = []
    
    print("="*60)
    print(" MUSICBRAINZ API SCALABILITY TEST (50 RECORDS)")
    print("="*60)
    print("Please wait, querying 50 artists (approx 60 seconds)...")
    
    for idx, artist in enumerate(artists, start=1):
        name = artist["name"]
        print(f"\rProgress: [{idx}/50] ...", end="", flush=True)
        mb_data = query_musicbrainz(name)
        
        if mb_data:
            hits += 1
            area = mb_data['begin_area']
            results_summary.append((name, mb_data['type'], area))
        else:
            misses += 1
            
        time.sleep(1.2) # Strict 1 request/sec limit
        
    print("\r" + " "*30 + "\r", end="") # Clear the progress line
        
    print("\n" + "="*60)
    print(" TEST SUMMARY: MUSICBRAINZ 50-RECORD SPIKE")
    print("="*60)
    print(f"Total Queried : {len(artists)}")
    print(f"Total Hits    : {hits} ({(hits/len(artists))*100:.1f}%)")
    print(f"Total Misses  : {misses} ({(misses/len(artists))*100:.1f}%)")
    print("-" * 60)
    print(f"{'Artist':<25} | {'Type':<8} | {'Origin'}")
    print("-" * 60)
    for res in results_summary:
        print(f"{res[0]:<25} | {res[1]:<8} | {res[2]}")
    print("="*60)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    run_test()
