"""
Candidate Matching and Similarity Scoring Logic

This module provides reusable matching algorithms to evaluate whether a raw artist search query 
matches a specific Spotify (or other source) result, penalizing global artists without Indonesian ties.
"""

import difflib

INDO_ANCHORS = ["indonesia", "indo", "jawa", "dangdut", "koplo", "sunda", "malay", "sholawat"]

def score_spotify_candidate(query_name, artist_data):
    """
    Scores a single Spotify artist response against a query name.
    
    Args:
        query_name (str): The raw artist name we are looking for.
        artist_data (dict): The Spotify API artist dictionary.
        
    Returns:
        dict: A dictionary containing the total_score and name_score.
    """
    query_clean = query_name.lower().strip()
    name_actual = artist_data.get("name", "")
    name_clean = name_actual.lower().strip()
    artist_genres = [g.lower() for g in artist_data.get("genres", [])]
    popularity = artist_data.get("popularity", 0)

    # A. Semantic Similarity (difflib ratio)
    name_score = difflib.SequenceMatcher(None, query_clean, name_clean).ratio()
    
    # B. Geographic Bonus
    genre_bonus = 0.25 if any(any(anchor in g for anchor in INDO_ANCHORS) for g in artist_genres) else 0.0
    
    # C. Popularity Tie-breaker (Max 0.05)
    pop_score = (popularity / 100) * 0.05
    
    # D. Total Score
    total_score = name_score + genre_bonus + pop_score
    
    # E. Collision Penalty (The "David Guetta" Guard)
    # If the name is a weak match and no Indo-signal is present, penalize.
    if name_score < 0.6 and genre_bonus == 0:
        total_score -= 0.4

    # F. Layer 2: Global Star Filter (Follower Cap)
    # If the artist is massive (> 1M followers) and not a perfect name match,
    # we apply a heavy penalty unless they have a strong Indo-genre signal.
    followers = artist_data.get("followers", {}).get("total", 0)
    if followers > 1_000_000 and name_score < 0.95 and genre_bonus == 0:
        total_score -= 1.0

    return {
        "data": artist_data,
        "total_score": total_score,
        "name_score": name_score
    }
