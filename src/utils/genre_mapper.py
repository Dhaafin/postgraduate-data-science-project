import re

# 1. Raw Hierarchy Specification (Specific to Generic)
RAW_GENRE_HIERARCHY = [
    {
        "name": "Spiritual & Devotional",
        "keywords": {"sholawat", "worship"}
    },
    {
        "name": "J-Pop & ACG Subculture",
        "keywords": {"j-pop", "anime", "vocaloid"}
    },
    {
        "name": "Reggae, Ska & Island Vibes",
        "keywords": {"ska", "reggae"}
    },
    {
        "name": "Regional Roots & Folk",
        "keywords": {"lagu jawa", "lagu timur", "maluku", "batak", "sunda", "minang", "fújì"}
    },
    {
        "name": "Dangdut & Koplo",
        "keywords": {"dangdut", "koplo", "hipdut", "funkot", "breakbeat"}
    },
    {
        "name": "Melayu Pop",
        "keywords": {"malay", "malay pop", "malaysian pop"}
    },
    {
        "name": "Heavy & Underground",
        "keywords": {
            "death metal", "black metal", "grindcore", "metalcore", "melodic death metal", 
            "progressive metal", "drone metal", "mathcore", "punk", "skate punk", "pop punk"
        }
    },
    {
        "name": "Hip-Hop, Rap & Electronic Beats",
        "keywords": {"indonesian hip hop", "malay rap", "j-rap", "melodic house", "moombahton", "jazz house"}
    },
    {
        "name": "R&B, Soul & Urban Grooves",
        "keywords": {"indonesian r&b", "electro r&b"}
    },
    {
        "name": "Jazz & Blues Essentials",
        "keywords": {"jazz", "indonesian jazz", "jazz fusion", "indie jazz", "bossa nova", "christian jazz", "experimental jazz"}
    },
    {
        "name": "Sophisticated & City Pop",
        "keywords": {"pop kreatif", "city pop"}
    },
    {
        "name": "Classic & Heritage Rock",
        "keywords": {"indonesian rock", "indorock", "progressive rock"}
    },
    {
        "name": "Indie & Alternative",
        "keywords": {
            "indonesian indie", "indie", "indonesian indie rock", "post-rock", "grunge", 
            "math rock", "psychedelic rock", "surf rock", "experimental", "ambient", 
            "electroacoustic", "avant-garde"
        }
    },
    {
        "name": "Mainstream Pop & Ballad",
        "keywords": {"indonesian pop", "jazz pop", "children's music"}
    }
]

# Precompile regex word-boundary patterns at module level for optimal ETL throughput
GENRE_HIERARCHY = []
for level in RAW_GENRE_HIERARCHY:
    name = level["name"]
    keywords = level["keywords"]
    
    # We map keyword to its precompiled regex: r'\bkeyword\b'
    patterns = {
        kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
        for kw in keywords
    }
    GENRE_HIERARCHY.append({
        "name": name,
        "keywords": keywords,
        "patterns": patterns
    })


def resolve_primary_genre(raw_genres):
    """
    Resolves a list of raw genre tags into a single Primary Parent Genre based on hierarchy.
    Enforces dual-phase matching (Exact matches first, then word-boundary substring matches)
    to prevent cross-genre contamination.
    
    Args:
        raw_genres (list[str] | str | None): The raw genres from Spotify.
        
    Returns:
        str | None: The resolved Parent Genre name, or None if raw_genres is empty/None.
    """
    if not raw_genres:
        return None
        
    # Handle string representation of lists if they come from DB as string
    if isinstance(raw_genres, str):
        # Clean standard string lists like "['pop', 'rock']" or "{pop, rock}"
        clean_str = raw_genres.strip('{}[]()""\'\'')
        if not clean_str:
            return None
        tags = [t.strip().strip('"\'').lower() for t in clean_str.split(',') if t.strip()]
    elif isinstance(raw_genres, list):
        tags = [str(t).lower().strip() for t in raw_genres if t]
    else:
        tags = [str(raw_genres).lower().strip()]
        
    if not tags:
        return None

    # PHASE 1: Scan all genres for EXACT string matches (highest precision)
    for level in GENRE_HIERARCHY:
        parent_name = level["name"]
        keywords = level["keywords"]
        for tag in tags:
            if tag in keywords:
                return parent_name

    # PHASE 2: Scan all genres for Word-Boundary Substring matches (fallback for composite tags)
    for level in GENRE_HIERARCHY:
        parent_name = level["name"]
        patterns = level["patterns"]
        for tag in tags:
            for kw, pattern in patterns.items():
                if pattern.search(tag):
                    return parent_name
                    
    # Default fallback if there are tags but none matched the rules
    return "Mainstream Pop & Ballad"

