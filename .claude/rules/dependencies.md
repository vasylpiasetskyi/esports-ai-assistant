---
name: dependencies
alwaysApply: true
---

# Dependency Rules

## Goal

Keep the dependency graph as small and maintainable as possible.

## Principles

Every dependency must have a clear purpose.

Before adding a package, consider whether the standard library is sufficient.

## Preferred Libraries

- FastAPI
- LangChain
- LangChain Community
- LangChain OpenAI
- Qdrant Client
- Pydantic
- httpx
- BeautifulSoup
- Trafilatura

Planned for the AI assistant roadmap (`docs/roadmap-ai-assistant.md`) — add only
when the corresponding milestone is actually reached, not upfront:

- LangGraph — Milestone 6 (investigation workflow), only once a real workflow
  needs explicit multi-step orchestration.
- An MCP SDK (e.g. the official `mcp` Python package) — Milestone 7.

## Avoid

Avoid dependencies that:

- duplicate existing functionality
- are abandoned
- have poor documentation
- significantly increase complexity

## LangChain

Always prefer official LangChain packages over community forks unless there is a clear reason.

## Replacements

Design the code so these components can be replaced with minimal changes:

- LLM
- Embedding model
- Vector database