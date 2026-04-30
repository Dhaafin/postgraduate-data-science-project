# Product Requirement Documents

## 1. Executive Summary

**Analisis Spasial Ketimpangan Digital pada Industri Musik Indonesia** is a full-stack data-driven web application that performs spatial analysis of the Indonesian music industry on digital streaming platforms. The project investigates the long-standing hypothesis of 'Jakarta-centrism' — the structural dominance of the Greater Jakarta area (Jabodetabek) in the Indonesian creative industry — by gathering empirical, data-backed evidence from Spotify's platform.

The platform collects approximately 300 Indonesian artists from Viberate, enriches each profile with Spotify metrics (popularity, followers, genre), geo-codes each artist's origin city, and presents the findings through an interactive spatial dashboard. The end goal is to quantify whether digital streaming platforms like Spotify have democratized music distribution for regional talent, or whether the structural dominance of Jakarta persists in the digital age.

## **2. Problem Statement**

### 2.1 Background

Indonesia's music industry has historically been centered in Jakarta, where major recording studios, talent agencies, promoters, and label headquarters are concentrated. This phenomenon, colloquially referred to as 'Jakarta-centrism,' has created deep structural inequalities in which musicians from outside Jabodetabek face significant barriers to achieving national recognition.

Counterexamples exist — most notably Ambon, recognized by UNESCO as a City of Music — demonstrating that creative talent is geographically distributed across the archipelago. The rise of digital streaming platforms like Spotify was widely expected to level the playing field for regional artists by removing physical distribution barriers.

## **3. Project Objectives**

1. Build a robust, automated data pipeline that collects, cleans, and enriches artist data from Viberate and Spotify.
2. Produce a clean, analysis-ready dataset of ~300 Indonesian artists with geospatial coordinates.
3. Perform spatial analysis to identify distribution patterns and regional genre hubs.
4. Deliver an interactive web dashboard with a talent map, genre deep-dive filters, and comparative analytics.
5. Generate actionable insights for policymakers (Kemenparekraf) and industry stakeholders (talent scouts, labels).

## **4. Scope & Boundaries**

### 4.1 In Scope

- Artist data collection from Viberate (top ~300 Indonesian artists)
- Spotify metadata enrichment via Spotify Web API (artist ID, followers, genre)
- Popularity index collection via Playwright-based automated browser scraping of Spotify Web Player
- Origin city geo-coding using Wikipedia / Wikidata
- Spatial analysis using Pandas and GeoPandas
- Interactive dashboard (Next.js frontend + Express backend)
- PostgreSQL database hosted on Neon (serverless)
- Deployment with Docker and asset storage via Cloudflare / Cloudinary

### 4.2 Out of Scope

- Real-time streaming data or live Spotify listener counts
- Audio analysis or music content features (tempo, key, valence, etc.)
- Social media metrics (TikTok, Instagram follower counts)
- Monetization, paywall, or user account system
- Recommendation engine or collaborative filtering

## **5. Methodology — OSEMN Framework**

The project follows the OSEMN data science methodology to ensure a systematic, reproducible pipeline from raw data acquisition to communicable spatial insights.

| **Phase** | **Stage** | **Description** |
| --- | --- | --- |
| **O** | **Obtain** | Scrape ~300 artist names from Viberate. Query Spotify Search API to get Spotify IDs. Scrape Wikipedia/Wikidata for city of origin with coordinates. |
| **S** | **Scrub** | Normalize artist names (handle aliases, diacritics). Deduplicate entries. Handle missing genre/city data. Validate geo-coordinates for Indonesian territory. |
| **E** | **Explore** | Perform EDA: distribution of popularity scores, follower counts by province/island, genre frequency analysis, geographic clustering. |
| **M** | **Model** | Kernel Density Estimation (KDE) for spatial hotspot detection. Correlation analysis (Spearman) between origin city and popularity. Genre-region mapping. |
| **N** | **Interpret** | Build interactive dashboard with Indonesia bubble map, genre deep-dive filters, and province-level comparative bar charts. |

## **6. Data Acquisition Pipeline**

### 6.1 Step 1 — Initial Artist Pool (Viberate)

Source: https://www.viberate.com/music-charts/top-artists-from-indonesia/

Method: Web scraping (Playwright or Cheerio) to extract approximately 300 top Indonesian artist names. This produces the primary seed list for the entire pipeline.

| **Field** | **Details** |
| --- | --- |
| **Output** | List of ~300 artist names (CSV/JSON) |
| **Rate limit** | Respect robots.txt; use 1–2s delays between requests |
| **Error handling** | Retry on 429/503; log failed rows |

### 6.2 Step 2 — Spotify ID Retrieval

Using the Spotify Search API (GET /v1/search?type=artist&q={name}), each artist name from the Viberate list is queried to obtain their unique Spotify Artist ID. A new column spotify_id is appended to the dataset.

- Tool: Spotipy (Python SDK for Spotify Web API)
- Matching strategy: Fuzzy match on artist name if exact match fails; flag low-confidence matches for manual review
- Output column added: spotify_id (string)

### 6.3 Step 3 — Spotify Metadata Enrichment

With the spotify_id, the Spotify Web API returns structured metadata. Three new columns are added to the dataset:

| **Column** | **API Field** | **Description** |
| --- | --- | --- |
| **popularity** | popularity | Integer 0–100, Spotify's internal score based on recent streams |
| **followers** | followers.total | Total follower count on Spotify |
| **genres** | genres | Array of genre tags assigned by Spotify (e.g., 'indie pop', 'dangdut') |

Note: The standard Spotify API does not consistently return the popularity field in all contexts. Where the API response omits it, Playwright automation is used to scrape the Spotify Web Player for the artist's popularity score.

### 6.4 Step 4 — Geospatial Enrichment

For each artist, their city of origin is retrieved from Wikipedia / Wikidata. The origin city is then geo-coded to obtain latitude and longitude coordinates for spatial analysis.

- Primary source: Wikidata SPARQL query for birthplace linked to the artist's Wikipedia page
- Fallback: Manual lookup for artists without Wikipedia entries
- Output columns added: origin_city, province, island, latitude, longitude

This step may be revisited and extended as additional correlation variables are identified (e.g., regional HDI, internet penetration index, music school density).

### **7. Technical Architecture & Stack**

### 7.1 Architecture Overview

This project follows a monorepo architecture with a clear separation of concerns between the data pipeline, the backend API, and the frontend dashboard.

| **Layer** | **Technology** | **Rationale** |
| --- | --- | --- |
| **Frontend** | Next.js (App Router) | SSR/SSG for SEO, React ecosystem, excellent map library support, TypeScript |
| **Backend API** | Express.js (Node) | Lightweight REST API, easy middleware chain, familiar JS ecosystem |
| **Database** | PostgreSQL via Supabase | Serverless Postgres — built-in Auth, Storage, Edge Functions, auto-scaling, generous free tier, and a built-in dashboard |
| **ORM** | Prisma or Drizzle ORM | Type-safe queries, schema migrations, works well with Supabase JS client and REST API |
| **Data Pipeline** | Python (Pandas, GeoPandas, Spotipy, Playwright) | Pandas/GeoPandas for spatial analysis; Playwright for browser automation scraping |
| **Storage** | Cloudflare R2 or Cloudinary | Store processed GeoJSON files, static assets; low-cost object storage |
| **Containerization** | Docker + Docker Compose | Consistent dev environment, easy deployment; separate containers for API and pipeline |
| **Deployment** | Vercel (frontend) + Railway/Render (backend) | Vercel for Next.js edge deployment; Railway for Express + background jobs |

### 7.2 Database — Why Supabase (Serverless PostgreSQL)

Given the requirement for ‘new things’ alongside the existing familiarity with Next.js monorepo setups, Supabase is the recommended database choice for this project:

- Serverless-first: Supabase scales to zero on the free tier — ideal for an academic project with bursty traffic
- Free tier: 500MB database, 2 projects, and 50,000 monthly active users — more than enough for an academic project
- PostgreSQL-compatible: Full SQL support including PostGIS for native spatial queries
- Built-in extras: Row Level Security, Auth, Storage, and REST/GraphQL auto-generated APIs come out of the box
- Edge-ready: Works seamlessly with Next.js via the official @supabase/ssr package

### 7.3 Data Schema (Core Tables)

artists — Core table storing all artist profiles with geospatial data.

- id, spotify_id, name, origin_city, province, island, latitude, longitude, popularity, followers, genres (JSON array), created_at, updated_at

pipeline_runs — Audit log of data collection runs.

- id, run_date, source (viberate | spotify | wikidata), records_processed, errors, status