import requests
from bs4 import BeautifulSoup
import time
import re

def experiment_wikipedia(artist_name):
    """Experiment: Search Wikipedia (id) and try to extract birthplace from Infobox."""
    print(f"Testing Wikipedia for: {artist_name}")
    api_url = "https://id.wikipedia.org/w/api.php"
    headers = {"User-Agent": "IndoMusicResearch/1.0 (contact: your-email@example.com)"}
    
    # 1. Search for page
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": artist_name,
        "format": "json"
    }
    try:
        r = requests.get(api_url, params=search_params, headers=headers, timeout=10)
        data = r.json()
        if not data.get("query", {}).get("search"):
            return "No page found"
        
        title = data["query"]["search"][0]["title"]
        print(f"  Found page: {title}")
        
        # 2. Get Infobox HTML
        parse_params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json"
        }
        r = requests.get(api_url, params=parse_params, headers=headers, timeout=10)
        html = r.json()["parse"]["text"]["*"]
        soup = BeautifulSoup(html, "html.parser")
        
        # 3. Extract Infobox rows
        infobox = soup.find("table", {"class": "infobox"})
        if not infobox:
            # Fallback to searching first paragraph for "lahir di..."
            paragraphs = soup.find_all("p")
            for p in paragraphs[:3]:
                text = p.get_text()
                match = re.search(r"lahir (?:di|pada) ([\w\s,]+)", text, re.I)
                if match:
                    return f"Found in text: {match.group(1).strip()}"
            return "No infobox found"
        
        rows = infobox.find_all("tr")
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                header = th.get_text().lower()
                if "lahir" in header or "asal" in header:
                    return td.get_text().strip()
                    
        return "Key not found in infobox"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    test_artists = ["Caitlin Halderman", "Raim LaOde", "Denny Caknan", "Thomas Arya"]
    for artist in test_artists:
        result = experiment_wikipedia(artist)
        print(f"RESULT: {result}\n")
        time.sleep(1)
