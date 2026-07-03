# Phase-wise Evaluation Framework

This document establishes the testing protocols, verification methods, and strict exit criteria for each implementation phase of the Spotify AI-powered Music Discovery System.

---

## Evaluation Grid Summary

| Phase | Core Objective | Primary Verification Method | Exit Criteria |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Review Discovery Engine | Sentiment classification accuracy & MCP logging | 100% review data categorized, report uploaded to Google Docs, Gmail summary sent |
| **Phase 2** | Research Staging | Interview note staging & PRD compilation | Docs created via MCP, synthesis PRD synced to shared Drive |
| **Phase 3** | Discovery MVP Engine | RAG precision & Spotify playlist sync | >= 85% semantic match accuracy, successful playlist sync on active Spotify account |
| **Phase 4** | Conversation & Feedback | Multi-turn memory & Automated survey triggers | Correct state retention across 3+ chat turns, emails dispatched & feedback logged via MCP |
| **Phase 5** | Production & Polish | System latency, security, and catalog coverage | Latency < 3s, catalog coverage increased by 30%, zero API credential exposures |

---

## Phase 1: Review Discovery Engine Evaluation

### Testing Protocol
- Feed a mock dataset of 100 user reviews (containing diverse sentiments and specific feature requests) into the analysis pipeline.
- Verify that the clustering algorithm groups them into accurate pain-point categories (e.g., "algorithm repetition", "UI clutter", "stale suggestions").

### MCP Integration Verification
- Verify that a document named `Review Analysis & Discovery Insights Report` is created in Google Workspace using the Google Docs MCP tool.
- Verify that a draft or sent email containing the document link is created in Gmail using the Gmail MCP tool.

### Exit Criteria
- [ ] 100% of reviews processed and categorized.
- [ ] Sentiment analysis categorizes reviews with at least 85% thematic accuracy.
- [ ] Google Doc contains structured headings for App Store, Reddit, and Community forums.
- [ ] Stakeholder notification email successfully dispatched via Gmail.

---

## Phase 2: User Research Staging & Problem Definition Evaluation

### Testing Protocol
- Execute the research script to generate 5 mocked interview guide files in Google Workspace.
- Input raw transcript files and verify that the synthesis script extracts the target "Routine Listener" persona challenges.

### MCP Integration Verification
- Verify that the interview transcripts are appended correctly using the `append_text` tool of the Google Docs MCP server without duplicating content.
- Verify that the final PRD matches the structure defined in `ProblemStatement` and exists in Google Workspace.

### Exit Criteria
- [ ] 5 structured interview documents successfully populated via MCP.
- [ ] Problem definition document (PRD) successfully uploaded to the master workspace doc via MCP.
- [ ] Persona details are correctly parsed and categorized (Target profile, friction points, alternatives).

---

## Phase 3: Music Recommendation MVP Engine Evaluation

### Testing Protocol
- Perform automated semantic queries (e.g., "rainy afternoon jazz", "energetic synthwave for coding") against the local vector database.
- Evaluate search precision by manually auditing the top 5 retrieved tracks for each query.
- Authorize the Spotify client and check if tracks are added to a newly created playlist.

### Exit Criteria
- [ ] Semantic query accuracy: >= 85% of recommended tracks align with the user's semantic prompt description.
- [ ] Spotify OAuth flow successfully exchanges code for access/refresh tokens.
- [ ] A playlist containing at least 10 retrieved tracks is successfully created in the test user's Spotify account.
- [ ] Latency for vector search + Spotify playlist creation is under 4 seconds.

---

## Phase 4: Feedback Loops & Conversational Agent Evaluation

### Testing Protocol
- Simulate multi-turn conversations in the chatbot UI:
  1. *"Recommend high-energy rock songs."*
  2. *"Make it instrumental."* (Verify rock songs are kept, but vocals are filtered out).
  3. *"Now make them slow."* (Verify acoustic/slow rock tracks are prioritized).
- Trigger a mock 24-hour scheduler event to send the survey.
- Simulate an email reply and confirm the content is appended to the feedback sheet.

### MCP Integration Verification
- Verify that Gmail MCP drafts the follow-up survey with personalized details.
- Verify that the feedback logging script appends survey replies to the centralized `User Feedback Log` Google Doc.

### Exit Criteria
- [ ] Chat agent retains context and applies incremental filters correctly across 3+ consecutive conversation turns.
- [ ] Automated Gmail dispatch fires on event trigger with zero failures.
- [ ] Google Docs feedback log successfully appends incoming answers dynamically without syntax errors.

---

## Phase 5: Production Deployment & Metric Evaluation

### Testing Protocol
- Run load testing (simulating concurrent user queries).
- Perform security scan on environment variables (ensure Spotify API secrets, Google OAuth credentials are not exposed in client bundles).
- Measure catalog coverage (diversity metric: ratio of unique artists surfaced relative to total recommendation volume).

### Exit Criteria
- [ ] Total application end-to-end latency (request to track listing) is < 3 seconds under normal load.
- [ ] System handles 20+ concurrent user sessions without database locks or token rate limits.
- [ ] Zero environment variables or credentials exposed in the public frontend bundle.
- [ ] Diversity Index: Catalog coverage is increased by at least 30% compared to standard Spotify home recommendations for the test segment.
