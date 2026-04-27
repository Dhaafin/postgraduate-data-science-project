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
        
        # We try standard Wikipedia disambiguation titles
        titles_to_try = [
            f"{artist_name} (penyanyi)",
            f"{artist_name} (grup musik)",
            f"{artist_name} (musisi)",
            artist_name
        ]
        
        for title in titles_to_try:
            params = {
                "action": "query",
                "titles": title,
                "format": "json",
                "redirects": "true"
            }
            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                data = response.json()
                
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    # If page_id > 0, the page exists.
                    if int(page_id) > 0 and "missing" not in page_info:
                        return page_info["title"]
            except Exception as e:
                print(f"Error checking title {title}: {e}")
                
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
                if th:
                    th_text = th.text.lower().strip()
                    td = row.find("td")
                    if td:
                        # Clean out references
                        for sup in td.find_all("sup"):
                            sup.decompose()
                            
                        # Replace <br> with commas so we can split easily
                        for br in td.find_all("br"):
                            br.replace_with(", ")
                            
                        # STRICT MATCHING to prevent catching "nama lahir"
                        if th_text in ["asal", "kota asal"]:
                            origin = td.get_text(separator=", ", strip=True)
                            return self.parse_origin_string(origin, is_birthplace=False)
                        elif th_text in ["lahir", "tempat lahir"]:
                            origin = td.get_text(separator=", ", strip=True)
                            return self.parse_origin_string(origin, is_birthplace=True)
                            
        except Exception as e:
            print(f"Error extracting infobox for {page_title}: {e}")
            
        return None, None
        
    def parse_origin_string(self, origin_string, is_birthplace=False):
        """
        Splits string into City and Province.
        """
        # Remove parentheticals like (umur 38)
        origin_string = re.sub(r'\(.*?\)', '', str(origin_string))
        
        parts = [p.strip() for p in origin_string.split(",")]
        
        cleaned_parts = []
        for p in parts:
            # Ignore purely numeric/date parts (e.g. 31 Desember 1966)
            if re.search(r'\d{4}', p): 
                continue
            # Ignore country names
            if p and p.lower() not in ["indonesia", "hindia belanda"]:
                cleaned_parts.append(p)
                
        KNOWN_PROVINCES = {
            "aceh", "sumatra utara", "sumatera utara", "sumatra barat", "sumatera barat",
            "riau", "jambi", "sumatra selatan", "sumatera selatan", "bengkulu", "lampung",
            "kepulauan bangka belitung", "bangka belitung", "kepulauan riau", "dki jakarta", "jakarta",
            "jawa barat", "jawa tengah", "daerah istimewa yogyakarta", "di yogyakarta", "yogyakarta", 
            "jawa timur", "banten", "bali", "nusa tenggara barat", "ntb", "nusa tenggara timur", "ntt",
            "kalimantan barat", "kalimantan tengah", "kalimantan selatan", "kalimantan timur",
            "kalimantan utara", "sulawesi utara", "sulawesi tengah", "sulawesi selatan",
            "sulawesi tenggara", "gorontalo", "sulawesi barat", "maluku", "maluku utara",
            "papua barat", "papua", "papua selatan", "papua tengah", "papua pegunungan", "papua barat daya"
        }

        temp_cleaned = []
        for p in cleaned_parts:
            # If a part has 3 or more words and is not a known 3+ word province, it's highly likely to be a person's name
            if len(p.split()) >= 3 and p.lower() not in KNOWN_PROVINCES:
                continue
            temp_cleaned.append(p)
        cleaned_parts = temp_cleaned
                
        if not cleaned_parts:
            return None, None
            
        city, province = None, None
        
        if len(cleaned_parts) >= 2:
            if cleaned_parts[-1].lower() in KNOWN_PROVINCES:
                province = cleaned_parts[-1]
                city = cleaned_parts[-2]
            else:
                city = cleaned_parts[-2]
                province = cleaned_parts[-1]
        elif len(cleaned_parts) == 1:
            val = cleaned_parts[0]
            if val.lower() in KNOWN_PROVINCES:
                province = val
                city = val
            else:
                city = val
        
        # Edge Cases
        if city and "jakarta" in city.lower():
            province = "DKI Jakarta"
            city = "Jakarta"
        if province and "jakarta" in province.lower():
            province = "DKI Jakarta"
            if not city:
                city = "Jakarta"
            
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
