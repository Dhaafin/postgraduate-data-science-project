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
| ID | Milestone | Status | Details |
|:---|:---|:---:|:---|
| M1 | Core ETL Engine | [Complete] | Async infrastructure & DB Schema. |
| M2 | Source 1: Viberate | [Complete] | Extraction of top ~300 Indonesian candidates. |
| M3 | Source 2: Spotify | [Complete] | Hybrid API/Scraper pipeline for popularity & metadata. |
| M4 | Geo-Enrichment | [Active] | Wikipedia/Wikidata origin city mapping. |
| M5 | Spatial Analytics | [Pending] | GeoPandas analysis of regional density & genre hubs. |
| M6 | Web Dashboard | [Pending] | Next.js / Express interactive spatial map. |
| M7 | Deployment | [Pending] | Dockerization and Cloud Infrastructure setup. |

---

## 🛠️ ACTIVE FEATURE: M4 - Wikipedia/Wikidata Geo-Coding
> **Objective**: Identify the "Origin City" for each artist to provide the geospatial basis for analysis.

- [x] **DB Schema Expansion**: Add `origin_city`, `origin_province`, `latitude`, and `longitude` columns.
- [x] **Wiki Scraper Prototype**: Extraction of "Asal" or "Tempat lahir" from inflection boxes.
- [x] **Geocoding Pipeline**: Integration with OpenStreetMap/Nominatim for coordinate mapping.
- [ ] **Fix Extraction Bug**: Refine `parse_origin_string` to properly filter out remaining full names (e.g., "Daniel Baskara Putra") when length is 3.

---

## 📓 RESEARCH PARKING LOT (Future Architectural Problems)
*These items are high-priority for the research thesis but deferred until M4 baseline data is collected.*

- [ ] **The "Migration" Disambiguation**: Define logic to handle artists who were born in Region A but moved/formed in Jakarta.
- [ ] **Temporal Correlation**: Correlate "Spotify Breakthrough" date with "Migration Year" to assess digital democratization vs. legacy networks.
- [ ] **Genre-Location Variance**: Analyze if certain genres (e.g., Koplo) are more resistant to Jakarta migration than others (e.g., Pop).

---

## 📝 CHRONOLOGICAL ACTIVITY LOG
| Timestamp | Persona | Action | Impact |
|:---|:---:|:---|:---|
| 2026-04-26 | PM | End of Session Briefing | Logged remaining parsing bugs; pipeline architecture is operational for M4. |
| 2026-04-26 | Dev | feat: geocoding pipeline | Built `geo_pipeline.py` fusing Wikipedia scraper with Nominatim coordinates. |
| 2026-04-26 | Dev | feat: wiki scraper prototype | Developed MediaWiki API integration for city/province extraction. |
| 2026-04-26 | Dev | feat: db schema expansion | Refactored `music_data` table to include geospatial and province fields. |
| 2026-04-26 | PM | Pivot to Spatial Analysis | Updated Ledger to align with PRD focused on "Jakarta-centrism". |
| 2026-04-26 | Dev | fix: spotify event loop | Resolved Windows-specific async concurrency issues. |
| 2026-04-26 | Dev | feat: spotify_search_scraper.py | Added browser-based popularity extraction. |

---

## 🚩 PM STATUS: GREEN
**Next Immediate Step**: Update the database schema to support origin geospatial data and initiate research on Wikipedia extraction for Indonesian artist bios.
