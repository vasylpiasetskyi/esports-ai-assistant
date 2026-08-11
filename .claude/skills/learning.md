---
name: learning
description: Optimize implementations for learning LangChain concepts
---

# Learning Skill

## Goal

This repository is educational.

Optimize the code to help the developer understand LangChain and modern AI engineering.

## Principles

When multiple valid implementations exist:

- Prefer the more educational implementation.
- Avoid unnecessary abstractions.
- Keep important LangChain concepts visible.
- Explain architectural decisions when appropriate.

## Progression

Introduce concepts gradually.

Preferred order:

1. Documents
2. Loaders
3. Splitters
4. Embeddings
5. Vector Store
6. Retriever
7. LCEL
8. Prompt Templates
9. Retrieval Chains
10. FastAPI Integration

Do not skip intermediate concepts.

## Code

Favor explicit implementations over "magic".

The developer should be able to understand each layer independently.

## Documentation

Whenever a new LangChain concept is introduced:

- explain why it is used
- explain what problem it solves
- explain how it interacts with existing components