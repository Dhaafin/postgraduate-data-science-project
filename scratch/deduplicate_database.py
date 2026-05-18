"""
Database Deduplication and Sanitation Utility

This script identifies and resolves duplicate records in staging.music_data_staging.
It categorizes duplicates into:
1. Identity Duplicates (Category A): Same artist and same Spotify ID.
2. Spelling Merges (Category B): Spelling variants that resolved to the same Spotify ID.
3. Scraper Race Collisions (Category C): Unrelated artists mapped to the same Spotify ID.

It operates in --preview mode by default and requires --execute to commit changes.
"""

import asyncio
import os
import sys
import argparse
import difflib
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import engine

# Hardcoded known scraper race collisions for precision
KNOWN_COLLISONS = {
    # Spotify ID: Incorrect Record ID to reset
    "13y29W8mEcA2gKqUr1SPLJ": 290,  # Nyoman Paul (Incorrect) vs Rony Parulian (55, Correct)
    "374NOHOFF57pYs9QOhuKJq": 387,  # Sari Simorangkir (Incorrect) vs Sammy Simorangkir (217, Correct)
    "4xCe99Ojwtbdi2aAVpSuo2": 336,  # Hal (Incorrect) vs Halstage (296, Correct)
}

def get_completeness_score(row):
    """
    Computes a score based on how many metadata fields are populated.
    """
    fields_to_check = [
        "origin_city", "origin_province", "latitude", "longitude", 
        "is_indonesian", "artist_type", "wikipedia_url", 
        "profile_picture", "genre", "followers", "popularity"
    ]
    
    score = 0
    # row is a SQLAlchemy Row mapping or sequence. 
    # We access by field index or name.
    row_dict = row._asdict()
    for field in fields_to_check:
        val = row_dict.get(field)
        if val is not None and val != "" and val != [] and val != {}:
            score += 1
    return score

async def run_deduplicator(execute=False):
    if not engine:
        print("[-] Database engine not initialized. Check your DATABASE_URL in .env.")
        return
        
    async with engine.connect() as conn:
        print("\n" + "="*70)
        print(f"      DATABASE SANITATION: DEDUPLICATION ENGINE ({'EXECUTE' if execute else 'PREVIEW'} MODE)")
        print("="*70 + "\n")
        
        # 1. Fetch all records from staging.music_data_staging
        query = text("""
            SELECT id, artist_name, spotify_id, spotify_link, profile_picture, genre, 
                   followers, popularity, artist_type, origin_city, origin_province, 
                   latitude, longitude, is_indonesian, wikipedia_url
            FROM staging.music_data_staging
            ORDER BY id ASC
        """)
        result = await conn.execute(query)
        all_rows = result.fetchall()
        
        print(f"[*] Read {len(all_rows)} total rows from staging.music_data_staging.")
        
        # Group records by Spotify ID (excluding null/empty ones)
        spotify_groups = {}
        null_spotify_records = []
        
        for row in all_rows:
            sp_id = row.spotify_id
            if sp_id and sp_id.strip():
                spotify_groups.setdefault(sp_id.strip(), []).append(row)
            else:
                null_spotify_records.append(row)
                
        to_delete_ids = []
        to_reset_ids = []
        merged_pairs = []
        collision_resets = []
        
        # 2. Process groups sharing the same Spotify ID
        for sp_id, group in spotify_groups.items():
            if len(group) <= 1:
                continue
                
            # We have duplicates/collisions sharing this Spotify ID!
            # Check if it is a collision or a mergeable spelling duplicate.
            # Measure name similarity between all pairs in the group.
            is_collision = False
            
            # Check against hardcoded known collisions
            for row in group:
                if sp_id in KNOWN_COLLISONS and row.id == KNOWN_COLLISONS[sp_id]:
                    is_collision = True
                    break
            
            # If not hardcoded, check mathematically
            if not is_collision:
                base_name = group[0].artist_name.lower().strip()
                for other_row in group[1:]:
                    other_name = other_row.artist_name.lower().strip()
                    similarity = difflib.SequenceMatcher(None, base_name, other_name).ratio()
                    if similarity < 0.65:
                        is_collision = True
                        break
            
            if is_collision:
                # Category C: Scraper Race Collision!
                # We reset the incorrect record(s) and keep the correct one intact.
                print(f"[!] Scraper Collision Detected for Spotify ID: {sp_id}")
                
                # Determine which one to reset
                correct_row = None
                incorrect_rows = []
                
                if sp_id in KNOWN_COLLISONS:
                    incorrect_id = KNOWN_COLLISONS[sp_id]
                    for r in group:
                        if r.id == incorrect_id:
                            incorrect_rows.append(r)
                        else:
                            correct_row = r  # Assume the other is correct
                else:
                    # Generic fallback: Keep the one with the highest similarity to... 
                    # well, we don't have the Spotify profile name, so we keep the first one
                    # and reset the others, marking both for review.
                    correct_row = group[0]
                    incorrect_rows = group[1:]
                
                for inc_row in incorrect_rows:
                    to_reset_ids.append(inc_row.id)
                    collision_resets.append({
                        "id": inc_row.id,
                        "name": inc_row.artist_name,
                        "spotify_id": sp_id,
                        "action": "Reset (spotify_id -> NULL, needs_review -> TRUE)"
                    })
                    print(f"  -> Reset target: ID {inc_row.id} ('{inc_row.artist_name}')")
                if correct_row:
                    print(f"  -> Keep target:  ID {correct_row.id} ('{correct_row.artist_name}')")
                    
            else:
                # Category A or B: Identity Duplicate or Spelling Merge
                # Score them by metadata completeness to pick the master record
                scored_group = []
                for row in group:
                    score = get_completeness_score(row)
                    scored_group.append((score, row.id, row))
                
                # Sort by score descending, then by ID ascending (oldest first)
                scored_group.sort(key=lambda x: (-x[0], x[1]))
                
                master_row = scored_group[0][2]
                duplicate_rows = [x[2] for x in scored_group[1:]]
                
                print(f"[+] Duplicate Group found for Spotify ID: {sp_id}")
                print(f"  -> MASTER: ID {master_row.id} ('{master_row.artist_name}') [Completeness Score: {scored_group[0][0]}]")
                
                for dup in duplicate_rows:
                    to_delete_ids.append(dup.id)
                    merged_pairs.append({
                        "delete_id": dup.id,
                        "delete_name": dup.artist_name,
                        "keep_id": master_row.id,
                        "keep_name": master_row.artist_name,
                        "spotify_id": sp_id
                    })
                    print(f"  -> DELETE: ID {dup.id} ('{dup.artist_name}') [Completeness Score: get_completeness_score({dup.id})]")
        
        print("\n" + "-"*50)
        print("      SUMMARY OF ACTIONS")
        print("-"*50)
        print(f"Identical/Spelling Duplicates to DELETE : {len(to_delete_ids)}")
        print(f"Scraper Race Collisions to RESET        : {len(to_reset_ids)}")
        
        # 3. Execution phase (inside transaction)
        if execute:
            if not to_delete_ids and not to_reset_ids:
                print("\n✅ No actions to execute. Database is already clean.")
                return
                
            print(f"\n[*] Executing sanitation transaction for {len(to_delete_ids) + len(to_reset_ids)} operations...")
            
            async with engine.begin() as transaction_conn:
                # A. Delete identity/spelling duplicates
                if to_delete_ids:
                    delete_query = text("DELETE FROM staging.music_data_staging WHERE id = ANY(:ids)")
                    res = await transaction_conn.execute(delete_query, {"ids": to_delete_ids})
                    print(f"  -> Successfully deleted {res.rowcount} duplicate records.")
                    
                # B. Reset scraper collisions
                if to_reset_ids:
                    reset_query = text("""
                        UPDATE staging.music_data_staging
                        SET spotify_id = NULL,
                            spotify_link = NULL,
                            genre = NULL,
                            followers = NULL,
                            popularity = NULL,
                            needs_review = TRUE,
                            profile_picture = NULL
                        WHERE id = ANY(:ids)
                    """)
                    res = await transaction_conn.execute(reset_query, {"ids": to_reset_ids})
                    print(f"  -> Successfully reset {res.rowcount} collided records to queue.")
                    
            print("\n✨ Database sanitation transaction committed successfully! Database is now clean.")
        else:
            print("\n💡 NOTE: This was a PREVIEW. No changes were written to the database.")
            print("To commit these changes, run the script with the '--execute' flag:")
            print("  python scratch/deduplicate_database.py --execute")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean duplicates and collisions in Supabase music staging table.")
    parser.add_argument('--execute', action='store_true', help='Execute the sanitation changes in the database')
    args = parser.parse_args()
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(run_deduplicator(execute=args.execute))
