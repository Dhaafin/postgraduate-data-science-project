import os
import sys
import re
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from src.database.connection import sync_engine
from src.utils.geo_constants import is_indonesian_location

class MusicBrainzRefiner:
    def __init__(self):
        self.report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../docs/musicbrainz/FOREIGN_BORN_REPORT.md'))
        self.resolved_count = 0
        self.still_foreign_count = 0
        self.unknown_count = 0

    def parse_report(self):
        """Parse the markdown table in the Foreign Born Report."""
        if not os.path.exists(self.report_path):
            print(f"[!] Report not found at {self.report_path}")
            return []

        with open(self.report_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        extracted_data = []
        # Table rows start after line 6
        for line in lines[6:]:
            if line.strip().startswith("|"):
                # Split and clean parts
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:
                    extracted_data.append({
                        "id": parts[0],
                        "name": parts[1],
                        "country": parts[2],
                        "area": parts[3]
                    })
        return extracted_data

    def parse_manual_queue(self):
        """Parse the existing Manual Origin Queue."""
        manual_path = os.path.abspath(os.path.join(os.path.dirname(self.report_path), 'MANUAL_ORIGIN_QUEUE.md'))
        if not os.path.exists(manual_path):
            return []

        with open(manual_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        extracted_data = []
        # Table rows start after line 6
        for line in lines[6:]:
            if line.strip().startswith("|"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    extracted_data.append({
                        "id": parts[0],
                        "name": parts[1]
                    })
        return extracted_data

    def run(self):
        print("\n" + "="*60)
        print(" MUSICBRAINZ REPORT REFINEMENT (M4)")
        print("="*60)
        
        records = self.parse_report()
        if not records:
            return

        print(f"Analyzing {len(records)} records from the Foreign Born Report...\n")
        
        resolved_list = []
        remaining_foreign = []

        for record in records:
            db_id = record["id"]
            name = record["name"]
            area = record["area"]
            
            if is_indonesian_location(area):
                print(f"  [✓] RESOLVED: {name:<25} -> {area}")
                
                with sync_engine.begin() as conn:
                    conn.execute(
                        text("UPDATE music_data SET is_indonesian = TRUE, origin_city = :city WHERE id = :id"),
                        {"city": area, "id": db_id}
                    )
                self.resolved_count += 1
                resolved_list.append(record)
            else:
                if area == "Unknown":
                    self.unknown_count += 1
                else:
                    self.still_foreign_count += 1
                remaining_foreign.append(record)

        # Get the manual queue to combine
        manual_queue = self.parse_manual_queue()
        
        # Generate the combined master list
        self.write_updated_reports(resolved_list, remaining_foreign, manual_queue)
        
        print("\n" + "="*60)
        print(" REFINEMENT COMPLETE")
        print("="*60)
        print(f"Total Analyzed      : {len(records)}")
        print(f"Moved to Indonesian : {self.resolved_count}")
        print(f"Remaining Foreign   : {self.still_foreign_count}")
        print(f"Still Unknown Area  : {self.unknown_count}")
        print(f"Manual Queue Size   : {len(manual_queue)}")
        print("="*60)

    def write_updated_reports(self, resolved, foreign, manual):
        """Update the reports to reflect the new classification."""
        docs_dir = os.path.dirname(self.report_path)
        
        # 1. Update Foreign Born Report (Only true foreigns)
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write("# Foreign-Born Artist Report (Refined)\n\n")
            f.write("Artists flagged as non-Indonesian. Verified to NOT have Indonesian origin strings.\n\n")
            f.write("| Database ID | Artist Name | MB Country | Begin Area |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for item in foreign:
                f.write(f"| {item['id']} | {item['name']} | {item['country']} | {item['area']} |\n")

        # 2. Create the Master Geocoding Queue (Combined)
        master_path = os.path.join(docs_dir, "FINAL_GEO_ENRICHMENT_QUEUE.md")
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("# Final Geo-Enrichment Master Queue\n\n")
            f.write("Combined list of rescued Indonesian artists and manual research requirements. Fill empty cities before geocoding.\n\n")
            f.write("| Database ID | Artist Name | Origin City (Manual/MB) | Source Status |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            
            # Add Rescued Artists first
            for item in resolved:
                f.write(f"| {item['id']} | {item['name']} | {item['area']} | MB_RESCUED |\n")
                
            # Add Manual Queue Artists
            for item in manual:
                f.write(f"| {item['id']} | {item['name']} |  | MANUAL_PENDING |\n")
        
        print(f"\n[+] Updated {self.report_path}")
        print(f"[+] Generated {master_path}")

if __name__ == "__main__":
    MusicBrainzRefiner().run()
