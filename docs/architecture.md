Crawler reads its page list from config/pages.json.

## RAG pipeline (foundation, preserved)

Crawler

↓

Raw JSON

↓

Indexer

↓

Qdrant

↓

Retriever

↓

LLM

↓

API

## Target architecture (per docs/roadmap-ai-assistant.md)

The RAG pipeline above becomes one capability among several, reached through an
Agent:

```text
                         User
                           │
                           ▼
                    AI Assistant API
                           │
                           ▼
                         Agent
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
             RAG          Tools       Workflows
              │            │            │
              ▼            ▼            ▼
           Qdrant      Esports API   LangGraph
                           │
                           ▼
                    External services
                           │
                           ▼
                          MCP
```

Principle:

```text
RAG        = knowledge / unstructured information
Tools      = structured or current information / actions
Agent      = decides which capability to use
LangGraph  = controls complex multi-step workflows
MCP        = standardized interface for exposing tools to AI clients
```

Do not build these ahead of need. Follow the milestone order in
`docs/roadmap-ai-assistant.md` §24 — RAG is refactored into a `RAGService` first,
then Tools, then the manual tool-calling loop, then the Agent, then LangGraph,
then MCP.