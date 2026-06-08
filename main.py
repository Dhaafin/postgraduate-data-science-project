"""
Orchestrator for the Spatial Analytics Data Pipeline
Provides an interactive menu and a robust `--ingest` CLI for seamless database expansion.
"""

import sys
import argparse
import asyncio
from src.scrapers.discovery.discovery import fetch_viberate_artists
from src.scrapers.discovery.musicbrainz import MusicBrainzDiscovery
from src.scrapers.enrichment.enrichment import run_spotify_enrichment
from src.scrapers.validation.nationality_validator import NationalityValidator
from src.scrapers.origin.musicbrainz import MusicBrainzEnrichment
from src.scrapers.origin.wikipedia import WikipediaSweeper
from src.scrapers.origin.normalizer import GeoNormalizer
from src.database.operations import insert_seed_artist_sync

def run_ingestion_pipeline(artist_name):
    """
    Executes the end-to-end ingestion pipeline for a single new artist.
    Seed -> Enrich -> Validate -> Origin Resolve -> Normalize
    """
    print("="*60)
    print(f" END-TO-END INGESTION PIPELINE: '{artist_name}'")
    print("="*60)
    
    print("\n[Step 1/5] Seeding Database...")
    db_id = insert_seed_artist_sync(artist_name)
    if not db_id:
        print("Failed to insert seed. Aborting.")
        return
    print(f" -> Artist seeded successfully with ID {db_id}.")
    
    print("\n[Step 2/5] Spotify Enrichment...")
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_spotify_enrichment())
    
    print("\n[Step 3/5] Nationality Validation...")
    NationalityValidator().run_validation()
    
    print("\n[Step 4/5] Origin Discovery...")
    # Wikipedia gets highest precision for Indo artists
    sweeper = WikipediaSweeper()
    sweeper.run_origin_sweep()
    sweeper.run_type_sweep()
    # MusicBrainz for fallbacks
    MusicBrainzEnrichment().run()
    
    print("\n[Step 5/5] Geo-Normalization...")
    GeoNormalizer().run(dry_run=False)
    
    print("\n" + "="*60)
    print(f" PIPELINE COMPLETE FOR '{artist_name}'")
    print("="*60)

def display_menu():
    print("\n" + "="*60)
    print(" INDONESIAN MUSIC SPATIAL ANALYTICS PIPELINE")
    print("="*60)
    print("1. Discover New Artists (Viberate Charts)")
    print("2. Discover New Artists (MusicBrainz Deep Search)")
    print("3. Enrich Missing Spotify Metadata")
    print("4. Run Nationality Validation (Hybrid)")
    print("5. Resolve Missing Origins (Wikipedia + MusicBrainz)")
    print("6. Standardize Geolocation Hierarchy")
    print("7. Execute Full End-to-End Database Sweep")
    print("0. Exit")
    print("="*60)
    
    choice = input("\nEnter choice [0-7]: ")
    return choice

def main():
    parser = argparse.ArgumentParser(description="Data Ingestion and Processing Pipeline")
    parser.add_argument("--ingest", type=str, help="Run end-to-end ingestion for a single artist")
    args = parser.parse_args()

    if args.ingest:
        run_ingestion_pipeline(args.ingest)
        return

    while True:
        choice = display_menu()
        
        if choice == '0':
            print("Exiting pipeline. Goodbye!")
            break
        elif choice == '1':
            pages = input("Enter page indices to scrape (comma separated, e.g., 0,1,2): ")
            try:
                page_list = [int(p.strip()) for p in pages.split(',')]
                artists = fetch_viberate_artists(page_indices=page_list)
                for a in artists:
                    insert_seed_artist_sync(a)
                print(f"Successfully discovered and seeded {len(artists)} artists.")
            except ValueError:
                print("Invalid input. Please provide comma-separated integers.")
        elif choice == '2':
            pages = input("Enter max pages to pull from MusicBrainz (100 results per page, e.g., 5): ")
            try:
                max_pages = int(pages.strip())
                # Step 1: Run in preview mode
                preview_list = MusicBrainzDiscovery().run_discovery(max_pages=max_pages, dry_run=True)
                
                if not preview_list:
                    print("No artists with locations found.")
                    continue
                    
                # Step 2: Prompt for confirmation
                confirm = input(f"\nFound {len(preview_list)} artists with valid locations. Insert into database? (y/n): ")
                if confirm.lower() == 'y':
                    from src.database.operations import insert_musicbrainz_seed_sync
                    total_inserted = 0
                    for a in preview_list:
                        db_id = insert_musicbrainz_seed_sync(a["name"], a["type"], a["city"], a["prov"])
                        if db_id:
                            total_inserted += 1
                    print(f"\nSuccessfully inserted {total_inserted} new artists!")
                else:
                    print("Ingestion cancelled.")
                    
            except ValueError:
                print("Invalid input. Please provide an integer.")
        elif choice == '3':
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.run(run_spotify_enrichment())
        elif choice == '4':
            NationalityValidator().run_validation()
        elif choice == '5':
            WikipediaSweeper().run_origin_sweep()
            WikipediaSweeper().run_type_sweep()
            MusicBrainzEnrichment().run()
        elif choice == '6':
            GeoNormalizer().run(dry_run=False)
        elif choice == '7':
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.run(run_spotify_enrichment())
            NationalityValidator().run_validation()
            WikipediaSweeper().run_origin_sweep()
            WikipediaSweeper().run_type_sweep()
            MusicBrainzEnrichment().run()
            GeoNormalizer().run(dry_run=False)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
