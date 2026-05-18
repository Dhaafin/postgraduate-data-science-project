"""
Unified Artist Discovery Module

Provides tools to discover and ingest new raw artists into the database.
Currently supports fetching artists from Viberate charts.
"""

import requests
from bs4 import BeautifulSoup

VIBERATE_BASE_URL = "https://www.viberate.com/music-charts/top-artists-from-indonesia-"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_viberate_artists(page_indices=[1]):
    """
    Fetch and extract unique artist names from multiple Viberate chart pages.
    """
    all_artists = []
    seen = set()

    for idx in page_indices:
        url = f"{VIBERATE_BASE_URL}{idx}/"
        print(f"Fetching: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            page_count = 0
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"]
                if href.startswith("/artist/"):
                    name = anchor.get_text(strip=True)
                    if name and name not in seen:
                        seen.add(name)
                        all_artists.append(name)
                        page_count += 1
            print(f"  -> Extracted {page_count} new artists from page {idx}.")
        except Exception as e:
            print(f"Error fetching Viberate page {idx}: {e}")
            
    return all_artists

if __name__ == "__main__":
    artists = fetch_viberate_artists(page_indices=[0, 1])
    print(f"\nTotal unique artists collected: {len(artists)}")
