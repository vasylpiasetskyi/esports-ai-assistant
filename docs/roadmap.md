Status: see docs/PROJECT_STATUS.md for detail. As of 2026-08-09, everything through Phase 4 plus Phase 6's first three Future Improvements (Hybrid Search, Multi Query Retriever, Contextual Compression/Reranker) is merged to `master`; new work branches directly off `master`.

Phase 1

Crawler — Done (feature/crawler)

Phase 2

Indexer — Done, split into Ingestion/Chunking/Embeddings/Indexer sub-stages (feature/ingestion, feature/chunking, feature/embeddings, feature/indexer)

Phase 3

Retriever — Done (feature/retriever), plus RAG Chain (feature/rag-chain)

Phase 4

API — Done: POST /ask + GET /health (feature/api), POST /reindex + POST /crawl (feature/api-reindex-crawl)

Phase 5

UI — Optional, not part of this project's current scope; also conflicts with docs/TDD.md's "No frontend" non-goal. Skip unless a demoable UI becomes a separate explicit goal; prefer Phase 6 next.

Phase 6

Hybrid Search

Phase 7

Agents — Beyond the current version's scope; docs/TDD.md's non-goals say "No Agents", justified by "the first version should focus exclusively on RAG." Not a permanent exclusion (the TDD scopes it to "the first version"), just not part of the current RAG-focused work. Revisit after the Future Improvements list (Phase 6) is done.

Phase 8

LangGraph — Same as Phase 7: docs/TDD.md lists "No LangGraph" as a non-goal for the first version, not a permanent one. Natural next step after Agents, not before.