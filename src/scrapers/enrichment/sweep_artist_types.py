"""
Wikipedia Artist-Type Sweep Tool

Specifically runs the artist_type sweep (Person/Group) using Wikipedia 
without running the origin/location sweep pipeline.
"""

import os
import sys

# Add project root to sys.path to ensure modules can be imported correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(project_root)

from src.scrapers.origin.wikipedia import WikipediaSweeper

def main():
    print("=" * 60)
    print(" STARTING: Isolated Wikipedia Artist-Type Sweep")
    print("=" * 60)
    try:
        sweeper = WikipediaSweeper()
        sweeper.run_type_sweep()
    except KeyboardInterrupt:
        print("\n[!] Sweep aborted by user.")
    except Exception as e:
        print(f"\n[!] An error occurred during the sweep: {e}")
    print("=" * 60)
    print(" PROCESS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    # Ensure stdout handles UTF-8 output nicely on Windows terminals
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    main()
