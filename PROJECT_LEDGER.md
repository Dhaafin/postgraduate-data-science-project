# PROJECT LEDGER: Digital Inequality in Indonesian Music

## 🎯 COMMANDER'S INTENT (CCI)

**Vision**: An end-to-end spatial analytics platform investigating "Jakarta-centrism" in the Indonesian music industry. By quantifying Spotify metrics against geographic origins, we aim to verify if digital platforms have truly "democratized" music distribution.

**Core Constraints**:

- **Pipeline**: Python (Asyncio/Playwright) for ETL.
- **Spatial**: Pandas/GeoPandas for regional hub analysis.
- **Stack**: Next.js (Frontend) + Express (API) + PostgreSQL (Supabase).
- **Ops**: Dockerized deployment with Cloudflare/Cloudinary asset management.

---

## 🗺️ MILESTONE ROADMAP

| ID  | Milestone          |   Status   | Details                                                            |
| :-- | :----------------- | :--------: | :----------------------------------------------------------------- |
| M1  | Core ETL Engine    | [Complete] | Async infrastructure & DB Schema.                                  |
| M2  | Source 1: Viberate | [Complete] | Expanded pool to 600 candidates (Pages 0 & 1).                     |
| M3  | Source 2: Spotify  | [Complete] | Re-scraped 600 records with Weighted Scoring & Profile Pics. |
| M4  | Geo-Enrichment     |  [Active]  | Validating nationality and extracting Origin City/Province.        |
| M5  | Spatial Analytics  | [Pending]  | GeoPandas analysis of regional density & genre hubs.               |
| M6  | Web Dashboard      | [Pending]  | Next.js / Express interactive spatial map.                         |
| M7  | Deployment         | [Pending]  | Dockerization and Cloud Infrastructure setup.                      |

---

## 🛠️ ACTIVE FEATURE: M4 - Multi-Source Geo-Enrichment (MusicBrainz Pivot)

> **Objective**: Identify "Origin City" using a Provenance-First model to quantify Jakarta-centric migration.

- [x] **DB Schema Expansion**: Add `artist_type`, `origin_city`, `origin_province`, `latitude`, and `longitude` columns.
- [x] **Nationality Validation**: Tier 1 (Spotify) & Tier 2 (Wiki Keywords) complete.
- [x] **MusicBrainz Origin Scraper**: 
    - [x] **Sprint 4.1 (API Spike)**: Validated MusicBrainz payload accuracy.
    - [x] **Sprint 4.2 (Extraction Engine)**: Built `musicbrainz_enrichment.py` with 2s rate limit.
    - [x] **Sprint 4.2.1 (City Validator)**: Implemented `geo_constants.py` and `refine_musicbrainz_reports.py` for semantic recovery.
    - [x] **Sprint 4.3 (Execution & Manual Review)**: Built `01_wikipedia_origin_sweep.py` and `02_wikipedia_type_sweep.py` for automated enrichment.
- [ ] **Geocoding Implementation**: Batch process `origin_city` via Nominatim for spatial coordinates.
- [x] **Target**: Reach 500+ "Clean" records for final spatial analysis.

---

## 📓 RESEARCH PARKING LOT (Future Architectural Problems)

- [ ] **The "Migration" Disambiguation**: Cross-reference `Birthplace` with `Active City` to quantify the "Jakarta Drain."
- [ ] **Temporal Correlation**: Correlate "Spotify Breakthrough" date with "Migration Year" to assess digital democratization vs. legacy networks.
- [ ] **Genre-Location Variance**: Analyze if certain genres (e.g., Koplo) are more resistant to Jakarta migration than others (e.g., Pop).
- [ ] **Industrial Artifacts vs Talent**: Define exclusionary criteria for "Brand Artists" (children's IPs, corporate lo-fi).

---

| 2026-05-16 |   Dev   | feat: implement wikipedia artist-type classification sweep | Developed `02_wikipedia_type_sweep.py` to classify records as Person/Group using Wikipedia infoboxes. |
| 2026-05-16 |   Dev   | fix: implement rate-limit handling and retries for wiki sweep | Developed defensive scraping logic to handle HTTP 429 errors in Wikipedia pipelines. |
| 2026-05-16 |   Dev   | feat: implement wikipedia origin sweep pipeline | Developed `01_wikipedia_origin_sweep.py` to automate origin extraction from Wikipedia infoboxes for staging data. |
| 2026-05-16 |   PM    | status: Supabase Migration Complete | Successfully migrated from Neon to Supabase. Aligned all scripts to target `staging.music_data_staging`. |
| 2026-05-16 |   Dev   | feat: consolidate enrichment master queue | Updated `refine_musicbrainz_reports.py` to merge rescued artists and manual queues into `FINAL_GEO_ENRICHMENT_QUEUE.md`. |
| 2026-05-16 |   Dev   | feat: implement semantic city validation | Created `geo_constants.py` and `refine_musicbrainz_reports.py` to recover Indonesian artists from MB foreign reports. |
| 2026-05-16 |   Dev   | refactor: move MusicBrainz reports to dedicated subdirectory | Reorganized `docs/` by moving MusicBrainz reports to `docs/musicbrainz/` and updating the scraper. |
| 2026-05-11 |   Dev   | feat: build musicbrainz extraction engine | Developed `musicbrainz_enrichment.py` with strict rate limiting and dual reporting logic for manual reviews. |
| 2026-05-11 |   PM    | Strategic Pivot: MusicBrainz First | Abandoned Wikipedia scraping in favor of MusicBrainz API due to superior data structure. |
| 2026-05-11 |   Dev   | fix: add ux progress indicator to test script | Added carriage return progress indicator to prevent perceived script freezing during MusicBrainz rate limiting. |
| 2026-05-11 |   Dev   | test: implement 50-record musicbrainz api scalability test | Created spike script to validate MusicBrainz data structure for artist origin extraction. |
| 2026-05-08 |   Dev   | fix: wiki discovery v3 | Implemented Expert Mode with substring matching, randomized jitter, and 429 auto-retry logic. |
| 2026-05-08 |   Dev   | fix: wiki discovery v2 | Refactored discovery to use Opensearch and Similarity checking to eliminate false positives. |
| 2026-05-08 |   Dev   | feat: wikipedia discovery pipeline | Implemented Sprint 4.1 (Wikidata Bridge + Anchored Search) to map artist IDs to Wiki URLs. |
| 2026-05-08 |   PM    | Strategic Pivot: Provenance First   | Decided on Option A: Solo=Birthplace, Band=Formation to preserve the "Original Location" signal against Jakarta-centrism. |
| 2026-05-04 |   Dev   | feat: data hygiene purge utility    | Built script to remove foreign artists and records without genres. |
| 2026-05-04 |   Dev   | fix: sync script import paths       | Resolved ModuleNotFoundError by adding root to sys.path. |
| 2026-05-04 |   Dev   | feat: manual validation sync utility | Implementation of 4th column parsing to sync report overrides to Postgres. |
| 2026-05-03 |   Dev   | docs: separate foreign vs uncertain | Split `ARTIST_VALIDATION_REPORT.md` into dedicated sections for Foreign and Uncertain. |
| 2026-05-03 |   Dev   | feat: automated validation reporting | Added markdown report generation to `NationalityValidator` to track auditing logic in `docs/`.            |
| 2026-05-03 |   Dev   | feat: integrate nationality validator| Integrated `NationalityValidator` into `main.py` with CLI and Interactive Menu support.                   |
| 2026-05-03 |   PM    | status: M3 Spotify Recovery Complete | Successfully re-scraped 600 artists using Weighted Similarity Scoring and added Profile Pictures.         |
| 2026-05-03 |   Dev   | refactor: secure main.py db inserts  | Switched to kwargs for `insert_artist_data` to handle schema expansion safely.                            |
| 2026-05-03 |   Dev   | feat: profile picture integration    | Added `profile_picture` column and extraction logic to Spotify scraper.                                   |
| 2026-05-02 |   Dev   | refactor: browser engine swap        | Restored Firefox/Chromium stability for Playwright sessions.                                              |
| 2026-05-02 |   PM    | Strategic Pivot: Clean Slate         | Initiated full scrub of Spotify/Nationality data due to previous logic failures.                         |
| 2026-05-02 |   Dev   | feat: weighted similarity scoring    | Implemented robust scoring to prevent false positive matches for global stars.                            |
| 2026-05-01 |   PM    | task: manual review queue            | Generated `docs/MANUAL_REVIEW_QUEUE.md` for 82 ambiguous records.                                         |
| 2026-05-01 |   PM    | doc: artist validation report        | Formalized 516 validated records in `docs/ARTIST_VALIDATION_REPORT.md`.                                   |
| 2026-04-30 |   PM    | Status Report: Validation Complete   | 516 artists successfully validated. Exceeded target of 400 clean records.                                 |
| 2026-04-30 |   Dev   | fix: validator rate limits & genres  | Added delay to prevent HTTP 429 and expanded Indo-specific genre keywords.                                |
| 2026-04-30 |   Dev   | feat: metadata validator v3          | Implemented Spotify genre-first logic, improving accuracy to ~80%.                                        |
| 2026-04-30 |   Dev   | fix: database schema migration       | Fixed brittle column detection in `init_db`.                                                              |
| 2026-04-30 |   Dev   | feat: nationality flagging logic     | Replaced hard-purge with safe flagging using `is_indonesian` column.                                      |
| 2026-04-30 |   Dev   | feat: nationality purge auditor      | Built `nationality_purge.py` to automate noise reduction.                                                 |
| 2026-04-27 |   Dev   | feat: NLP dom scanning fallback      | Built `re` based NLP extraction for missing infoboxes on Wikipedia.                                       |
| 2026-04-26 |   Dev   | feat: geocoding pipeline             | Built `geo_pipeline.py` fusing Wikipedia scraper with Nominatim coordinates.                              |
| 2026-04-26 |   Dev   | feat: db schema expansion            | Refactored `music_data` table to include geospatial and province fields.                                  |
| 2026-04-26 |   PM    | Pivot to Spatial Analysis            | Updated Ledger to align with PRD focused on "Jakarta-centrism".                                           |

---

## 🚩 PM STATUS: GREEN

**Next Immediate Step**: Process `docs/musicbrainz/FINAL_GEO_ENRICHMENT_QUEUE.md` and initiate the Geocoding pipeline.
