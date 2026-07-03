# Deployment Guide — Spotify AI Discovery

## Prerequisites

- **Docker** and **Docker Compose** installed
- Python 3.11+ (for local development)
- `.env` file configured at project root (see below)

---

## Environment Variables

Create a `.env` file in the project root:

```env
# ── Required ───────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here

# ── Optional (mock mode if not set) ───────────────────
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8000/callback

REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=SpotifyDiscoveryBot/1.0

# ── Mode Control ──────────────────────────────────────
WORKSPACE_MODE=offline
```

---

## 1. Local Development

### Run Backend
```bash
cd src/backend
python main.py
# Backend runs at http://localhost:8081
# API docs at http://localhost:8081/docs
```

### Seed Track Catalog
```bash
python src/phase4/seed_tracks.py
```

### Run Frontend
```bash
streamlit run src/phase4/app.py
# Dashboard at http://localhost:8501
```

---

## 2. Docker (Local)

### Build & Start All Services
```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| FastAPI Backend | http://localhost:8081 |
| API Docs (Swagger) | http://localhost:8081/docs |
| Streamlit Dashboard | http://localhost:8501 |

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up --build -d
```

---

## 3. Railway Deployment

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### Step 2: Create Project
```bash
railway init
```

### Step 3: Deploy Backend Service
```bash
railway up --service fastapi-backend
```

Railway will auto-detect `railway.json` and use `Dockerfile.backend`.

### Step 4: Deploy Frontend Service
Create a second service in your Railway project:
```bash
railway service create dashboard-frontend
railway up --service dashboard-frontend
```

### Step 5: Configure Environment Variables
In the Railway dashboard, add all variables from `.env` to both services.

Additionally set:
```
API_BASE_URL=https://<backend-service-url>/api/v1
PORT=8081  # for backend
```

### Step 6: Verify Health
```bash
curl https://<backend-url>/api/v1/health
```

---

## 4. Evaluation Suite

Run the evaluation scripts to verify production readiness:

```bash
# Search precision (target: >= 85%)
python src/phase5/evaluate_search_precision.py

# Catalog coverage (target: 30% improvement)
python src/phase5/evaluate_catalog_coverage.py

# Load testing (target: <3s latency, 20+ concurrent)
# Note: Start backend first
python src/phase5/evaluate_load_test.py

# Security scan (target: zero credential leaks)
python src/phase5/evaluate_security.py
```

Reports are saved to `data/workspace/eval_*.json`.

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│  Streamlit Frontend  │────▶│   FastAPI Backend    │
│     (Port 8501)      │     │     (Port 8081)      │
└─────────────────────┘     └─────────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                   │
              ┌─────▼─────┐   ┌──────▼──────┐   ┌──────▼──────┐
              │  SQLite DB │   │  ChromaDB   │   │  Groq LLM   │
              │ (reviews)  │   │  (vectors)  │   │ (Llama 3.1) │
              └───────────┘   └─────────────┘   └─────────────┘
```
