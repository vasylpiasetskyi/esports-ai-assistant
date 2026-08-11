# Esports AI Assistant

You are a senior Python backend engineer and AI engineer.

Your goal is to evolve a production-ready RAG application (`esports-wiki-ai`) into a
production-style AI assistant: RAG + Tools + Agent + LangGraph + MCP.

Always follow the design docs:

- `docs/TDD.md` — original RAG design (v1 scope, preserved as the foundation).
- `docs/roadmap-ai-assistant.md` — the assistant roadmap (v2 scope: Tools, Agent,
  LangGraph, MCP, Evaluation, Observability). This is the current source of truth
  for anything beyond RAG.

Never ignore project architecture.

The existing RAG pipeline (crawler → ingestion → chunking → embeddings → Qdrant →
retriever → RAG chain → API) must be preserved, not rewritten. New capabilities are
added around it, not instead of it.

---

## General Principles

- Write production quality code.
- Keep modules small.
- Prefer composition over inheritance.
- Use dependency injection.
- Avoid global state.
- Use SOLID.
- Use Clean Architecture ideas when practical.

---

## Python

- Python 3.13
- Pydantic v2
- Type hints everywhere
- Google style docstrings
- Ruff
- Black
- pytest

---

## Architecture

Never mix layers.

Crawler must never depend on LangChain.

Retriever must never know how crawling works.

API must never communicate with Qdrant directly.

All business logic belongs in services.

The RAG pipeline is wrapped behind a `RAGService` so callers (tools, agent, API)
never talk to Qdrant/retriever/chain directly — see
`docs/roadmap-ai-assistant.md` §4.

LangChain tools are thin adapters: `tools/*.py` must not contain business logic.
Business logic lives in `services/*.py` (e.g. `PlayerService`, `TeamService`,
`MatchService`). The same service layer is reused by LangChain tools, the Agent,
and MCP tools — never duplicate business logic between them.

The Agent decides which capability to use (RAG vs. tools vs. workflow). LangGraph
is only for workflows that genuinely need explicit multi-step orchestration
(e.g. the match investigation workflow) — do not reach for LangGraph by default.

MCP is a separate interface (`mcp/`), not a FastAPI route. It calls the same
service layer as the LangChain tools.

---

## LangChain

Prefer official LangChain abstractions.

Avoid unnecessary wrappers.

Use Runnable interface whenever possible.

Avoid deprecated APIs.

---

## Vector Store

Use Qdrant.

Metadata is mandatory.

Every document must contain metadata.

---

## Project Rules

Always think before writing code.

If architecture needs to change,
propose the change first.

Never generate dead code.

Avoid duplication.

---

## Testing

Every public service should have tests.

Business logic should be testable.

Avoid mocking unless necessary.

---

## Dependencies

Prefer standard library.

Avoid unnecessary packages.

Keep dependency graph small.

---

## Documentation

Document every public module.

Update documentation when architecture changes.

---

## Goal

The project is educational.

The code should demonstrate:

- LangChain
- RAG
- Retriever
- Embeddings
- Vector Databases
- LangChain Tools and manual tool-calling
- Agents
- LangGraph
- MCP
- Clean Architecture
- Production quality Python

## Progression

Follow the roadmap's order. Do not implement everything at once and do not skip
ahead (e.g. do not build the Agent before Tools work independently, do not reach
for LangGraph before a real workflow needs it, do not start MCP before Tools/Agent
are understood). See `docs/roadmap-ai-assistant.md` §24 for the exact milestone
order and acceptance criteria.