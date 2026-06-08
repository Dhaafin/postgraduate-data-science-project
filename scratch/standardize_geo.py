"""
Standardize Geographic Fields for Indonesian Music Platform.
Aligns origin_city and origin_province in the Supabase staging database
with the front-end recognized cities and mapped provinces.
"""

import os
import re
import sys
import argparse
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

# 1. FE Recognized Cities
RECOGNIZED_CITIES = {
    # DKI Jakarta
    "Jakarta",
    # Jawa Barat
    "Bandung", "Bogor", "Depok", "Bekasi", "Cimahi", "Sukabumi", "Cirebon", "Tasikmalaya", "Garut",
    # Jawa Tengah
    "Semarang", "Surakarta", "Solo", "Surakarta (Solo)", "Magelang", "Tegal", "Pekalongan", "Purwokerto", "Salatiga", "Brebes", "Kendal",
    # DI Yogyakarta
    "Yogyakarta", "Sleman", "Bantul",
    # Jawa Timur
    "Surabaya", "Malang", "Sidoarjo", "Kediri", "Madiun", "Banyuwangi", "Jember", "Probolinggo", "Pasuruan", "Nganjuk",
    # Banten
    "Tangerang", "Serang", "Cilegon", "Pandeglang",
    # Bali & Nusa Tenggara
    "Denpasar", "Gianyar", "Mataram", "Kupang",
    # Sumatera
    "Medan", "Padang", "Palembang", "Pekanbaru", "Banda Aceh", "Bandar Lampung", "Batam", "Jambi", "Bengkulu",
    # Kalimantan
    "Pontianak", "Balikpapan", "Samarinda", "Banjarmasin", "Palangkaraya",
    # Sulawesi
    "Makassar", "Manado", "Palu", "Kendari", "Gorontalo", "Soppeng",
    # Maluku & Papua
    "Ambon", "Ternate", "Jayapura", "Sorong", "Manokwari", "Timika"
}

CITY_TO_PROVINCE = {
    "Jakarta": "DKI Jakarta",
    "Bandung": "Jawa Barat", "Bogor": "Jawa Barat", "Depok": "Jawa Barat", "Bekasi": "Jawa Barat",
    "Cimahi": "Jawa Barat", "Sukabumi": "Jawa Barat", "Cirebon": "Jawa Barat", "Tasikmalaya": "Jawa Barat", "Garut": "Jawa Barat",
    "Semarang": "Jawa Tengah", "Surakarta": "Jawa Tengah", "Solo": "Jawa Tengah", "Surakarta (Solo)": "Jawa Tengah",
    "Magelang": "Jawa Tengah", "Tegal": "Jawa Tengah", "Pekalongan": "Jawa Tengah", "Purwokerto": "Jawa Tengah",
    "Salatiga": "Jawa Tengah", "Brebes": "Jawa Tengah", "Kendal": "Jawa Tengah",
    "Yogyakarta": "DI Yogyakarta", "Sleman": "DI Yogyakarta", "Bantul": "DI Yogyakarta",
    "Surabaya": "Jawa Timur", "Malang": "Jawa Timur", "Sidoarjo": "Jawa Timur", "Kediri": "Jawa Timur",
    "Madiun": "Jawa Timur", "Banyuwangi": "Jawa Timur", "Jember": "Jawa Timur", "Probolinggo": "Jawa Timur",
    "Pasuruan": "Jawa Timur", "Nganjuk": "Jawa Timur",
    "Tangerang": "Banten", "Serang": "Banten", "Cilegon": "Banten", "Pandeglang": "Banten",
    "Denpasar": "Bali", "Gianyar": "Bali", "Mataram": "Nusa Tenggara Barat", "Kupang": "Nusa Tenggara Timur",
    "Medan": "Sumatera Utara", "Padang": "Sumatera Barat", "Palembang": "Sumatera Selatan", "Pekanbaru": "Riau",
    "Banda Aceh": "Aceh", "Bandar Lampung": "Lampung", "Batam": "Kepulauan Riau", "Jambi": "Jambi", "Bengkulu": "Bengkulu",
    "Pontianak": "Kalimantan Barat", "Balikpapan": "Kalimantan Timur", "Samarinda": "Kalimantan Timur",
    "Banjarmasin": "Kalimantan Selatan", "Palangkaraya": "Kalimantan Tengah",
    "Makassar": "Sulawesi Selatan", "Manado": "Sulawesi Utara", "Palu": "Sulawesi Tengah",
    "Kendari": "Sulawesi Tenggara", "Gorontalo": "Gorontalo", "Soppeng": "Sulawesi Selatan",
    "Ambon": "Maluku", "Ternate": "Maluku Utara", "Jayapura": "Papua",
    "Sorong": "Papua Barat Daya", "Manokwari": "Papua Barat", "Timika": "Papua Tengah"
}

# 2. 31 Mapped Provinces
PROVINCE_FALLBACKS = {
    "DKI Jakarta", "Jawa Barat", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur",
    "Banten", "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur", "Sumatera Utara",
    "Sumatera Barat", "Sumatera Selatan", "Riau", "Kepulauan Riau", "Aceh",
    "Lampung", "Jambi", "Bengkulu", "Kalimantan Barat", "Kalimantan Timur",
    "Kalimantan Selatan", "Kalimantan Tengah", "Sulawesi Selatan", "Sulawesi Utara",
    "Sulawesi Tengah", "Sulawesi Tenggara", "Gorontalo", "Maluku", "Maluku Utara",
    "Papua", "Papua Barat", "Kepulauan Bangka Belitung", "Papua Tengah", "Papua Barat Daya"
}

# 3. Explicit Corrections Lookup for 90+ Unmatched/Incorrect records
ARTIST_CORRECTIONS = {
    "ARMADA": {"city": "Palembang", "province": "Sumatera Selatan"},
    "dia": {"city": "Makassar", "province": "Sulawesi Selatan"},
    "Astrid": {"city": "Surabaya", "province": "Jawa Timur"},
    "Mawar De Jongh": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Gigi": {"city": "Bandung", "province": "Jawa Barat"},
    "Rayola": {"city": "Padang", "province": "Sumatera Barat"},
    "Near": {"city": "Kupang", "province": "Nusa Tenggara Timur"},
    "The Rain": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "Julian Jacob": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Souljah": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Cindy Bernadette": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Pete Swinton": {"city": "Bandung", "province": "Jawa Barat"},
    "Rahmania Astrini": {"city": "Bandung", "province": "Jawa Barat"},
    "Meiska": {"city": "Denpasar", "province": "Bali"},
    "Drive": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Beside": {"city": "Bandung", "province": "Jawa Barat"},
    "Alfina Nindiyani": {"city": "Surabaya", "province": "Jawa Timur"},
    "Billy Surya Dilaga": {"city": "Samarinda", "province": "Kalimantan Timur"},
    "Extreme Decay": {"city": "Malang", "province": "Jawa Timur"},
    "Heiakim": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Ritta Rubby Adiwidjaja": {"city": "Bandung", "province": "Jawa Barat"},
    "Edane": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Batas Senja": {"city": "Bandar Lampung", "province": "Lampung"},
    "Michi Mochievee": {"city": "Jakarta", "province": "DKI Jakarta"},
    "radiotua": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "M. Tri Hamdani": {"city": "Medan", "province": "Sumatera Utara"},
    "Jontrall": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Joey Alexander": {"city": "Denpasar", "province": "Bali"},
    "Terto Djen": {"city": "Kupang", "province": "Nusa Tenggara Timur"},
    "Ipank": {"city": "Padang", "province": "Sumatera Barat"},
    "Sridevi": {"city": "Palembang", "province": "Sumatera Selatan"},
    "RAN": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Peterpan": {"city": "Bandung", "province": "Jawa Barat"},
    "Jaz": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Enau": {"city": "Bandung", "province": "Jawa Barat"},
    "Ramengvrl": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Kill The DJ": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "Silet Open Up": {"city": "Timika", "province": "Papua Tengah"},
    "Diva Aurel": {"city": "Surabaya", "province": "Jawa Timur"},
    "Wira Nagara": {"city": "Purwokerto", "province": "Jawa Tengah"},
    "Nuca": {"city": "Surakarta", "province": "Jawa Tengah"},
    "Devano": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Paul Partohap": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Zaskia Gotik": {"city": "Bekasi", "province": "Jawa Barat"},
    "Hal": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "DJ Nansuya": {"city": "Jakarta", "province": "DKI Jakarta"},
    "LAVORA": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "Glitter": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Cinta Laura": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Idgitaf": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Tulus": {"city": "Bandung", "province": "Jawa Barat"},
    "Juan Reza": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Bravy": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Keisya Levronka": {"city": "Malang", "province": "Jawa Timur"},
    "Tipe-X": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Sabyan": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Felix Irwan": {"city": "Yogyakarta", "province": "DI Yogyakarta"},
    "adis": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Padi": {"city": "Surabaya", "province": "Jawa Timur"},
    "Al Ghazali": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Marcell Siahaan": {"city": "Bandung", "province": "Jawa Barat"},
    "Bastian Steel": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Jason Ranti": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Fildan": {"city": "Kendari", "province": "Sulawesi Tenggara"},
    "GOVINDA": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Tereza Fahlevi": {"city": "Banda Aceh", "province": "Aceh"},
    "Vierra": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Sandrina": {"city": "Jakarta", "province": "DKI Jakarta"},
    "SULE": {"city": "Bandung", "province": "Jawa Barat"},
    "Novia Bachmid": {"city": "Manado", "province": "Sulawesi Utara"},
    "Lyla": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Syahiba Saufa": {"city": "Banyuwangi", "province": "Jawa Timur"},
    "Maria Shandi": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Adnan Veron": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Whisnu Santika": {"city": "Jakarta", "province": "DKI Jakarta"},
    "510": {"city": "Bandung", "province": "Jawa Barat"},
    "Pas Band": {"city": "Bandung", "province": "Jawa Barat"},
    "Muria": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Haico": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Evie Tamala": {"city": "Tasikmalaya", "province": "Jawa Barat"},
    "Aruma": {"city": "Bandung", "province": "Jawa Barat"},
    "SIVIA": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Adhitia Sofyan": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Neona": {"city": "Jakarta", "province": "DKI Jakarta"},
    "Amigdala": {"city": "Bandung", "province": "Jawa Barat"},
    "Superman Is Dead": {"city": "Denpasar", "province": "Bali"},
    "Rainych": {"city": "Padang", "province": "Sumatera Barat"},
    "Hamdan ATT": {"city": "Ambon", "province": "Maluku"},
    "Ming Luhulima": {"city": "Ambon", "province": "Maluku"},
    "Titiek Puspa": {"city": "Banjarmasin", "province": "Kalimantan Selatan"},
    "Kangen Band": {"city": "Bandar Lampung", "province": "Lampung"},
    "Tri Suaka": {"city": "Bandar Lampung", "province": "Lampung"},
    "BAP.": {"city": "Jakarta", "province": "DKI Jakarta"}
}

PROVINCE_ALIASES = {
    "bangka belitung": "Kepulauan Bangka Belitung",
    "kepulauan bangka belitung": "Kepulauan Bangka Belitung",
    "nanggroe aceh darussalam": "Aceh",
    "aceh darussalam": "Aceh",
    "jogjakarta": "DI Yogyakarta",
    "jogja": "DI Yogyakarta",
    "yogyakarta": "DI Yogyakarta",
    "daerah istimewa yogyakarta": "DI Yogyakarta",
    "diy": "DI Yogyakarta",
    "daerah khusus ibukota jakarta": "DKI Jakarta",
    "jakarta": "DKI Jakarta",
    "papua barat daya": "Papua Barat Daya",
    "papua tengah": "Papua Tengah"
}

def clean_name(name_str):
    if not name_str:
        return ""
    # Remove common geographic suffixes
    clean = re.sub(r' (Regency|City|Kabupaten|Kota)$', '', name_str.strip(), flags=re.I).strip()
    
    # Fix typos
    if clean.lower() == "tasimalaya":
        return "Tasikmalaya"
    
    return clean

def match_province(prov_str):
    if not prov_str:
        return None
    p_clean = prov_str.strip().lower()
    
    # Check aliases first
    if p_clean in PROVINCE_ALIASES:
        return PROVINCE_ALIASES[p_clean]
        
    for p in PROVINCE_FALLBACKS:
        if p.lower() == p_clean or p_clean in p.lower() or p.lower() in p_clean:
            return p
            
    return None

def match_city(city_str):
    if not city_str:
        return None
    c_clean = clean_name(city_str)
    
    # Handle specific combinations
    if c_clean.lower() == "solo" or c_clean.lower() == "surakarta":
        return "Surakarta (Solo)"
        
    for c in RECOGNIZED_CITIES:
        if c.lower() == c_clean.lower():
            return c
            
    return None

def run_standardization(dry_run=True):
    print("\n" + "="*70)
    print(f" GEOGRAPHIC STANDARDIZATION PIPELINE {'(DRY RUN)' if dry_run else '(LIVE EXECUTION)'}")
    print("="*70 + "\n")
    
    if not sync_engine:
        print("Error: Could not connect to database.")
        return
        
    with sync_engine.begin() as conn:
        records = conn.execute(text("SELECT id, artist_name, origin_city, origin_province FROM staging.music_data_staging ORDER BY id")).fetchall()
        
    total_records = len(records)
    updates_count = 0
    unresolved_count = 0
    
    for r in records:
        db_id, name, city, prov = r
        orig_city = city
        orig_prov = prov
        
        target_city = None
        target_prov = None
        
        # 1. Apply explicit overrides if name matches
        if name in ARTIST_CORRECTIONS:
            corr = ARTIST_CORRECTIONS[name]
            target_city = corr["city"]
            target_prov = corr["province"]
        else:
            # 2. General Standardization
            # Clean and match city
            matched_c = match_city(city)
            if matched_c:
                target_city = matched_c
                target_prov = CITY_TO_PROVINCE[matched_c]
            else:
                # If city not recognized, check if we can reconstruct (e.g. city='Banda', prov='Aceh' -> Banda Aceh)
                if city and prov:
                    combined = f"{city} {prov}".strip()
                    matched_c = match_city(combined)
                    if matched_c:
                        target_city = matched_c
                        target_prov = CITY_TO_PROVINCE[matched_c]
                
                # If still no city matched, check province fallback
                if not target_city:
                    matched_p = match_province(prov)
                    if matched_p:
                        target_prov = matched_p
                        # Unrecognized cities are set to None/NULL in database
                        target_city = None
                    else:
                        # Try to find province from city string if province is None
                        if city and not prov:
                            matched_p = match_province(city)
                            if matched_p:
                                target_prov = matched_p
                                target_city = None
        
        # Check if updates are needed
        needs_update = False
        if target_city != orig_city:
            needs_update = True
        if target_prov != orig_prov:
            needs_update = True
            
        if needs_update:
            print(f"[*] ID {db_id:<4} | {name:<25} :")
            print(f"    FROM: City: '{orig_city}', Prov: '{orig_prov}'")
            print(f"    TO:   City: '{target_city}', Prov: '{target_prov}'")
            updates_count += 1
            
            if not dry_run:
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("""
                            UPDATE staging.music_data_staging 
                            SET origin_city = :city, 
                                origin_province = :prov 
                            WHERE id = :id
                        """),
                        {"city": target_city, "prov": target_prov, "id": db_id}
                    )
        elif not target_prov:
            print(f"[!] ID {db_id:<4} | {name:<25} : UNRESOLVED LOCATION (City: '{orig_city}', Prov: '{orig_prov}')")
            unresolved_count += 1
            
    print("\n" + "="*70)
    print(f"Summary Statistics:")
    print(f"  - Total Records Scanned: {total_records}")
    print(f"  - Total Records Updated: {updates_count}")
    print(f"  - Unresolved Records   : {unresolved_count}")
    print("="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standardize geographic coordinates and names in Supabase staging database.")
    parser.add_argument("--execute", action="store_true", help="Apply updates to the database (defaults to dry-run)")
    args = parser.parse_args()
    
    run_standardization(dry_run=not args.execute)
