---
name: architecture
description: Guidelines for project architecture and module boundaries
---

# Architecture Skill

## Goal

Ensure the project follows a clean, production-ready architecture.

## Principles

- Follow SOLID principles.
- Prefer composition over inheritance.
- Keep business logic independent from infrastructure.
- Separate crawling, ingestion, indexing and retrieval.

## Layer Responsibilities

### crawler

Responsible only for downloading and normalizing data.

Must NOT:

- depend on LangChain
- generate embeddings
- communicate with Qdrant

### ingestion

Responsible for converting raw documents into LangChain Documents.

### indexing

Responsible for:

- chunking
- embeddings
- indexing into Qdrant

### rag

Responsible for:

- retriever
- prompt
- chain

### api

Responsible only for HTTP.

Business logic must live in services.

### rag (as a service)

Wrapped behind a `RAGService` so callers never touch Qdrant/retriever/chain
directly. See `docs/roadmap-ai-assistant.md` §4.

### tools

Thin LLM-facing adapters (LangChain `Tool`/`@tool` functions with schemas).
Must NOT contain business logic — delegate to `services/`.

### services (esports data)

Responsible for business logic behind each tool (`PlayerService`, `TeamService`,
`MatchService`). Talk to a data source (mock API / fixtures / public API), not
the LLM. Shared by LangChain tools, the Agent, and MCP tools — never duplicated.

### agents

Responsible for deciding which capability to use (RAG vs. tools vs. workflow),
selecting tools, and producing a final answer. Must not fabricate tool results.

### workflows (LangGraph)

Responsible only for workflows that genuinely need explicit multi-step
orchestration with typed state and conditional routing (e.g. match
investigation). Not a default replacement for the Agent.

### mcp

A separate interface exposing the same `services/` layer to MCP clients. Must
NOT contain business logic of its own, and must NOT be a FastAPI route.

## Best Practices

- Small classes.
- One responsibility per module.
- Explicit dependencies.
- Constructor dependency injection.

## Anti-patterns

- God classes
- Circular imports
- Utility modules with unrelated functions
- Hidden global state