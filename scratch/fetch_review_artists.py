import os
import sys
import json
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connection import sync_engine

def get_flagged_artists():
    if not sync_engine:
        print("Error: Database engine not initialized.")
        return

    with sync_engine.begin() as conn:
        # Fetch Foreign
        foreign_res = conn.execute(text("SELECT id, artist_name, spotify_link, genre FROM music_data WHERE is_indonesian = FALSE"))
        foreign_artists = [dict(row._mapping) for row in foreign_res.fetchall()]

        # Fetch Uncertain (is_indonesian is NULL)
        uncertain_res = conn.execute(text("SELECT id, artist_name, spotify_link, genre FROM music_data WHERE is_indonesian IS NULL"))
        uncertain_artists = [dict(row._mapping) for row in uncertain_res.fetchall()]

    return foreign_artists, uncertain_artists

if __name__ == "__main__":
    foreign, uncertain = get_flagged_artists()
    
    report_path = os.path.join(os.path.dirname(__file__), "../docs/MANUAL_REVIEW_QUEUE.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 📋 Manual Review Queue: Nationality Validation\n\n")
        f.write("This file contains artists flagged as **Foreign** or **Uncertain** by the automated validator.\n\n")
        
        f.write("## 🌎 Identified Foreign Artists (Potential False Negatives)\n")
        f.write("| ID | Artist Name | Genres | Spotify Link | Action |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for a in foreign:
            genre_str = ", ".join(a['genre']) if a['genre'] else "None"
            link = a['spotify_link'] if a['spotify_link'] else "N/A"
            f.write(f"| {a['id']} | {a['artist_name']} | {genre_str} | [Link]({link}) | [ ] |\n")
            
        f.write("\n## ❓ Uncertain Artists (Requires Manual Check)\n")
        f.write("| ID | Artist Name | Genres | Spotify Link | Action |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for a in uncertain:
            genre_str = ", ".join(a['genre']) if a['genre'] else "None"
            link = a['spotify_link'] if a['spotify_link'] else "N/A"
            f.write(f"| {a['id']} | {a['artist_name']} | {genre_str} | [Link]({link}) | [ ] |\n")

    print(f"Report generated: {report_path}")
