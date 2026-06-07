import os
import sys
import argparse
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine
from src.utils.genre_mapper import resolve_primary_genre

def run_mapping(dry_run=True):
    if not sync_engine:
        print("Database connection failed.")
        return
        
    print(f"\n--- [GENRE BACKFILL V2 PIPELINE {'(DRY RUN)' if dry_run else '(LIVE EXECUTION)'}] ---")
    
    with sync_engine.begin() as conn:
        # Get all artists with genres
        all_query = text("SELECT id, artist_name, genre FROM staging.music_data_staging ORDER BY id ASC")
        records = conn.execute(all_query).fetchall()
        
        print(f"Loaded {len(records)} artists from database.")
        
        mapped_counts = {}
        updates = []
        
        # We will keep track of specific edge cases to print them for verification
        target_artists = ["Tipe-X", "Souljah", "SHAGGY DOG", "Dhyo Haw", "Glenn Fredly", "Lyodra", "Rizky Febian", "Stand Here Alone", "Superman Is Dead"]
        resolved_targets = []
        
        for r in records:
            db_id = r[0]
            artist_name = r[1]
            raw_genres = r[2]
            
            resolved = resolve_primary_genre(raw_genres)
            
            # Keep counts
            status_label = resolved if resolved else "NULL (No Genre)"
            mapped_counts[status_label] = mapped_counts.get(status_label, 0) + 1
            
            # Check edge cases
            if artist_name in target_artists:
                resolved_targets.append((artist_name, raw_genres, resolved))
                
            updates.append({"id": db_id, "primary_genre": resolved})
            
        # Display edge case verification
        print("\n--- EDGE CASE VERIFICATION ---")
        print("-" * 110)
        print(f"{'Artist Name':<25} | {'Raw Genre Tags':<50} | {'Primary Parent Genre':<30}")
        print("-" * 110)
        for s in resolved_targets:
            raw_str = str(s[1])[:48] + '...' if len(str(s[1])) > 50 else str(s[1])
            resolved_str = s[2] if s[2] else "NULL"
            print(f"{s[0]:<25} | {raw_str:<50} | {resolved_str:<30}")
        print("-" * 110)
        
        # Display stats
        print("\n--- NEW GENRE DISTRIBUTION STATS ---")
        print(f"{'Parent Genre':<35} | {'Artist Count':<12}")
        print("-" * 52)
        sorted_stats = sorted(mapped_counts.items(), key=lambda x: x[1], reverse=True)
        for genre, count in sorted_stats:
            print(f"{genre:<35} | {count:<12}")
        print("-" * 52)
        
        if not dry_run:
            print(f"\nExecuting updates for {len(updates)} records...")
            update_query = text("""
                UPDATE staging.music_data_staging 
                SET primary_genre = :primary_genre 
                WHERE id = :id
            """)
            conn.execute(update_query, updates)
            print("Successfully updated database records in Supabase staging schema!")
        else:
            print("\nDry-run complete. No database changes were made.")
            
    print("=" * 60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill V2 Primary Genre mapping for existing database records.")
    parser.add_argument("--execute", action="store_true", help="Run the actual database updates (default is dry-run)")
    args = parser.parse_args()
    
    run_mapping(dry_run=not args.execute)
