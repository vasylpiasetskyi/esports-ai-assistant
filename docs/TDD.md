# Esports Wiki AI

## Overview

Esports Wiki AI is a Retrieval-Augmented Generation (RAG) application that answers questions about esports using a private knowledge base instead of relying solely on an LLM.

The project is intended as a portfolio project demonstrating LangChain and RAG architecture.

Primary goal:

- Learn the complete RAG lifecycle.
- Learn LangChain abstractions.
- Build a production-like architecture.
- Keep ingestion separated from inference.

---

# Scope

The first version supports four games:

- Counter Strike 2
- Dota 2
- League of Legends
- Valorant

The assistant should answer questions like:

- What is ADR?
- Explain Economy Round.
- How does Swiss Stage work?
- Tell me about Natus Vincere.
- What is Inferno?
- Explain Roshan.
- What is Baron Nashor?
- Explain Eco Round in CS2.
- What is an Operator in Valorant?

The assistant must answer only from indexed knowledge.

---

# High Level Architecture

                     +----------------------+
                     |   Liquipedia         |
                     +----------+-----------+
                                |
                                |
                         Crawlers
                                |
                                |
                     +----------v-----------+
                     | Raw Documents (JSON) |
                     +----------+-----------+
                                |
                                |
                          Indexing Pipeline
                                |
                                |
                  Chunking + Embeddings + Metadata
                                |
                                |
                          Qdrant Vector DB
                                |
                                |
                           Retriever
                                |
                                |
                              LLM
                                |
                                |
                           Final Answer

---

# Project Structure

esports-wiki-ai/

    config/

        pages.json

    crawler/

        liquipedia/

        base.py

        parser.py

        models.py

    ingestion/

        loader.py

        splitter.py

        embeddings.py

        indexer.py

    rag/

        retriever.py

        prompts.py

        chains.py

    api/

        routes.py

        schemas.py

        main.py

    data/

        raw/

        processed/

    tests/

    docker/

    README.md

**Note (2026-08-11):** this structure describes the frozen RAG-only v1
baseline. As of Milestone 2.5 in `docs/roadmap-ai-assistant.md`, `rag/` and
`api/` (along with `tools/` and `services/`, added in Milestone 2) live under
a new top-level `app/` package — see `docs/architecture.md` and
`docs/roadmap-ai-assistant.md` §23 for the current layout. `crawler/`,
`ingestion/`, `scripts/`, `config/`, `data/` are unaffected.

---

# Technologies

Python 3.13

FastAPI

LangChain

LangChain Community

LangChain OpenAI

Qdrant

OpenAI Embeddings

Pydantic v2

Docker

Poetry or uv

---

# Knowledge Source

The initial source will be Liquipedia.

The system must be designed in a way that allows adding new sources later without changing the ingestion pipeline.

Future sources:

- HLTV
- VLR
- Dotabuff
- Riot Documentation
- Valve Documentation

---

# Stage 1 — Crawler

Purpose:

Download esports articles from Liquipedia.

Output:

JSON files.

Example:

data/raw/cs2/teams/navi.json

Example schema:

{
    "title": "Natus Vincere",
    "game": "cs2",
    "category": "team",
    "url": "...",
    "content": "...",
    "updated_at": "...",
    "tags": [
        "team",
        "ukraine"
    ]
}

Crawler responsibilities:

- download page
- extract article text
- remove menus
- remove navigation
- remove advertisements
- save JSON

Crawler MUST NOT perform embeddings.

Crawler MUST NOT communicate with Qdrant.

Crawler MUST NOT depend on LangChain.

---

# Stage 2 — Ingestion

Purpose:

Convert raw JSON documents into LangChain Documents.

Responsibilities:

- read JSON
- validate schema
- create LangChain Document
- attach metadata

Metadata:

game

category

title

url

updated_at

tags

---

# Stage 3 — Chunking

Use

RecursiveCharacterTextSplitter

Experiment with:

chunk_size

chunk_overlap

Multiple configurations should be easy to test.

---

# Stage 4 — Embeddings

Use

OpenAIEmbeddings

Every chunk must receive an embedding.

---

# Stage 5 — Vector Database

Use

Qdrant

Collection:

esports-wiki

Each point should contain:

id

embedding

page_content

metadata

---

# Stage 6 — Retriever

Use LangChain Retriever.

The retriever should support:

Similarity Search

MMR Search

Top K

Metadata Filters

Example:

game == "cs2"

category == "maps"

---

# Stage 7 — RAG Chain

The chain should:

Question

↓

Retriever

↓

Context

↓

Prompt

↓

LLM

↓

Answer

Prompt rules:

- Never hallucinate.
- Use only retrieved context.
- If information is unavailable, explicitly say so.
- Include sources.

---

# API

FastAPI

Endpoints

POST /ask

Request

{
    "question": "...",
    "game": "cs2"
}

Response

{
    "answer": "...",
    "sources": [
        ...
    ]
}

GET /health

POST /reindex

POST /crawl

---

# Metadata Filtering

Questions like

"What is ADR?"

should automatically search inside

game=cs2

Questions like

"What is Baron Nashor?"

should search

game=lol

The architecture should support automatic routing in future versions.

---

# Future Improvements

Hybrid Search

Reranker

Parent Document Retriever

Contextual Compression Retriever

History-aware Retriever

Streaming Responses

Conversation Memory

Multi Query Retriever

---

# Non Goals

No authentication.

No frontend.

No Agents.

No LangGraph.

No MCP.

No SQL.

The first version should focus exclusively on RAG.

**Scope note (2026-08-11):** these non-goals were scoped to "the first version"
only, and the first version is done. Agents, LangGraph and MCP are now the
active scope of `docs/roadmap-ai-assistant.md` — they are deferred here, not
permanently excluded. This document (`docs/TDD.md`) still governs the RAG
pipeline itself, which is preserved as-is and wrapped (not rewritten) by the new
work. No authentication, no frontend and no SQL remain non-goals for the
assistant too.

---

# Definition of Done

The project is complete when it can:

✓ Crawl Liquipedia pages

✓ Save structured JSON documents

✓ Index documents into Qdrant

✓ Retrieve relevant chunks

✓ Answer questions using only retrieved context

✓ Display sources

✓ Filter by game

✓ Be fully dockerized

✓ Be easy to extend with additional crawlers

---

# Learning Goals

This project should provide practical experience with:

- LangChain Documents
- Document Loaders
- RecursiveCharacterTextSplitter
- OpenAI Embeddings
- Qdrant
- Vector Search
- Retrievers
- Metadata
- Prompt Templates
- Retrieval Chains
- FastAPI integration
- Production-ready RAG architecture