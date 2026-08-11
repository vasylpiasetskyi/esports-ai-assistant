# Esports AI Assistant

An AI assistant for esports (CS2, Dota 2, League of Legends, Valorant) that combines Retrieval-Augmented Generation (RAG) over a private knowledge base crawled from Liquipedia with structured-data tools, a tool-calling Agent, a LangGraph investigation workflow, and an MCP server — three ways to ask the same underlying capabilities (`/ask`, `/assistant`, `/investigate`), plus a fourth, protocol-level way for any MCP client (Claude Code, Claude Desktop, etc.) to use them directly.

See `docs/TDD.md` for the original RAG technical design, `docs/roadmap-ai-assistant.md` for the assistant roadmap that builds on top of it, and `docs/architecture.md` / `docs/decisions.md` for architecture decisions.

## Status

Milestones 1-7 of `docs/roadmap-ai-assistant.md` are done. See `docs/PROJECT_STATUS.md` for the full history; summary below.

**RAG foundation** (frozen, preserved): crawl → ingest → chunk → embed → index → retrieve → answer.

- **Crawler** — fetches a fixed set of Liquipedia articles per game via the MediaWiki API, cleans the HTML into article text, and writes normalized JSON to `data/raw/<game>/<category>/<slug>.json`.
- **Ingestion / Chunking / Embeddings / Indexer** — loads the crawled JSON, splits it into chunks, embeds them (`text-embedding-3-small`), and indexes them into Qdrant.
- **Retriever** — dense vector search by default, with three independent, freely-combinable opt-in modes: `use_hybrid` (dense + BM25 fusion), `use_multi_query` (LLM-generated question rephrasings), `use_compression` (LLM relevance filtering of retrieved documents).
- **RAG Chain** — builds an answer from retrieved context using an OpenAI chat model, with source URLs attached, wrapped behind `RAGService.answer(...)` (`app/rag/service.py`) so no caller touches Qdrant/the retriever/the chain directly.

**AI assistant layer** (built on top, `app/`):

- **Tools** (`app/tools/`) — `get_player`, `get_team`, `get_match` (structured lookups over `app/services/*.py`, backed by mock fixtures — no real company data) and `search_knowledge_base` (wraps `RAGService`). Thin adapters; all business logic lives in `app/services/`.
- **Agent** (`app/agents/esports_agent.py`) — a LangChain tool-calling agent with access to all four tools, exposed via `POST /assistant` alongside the unchanged `POST /ask`.
- **LangGraph workflow** (`app/workflows/`) — a typed-state match-investigation graph (`analyze_question → get_match → get_match_data → retrieve_knowledge → analyze_evidence`, with a bounded retry loop and a final report), exposed via `POST /investigate`.
- **MCP server** (`mcp_server/`) — exposes the same four tools over the Model Context Protocol (stdio), reusing the exact same `app/services/*.py` layer as the LangChain tools. Named `mcp_server/`, not `mcp/`, to avoid shadowing the installed `mcp` SDK package.

See `docs/roadmap-esports-wiki-ai.md` for the RAG-only improvements that were considered separately, and `docs/roadmap-ai-assistant.md` for what's left (Milestone 8: evaluation dataset + observability).

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

curl -X POST http://localhost:8000/assistant -H "Content-Type: application/json" \
  -d '{"question": "Tell me about s1mple and his current team.", "game": "cs2"}'

curl -X POST http://localhost:8000/investigate -H "Content-Type: application/json" \
  -d '{"question": "Why did NAVI lose their latest match?", "game": "cs2"}'

curl http://localhost:8000/health

curl -X POST http://localhost:8000/crawl      # 202, runs in the background
curl -X POST http://localhost:8000/reindex    # 202, runs in the background
```

- `POST /ask` — direct RAG. Accepts three optional boolean flags (all default `false`, combinable): `use_hybrid`, `use_multi_query`, `use_compression`.
- `POST /assistant` — Agent + tools + RAG. The agent decides which of `get_player`/`get_team`/`get_match`/`search_knowledge_base` to call, if any.
- `POST /investigate` — LangGraph match-investigation workflow. Returns `{"report": str, "findings": list[str]}`.

All three accept `{"question": str, "game": str | None}` and can be compared side by side for the same question.

## Running the MCP server

Exposes `get_player`/`get_team`/`get_match`/`search_knowledge_base` to any MCP client (Claude Code, Claude Desktop, etc.) over stdio, reusing the same `app/services/*.py` layer as the LangChain tools above — no duplicated business logic.

```bash
claude mcp add esports-ai -- uv run --directory $(pwd) python -m mcp_server.server
```

Then, in a Claude Code session, try asking things like "Find information about s1mple." or "Get the latest match for NAVI." and confirm the tools get discovered and called.

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

This started as a personal project for practicing LangChain, RAG, and production-style Python architecture. It grew into a broader AI assistant covering LangChain tools, a tool-calling agent, a LangGraph workflow, and an MCP server — see `docs/roadmap-ai-assistant.md` for the full milestone history, and `docs/PROJECT_STATUS.md` for exactly what's done and what's left (Milestone 8: evaluation + observability).
