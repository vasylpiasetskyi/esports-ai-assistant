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
* LangGraph Migration
* Local Embedding Models
* Support for Additional Knowledge Sources
