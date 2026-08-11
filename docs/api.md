## Implemented

POST /ask
    Direct RAG (dense / hybrid / multi-query / contextual-compression, opt-in flags)

POST /crawl
    Knowledge ingestion (background task)

POST /reindex
    Knowledge indexing (background task)

GET /health

## Planned (docs/roadmap-ai-assistant.md)

POST /assistant
    Agent + Tools + RAG — Milestone 5

POST /investigate
    LangGraph match investigation workflow — Milestone 6

MCP is a separate interface (`mcp/server.py`), not a FastAPI route — Milestone 7.

Note: `POST /index` above was never implemented as a separate endpoint; indexing
happens via `POST /reindex`.