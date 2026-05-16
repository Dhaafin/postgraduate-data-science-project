# Indonesian Toponyms for Geographic Validation

# A collection of Cities, Regencies (Kabupaten), and Provinces in Indonesia
# used to validate MusicBrainz origin strings.

INDO_CITIES = {
    # Major Metropolitans
    "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Palembang",
    "Tangerang", "South Tangerang", "Bekasi", "Depok", "Bogor", "Malang", "Yogyakarta",
    "Denpasar", "Surakarta", "Solo", "Banjarmasin", "Balikpapan", "Pontianak",
    "Samarinda", "Batam", "Pekanbaru", "Bandar Lampung", "Padang", "Jambi",
    "Manado", "Mataram", "Kupang", "Ambon", "Jayapura",
    
    # Regional Hubs found in dataset
    "Singkawang", "Probolinggo", "Cimahi", "Sukabumi", "Cirebon", "Tegal", "Pekalongan",
    "Kediri", "Madiun", "Blitar", "Pasuruan", "Mojokerto", "Batu", "Salatiga",
    "Magelang", "Binjai", "Pematangsiantar", "Tanjungbalai", "Tebing Tinggi",
    "Padang Sidempuan", "Lubuklinggau", "Prabumulih", "Pagar Alam", "Metro",
    "Tanjungpinang", "Dumai", "Banda Aceh", "Lhokseumawe", "Langsa", "Sabang",
    "Palangkaraya", "Banjarbaru", "Tarakan", "Bontang", "Palu", "Kendari", 
    "Bitung", "Gorontalo", "Ternate", "Sorong",
    
    # Specific Regencies found in dataset
    "Pemalang", "Banyumas", "Cilacap", "Kebumen", "Purworejo", "Wonosobo",
    "Magelang", "Boyolali", "Klaten", "Sukoharjo", "Wonogiri", "Karanganyar",
    "Sragen", "Grobogan", "Blora", "Rembang", "Pati", "Kudus", "Jepara",
    "Demak", "Temanggung", "Kendal", "Batang", "Banjarnegara"
}

INDO_PROVINCES = {
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
    "Jambi", "Bengkulu", "Sumatera Selatan", "Kepulauan Bangka Belitung",
    "Lampung", "Banten", "DKI Jakarta", "Jawa Barat", "Jawa Tengah",
    "DI Yogyakarta", "Jawa Timur", "Bali", "Nusa Tenggara Barat",
    "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah",
    "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara",
    "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat",
    "Sulawesi Selatan", "Sulawesi Tenggara", "Maluku", "Maluku Utara",
    "Papua Barat", "Papua", "Papua Tengah", "Papua Pegunungan",
    "Papua Selatan", "Papua Barat Daya"
}

def is_indonesian_location(location_string):
    """
    Returns True if the location string contains an Indonesian city or province.
    Handles 'Regency', 'City', or 'Province' suffixes often found in MB data.
    """
    if not location_string:
        return False
        
    location_lower = location_string.lower()
    
    # Check for direct matches in cities
    for city in INDO_CITIES:
        if city.lower() in location_lower:
            return True
            
    # Check for direct matches in provinces
    for province in INDO_PROVINCES:
        if province.lower() in location_lower:
            return True
            
    # Catch-all for country name
    if "indonesia" in location_lower:
        return True
        
    return False
