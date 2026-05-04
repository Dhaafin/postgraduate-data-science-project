import os
import sys
from sqlalchemy import text

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database.connection import sync_engine

def purge_records():
    """
    Data Hygiene Utility: Identifies and removes invalid artist records.
    Criteria: 
    1. Confirmed Foreign (is_indonesian = FALSE)
    2. Missing Metadata (No genres)
    """
    # Using 'is_indonesian = FALSE' specifically removes those tagged manually or by script.
    # 'NULL' records are left alone as they might still be Indonesian.
    purge_criteria = {
        "Confirmed Foreign Artists": "is_indonesian = FALSE",
        "Records with No Genre Data": "genre IS NULL OR cardinality(genre) = 0"
    }

    if not sync_engine:
        print("Error: Database engine not initialized.")
        return

    with sync_engine.begin() as conn:
        print("\n" + "="*50)
        print("      DATA HYGIENE AUDIT: DATABASE PURGE")
        print("="*50 + "\n")
        
        total_to_delete = 0
        impact_summary = []
        
        for label, condition in purge_criteria.items():
            count = conn.execute(text(f"SELECT COUNT(*) FROM music_data WHERE {condition}")).scalar()
            print(f"🔍 {label:<28}: {count} records found.")
            if count > 0:
                impact_summary.append((label, condition, count))
                total_to_delete += count
            
        if total_to_delete == 0:
            print("\n✅ Database is clean. No records match the purge criteria.")
            return

        print(f"\n⚠️ WARNING: You are about to permanently delete {total_to_delete} records.")
        confirm = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
        
        if confirm == 'y':
            for label, condition, count in impact_summary:
                res = conn.execute(text(f"DELETE FROM music_data WHERE {condition}"))
                print(f"   - Deleted {res.rowcount} {label}.")
            print("\n✨ Database Purge Complete.")
        else:
            print("\n❌ Operation cancelled by user. No changes made.")

if __name__ == "__main__":
    try:
        purge_records()
    except KeyboardInterrupt:
        print("\n\nProcess stopped by user.")
    except Exception as e:
        print(f"\nFatal error during purge: {e}")
