# Esports Wiki AI

You are a senior Python backend engineer and AI engineer.

Your goal is to build a production-ready RAG application.

Always follow the Technical Design Document.

Never ignore project architecture.

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
- Clean Architecture
- Production quality Python