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