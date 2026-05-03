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
| M3  | Source 2: Spotify  | [Complete] | Re-scraped 600 records with Weighted Scoring & Profile Pics. |
| M4  | Geo-Enrichment     |  [Active]  | Validating nationality and extracting Origin City/Province.        |
| M5  | Spatial Analytics  | [Pending]  | GeoPandas analysis of regional density & genre hubs.               |
| M6  | Web Dashboard      | [Pending]  | Next.js / Express interactive spatial map.                         |
| M7  | Deployment         | [Pending]  | Dockerization and Cloud Infrastructure setup.                      |

---

## 🛠️ ACTIVE FEATURE: M4 - Wikipedia/Wikidata Geo-Coding & Validation

> **Objective**: Identify "Origin City" and enforce strict data hygiene by purging non-Indonesian and corporate records.

- [x] **DB Schema Expansion**: Add `origin_city`, `origin_province`, `latitude`, and `longitude` columns.
- [x] **Viberate Expansion**: Refactor `viberate.py` to collect 600 candidates.
- [x] **Spotify Enrichment**: **RE-RUNNING** with Weighted Similarity Scoring.
- [x] **Spotify Enrichment**: Add profile picture extraction to database.
- [ ] **Nationality Validation**: Re-running nationality check against new Spotify metadata.
- [ ] **Wiki/Geo Scraper**: Extracting origin city/province for 600 artists.
- [ ] **Target Target**: Reach 500+ "Clean" records for final spatial analysis.

---

## 📓 RESEARCH PARKING LOT (Future Architectural Problems)

_These items are high-priority for the research thesis but deferred until M4 baseline data is collected._

- [ ] **The "Migration" Disambiguation**: Define logic to handle artists who were born in Region A but moved/formed in Jakarta.
- [ ] **Temporal Correlation**: Correlate "Spotify Breakthrough" date with "Migration Year" to assess digital democratization vs. legacy networks.
- [ ] **Genre-Location Variance**: Analyze if certain genres (e.g., Koplo) are more resistant to Jakarta migration than others (e.g., Pop).
- [ ] **Industrial Artifacts vs Talent**: Define exclusionary criteria for "Brand Artists" (children's IPs, corporate lo-fi) to refine the spatial inequality signal.

---

| Timestamp  | Persona | Action                               | Impact                                                                                                    |
| :--------- | :-----: | :----------------------------------- | :-------------------------------------------------------------------------------------------------------- |
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

**Next Immediate Step**: Run `nationality_validator.py` (M4) to filter the 600 records and prepare for Geo-Coding.
