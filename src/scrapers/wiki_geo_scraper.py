import asyncio
import requests
import json
import re
from bs4 import BeautifulSoup

class WikiGeoScraper:
    """
    A scraper that hits the public MediaWiki API to find Indonesian artist Wikipedia pages
    and extracts their 'origin_city' and 'origin_province' from the infobox.
    Runs synchronously via requests, wrapped in asyncio.to_thread for non-blocking execution.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "MusicDataScraper/1.0 (Research Project; contact via github)"
        }
        
    def _search_artist_sync(self, artist_name):
        url = "https://id.wikipedia.org/w/api.php"
        # Try with disambiguation first (e.g. "Tulus (musisi)")
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{artist_name} (musisi)",
            "format": "json"
        }
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            if data.get("query", {}).get("search"):
                return data["query"]["search"][0]["title"]
                
            # Fallback: Plain Name
            params["srsearch"] = artist_name
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            if data.get("query", {}).get("search"):
                return data["query"]["search"][0]["title"]
        except Exception as e:
            print(f"Error searching Wikipedia for {artist_name}: {e}")
            
        return None

    def _get_infobox_data_sync(self, page_title):
        url = "https://id.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "text",
            "format": "json",
            "redirects": "true"
        }
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if "parse" not in data:
                return None, None
                
            html_content = data["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, "html.parser")
            
            infobox = soup.find("table", class_="infobox")
            if not infobox:
                return None, None
                
            origin = None
            for row in infobox.find_all("tr"):
                th = row.find("th")
                if th and any(keyword in th.text.lower() for keyword in ["asal", "tempat lahir", "lahir"]):
                    td = row.find("td")
                    if td:
                        # Clean out references like [1]
                        for sup in td.find_all("sup"):
                            sup.decompose()
                        origin = td.get_text(separator=", ", strip=True)
                        break
                        
            if origin:
                return self.parse_origin_string(origin)
        except Exception as e:
            print(f"Error extracting infobox for {page_title}: {e}")
            
        return None, None
        
    def parse_origin_string(self, origin_string):
        """
        Splits 'City, Province, Country' into just City and Province.
        """
        parts = [p.strip() for p in str(origin_string).split(",")]
        
        cleaned_parts = []
        for p in parts:
            # Common Wikipedia debris cleanup (remove exact birthdates if present in 'Tempat lahir' field)
            p = re.sub(r'^[0-9]+\s+[A-Za-z]+\s+[0-9]+', '', p).strip()
            # Ignore country names as we already know they are Indonesian
            if p and p.lower() not in ["indonesia", "hindia belanda"]:
                cleaned_parts.append(p)
                
        if not cleaned_parts:
            return None, None
            
        city = cleaned_parts[0]
        province = cleaned_parts[1] if len(cleaned_parts) > 1 else None
        
        # Hardcode the Jakarta Edge Case
        if "jakarta" in city.lower():
            province = "DKI Jakarta"
            
        return city, province

    async def get_artist_geo(self, artist_name):
        """
        Public async entry point.
        """
        title = await asyncio.to_thread(self._search_artist_sync, artist_name)
        if not title:
            return {"origin_city": None, "origin_province": None, "source": "Not Found", "matched_title": None}
            
        city, province = await asyncio.to_thread(self._get_infobox_data_sync, title)
        return {
            "origin_city": city,
            "origin_province": province,
            "source": "Wikipedia Infobox",
            "matched_title": title
        }

if __name__ == "__main__":
    # Smoke Test Loop
    async def test():
        scraper = WikiGeoScraper()
        test_artists = ["Tulus", "Hindia", "Didi Kempot", "Superman Is Dead"]
        
        print(f"{'Artist':<20} | {'City':<20} | {'Province':<20} | {'Wiki Page'}")
        print("-" * 80)
        for artist in test_artists:
            res = await scraper.get_artist_geo(artist)
            city = str(res['origin_city'])[:20]
            prov = str(res['origin_province'])[:20]
            title = str(res['matched_title'])
            print(f"{artist:<20} | {city:<20} | {prov:<20} | {title}")

    asyncio.run(test())
