# Indonesian Music Spatial Analytics & Data Ingestion Pipeline

An end-to-end, modular data engineering and scraping pipeline designed to analyze geographic concentration ("Jakarta-centrism") in the Indonesian music industry. The system automates artist discovery, enriches Spotify metrics, validates nationality, extracts birthplaces/formation locations, and standardizes geographic data into a structured PostgreSQL database.

---

## 📁 Project Structure

```text
data-scraping/
├── src/
│   ├── database/           # Database schema, connections, and CRUD operations
│   │   ├── connection.py   # SQLAlchemy engine setup (async and sync)
│   │   ├── operations.py   # Database insertion and update queries
│   │   └── supabase_client.py # Client wrapper for Supabase database integration
│   │
│   ├── scrapers/           # Modular scraping and crawling components
│   │   ├── discovery/      # Candidate discovery (Viberate charts, MusicBrainz)
│   │   ├── enrichment/     # Spotify metadata & popularity enrichment
│   │   ├── origin/         # Birthplace/formation city extraction (Wikipedia, MusicBrainz)
│   │   └── validation/     # Nationality checking and filtering
│   │
│   └── utils/              # Shared helper modules
│       ├── genre_mapper.py # Spotify genre standardizer and mapping logic
│       ├── geo_constants.py# Geo-mapping dictionaries and Indonesian province/city lists
│       └── scoring.py      # Weighted similarity algorithms for artist matching
│
├── docs/                   # Architectural documents and audit reports
│   ├── ARTIST_VALIDATION_REPORT.md # Details on validated vs. filtered artists
│   └── MANUAL_REVIEW_QUEUE.md      # Ambiguous cases flagged for human inspection
│
├── tests/                  # Verification and diagnostic scripts
│   ├── check_genres.py     # Inspects specific artist genre tags
│   ├── check_genre_count.py# Calculates count of artists with Indonesian genres
│   └── check_foreign_genres.py # Analyzes foreign genre distribution for debugging
│
├── main.py                 # Unified pipeline CLI orchestrator and entry point
├── requirements.txt        # Python package dependencies
├── .env.example            # Template for environment configuration
└── .gitignore              # Files and directories ignored by Git (.venv, .env, Playwright cache)
```

---

## 🚀 Key Features

*   **CLI Orchestrator**: Interactive CLI menu and command-line flags to trigger the pipeline end-to-end or run specific stages.
*   **Dual-Source Artist Discovery**: Discover new Indonesian artists using BeautifulSoup to scrape Viberate music charts or query the MusicBrainz database.
*   **Playwright Spotify Enrichment**: Automates browser sessions using Playwright to extract Spotify popularity indices, genres, and profile pictures.
*   **Wikipedia & MusicBrainz Origin Extraction**: Crawls Wikipedia infoboxes (with regex-based NLP parsing fallback) and MusicBrainz API to find hometowns or birthplaces.
*   **Nationality Validation**: A hybrid validation engine that scores and flags artists based on genre keywords and geographic markers.
*   **Geospatial Normalization**: Standardizes regional administrative hierarchies (resolves Jakarta/Yogyakarta subdivisions and formatting anomalies).

---

## 🛠️ Setup & Installation

### Prerequisites
*   Python 3.10 or higher
*   PostgreSQL Database (e.g., Supabase, Local Postgres, or Neon)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Playwright Browsers
Install the headless Chromium browser used by the Spotify metadata scraper:
```bash
playwright install chromium
```

### 3. Configure the Environment
Copy the example environment file and fill in your database credentials:
```bash
copy .env.example .env
```
Open the `.env` file and set your PostgreSQL connection string:
```env
DATABASE_URL=postgresql://your_db_user:your_db_password@your_db_host:5432/your_db_name
```

---

## 🚦 Usage & Commands

### Running the Orchestrator
To launch the interactive terminal menu:
```bash
python main.py
```
This menu allows you to trigger specific stages:
1. **Discover New Artists (Viberate Charts)**
2. **Discover New Artists (MusicBrainz Deep Search)**
3. **Enrich Missing Spotify Metadata**
4. **Run Nationality Validation (Hybrid)**
5. **Resolve Missing Origins (Wikipedia + MusicBrainz)**
6. **Standardize Geolocation Hierarchy**
7. **Execute Full End-to-End Database Sweep**

### Command Line Ingestion (Single Artist)
To ingest, enrich, validate, and geocode a single artist end-to-end:
```bash
python main.py --ingest "Mahalini"
```

---

## 🧪 Diagnostic & Verification Scripts

Diagnostic scripts are located in the `tests/` directory to safely verify data integrity and analyze database distributions:

*   **Check Artist Genres**:
    ```bash
    python -m tests.check_genres
    ```
*   **Check Indonesian Genre Counts**:
    ```bash
    python -m tests.check_genre_count
    ```
*   **Identify Foreign Genre Outliers**:
    ```bash
    python -m tests.check_foreign_genres
    ```

---

## 📝 License
This project is licensed under the MIT License.
