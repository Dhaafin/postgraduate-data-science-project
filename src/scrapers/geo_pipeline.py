import asyncio
import requests
from src.database.connection import engine
from sqlalchemy import text

# Import the Wikipedia scraper we just built
from src.scrapers.wiki_geo_scraper import WikiGeoScraper

class GeoPipeline:
    """
    Orchestrates the Geo-Enrichment process:
    1. Fetches artist names from the DB.
    2. Uses WikiGeoScraper to find City/Province.
    3. Uses Nominatim/OpenStreetMap to find Lat/Lon coordinates.
    4. Updates the DB.
    """
    def __init__(self):
        self.wiki_scraper = WikiGeoScraper()
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "MusicDataScraper/1.0 (Research Project; contact via github)"
        }

    def _geocode_sync(self, city, province):
        """Hits Nominatim API to convert City string into Lat/Lon."""
        # Include province for better accuracy if available, else just city
        query = f"{city}, {province}" if province else city
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }
        try:
            response = requests.get(self.nominatim_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            print(f"Error geocoding '{query}': {e}")
        return None, None

    async def get_coordinates(self, city, province):
        if not city:
            return None, None
        return await asyncio.to_thread(self._geocode_sync, city, province)

    async def process_top_5(self):
        print("Starting Geo-Enrichment Pipeline for Top 5 Artists...\n")
        
        # 1. Fetch 5 records from DB
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT id, artist_name FROM music_data LIMIT 5"))
            artists = [{"id": row[0], "name": row[1]} for row in result.fetchall()]

        if not artists:
            print("No artists found in the database. Run the Viberate scraper first.")
            return

        for artist in artists:
            db_id = artist["id"]
            name = artist["name"]
            print(f"--- Processing: {name} ---")

            # 2. Extract City/Province from Wikipedia
            wiki_data = await self.wiki_scraper.get_artist_geo(name)
            city = wiki_data["origin_city"]
            prov = wiki_data["origin_province"]
            
            print(f"  Wiki Extracted -> City: {city} | Prov: {prov}")

            # 3. Geocode with Nominatim
            lat, lon = await self.get_coordinates(city, prov)
            print(f"  Coordinates -> Lat: {lat} | Lon: {lon}")

            # 4. Update Database
            async with engine.begin() as conn:
                await conn.execute(
                    text("""
                        UPDATE music_data 
                        SET origin_city = :city, 
                            origin_province = :prov, 
                            latitude = :lat, 
                            longitude = :lon 
                        WHERE id = :id
                    """),
                    {
                        "city": city,
                        "prov": prov,
                        "lat": lat,
                        "lon": lon,
                        "id": db_id
                    }
                )
            print(f"  ✅ Database updated for {name}.\n")

if __name__ == "__main__":
    import sys
    # Essential Windows asyncio fix to prevent loop hanging
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    pipeline = GeoPipeline()
    asyncio.run(pipeline.process_top_5())
