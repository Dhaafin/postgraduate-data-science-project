import os
import sys
import re
from sqlalchemy import text

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database.connection import sync_engine, update_nationality_sync

# Configuration
REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../docs/ARTIST_VALIDATION_REPORT.md'))

def sync_from_markdown():
    """
    Parses the ARTIST_VALIDATION_REPORT.md file and updates the database
    based on manual overrides found in the 4th column (--Indonesia/--Foreign).
    """
    if not os.path.exists(REPORT_PATH):
        print(f"Error: Report not found at {REPORT_PATH}")
        return

    print(f"Reading manual validations from {REPORT_PATH}...")
    
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updates = 0
    overrides = 0
    
    # Regex to match the table row and capture:
    # 1. Artist Name
    # 2. Automated Status (for context/logging)
    # 3. Manual Override Tag (--Indonesia or --Foreign)
    # Pattern looks for: | Name | Status | Reason | --Override |
    pattern = re.compile(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*--(.*?)\s*\|")

    print("\n" + "="*60)
    print(f"{'ARTIST NAME':<25} | {'AUTO':<10} | {'MANUAL SYNC'}")
    print("="*60)

    for line in lines:
        match = pattern.search(line)
        if match:
            artist_name = match.group(1).strip()
            auto_status = match.group(2).strip()
            manual_tag = match.group(4).strip().lower()
            
            # Logic: If manual tag exists, it overrides everything.
            if 'indonesia' in manual_tag:
                is_indonesian = True
                status_label = "🇮🇩 INDO"
            elif 'foreign' in manual_tag:
                is_indonesian = False
                status_label = "🌎 FOREIGN"
            else:
                continue # No recognized tag

            # Database Update
            with sync_engine.connect() as conn:
                # Find the record
                result = conn.execute(
                    text("SELECT id, is_indonesian FROM music_data WHERE artist_name = :name"),
                    {"name": artist_name}
                ).fetchone()
                
                if result:
                    db_id, current_val = result
                    
                    # Check if an update is actually needed (don't write if same)
                    if current_val != is_indonesian:
                        update_nationality_sync(db_id, is_indonesian)
                        print(f"{artist_name:<25} | {auto_status:<10} | -> {status_label}")
                        updates += 1
                        
                        # Log as override if auto status was different
                        if (is_indonesian and "FOREIGN" in auto_status) or (not is_indonesian and "INDO" in auto_status):
                            overrides += 1
                    else:
                        # Already synced
                        pass
                else:
                    print(f"Warning: Artist '{artist_name}' not found in database.")

    print("="*60)
    print(f"\n✅ Synchronization Summary:")
    print(f"  - Database Updates: {updates}")
    print(f"  - Manual Overrides Applied: {overrides}")
    print(f"  - Status: M4 Nationality Validation Finalized.")

if __name__ == "__main__":
    sync_from_markdown()
