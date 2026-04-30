# PROJECT LEDGER: Digital Inequality in Indonesian Music

## 🎯 COMMANDER'S INTENT (CCI)

**Vision**: An end-to-end spatial analytics platform investigating "Jakarta-centrism" in the Indonesian music industry. By quantifying Spotify metrics against geographic origins, we aim to verify if digital platforms have truly "democratized" music distribution.

**Core Constraints**:

- **Pipeline**: Python (Asyncio/Playwright) for ETL.
- **Spatial**: Pandas/GeoPandas for regional hub analysis.
- **Stack**: Next.js (Frontend) + Express (API) + PostgreSQL (Neon).
- **Ops**: Dockerized deployment with Cloudflare/Cloudinary asset management.

---

## 🗺️ MILESTONE ROADMAP

| ID  | Milestone          |   Status   | Details                                                            |
| :-- | :----------------- | :--------: | :----------------------------------------------------------------- |
| M1  | Core ETL Engine    | [Complete] | Async infrastructure & DB Schema.                                  |
| M2  | Source 1: Viberate | [Complete] | Expanded pool to 600 candidates (Pages 0 & 1).                     |
| M3  | Source 2: Spotify  |  [Active]  | Enriching popularity & metadata for 600 candidates.                |
| M4  | Geo-Enrichment     |  [Active]  | Nationality Validation (Flagging) followed by Wiki/Geo mapping.            |
| M5  | Spatial Analytics  | [Pending]  | GeoPandas analysis of regional density & genre hubs.               |
| M6  | Web Dashboard      | [Pending]  | Next.js / Express interactive spatial map.                         |
| M7  | Deployment         | [Pending]  | Dockerization and Cloud Infrastructure setup.                      |

---

## 🛠️ ACTIVE FEATURE: M4 - Wikipedia/Wikidata Geo-Coding & Validation

> **Objective**: Identify "Origin City" and enforce strict data hygiene by purging non-Indonesian and corporate records.

- [x] **DB Schema Expansion**: Add `origin_city`, `origin_province`, `latitude`, and `longitude` columns.
- [x] **Viberate Expansion**: Refactor `viberate.py` to collect 600 candidates.
- [ ] **Spotify Enrichment**: Process 300+ new records with empty `spotify_link`.
- [x] **Nationality Validation (Flagging)**: Create `nationality_validator.py` to flag `is_indonesian` status.
- [ ] **Wiki/Geo Scraper**: Refine extraction for remaining valid 400 records.
- [ ] **Target Target**: Reach 350-400 "Clean" records for final spatial analysis.

---

## 📓 RESEARCH PARKING LOT (Future Architectural Problems)

_These items are high-priority for the research thesis but deferred until M4 baseline data is collected._

- [ ] **The "Migration" Disambiguation**: Define logic to handle artists who were born in Region A but moved/formed in Jakarta.
- [ ] **Temporal Correlation**: Correlate "Spotify Breakthrough" date with "Migration Year" to assess digital democratization vs. legacy networks.
- [ ] **Genre-Location Variance**: Analyze if certain genres (e.g., Koplo) are more resistant to Jakarta migration than others (e.g., Pop).
- [ ] **Industrial Artifacts vs Talent**: Define exclusionary criteria for "Brand Artists" (children's IPs, corporate lo-fi) to refine the spatial inequality signal.

---

## 📝 CHRONOLOGICAL ACTIVITY LOG

| Timestamp  | Persona | Action                               | Impact                                                                                                    |
| :--------- | :-----: | :----------------------------------- | :-------------------------------------------------------------------------------------------------------- |
| 2026-04-30 | Dev | feat: limit validator prototype to 100 | Capping nationality scan at 100 records for initial high-accuracy testing. |
| 2026-04-30 | Dev | fix: enhance nationality validator v2 | Expanded keywords, added multi-paragraph scan, and robust JSON error handling. |
| 2026-04-30 | Dev | fix: restore update_spotify_id function | Resolved ImportError in scraper by restoring the asynchronous update function. |
| 2026-04-30 | Dev | fix: robust database schema migration | Fixed brittle column detection and schema-aware existence checks in `init_db`. |
| 2026-04-30 | Dev | feat: nationality flagging logic | Pivoted from hard-purge to a safer flagging system using `is_indonesian` column. |
| 2026-04-30 |   Dev   | feat: implement nationality purge auditor | Built `nationality_purge.py` to automate the deletion of non-Indonesian/Corporate records. |
| 2026-04-30 |   PM    | Strategic Pivot: Purge Batch         | Decided to run a standalone `nationality_purge.py` script before geo-enrichment to clean the 600-artist pool. |
| 2026-04-30 |   PM    | Status Report: M3 Complete           | Spotify enrichment finalized for 600 artists. Transitioning to 'The Purge' (M4).                          |
| 2026-04-30 |   Dev   | feat: multi-page viberate extraction | Scaled Viberate pool to 600 candidates by integrating Page 0 and Page 1.                                  |
| 2026-04-30 |   PM    | Strategic Pivot: Purge & Expand      | Re-opened M2; pivoting M4 to include "The Purge" (deletion of noise) to target 350-400 clean records.     |
| 2026-04-27 |   Dev   | feat: NLP dom scanning fallback      | Built `re` based NLP extraction parsing the first 5 paragraphs if the infobox is missing or empty.        |
| 2026-04-27 |   Dev   | fix: province-only fallback          | Implemented fallback assigning province values to city nulls for isolated geodata (e.g., Bali).           |
| 2026-04-27 |   PM    | Strategic Pivot: Entity Type         | Flagged corporate IPs (Baba Lili Tata) as data noise; added task to distinguish human talent from brands. |
| 2026-04-26 |   PM    | End of Session Briefing              | Logged remaining parsing bugs; pipeline architecture is operational for M4.                               |
| 2026-04-26 |   Dev   | feat: geocoding pipeline             | Built `geo_pipeline.py` fusing Wikipedia scraper with Nominatim coordinates.                              |
| 2026-04-26 |   Dev   | feat: wiki scraper prototype         | Developed MediaWiki API integration for city/province extraction.                                         |
| 2026-04-26 |   Dev   | feat: db schema expansion            | Refactored `music_data` table to include geospatial and province fields.                                  |
| 2026-04-26 |   PM    | Pivot to Spatial Analysis            | Updated Ledger to align with PRD focused on "Jakarta-centrism".                                           |
| 2026-04-26 |   Dev   | fix: spotify event loop              | Resolved Windows-specific async concurrency issues.                                                       |
| 2026-04-26 |   Dev   | feat: spotify_search_scraper.py      | Added browser-based popularity extraction.                                                                |

---

## 🚩 PM STATUS: GREEN

**Next Immediate Step**: Run `python src/scrapers/nationality_purge.py` to clean the database.
