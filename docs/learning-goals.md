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

Concept order (RAG foundation, done):

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

Concept order (AI assistant, active — see `docs/roadmap-ai-assistant.md`):

11. Service boundaries (`RAGService`) — hiding a pipeline behind a clean interface
12. LangChain Tools — schemas, descriptions, structured input/output
13. Manual tool-calling loop — tool call → execution → `ToolMessage` → LLM
14. Agents — tool selection, multi-tool calls, combining RAG + structured data
15. LangGraph — state, nodes, conditional edges, loops/retries
16. MCP — exposing the same tools/services through a standardized interface
17. Evaluation — repeatable question sets, retrieval/tool/answer correctness
18. Observability — tracing tool calls, latency, token usage

Do not skip steps.