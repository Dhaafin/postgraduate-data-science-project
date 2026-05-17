import os
import sys
import re
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from src.database.connection import sync_engine
from src.utils.geo_constants import INDO_PROVINCES, INDO_CITIES

# Comprehensive City to Province Mapping
CITY_TO_PROVINCE = {
    # Jawa Timur
    "Surabaya": "Jawa Timur",
    "Malang": "Jawa Timur",
    "Batu": "Jawa Timur",
    "Kediri": "Jawa Timur",
    "Madiun": "Jawa Timur",
    "Blitar": "Jawa Timur",
    "Pasuruan": "Jawa Timur",
    "Mojokerto": "Jawa Timur",
    "Ngawi": "Jawa Timur",
    "Sidoarjo": "Jawa Timur",
    "Jember": "Jawa Timur",
    "Nganjuk": "Jawa Timur",
    "Pamekasan": "Jawa Timur",
    "Probolinggo": "Jawa Timur",
    "Lumajang": "Jawa Timur",
    
    # Jawa Tengah
    "Semarang": "Jawa Tengah",
    "Solo": "Jawa Tengah",
    "Surakarta": "Jawa Tengah",
    "Blora": "Jawa Tengah",
    "Pemalang": "Jawa Tengah",
    "Banjarnegara": "Jawa Tengah",
    "Temanggung": "Jawa Tengah",
    "Pati": "Jawa Tengah",
    "Magelang": "Jawa Tengah",
    "Cilacap": "Jawa Tengah",
    "Banyumas": "Jawa Tengah",
    "Kebumen": "Jawa Tengah",
    "Klaten": "Jawa Tengah",
    "Wonogiri": "Jawa Tengah",
    
    # DI Yogyakarta
    "Yogyakarta": "DI Yogyakarta",
    
    # Jawa Barat
    "Bandung": "Jawa Barat",
    "Cimahi": "Jawa Barat",
    "Sukabumi": "Jawa Barat",
    "Bogor": "Jawa Barat",
    "Depok": "Jawa Barat",
    "Bekasi": "Jawa Barat",
    "Cirebon": "Jawa Barat",
    "Tasikmalaya": "Jawa Barat",
    "Garut": "Jawa Barat",
    "Majalengka": "Jawa Barat",
    "Indramayu": "Jawa Barat",
    
    # Banten
    "Tangerang": "Banten",
    "South Tangerang": "Banten",
    "Serang": "Banten",
    "Ciputat": "Banten",
    
    # Bali
    "Denpasar": "Bali",
    "Gianyar": "Bali",
    
    # Nusa Tenggara
    "Mataram": "Nusa Tenggara Barat",
    "Lombok": "Nusa Tenggara Barat",
    "Kupang": "Nusa Tenggara Timur",
    "Atambua": "Nusa Tenggara Timur",
    "Alor": "Nusa Tenggara Timur",
    "Sikka": "Nusa Tenggara Timur",
    "Manggarai": "Nusa Tenggara Timur",
    
    # Sumatera
    "Medan": "Sumatera Utara",
    "Binjai": "Sumatera Utara",
    "Pematangsiantar": "Sumatera Utara",
    "Langkat": "Sumatera Utara",
    "Dairi": "Sumatera Utara",
    "Padang": "Sumatera Barat",
    "Pekanbaru": "Riau",
    "Dumai": "Riau",
    "Kampar": "Riau",
    "Batam": "Kepulauan Riau",
    "Tanjungpinang": "Kepulauan Riau",
    "Jambi": "Jambi",
    "Palembang": "Sumatera Selatan",
    "Prabumulih": "Sumatera Selatan",
    "Bengkulu": "Bengkulu",
    "Bandar Lampung": "Lampung",
    "Banda Aceh": "Aceh",
    "Bireuen": "Aceh",
    "Bener Meriah": "Aceh",
    "Lhokseumawe": "Aceh",
    
    # Kalimantan
    "Pontianak": "Kalimantan Barat",
    "Singkawang": "Kalimantan Barat",
    "Palangkaraya": "Kalimantan Tengah",
    "Banjarmasin": "Kalimantan Selatan",
    "Banjarbaru": "Kalimantan Selatan",
    "Samarinda": "Kalimantan Timur",
    "Balikpapan": "Kalimantan Timur",
    
    # Sulawesi
    "Makassar": "Sulawesi Selatan",
    "Masamba": "Sulawesi Selatan",
    "Manado": "Sulawesi Utara",
    "Kotamobagu": "Sulawesi Utara",
    "Kendari": "Sulawesi Tenggara",
    
    # Maluku & Papua
    "Ambon": "Maluku",
    "Jayapura": "Papua",
}

class GeoNormalizer:
    def __init__(self):
        self.updates = 0

    def normalize(self, city, province):
        """Standardize city and province strings."""
        if not city:
            return None, province

        # 1. Clean date patterns (e.g. "27 September 1977" or "27 Juli 1992") and ages
        months_pattern = r'(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember|January|February|March|May|June|July|August|October|December)'
        date_pattern = rf'\b\d{{1,2}}\s+{months_pattern}\s+\d{{4}}\b'
        
        clean_city = re.sub(date_pattern, '', city, flags=re.I).strip()
        clean_city = re.sub(r'\(umur \d{1,3}\)', '', clean_city, flags=re.I).strip()
        
        # Remove trailing/leading garbage, citations, and "Indonesia"
        clean_city = re.sub(r'\[\d+\]', '', clean_city)
        clean_city = re.sub(r',? Indonesia$', '', clean_city, flags=re.I).strip()
        
        # Clean common administrative noise but keep if it is part of actual city name
        clean_city = re.sub(r' (Regency|City|Kabupaten|Kota)$', '', clean_city, flags=re.I).strip()
        
        # Clean any remaining stray commas or spaces
        clean_city = clean_city.strip(', ').strip()

        # Direct country-only fallback
        if clean_city.lower() == "indonesia":
            return None, None
            
        # 2. Jakarta Exception
        if "Jakarta" in clean_city:
            return "Jakarta", "DKI Jakarta"

        # 3. Dynamic Province Extraction (split by commas and match from right to left)
        parts = [p.strip() for p in clean_city.split(',') if p.strip()]
        extracted_prov = province
        
        PROVINCE_ALIASES = {
            "Bangka Belitung": "Kepulauan Bangka Belitung",
            "Nanggroe Aceh Darussalam": "Aceh",
            "Aceh Darussalam": "Aceh",
            "Jogjakarta": "DI Yogyakarta",
            "Jogja": "DI Yogyakarta",
        }

        # Match longer province names first to avoid partial matches (e.g. "Papua Barat" before "Papua")
        sorted_provinces = sorted(INDO_PROVINCES, key=len, reverse=True)

        for idx in range(len(parts) - 1, -1, -1):
            part = parts[idx]
            matched = False
            
            # A. Exact match with standard provinces
            for prov in sorted_provinces:
                if part.lower() == prov.lower():
                    extracted_prov = prov
                    parts.pop(idx)
                    matched = True
                    break
            if matched:
                break
                
            # B. Exact match with province aliases
            for alias, target in PROVINCE_ALIASES.items():
                if part.lower() == alias.lower():
                    extracted_prov = target
                    parts.pop(idx)
                    matched = True
                    break
            if matched:
                break
                
            # C. Substring match (province name is a word inside this part)
            for prov in sorted_provinces:
                if re.search(rf'\b{re.escape(prov)}\b', part, flags=re.I):
                    extracted_prov = prov
                    # Remove from part
                    parts[idx] = re.sub(rf'\b{re.escape(prov)}\b', '', part, flags=re.I).strip()
                    # Clean up trailing/leading commas or spaces in this part
                    parts[idx] = re.sub(r'^,\s*|,\s*$', '', parts[idx]).strip().strip(',').strip()
                    if not parts[idx]:
                        parts.pop(idx)
                    matched = True
                    break
            if matched:
                break

            # D. Substring match for aliases (alias is a word inside this part)
            for alias, target in PROVINCE_ALIASES.items():
                if re.search(rf'\b{re.escape(alias)}\b', part, flags=re.I):
                    extracted_prov = target
                    parts[idx] = re.sub(rf'\b{re.escape(alias)}\b', '', part, flags=re.I).strip()
                    parts[idx] = re.sub(r'^,\s*|,\s*$', '', parts[idx]).strip().strip(',').strip()
                    if not parts[idx]:
                        parts.pop(idx)
                    matched = True
                    break
            if matched:
                break
                
        clean_city = ", ".join(parts)

        # 4. Check if 'City' is actually just a Province name
        for prov in INDO_PROVINCES:
            if clean_city.lower() == prov.lower():
                return None, prov

        # 5. Auto-fill Province based on City (using expanded mappings)
        mapped_prov = extracted_prov
        if not mapped_prov:
            for city_key, prov_val in CITY_TO_PROVINCE.items():
                if city_key.lower() in clean_city.lower():
                    mapped_prov = prov_val
                    break

        # Final sanity check: if the city string is empty after extracting province, return None
        if not clean_city:
            return None, mapped_prov

        return clean_city, mapped_prov

    def run(self):
        print("\n" + "="*60)
        print(" GEO-DATA NORMALIZATION PIPELINE")
        print("="*60)
        
        if not sync_engine:
            print("Database connection failed.")
            return

        with sync_engine.begin() as conn:
            query = text("SELECT id, origin_city, origin_province FROM staging.music_data_staging WHERE origin_city IS NOT NULL")
            records = conn.execute(query).fetchall()

        print(f"Analyzing {len(records)} records for hierarchy standardization...\n")

        for record in records:
            db_id, raw_city, raw_prov = record
            
            new_city, new_prov = self.normalize(raw_city, raw_prov)

            if new_city != raw_city or new_prov != raw_prov:
                print(f" [!] ID {db_id}: '{raw_city}' -> City: '{new_city}', Prov: '{new_prov}'")
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE staging.music_data_staging SET origin_city = :city, origin_province = :prov WHERE id = :id"),
                        {"city": new_city, "prov": new_prov, "id": db_id}
                    )
                self.updates += 1

        print("\n" + "="*60)
        print(" NORMALIZATION COMPLETE")
        print("="*60)
        print(f"Total Updated Records: {self.updates}")
        print("="*60)

if __name__ == "__main__":
    GeoNormalizer().run()
