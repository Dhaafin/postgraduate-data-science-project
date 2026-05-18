import sys
import os
sys.path.append('c:\\[Dhaafin]\\Projects\\Personal Projects\\data-scraping')
from src.scrapers.discovery.musicbrainz import MusicBrainzDiscovery

disc = MusicBrainzDiscovery()
preview = disc.run_discovery(max_pages=1, dry_run=True)

with open('C:\\Users\\Dhaafin\\.gemini\\antigravity\\brain\\13c51717-40fe-4f3a-91da-f3a3a85f04af\\musicbrainz_preview.md', 'w', encoding='utf-8') as f:
    f.write('# MusicBrainz Dry Run Preview\n\n')
    f.write('| Artist Name | Type | Origin City |\n')
    f.write('|---|---|---|\n')
    for a in preview:
        name = a.get("name", "Unknown")
        atype = a.get("type", "Unknown")
        city = a.get("city", "Unknown")
        f.write(f'| {name} | {atype} | {city} |\n')
print('Preview saved!')
