# Decision Log: Technical & Business Decisions

This document acts as the Architecture Decision Record (ADR) log for the Spotify AI-powered Music Discovery System. It captures key technical design choices and business directions, providing context, alternatives, and rationales.

---

## Decision Index

| ID | Title | Date | Status |
| :--- | :--- | :--- | :--- |
| **ADR-01** | Standardizing on Model Context Protocol (MCP) for Google Workspace | 2026-07-01 | **Approved** |
| **ADR-02** | Selection of ChromaDB as the Vector Database | 2026-07-01 | **Approved** |
| **ADR-03** | Target Segment Selection: Routine Spotify Listeners | 2026-07-01 | **Approved** |
| **ADR-04** | LLM Selection for Agent Orchestration | 2026-07-01 | **Approved** |

---

## ADR-01: Standardizing on Model Context Protocol (MCP) for Google Workspace

### Status
**Approved**

### Context
The application needs to integrate closely with Google Workspace (specifically Google Docs and Gmail) to:
- Document user interview guides and raw transcripts.
- Save and sync the Product Requirement Document (PRD) and problem statement.
- Compile sentiment analysis reports.
- Send feedback surveys and log subsequent replies.

Conventionally, this is achieved by registering credentials in the Google Cloud Console, dealing with OAuth 2.0 flow configurations, importing raw Google APIs clients, and writing custom wrapper code for document operations and email dispatches.

### Decision
Standardize on using the **Model Context Protocol (MCP)** using the pre-built `Google Docs MCP Server` and `Gmail MCP Server` rather than writing direct REST API clients.

### Rationale
- **Development Velocity**: MCP provides pre-built, standard tools (`create_document`, `append_text`, `send_email`) that LLM agents can call out-of-the-box, eliminating the need to write API-specific client code.
- **Security & Authorization**: Credential storage and authentication token flows are decoupled from the application logic and managed directly inside the local MCP host server configurations.
- **Agent Interoperability**: standardizes the way LLM agents interact with local tools and files, ensuring that future integration of different models (e.g., Anthropic vs. OpenAI) doesn't require rewriting API calls.

---

## ADR-02: Selection of ChromaDB as the Vector Database

### Status
**Approved**

### Context
To support natural language queries like *"jazz suitable for a rainy evening"* or *"nostalgic folk without heavy vocals"*, the agent needs to search acoustic features, genre tags, and track descriptions. This requires a database that supports semantic vector searches.

### Decision
Use **ChromaDB** as the vector database for the MVP phase.

### Rationale
- **Ease of Setup**: ChromaDB is lightweight, open-source, and can run completely local or in-memory, avoiding the overhead of setting up cloud database accounts (like Pinecone or Milvus) during development.
- **Rich Integration**: It has native support within Python and Node.js ecosystems, making vector insertion and query retrieval very straightforward.
- **Scaling Path**: If production scale demands it, ChromaDB can easily be swapped for Pinecone or PGVector with minimal agent orchestrator edits.

---

## ADR-03: Target Segment Selection: Routine Spotify Listeners

### Status
**Approved**

### Context
Spotify users suffer from "recommendation bubble fatigue." However, targeting all users is too broad. We need to identify a specific segment where this friction causes churn risk or low engagement.

### Decision
Focus the MVP and research on **Routine Spotify Listeners** who rely on background playlists (work, study, commute) but desire music discovery.

### Rationale
- **High Retention Risk**: These users are highly repetitive, which leads to boredom and eventual subscription churn.
- **Low Risk/High Reward**: They are already active music consumers. If they can discover a few highly satisfying tracks to insert into their routine, it builds significant brand loyalty and trust.
- **Clear Pain Point**: They experience high cognitive load when selecting music during routine tasks, making an automated context-aware AI agent extremely valuable.

---

## ADR-04: LLM Selection for Agent Orchestration

### Status
**Approved**

### Context
The agent orchestrator needs to parse user prompts, interface with vector databases, make decisions on when to trigger MCP tools, and manage multi-turn conversations. This requires an LLM with strong function-calling (tool-calling) capabilities, reasoning, and context retention.

### Decision
Utilize **Claude 3.5 Sonnet** (via Anthropic API) or **GPT-4o** (via OpenAI API) as the default intelligence model, implemented using **LangGraph** for workflow state management.

### Rationale
- **State-of-the-art Tool Calling**: Both models rank highest in reliability for converting user prompt intentions into structured JSON schema tool arguments.
- **Complex Orchestration**: LangGraph enables cyclic agent workflows (e.g., query vector database -> evaluate results -> refine query -> return output), which is essential for multi-turn music discovery.
