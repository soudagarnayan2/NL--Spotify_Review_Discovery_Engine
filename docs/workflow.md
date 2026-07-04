# Spotify Review Discovery Engine: Project Workflow

This document outlines the end-to-end workflow, data pipelines, and architectural components of the **Spotify Review Discovery Engine**. The engine integrates voice-of-the-customer (VoC) sentiment analysis with LLM-powered semantic music recommendation.

---

## 1. System Architecture Overview

The system is organized into a layered pipeline: **Ingestion**, **Vector Seeding**, **Discovery & Refinement**, **Production APIs**, and **Continuous Evaluation**.

```mermaid
graph TD
    %% Ingestion Flow %%
    subgraph Ingestion [1. Data Ingestion & MCP]
        A1[App Store Reviews] --> B1[ingest_reviews.py]
        A2[Play Store Reviews] --> B1
        A3[Reddit Feed] --> B1
        B1 --> C1[(raw_reviews.json)]
        C1 --> D1[analyze_reviews.py]
        D1 --> E1[(processed_insights.json)]
        E1 --> F1[review_mcp_server.py]
    end

    %% Vector & Search Flow %%
    subgraph CoreEngine [2. Music Discovery Engine]
        G1[seed_tracks.py] --> H1[(Chroma Vector DB)]
        I1[User Query / Prompt] --> J1[discovery_engine.py]
        H1 --> J1
        E1 --> J1
        J1 --> K1[feedback_agent.py]
    end

    %% Production API & UI %%
    subgraph Production [3. Production Layer]
        J1 --> L1[FastAPI Backend - main.py]
        L1 -->|REST API| M1[Static Web Dashboard - frontend/]
        K1 --> L1
        N1[Streamlit UI - app.py] -->|Direct Call| J1
    end

    %% Continuous loop %%
    subgraph Automation [4. Automation & Audit]
        O1[scheduler.py] -->|Triggers| B1
        O1 -->|Triggers| D1
        O1 -->|Runs Audits| P1[Phase 5 Evaluations]
    end

    classDef stage fill:#1b241e,stroke:#1DB954,stroke-width:1px,color:#fafafa;
    class Ingestion,CoreEngine,Production,Automation stage;
```

---

## 2. Phase-by-Phase Workflow

### Phase 1: Ingestion & Analysis Pipeline
1.  **Ingestion (`ingest_reviews.py`)**: Fetches raw user reviews from Apple App Store, Google Play Store, and Reddit threads. Saves the compiled logs into `data/raw_reviews.json`.
2.  **Analysis (`analyze_reviews.py`)**: Parses the raw texts to extract sentiment scores, core themes (e.g., UI updates, repetitiveness, bugs), and user requests. Saves the results to `data/processed_insights.json`.
3.  **MCP Integration (`review_mcp_server.py`)**: Exposes reviews as a Model Context Protocol tool, enabling agents and LLMs to query active user sentiment reports dynamically.

### Phase 2: PRD & Competitive Synthesis
1.  **Market Research (`stage_research.py`)**: Automates gathering competitor data and feature parity charts (e.g., Apple Music Lossless, YouTube Music cover catalogs).
2.  **PRD Generation (`synthesize_prd.py`)**: Compiles product requirement logs based on gaps found in user reviews and competitive audits.

### Phase 3: Concept Prototyping
- Contains the initial architecture schemas and mock endpoints used to structure backend contracts.

### Phase 4: Discovery Engine Core
1.  **Database Seeding (`seed_tracks.py`)**: populates the Chroma vector database (`data/chroma_db/`) with a catalog of songs, generating embeddings for track descriptions, tempos, and metadata.
2.  **AI Engine (`discovery_engine.py`)**: Fuses vector similarities with review data context. It executes queries on the vector database and formats LLM completion prompts (via Groq/OpenAI) to match tracks against user intentions.
3.  **Feedback Agent (`feedback_agent.py`)**: Operates a stateful session refinement loop, allowing users to modify search intents (e.g., *"Make it more energetic"* or *"Include only acoustic tracks"*).
4.  **Spotify Authorization (`spotify_auth.py`)**: Interfaces with Spotify API OAuth to allow users to sync search results as custom Spotify playlists.

### Phase 5: Evaluation & Auditing
Runs test jobs to verify pipeline safety and quality:
*   `evaluate_catalog_coverage.py`: Audits track distribution across searches.
*   `evaluate_search_precision.py`: Evaluates semantic matching precision.
*   `evaluate_security.py`: Tests against prompt injections and system leaks.
*   `evaluate_load_test.py`: Measures backend API response times under simulated request loads.

---

## 3. Production Request Lifecycle

The diagram below outlines a user search request lifecycle, demonstrating how the static HTML/JS/CSS frontend communicates with the FastAPI backend and AI engines:

```mermaid
sequenceDiagram
    autonumber
    actor User as User Interface
    participant FE as Static Frontend (script.js)
    participant BE as FastAPI Backend (main.py)
    participant DE as Discovery Engine (discovery_engine.py)
    participant VDB as Chroma Vector DB
    participant LLM as LLM API (Groq/OpenAI)

    User->>FE: Enters Query (e.g., "chill lofi beats") & clicks Search
    FE->>BE: HTTP POST /api/v1/discover {query}
    BE->>DE: process_discovery_query(query)
    DE->>VDB: Query Vector Similarities (semantic track matching)
    VDB-->>DE: Return Matching Tracks List
    DE->>LLM: Pass Query + Track Context + User Review Context
    LLM-->>DE: Return Synthesized VoC Summary & Recommendation
    DE-->>BE: Return DiscoveryResponse (Analysis + Tracks)
    BE-->>FE: Return JSON Response
    FE->>User: Render Results Panel, KPI Charts, & Track Cards
```

---

## 4. Automation & Maintenance

The system is automated via the background process `scheduler.py`:

```mermaid
stateDiagram-v2
    [*] --> Idle: Start Scheduler
    Idle --> Ingesting: Cron Trigger (Hourly/Daily)
    Ingesting --> Analyzing: Ingestion complete
    Analyzing --> ReSeeding: Insights updated
    ReSeeding --> Evaluating: Database synced
    Evaluating --> Idle: Audits complete & logs saved
```

*   **Ingesting**: Fetches new reviews.
*   **Analyzing**: Re-runs VoC classification.
*   **ReSeeding**: Integrates database updates.
*   **Evaluating**: Re-runs evaluation suites (`catalog coverage`, `search precision`, `security audit`) to ensure updates did not introduce regressions.
