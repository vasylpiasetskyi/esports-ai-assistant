# Learning Goals

This repository is primarily a learning project.

Claude should optimize the implementation for learning rather than minimizing code.

When there are multiple valid implementations:

- prefer the implementation that teaches LangChain concepts
- prefer explicit code over hidden abstractions
- explain why an abstraction is used
- keep LangChain components visible
- avoid "magic"

Every major PR should teach one LangChain concept.

Concept order:

1. Documents
2. Loaders
3. Splitters
4. Embeddings
5. Qdrant
6. Retriever
7. LCEL
8. Prompt Templates
9. RAG
10. FastAPI Integration

Do not skip steps.