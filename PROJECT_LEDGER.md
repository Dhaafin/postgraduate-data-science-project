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
| M3  | Source 2: Spotify  |  [Active]  | **RESET**: Re-scraping 600 records with Weighted Scoring.  |
| M4  | Geo-Enrichment     |  [Active]  | **RESET**: Re-validating nationality after Spotify scrub.       |
| M5  | Spatial Analytics  | [Pending]  | GeoPandas analysis of regional density & genre hubs.               |
| M6  | Web Dashboard      | [Pending]  | Next.js / Express interactive spatial map.                         |
| M7  | Deployment         | [Pending]  | Dockerization and Cloud Infrastructure setup.                      |

---

## 🛠️ ACTIVE FEATURE: M4 - Wikipedia/Wikidata Geo-Coding & Validation

> **Objective**: Identify "Origin City" and enforce strict data hygiene by purging non-Indonesian and corporate records.

- [x] **DB Schema Expansion**: Add `origin_city`, `origin_province`, `latitude`, and `longitude` columns.
- [x] **Viberate Expansion**: Refactor `viberate.py` to collect 600 candidates.
- [ ] **Spotify Enrichment**: **RE-RUNNING** with Weighted Similarity Scoring.
- [x] **Spotify Enrichment**: Add profile picture extraction to database.
- [ ] **Nationality Validation**: **RE-RUNNING** after Spotify data recovery.
- [ ] **Documentation**: `docs/ARTIST_VALIDATION_REPORT.md` is currently STALE.
- [ ] **Wiki/Geo Scraper**: Blocked until M3/M4 recovery.
- [ ] **Target Target**: Reach 500+ "Clean" records for final spatial analysis.

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
| Timestamp | Persona | Action | Impact |
|:---|:---:|:---|:---|
| 2026-05-03 | Dev | feat: add profile picture extraction to spotify scraper and db | Added `profile_picture` column to schema and updated Playwright scraper to extract API image URLs. |
| 2026-05-02 | Dev | refactor: revert to firefox engine | Restored Firefox as the primary browser for Playwright. |
| 2026-05-02 | Dev | fix: resolve browser crash & Layer 2 | Switched to Chromium and implemented Follower Cap filter for robust validation. |
| 2026-05-02 | PM | Strategic Pivot: Clean Slate Recovery | Initiated full scrub of Spotify/Nationality data due to scraper logic failure. |
| 2026-05-02 | Dev | fix: implement weighted similarity scoring | Refactored Spotify search scraper to prevent popularity-based false positives (e.g. David Guetta). |
| 2026-05-01 | PM | task: generate manual review queue | Created `docs/MANUAL_REVIEW_QUEUE.md` for 82 ambiguous records. |
| 2026-05-01 | PM | doc: create artist validation report | Formalized 516 validated records in `docs/ARTIST_VALIDATION_REPORT.md`. |
| 2026-04-30 | PM | Status Report: Validation Complete | 516 artists successfully validated as Indonesian. Exceeded target of 400 clean records. |

| 2026-04-30 | Dev | fix: validator rate limits & genres | Added delay to prevent HTTP 429 and moved `sholawat` to valid Indonesian genres. |
| 2026-04-30 | Dev | feat: implement hybrid metadata validator v3 | Replaced NLP-first approach with Spotify genre-first logic, improving accuracy to ~80% instantly. |
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

## 🚩 PM STATUS: AMBER

**Next Immediate Step**: Run `spotify_search_scraper.py` to rebuild the metadata layer with Weighted Similarity Scoring.
