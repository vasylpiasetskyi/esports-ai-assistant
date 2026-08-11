# Esports AI Assistant

A Retrieval-Augmented Generation (RAG) application that answers questions about esports (CS2, Dota 2, League of Legends, Valorant) from a private knowledge base crawled from Liquipedia, instead of relying solely on an LLM's own knowledge — now being extended into a full AI assistant (RAG + Tools + Agent + LangGraph + MCP).

See `docs/TDD.md` for the original RAG technical design, `docs/roadmap-ai-assistant.md` for the assistant roadmap that builds on top of it, and `docs/architecture.md` / `docs/decisions.md` for architecture decisions.

## Status

The RAG foundation is implemented end to end: crawl → ingest → chunk → embed → index → retrieve → answer, plus a FastAPI service in front of it. See `docs/PROJECT_STATUS.md` for exactly what's done and what's next (currently: Milestone 1 of `docs/roadmap-ai-assistant.md` — refactoring RAG into a reusable `RAGService`).

- **Crawler** — fetches a fixed set of Liquipedia articles per game via the MediaWiki API, cleans the HTML into article text, and writes normalized JSON to `data/raw/<game>/<category>/<slug>.json`.
- **Ingestion / Chunking / Embeddings / Indexer** — loads the crawled JSON, splits it into chunks, embeds them (`text-embedding-3-small`), and indexes them into Qdrant.
- **Retriever** — dense vector search by default, with three independent, freely-combinable opt-in modes: `use_hybrid` (dense + BM25 fusion), `use_multi_query` (LLM-generated question rephrasings), `use_compression` (LLM relevance filtering of retrieved documents).
- **RAG Chain** — builds an answer from retrieved context using an OpenAI chat model, with source URLs attached.
- **API** — `POST /ask`, `GET /health`, `POST /crawl`, `POST /reindex` (see below).

See `docs/roadmap-esports-wiki-ai.md` for the RAG-only improvements that were considered and `docs/roadmap-ai-assistant.md` for what's actually planned next (Tools, Agent, LangGraph, MCP).

## Setup

Requires Python 3.13, [uv](https://docs.astral.sh/uv/), and Docker (for Qdrant).

```bash
uv sync
```

Create a `.env` file with an OpenAI API key:

```bash
OPENAI_API_KEY=sk-...
```

Start Qdrant:

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Running the full pipeline

```bash
uv run --env-file .env python -m scripts.run_crawler   # crawl Liquipedia -> data/raw/
uv run --env-file .env python -m scripts.run_indexer    # ingest + chunk + embed + index -> Qdrant
uv run --env-file .env python -m scripts.run_retriever  # interactive retrieval, no API needed
```

`run_indexer` re-runs ingestion/chunking/embeddings internally, so it's enough on its own to go from `data/raw/` to a populated Qdrant collection.

## Running the API

```bash
uv run --env-file .env uvicorn app.api.main:app --reload
```

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "Who is s1mple?", "game": "cs2"}'

curl http://localhost:8000/health

curl -X POST http://localhost:8000/crawl      # 202, runs in the background
curl -X POST http://localhost:8000/reindex    # 202, runs in the background
```

`POST /ask` accepts three optional boolean flags (all default `false`, combinable): `use_hybrid`, `use_multi_query`, `use_compression`.

## Tests

```bash
uv run pytest          # unit tests only (default)
uv run pytest -m integration   # also hits the real Liquipedia API
```

## Linting and formatting

```bash
uv run ruff check .
uv run black --check .
```

## About

This started as a personal project for practicing LangChain, RAG, and production-style Python architecture. It's now being extended into a broader AI assistant to also practice LangChain tools, agents, LangGraph workflows, and MCP — see `docs/roadmap-ai-assistant.md`.
