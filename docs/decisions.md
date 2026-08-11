# Architecture Decision Records (ADR)

## Purpose

This document records important architectural decisions made during the development of the project.

Each decision should explain:

* What was decided.
* Why it was chosen.
* Which alternatives were considered.
* What trade-offs were accepted.

The goal is to make future maintenance easier and preserve the reasoning behind technical choices.

---

# ADR-001 — Separate Crawling from Indexing

## Status

Accepted

## Decision

The crawler and indexing pipeline are implemented as independent components.

Crawler:

* Downloads data.
* Cleans extracted content.
* Saves normalized JSON documents.

Indexer:

* Reads JSON documents.
* Converts them into LangChain Documents.
* Splits text into chunks.
* Generates embeddings.
* Stores vectors in Qdrant.

## Rationale

Separating responsibilities makes the system easier to maintain, test, and extend.

The crawler can be replaced without changing the indexing pipeline.

Future data sources (HLTV, VLR, Dotabuff, Riot documentation) can reuse the same indexer.

## Alternatives Considered

### Direct indexing during crawling

Rejected because it tightly couples crawling with LangChain and Qdrant.

---

# ADR-002 — JSON as the Intermediate Format

## Status

Accepted

## Decision

All crawled content is stored as structured JSON before indexing.

## Rationale

JSON provides a stable contract between the crawler and the indexing pipeline.

Benefits:

* Easy to inspect manually.
* Easy to test.
* Easy to version.
* Easy to regenerate embeddings.
* Independent from LangChain.

---

# ADR-003 — Qdrant as the Vector Database

## Status

Accepted

## Decision

Qdrant is the primary vector database.

## Rationale

Reasons:

* Excellent LangChain integration.
* Open source.
* Docker support.
* Metadata filtering.
* High performance.
* Production ready.

Alternatives:

* Chroma
* FAISS
* Pinecone
* Weaviate

---

# ADR-004 — OpenAI Embeddings

## Status

Accepted

## Decision

Use OpenAI embedding models for document indexing.

## Rationale

Reasons:

* High retrieval quality.
* Official LangChain support.
* Simple integration.
* Well documented.

Future embedding models should be replaceable with minimal code changes.

---

# ADR-005 — Metadata on Every Document

## Status

Accepted

## Decision

Every indexed document must contain metadata.

Required fields:

* title
* game
* category
* source
* url
* updated_at
* tags

## Rationale

Metadata enables:

* filtering
* debugging
* source attribution
* future hybrid search
* reranking

---

# ADR-006 — Use LangChain Abstractions

## Status

Accepted

## Decision

Prefer official LangChain abstractions instead of custom implementations whenever practical.

Examples:

* Document
* Retriever
* Runnable
* PromptTemplate
* RecursiveCharacterTextSplitter

## Rationale

Using official abstractions makes the code easier to understand and aligns with the LangChain ecosystem.

---

# ADR-007 — Clean Architecture

## Status

Accepted

## Decision

Separate the project into logical layers.

Infrastructure:

* crawler
* qdrant
* openai

Application:

* indexing
* retrieval

API:

* FastAPI

Domain:

* models
* business logic

## Rationale

Business logic should not depend directly on external libraries.

Replacing infrastructure should require minimal changes.

---

# ADR-008 — Educational Code Over Clever Code

## Status

Accepted

## Decision

When multiple implementations are possible, prefer the version that is easier to understand.

## Rationale

Readability is more important than minimizing the number of lines of code.

Avoid unnecessary abstractions and hidden behavior.

---

# ADR-009 — Dedicated Config Directory for Crawl Targets

## Status

Accepted

## Decision

Introduce a top-level `config/` directory. The crawler's v1 page list lives in `config/pages.json`.

## Rationale

The TDD's original Project Structure did not include a config location. A fixed, inspectable list of pages to crawl needs a stable, version-controlled home that is clearly input configuration, not code and not crawler output.

## Alternatives Considered

### Hardcoding the page list in Python

Rejected because it mixes configuration with code and makes the list harder to review or extend without touching source files.

### Storing the list under crawler/

Rejected to keep a clear boundary between code (`crawler/`) and configuration (`config/`), consistent with the project's layering principles.

---

# ADR-010 — Evolve RAG into an Agent-Based AI Assistant

## Status

Accepted

## Decision

Extend the existing RAG application (`esports-wiki-ai`) into an AI assistant
(`esports-ai-assistant`) by adding, in order: a `RAGService` boundary, LangChain
tools (`get_player`, `get_team`, `get_match`, `search_knowledge_base`), a manual
tool-calling loop, an Agent, a LangGraph investigation workflow, and an MCP
server. Full scope and milestone order live in `docs/roadmap-ai-assistant.md`.

The existing RAG pipeline is preserved as-is and wrapped, not rewritten. `/ask`
remains available as a direct RAG endpoint alongside the new `/assistant` and
`/investigate` endpoints.

## Rationale

The RAG-only v1 (`docs/TDD.md`) deliberately scoped out Agents, LangGraph and MCP
("the first version should focus exclusively on RAG"). That scope is now
complete. The natural next step for the learning goals of this project is to
build the surrounding agent architecture on top of a stable RAG foundation,
rather than starting a new project from scratch.

## Alternatives Considered

### Starting a new project

Rejected — the RAG pipeline (crawler → ingestion → embeddings → Qdrant →
retriever → chain → API) is exactly the kind of "knowledge" capability an agent
needs, and rebuilding it would not teach anything new.

### Rewriting the RAG pipeline to fit the new architecture upfront

Rejected — `docs/roadmap-ai-assistant.md` explicitly calls for wrapping the
existing implementation behind a `RAGService`, not rewriting it. Do not
over-engineer this boundary.

## Consequences

* `docs/TDD.md`'s non-goals for Agents/LangGraph/MCP are superseded for "the
  next version" — they were scoped to v1 only, not permanently excluded.
* Two roadmap documents now coexist: `docs/roadmap-esports-wiki-ai.md` (RAG-only
  future improvements, e.g. Reranker, Parent Document Retriever, Conversation
  Memory — independent of the agent work) and `docs/roadmap-ai-assistant.md`
  (the active scope: Tools, Agent, LangGraph, MCP, Evaluation, Observability).
* New dependencies will be needed later (LangGraph, an MCP SDK) — add them only
  when the corresponding milestone is reached, per `.claude/rules/dependencies.md`.

---

# Future ADRs

New architectural decisions should be added using the same structure:

* Status
* Decision
* Rationale
* Alternatives Considered
* Consequences

Examples of future decisions:

* Hybrid Search
* BM25 Integration
* Parent Document Retriever
* Multi Query Retriever
* Contextual Compression Retriever
* Reranking
* RAGService Boundary Design
* Tool Layer Architecture (tools/ vs services/)
* Mock Data Source for Player/Team/Match Tools
* Agent Framework Choice (LangChain AgentExecutor vs. manual loop vs. LangGraph)
* LangGraph Migration
* MCP Server Design
* Local Embedding Models
* Support for Additional Knowledge Sources
