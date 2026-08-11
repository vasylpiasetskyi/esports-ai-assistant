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