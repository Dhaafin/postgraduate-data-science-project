import re

# 1. Raw Hierarchy Specification with Weights (Specific to Generic)
RAW_GENRE_HIERARCHY = [
    {
        "name": "Spiritual & Devotional",
        "keywords": {
            "sholawat": 2.0,
            "worship": 2.0
        }
    },
    {
        "name": "J-Pop & ACG Subculture",
        "keywords": {
            "j-pop": 2.0,
            "anime": 2.0,
            "vocaloid": 2.0
        }
    },
    {
        "name": "Reggae, Ska & Island Vibes",
        "keywords": {
            "ska": 2.0,
            "reggae": 2.0
        }
    },
    {
        "name": "Regional Roots & Folk",
        "keywords": {
            "lagu jawa": 2.0,
            "lagu timur": 2.0,
            "sunda": 2.0,
            "minang": 2.0,
            "fújì": 2.0,
            "maluku": 0.5,
            "batak": 0.5
        }
    },
    {
        "name": "Dangdut & Koplo",
        "keywords": {
            "dangdut": 2.0,
            "koplo": 2.0,
            "hipdut": 2.0,
            "funkot": 2.0,
            "breakbeat": 1.0
        }
    },
    {
        "name": "Melayu Pop",
        "keywords": {
            "malay pop": 2.0,
            "malaysian pop": 2.0,
            "malay": 0.5
        }
    },
    {
        "name": "Heavy & Underground",
        "keywords": {
            "death metal": 2.0,
            "black metal": 2.0,
            "grindcore": 2.0,
            "metalcore": 2.0,
            "melodic death metal": 2.0,
            "progressive metal": 2.0,
            "drone metal": 2.0,
            "mathcore": 2.0,
            "punk": 1.5,
            "skate punk": 1.5,
            "pop punk": 1.5
        }
    },
    {
        "name": "Hip-Hop, Rap & Electronic Beats",
        "keywords": {
            "indonesian hip hop": 2.0,
            "malay rap": 2.0,
            "j-rap": 2.0,
            "melodic house": 1.5,
            "moombahton": 1.5,
            "jazz house": 1.5
        }
    },
    {
        "name": "R&B, Soul & Urban Grooves",
        "keywords": {
            "indonesian r&b": 2.0,
            "electro r&b": 2.0
        }
    },
    {
        "name": "Jazz & Blues Essentials",
        "keywords": {
            "jazz": 1.5,
            "indonesian jazz": 1.5,
            "jazz fusion": 1.5,
            "indie jazz": 1.5,
            "bossa nova": 1.5,
            "christian jazz": 1.5,
            "experimental jazz": 1.5
        }
    },
    {
        "name": "Sophisticated & City Pop",
        "keywords": {
            "pop kreatif": 1.5,
            "city pop": 1.5
        }
    },
    {
        "name": "Classic & Heritage Rock",
        "keywords": {
            "indonesian rock": 1.5,
            "indorock": 2.0,
            "progressive rock": 1.5
        }
    },
    {
        "name": "Indie & Alternative",
        "keywords": {
            "indonesian indie": 1.5,
            "indie": 1.0,
            "indonesian indie rock": 1.5,
            "post-rock": 1.5,
            "grunge": 1.5,
            "math rock": 1.5,
            "psychedelic rock": 1.5,
            "surf rock": 1.5,
            "experimental": 1.0,
            "ambient": 1.0,
            "electroacoustic": 1.0,
            "avant-garde": 1.0
        }
    },
    {
        "name": "Mainstream Pop & Ballad",
        "keywords": {
            "indonesian pop": 1.0,
            "jazz pop": 1.0,
            "children's music": 1.0
        }
    }
]

# Precompile regex patterns and map weights at module level for high ETL efficiency
GENRE_HIERARCHY = []
for level in RAW_GENRE_HIERARCHY:
    name = level["name"]
    keywords = level["keywords"]
    
    # Precompile regex for word boundary substring matching: r'\bkeyword\b'
    patterns = {
        kw: (weight, re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE))
        for kw, weight in keywords.items()
    }
    
    GENRE_HIERARCHY.append({
        "name": name,
        "keywords": keywords,
        "patterns": patterns
    })


def resolve_primary_genre(raw_genres):
    """
    Resolves a list of raw genre tags into a single Primary Parent Genre using a
    Weighted Scoring Classifier. Enforces exact-first scoring, falling back to 
    regex-safe word boundaries, and uses the hierarchy as a tie-breaker.
    
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

    # Track accumulated scores for each parent genre
    genre_scores = {level["name"]: 0.0 for level in GENRE_HIERARCHY}
    
    # Process each tag independently, accumulating weight for the best matching category
    for tag in tags:
        best_match = None  # tuple: (genre_name, weight)
        
        # Phase 1: Exact matches (high precision)
        for level in GENRE_HIERARCHY:
            genre_name = level["name"]
            keywords = level["keywords"]
            if tag in keywords:
                weight = keywords[tag]
                # Keep the match that gives the highest weight
                if not best_match or weight > best_match[1]:
                    best_match = (genre_name, weight)
                    
        # Phase 2: Substring matches with word boundaries (fallback)
        if not best_match:
            for level in GENRE_HIERARCHY:
                genre_name = level["name"]
                patterns = level["patterns"]
                for kw, (weight, pattern) in patterns.items():
                    if pattern.search(tag):
                        if not best_match or weight > best_match[1]:
                            best_match = (genre_name, weight)
                            
        # Accumulate score if a match was resolved for this tag
        if best_match:
            genre_name, weight = best_match
            genre_scores[genre_name] += weight

    # Find the maximum score achieved across all genres
    max_score = max(genre_scores.values())
    
    if max_score <= 0.0:
        return "Mainstream Pop & Ballad"
        
    # Find all genres that share the maximum score
    candidates = [name for name, score in genre_scores.items() if score == max_score]
    
    # Break ties by selecting the candidate higher up in the hierarchy (most specific)
    for level in GENRE_HIERARCHY:
        if level["name"] in candidates:
            return level["name"]
            
    return "Mainstream Pop & Ballad"

