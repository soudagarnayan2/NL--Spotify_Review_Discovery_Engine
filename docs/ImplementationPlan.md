# Implementation Plan: Spotify AI Discovery Agent

This document defines the phase-wise implementation plan for the **Spotify AI Discovery Agent**. The system comprises a **Python/FastAPI backend** for scraping and ingesting reviews, and a **Streamlit/React frontend** deployed on **Railway** to visualize sentiment trends, identify pain points, and summarize topics, integrated with Model Context Protocol (MCP) servers.

---

## System Architecture Overview

```
                  ┌─────────────────────────────────┐
                  │      Target Review Sources      │
                  │   Google Play, App Store, etc.  │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend (Python)                      │
│                                                                     │
│  ┌───────────────────────┐            ┌──────────────────────────┐  │
│  │   Ingestion & Scrape  ├───────────>│   Database (SQLite/PG)   │  │
│  │     Service Router    │            └────────────┬─────────────┘  │
│  └───────────────────────┘                         │                │
│                                                    ▼                │
│  ┌───────────────────────┐            ┌──────────────────────────┐  │
│  │   LLM & Rules-Based   │<───────────┤    Insights Analysis     │  │
│  │    Classifier Agent   │            │      Service Router      │  │
│  └───────────────────────┘            └────────────┬─────────────┘  │
│                                                    │                │
└────────────────────────────────────────────────────┼────────────────┘
                                                     │ (API Routes)
                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard (Railway)                     │
│                                                                     │
│  ┌───────────────────────┐            ┌──────────────────────────┐  │
│  │   Sentiment Trends    │            │     Topic Summaries      │  │
│  │      Visualizer       │            │     & Actionable Pain    │  │
│  └───────────────────────┘            │      Points Board        │  │
│                                       └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP Workspace Integrations                     │
│               [Google Docs MCP] & [Gmail MCP] Servers               │
+---------------------------------------------------------------------+
```

---

## Phase-wise Implementation Roadmap

### Phase 1: Ingestion & Scraping APIs (FastAPI Backend)
**Goal**: Build a robust ingestion service using FastAPI to trigger, scrape, mock, and store product reviews.

- **Backend Endpoints**:
  - `POST /api/v1/ingest`: Initiates asynchronous scraping routines for App Store, Google Play Store, and Product Hunt reviews, with mock fallback engines for Reddit/Twitter.
  - `GET /api/v1/reviews`: Fetches all raw reviews with pagination, search, and platform filtering support.
- **Scraper Implementations**:
  - App Store (`app-store-scraper`) and Google Play Store (`google-play-scraper`) targeted at Spotify.
  - Product Hunt scraper (using Playwright or mock fallback to read Spotify review profiles).
  - Schema standardization:
    ```json
    {
      "id": "string",
      "platform": "app_store | play_store | product_hunt | reddit | twitter",
      "rating": "int (1-5) | null",
      "content": "string",
      "date": "YYYY-MM-DD",
      "user": "string"
    }
    ```
- **Database Engine**:
  - SQLite backend database for local development, configured to easily switch to PostgreSQL for cloud hosting.

---

### Phase 2: AI Sentiment Analysis & Topic Categorization
**Goal**: Build the analysis pipeline to classify sentiments, cluster user complaints, and extract actionable insights.

- **Backend Endpoints**:
  - `POST /api/v1/analyze`: Triggers analysis of raw reviews in the database.
  - `GET /api/v1/insights`: Returns aggregated statistics (sentiments, topic counts, severity indices).
- **Core Processing Logic**:
  - Integrate LLM-based categorization using **Groq** APIs (e.g., Llama 3).
  - Set up a high-precision rules-based classifier fallback to run locally when no API credentials are provided.
  - Target Topics:
    - *Algorithmic Bubble / Recommendation Repetition*
    - *Smart Shuffle loop issues*
    - *Taste pollution / Lack of Sandbox mode*
    - *Decision overload*
    - *General Feedback / Other*

---

### Phase 3: Workspace Exporter & MCP Integration
**Goal**: Standardize integrations to Google Workspace using MCP servers instead of direct REST APIs.

- **Backend Endpoints**:
  - `POST /api/v1/export`: Triggers reports compilation and distribution.
- **MCP Workflows**:
  - Implement an asynchronous client connecting to **Google Docs MCP server** to auto-generate the `Review Analysis & Discovery Insights Report` document.
  - Connect to **Gmail MCP server** to draft and send stakeholder notifications containing the document link.
  - Maintain a mock filesystem logging mode (`data/workspace/`) for sandboxed offline testing.

---

### Phase 4: Frontend Visualization Dashboard
**Goal**: Build a modern Streamlit or React frontend dashboard to display findings, sentiment trends, and topic summaries.

- **Dashboard Visualizations**:
  - **Sentiment Trends**: Daily/weekly breakdown of positive, negative, and neutral ratings using interactive line/bar charts.
  - **Pain Points Board**: Highlighting the most frequent topic categories, matching user complaints, and severity indicators.
  - **Topic Summarizer**: AI-generated text summaries of each topic cluster accompanied by representative user quotes.
  - **Control Center**: Action buttons to trigger `/ingest`, `/analyze`, and `/export` directly from the dashboard interface.

---

### Phase 5: Railway Cloud Deployment
**Goal**: Package and deploy the FastAPI backend and Frontend dashboard to Railway.

- **Railway Deployment Architecture**:
  - Build multi-service layout on Railway:
    1. **fastapi-backend**: Python backend service running Uvicorn.
    2. **dashboard-frontend**: Streamlit/React frontend dashboard.
  - Use `railway.json` config or custom `Dockerfiles` for automated builds.
- **Configuration & Environment Variables**:
  - Ensure all API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`), Google OAuth tokens (for MCP servers), and environment flags are configured securely inside Railway's dashboard.
