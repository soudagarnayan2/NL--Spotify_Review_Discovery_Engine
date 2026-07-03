# Edge Case & Mitigation Strategy Registry

This document details the critical technical and behavioral edge cases for each implementation phase of the Spotify AI-powered Music Discovery System, along with their business/system impact and planned mitigations.

---

## Phase 1: Review Discovery Ingestion Engine Edge Cases

### 1.1 Store Scraper API Blocking or IP Rate Limiting
- **Context**: The Apple App Store or Google Play Store APIs may block the scraper’s IP address due to frequent requests, or return empty/malformed responses.
- **Impact**: Zero reviews collected, causing downstream data analysis pipeline failure.
- **Mitigation**:
  - Implement a fallback mock review generator that populates realistic reviews for the target platform (already implemented in `ingest_reviews.py`).
  - Introduce request delays and rotate User-Agent headers during active scraping.
  - Switch to local cache dataset if scraping is entirely blocked.

### 1.2 Non-English or Multi-lingual Reviews
- **Context**: Users writing reviews on US/Global stores in Spanish, French, or mixed language.
- **Impact**: Translation gaps during downstream LLM sentiment analysis and topic clustering.
- **Mitigation**:
  - Incorporate a language detection step.
  - Feed foreign reviews through a translation prompt or select multilingual LLMs (e.g., GPT-4o) capable of cross-lingual analysis.

### 1.3 Spam, Emojis, or Empty Review Content
- **Context**: App Store reviews consisting entirely of emojis (e.g., "⭐⭐⭐⭐⭐ 👍") or generic phrases (e.g., "good app").
- **Impact**: Noise in topic modeling, leading to clusters with zero actionable product feedback.
- **Mitigation**:
  - Filter out reviews with word counts below a minimum threshold (e.g., < 3 words) before processing.
  - Skip records containing zero alphanumeric characters.

---

## Phase 2: User Research Staging & PRD Sync Edge Cases

### 2.1 Google Docs MCP Server Connection Failures
- **Context**: Google OAuth token expiration, invalid workspace permissions, or network failure during real-time notes compilation.
- **Impact**: Real-time interview notes are lost or fail to write to Google Workspace.
- **Mitigation**:
  - Implement local scratch buffering: save transcript logs to local temporary files first.
  - Set up retry mechanisms inside the MCP tool client to automatically re-authenticate or re-attempt writing once connection resumes.

### 2.2 Transcript Size Exceeding LLM Context Limits
- **Context**: 1-hour interview transcripts containing 10,000+ words exceed the prompt limit of smaller reasoning models during synthesis.
- **Impact**: Incomplete synthesis, truncation of key insights, or model timeout.
- **Mitigation**:
  - Run a chunked-summarization pipeline: compress raw transcripts in 10-minute intervals before feeding them to the main persona extractor.
  - Standardize on models with large context windows (Claude 3.5 Sonnet / GPT-4o).

---

## Phase 3: Music Recommendation MVP Engine Edge Cases

### 3.1 Extreme or Contradictory Search Queries
- **Context**: A user inputs contradictory constraints (e.g., *"give me fast, high-energy sleep music"* or *"indie metal acoustic pop"*).
- **Impact**: Low-relevance or conflicting search results that confuse the user.
- **Mitigation**:
  - Configure the LLM query parser to identify contradiction and ask the user to clarify (e.g., *"I see you asked for both high energy and sleep music, which vibe should I prioritize?"*).
  - Split the search vector query weights evenly to surface tracks representing both boundaries, with UI labels explaining the match rationale.

### 3.2 Out-of-Vocabulary (OOV) or Vague Prompts
- **Context**: User typing a single word like *"music"* or *"good"*.
- **Impact**: Vector database retrieves highly arbitrary results, eroding user trust.
- **Mitigation**:
  - Implement prompt validation: if the query is less than 5 characters or contains no semantic intent, return a conversational guide prompt prompting the user for details (e.g., *"Try telling me: 'acoustic songs for a rainy Sunday morning'"*).

### 3.3 Spotify OAuth Token Expiration Mid-Session
- **Context**: Spotify access token expires (lasts 60 minutes) while the user is actively refining a playlist.
- **Impact**: "401 Unauthorized" errors when trying to create/sync a playlist, leading to broken UI experience.
- **Mitigation**:
  - Set up an automated background refresh handler that catches token expiration, uses the Spotify refresh token, and updates user session credentials transparently.

---

## Phase 4: Feedback Loops & Conversational Agent Edge Cases

### 4.1 Chat Context Drift
- **Context**: The user changes the topic from music discovery to unrelated themes (e.g., *"How do I bake a cake?"* or *"Who won the game last night?"*).
- **Impact**: The LLM agent tries to search the music database for cake recipes, causing database query exceptions.
- **Mitigation**:
  - Implement a system prompt system constraint: check if user intent is music-adjacent. If not, politely redirect the conversation back to music discovery.

### 4.2 Malformed Email Replies via Gmail MCP
- **Context**: The feedback survey receives email responses containing images, single-word answers (e.g., *"yes"*), or blank templates.
- **Impact**: Downstream feedback parser crashes or appends empty/unusable lines to the Google Docs feedback log.
- **Mitigation**:
  - Build validation checks in the email scraper: ignore blank replies, clean HTML tags, and sanitize the input before logging.
  - Set up a fallback category ("unstructured/short") in the Google Docs sheet for non-standard replies.

---

## Phase 5: Production Deployment & Scaling Edge Cases

### 5.1 Spotify Web API Rate Limits
- **Context**: A spike in concurrent user traffic triggers Spotify API rate limiting (HTTP 429).
- **Impact**: Playlists cannot be created or sync requests fail for all active users.
- **Mitigation**:
  - Implement caching: cache track details locally to avoid querying the Spotify API for identical tracks.
  - Apply exponential backoff retries on Spotify client requests and guide the UI to show a "Spotify is busy, retrying..." status.

### 5.2 Concurrent Vector Database Writes
- **Context**: Multiple agents trying to write user feedback reviews or track metadata to ChromaDB concurrently.
- **Impact**: SQLite/ChromaDB database locks or race conditions.
- **Mitigation**:
  - Implement a message queue (e.g., simple in-memory queue) to serialize database writes.
  - Set SQLite lock timeouts to be high enough to handle transient concurrency write locks.
