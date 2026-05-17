import asyncio
import os
import sys
import re
from sqlalchemy import text

# Add project root and normalizer paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/scrapers/origin/02_normalizer')))
from src.database.connection import sync_engine
from geo_normalizer import GeoNormalizer

def inspect_and_simulate():
    if not sync_engine:
        print("[!] Sync engine not initialized")
        return
        
    report_lines = []
    report_lines.append("--- [PEEKING SUPABASE & SIMULATING GEO-NORMALIZATION] ---")
    
    # 1. Fetch all records from staging table
    with sync_engine.begin() as conn:
        query = text("""
            SELECT id, artist_name, origin_city, origin_province 
            FROM staging.music_data_staging 
            ORDER BY id
        """)
        records = conn.execute(query).fetchall()
        
    normalizer = GeoNormalizer()
    
    total_records = len(records)
    with_city_or_prov = 0
    would_be_updated = 0
    unmapped_cities = set()
    
    report_lines.append(f"Total records in staging.music_data_staging: {total_records}\n")
    header = f"{'ID':<5} | {'Artist Name':<30} | {'Raw City':<40} | {'Raw Prov':<20} | {'Normalized City':<40} | {'Normalized Prov':<20} | {'Status':<10}"
    report_lines.append(header)
    report_lines.append("-" * 175)
    
    for r in records:
        db_id, name, city, province = r
        if not city and not province:
            continue
            
        with_city_or_prov += 1
        new_city, new_prov = normalizer.normalize(city, province)
        
        changed = (new_city != city) or (new_prov != province)
        status = "CHANGED" if changed else "OK"
        if changed:
            would_be_updated += 1
            
        row_str = f"{db_id:<5} | {name[:30]:<30} | {str(city)[:40]:<40} | {str(province)[:20]:<20} | {str(new_city)[:40]:<40} | {str(new_prov)[:20]:<20} | {status:<10}"
        report_lines.append(row_str)
        
        # Track unmapped cities (where normalized city is not None and province is not filled)
        if new_city and not new_prov:
            unmapped_cities.add(new_city)
            
    report_lines.append("\n" + "="*80)
    report_lines.append(" SUMMARY STATISTICS")
    report_lines.append("="*80)
    report_lines.append(f"Total Staging Records           : {total_records}")
    report_lines.append(f"Records with Geo Data           : {with_city_or_prov}")
    report_lines.append(f"Records that would be updated   : {would_be_updated}")
    report_lines.append(f"Records remaining unchanged     : {with_city_or_prov - would_be_updated}")
    
    if unmapped_cities:
        report_lines.append("\n[WARNING] Cities that could not be mapped to any Province:")
        for uc in sorted(unmapped_cities):
            report_lines.append(f" - {uc}")
    else:
        report_lines.append("\n[SUCCESS] All populated cities successfully mapped to a Province!")
    report_lines.append("="*80 + "\n")
    
    # Write full report to file
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'normalization_simulation_report.txt'))
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print(f"\n[+] Simulation run complete. Report saved to: {report_path}")
    print(f"Total records processed: {with_city_or_prov}")
    print(f"Updates simulated: {would_be_updated}")
    print(f"Unmapped cities: {len(unmapped_cities)}")

if __name__ == "__main__":
    inspect_and_simulate()
