# Music Data Scraping Project

A professional, modular Python-based data scraping pipeline that extracts music data from multiple sources (Spotify, Viberate) and stores it in a PostgreSQL database.

## 📁 Project Structure

```text
data-scraping/
├── src/
│   ├── database/       # Database connection & operations
│   ├── scrapers/       # Multi-source scrapers (Spotify, Viberate)
│   └── utils/          # Shared utilities (logging, formatting)
├── data/               # Raw output files and browser session data
├── main.py             # Main entry point to orchestrate scraping
├── requirements.txt    # Project dependencies
└── .env                # Environment variables (Database URL)
```

## 🚀 Features

- **Spotify Scraper**: Uses Playwright to automate interaction with Spotify Developer docs and extract API responses.
- **Viberate Scraper**: Uses BeautifulSoup to scrape top artist charts from Viberate.
- **Database Integration**: Automatically initializes and saves scraped data to a PostgreSQL database using SQLAlchemy.
- **Async Support**: Built with `asyncio` for efficient browser automation and database operations.

## 🛠️ Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Playwright**:
   ```bash
   playwright install chromium
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory with your database connection string:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

## 🚦 Usage

To run the entire scraping pipeline:
```bash
python main.py
```

To run individual scrapers for testing:
```bash
# Test Spotify Scraper
python -m src.scrapers.spotify

# Test Viberate Scraper
python -m src.scrapers.viberate
```

## 📝 License
MIT
