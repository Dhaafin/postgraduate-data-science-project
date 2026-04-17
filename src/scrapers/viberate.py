"""
Viberate Top Artists Scraper
"""

import sys
import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://www.viberate.com/music-charts/top-artists-from-indonesia-0/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_viberate_artists(url=TARGET_URL):
    """
    Fetch and extract unique artist names from Viberate chart page.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        seen = set()
        artists = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.startswith("/artist/"):
                name = anchor.get_text(strip=True)
                if name and name not in seen:
                    seen.add(name)
                    artists.append(name)
        return artists
    except Exception as e:
        print(f"Error fetching Viberate data: {e}")
        return []

if __name__ == "__main__":
    artists = fetch_viberate_artists()
    for rank, name in enumerate(artists, start=1):
        print(f"{rank}. {name}")
