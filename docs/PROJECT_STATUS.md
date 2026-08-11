# Project Status

Last updated: 2026-08-11 — **development resumed**, extending the `esports-wiki-ai` RAG baseline into an AI assistant per `docs/roadmap-ai-assistant.md`. The repo now lives at `esports-ai-assistant`. Everything below describes the RAG baseline (frozen, preserved as the foundation — see `claude.md`); the "What's next" section at the bottom is the current active scope.

Previously, as of 2026-08-09: **project wrapped up here, deliberately.** All 12 feature branches merged to `master`, pushed to `github.com:vasylpiasetskyi/esports-wiki-ai`, working tree clean and in sync. The user chose to stop active development at this point rather than continue through the remaining "Future Improvements" list.

**Conversation Memory was brainstormed and explicitly not pursued**: the user has already implemented conversation memory (with Postgres/Redis) in another project and didn't need to repeat it here. If resumed later, see the "What's left" section below for where that discussion stopped (client-side history was the agreed direction; Postgres/server-side persistence was explicitly rejected as conflicting with `docs/TDD.md`'s "No SQL" non-goal).

## Branch state — everything merged to master

As of 2026-08-09, the entire linear chain of feature branches was fast-forward-merged into `master` (all 41 commits, no merge commit needed — `master` was a direct ancestor of the chain's tip) and all 12 feature branches were deleted. This broke a long-standing pattern: every previous time the finishing-a-development-branch flow came up, the answer had been "keep the branch as-is." This time the user explicitly chose to merge the whole chain, once asked to clarify that the decision was about the full stack down to `master`, not just the tip branch into its immediate parent.

`master` now contains everything through Future Improvements #1–#4 (Hybrid Search, Multi Query Retriever, Contextual Compression/Reranker). 94/94 tests pass, ruff/black clean, verified on `master` after the merge.

**New work should branch directly off `master`** — the old "each stage branches off the previous stage's branch" convention is retired now that there's no chain of unmerged branches to stack on.

Former chain, for historical reference (`git log` still has all commits, just no branch pointers):
```
master (crawler → ingestion → chunking → embeddings → indexer → retriever → rag-chain
         → api → api-reindex-crawl → hybrid-search → multi-query-retriever → contextual-compression)
```

| Stage | Status |
|---|---|
| Stage 1 — Crawler | Done, verified (31 tests). Real crawl against Liquipedia confirmed working (12/12 pages fetched into `data/raw/`). |
| Stage 2 — Ingestion | Done, verified (43 tests). |
| Stage 3 — Chunking | Done, verified (49 tests). Real run confirmed: 12 documents → 232 chunks (chunk size 1000 chars, overlap 200 — see `ingestion/splitter.py`). |
| Stage 4 — Embeddings | Done, verified (52 tests, zero real OpenAI calls in the test suite). Real CLI run confirmed working once (232 chunks embedded via `text-embedding-3-small`). |
| Stage 5 — Indexer | Done, verified (62 tests). Includes a follow-up fix discovered while building Stage 6: `to_point_struct` now nests metadata under a `"metadata"` payload key (was flat) for `QdrantVectorStore` compatibility. Real CLI run against a live Qdrant not yet done — needs `docker compose up` + `OPENAI_API_KEY`. |
| Stage 6 — Retriever | Done, verified (67 tests). |
| Stage 7 — RAG Chain | Done, verified (71 tests). |
| Stage 8 — API (`POST /ask`, `GET /health` only; `/reindex`/`/crawl` deferred) | Done, verified (79 tests). `api/routes.py` never touches `qdrant_client` directly — infra is built once in `api/main.py`'s `lifespan` and injected via `Depends()`. |
| Stage 8.1 — API `POST /reindex` + `POST /crawl` | Done, verified (85 tests), 4 logical commits. Crawler/indexer business logic extracted into `crawler/service.py`/`ingestion/service.py` (`scripts/run_crawler.py`/`run_indexer.py` are now thin wrappers). Both endpoints are fire-and-forget via FastAPI `BackgroundTasks`, returning `202` immediately; `/crawl` has an in-memory `app.state.is_crawling` concurrency guard (`409` on overlap). Real server run confirmed: `uvicorn api.main:app` + real Qdrant + real `OPENAI_API_KEY`, `POST /ask` returns a real answer after indexing existing `data/raw/` content. `POST /crawl` not yet manually curl'd against the live server (only covered by the mocked-transport test suite). |
| Future Improvements #1 — Hybrid Search | Done, verified (88 tests), 5 commits (spec, plan, dense+BM25 mode, `/ask` wiring, doc corrections). `build_retriever(..., use_hybrid=True)` fuses the existing dense retriever with a `BM25Retriever` (corpus built by scrolling Qdrant, not re-reading `data/raw/`) via `EnsembleRetriever` (`langchain_classic`). Opt-in, dense-only stays default. New deps: `langchain-classic`, `langchain-community` (⚠️ upstream-deprecated/"sunset", accepted — no standalone `BM25Retriever` replacement exists), `rank-bm25`. |
| Future Improvements #2 — Multi Query Retriever | Done, verified (91 tests), 1 commit. `build_retriever(..., use_multi_query=True, llm=...)` wraps whatever retriever came before (dense or hybrid) in `MultiQueryRetriever` — LLM generates 3 rephrasings, retrieves per rephrasing, merges. Fails fast (`ValueError`) if `llm` is omitted. No new deps. Costs +1 LLM call per request. |
| Future Improvements #3+#4 — Contextual Compression Retriever + Reranker | Done, verified (94 tests), 2 commits. `build_retriever(..., use_compression=True, llm=...)` wraps the final retriever (after hybrid/multi-query) in `ContextualCompressionRetriever` + `LLMChainFilter` — LLM judges each retrieved document "YES"/"NO" relevant, drops the "NO"s. **Not** `LLMListwiseRerank` (the more literal "Reranker"): it requires real `with_structured_output()` support, which this project's `FakeListChatModel` test double doesn't provide (confirmed by direct testing — passes the capability check, then raises `NotImplementedError` at call time). No new deps. Costs up to +k LLM calls per request (most expensive of the three flags). |

`/ask` currently accepts three independent, freely-combinable opt-in flags: `use_hybrid`, `use_multi_query`, `use_compression` (all default `False`, preserving original dense-only behavior).

## What's left (per `docs/TDD.md` and `roadmap-esports-wiki-ai.md`)

- **Manual `POST /crawl` smoke test** against the live server — still only covered by the mocked-transport test suite, never curl'd for real.
- **Manual smoke test of `use_hybrid`/`use_multi_query`/`use_compression`** against a live server + real OpenAI — implemented and unit-tested, but never exercised for real end-to-end (see "How to resume" below for the curl commands to try).
- **Remaining `docs/TDD.md` "Future Improvements"** not yet started, in the order discussed:
  - **Parent Document Retriever** — discussed and **recommended to skip/defer**: it shines when child chunks are tiny (sentence-level) and need a much larger parent for LLM context; this project's chunks are already 1000 chars/200 overlap (`ingestion/splitter.py`), a size that doesn't have that problem. Doing it "properly" would mean revisiting Stage 3 chunking strategy first, which is a bigger scope than the last three retriever-flag features.
  - **Conversation Memory** — brainstormed 2026-08-09, then explicitly stopped by the user (already implemented elsewhere, with Postgres/Redis, no need to repeat it here). Agreed direction if resumed: client-side history only (`AskRequest` gains a `history: list[{role, content}]` field; no server-side persistence, no SQL) — the question of whether history should also affect retrieval (vs. only the final answer-generation prompt) was raised but never answered before the session ended. **History-aware Retriever** depends on Conversation Memory and was never reached.
  - **Streaming Responses** (API-layer, `/ask` → `StreamingResponse`) — not brainstormed, still open if development resumes.
- **Automatic game routing** (inferring the `game` metadata filter from the question text) — TDD explicitly defers this to "future versions." Right now callers must build the retriever with an explicit `metadata_filter={"game": ...}` themselves.
- **Non-goals per TDD** (still true for "the first version"): no auth, no frontend, no agents, no LangGraph, no MCP, no SQL. `roadmap-esports-wiki-ai.md`'s Phase 5 (UI), Phase 7 (Agents), Phase 8 (LangGraph) are annotated as explicitly deferred beyond v1, not permanently excluded — same status as before, now written down in the roadmap itself.
- **A genuine full end-to-end real run** (crawl → ingest → chunk → embed → index → retrieve → answer, all against live services in one sitting) still hasn't happened in one sitting.

## How to resume

1. Pick the next feature (Streaming Responses is the main open candidate — see above; Conversation Memory is deliberately parked, not abandoned for lack of a plan) and branch it directly off `master` — there's no longer a chain of unmerged branches to stack on.
2. To try the full pipeline for real, in order:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   uv run --env-file .env python -m scripts.run_crawler
   uv run --env-file .env python -m scripts.run_indexer
   uv run --env-file .env python -m scripts.run_retriever   # interactive
   uv run --env-file .env uvicorn api.main:app --reload     # then curl below
   ```
   Note: `run_indexer` re-runs ingestion/chunking/embeddings internally (it chains from `data/raw/` forward), so running just `run_indexer` alone is enough to exercise the whole pipeline up through Qdrant. Equivalently, `POST /reindex` does the same work via the API in the background.
3. To manually compare retrieval strategies once the server is up and the collection is populated:
   ```bash
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Who is s1mple?", "game": "cs2"}'                                          # dense-only (default)
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Who is s1mple?", "game": "cs2", "use_hybrid": true}'                       # + BM25 fusion
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Who is s1mple?", "game": "cs2", "use_multi_query": true}'                  # + LLM query rephrasing
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Who is s1mple?", "game": "cs2", "use_compression": true}'                  # + LLM relevance filter
   # all three combine freely:
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Who is s1mple?", "game": "cs2", "use_hybrid": true, "use_multi_query": true, "use_compression": true}'
   ```
   `use_multi_query` and `use_compression` each add real extra LLM calls (latency/cost) — `use_compression` the most (up to one per retrieved document).

## What's next — AI Assistant roadmap (active scope)

Per `docs/roadmap-ai-assistant.md`, in order:

1. **Milestone 1 — Done (2026-08-11).** `rag/service.py` now has `RAGService.answer(question, game=None, *, use_hybrid=False, use_multi_query=False, use_compression=False)`, hiding Qdrant/retriever/chain construction behind one call. `api/routes.py`'s `/ask` handler only depends on `RAGService` now (no more direct `build_retriever`/`answer_question`/`COLLECTION_NAME` imports). `rag/chains.py` and `rag/retriever.py` are unchanged, just called from inside the service. Sync, not async — the roadmap's illustrative signature was `async def answer(...)`, but the whole codebase (crawler, ingestion, API routes) is sync, and there was nothing actually I/O-bound-and-awaitable to gain from async here; kept consistent with existing conventions instead. Verified: 97/97 tests pass (3 new for `RAGService`), ruff/black clean. Three existing tests that spied on `build_retriever` at the `api.routes` module (`test_ask_passes_use_hybrid/use_multi_query/use_compression_flag_to_build_retriever`) were updated to spy on `rag.service` instead, since that's where the call moved to — expected fallout from moving the construction into the service layer, not a behavior change.
2. **Milestone 2** — `get_player`, `get_team`, `get_match` LangChain tools, each backed by its own `services/*_service.py`, backed initially by a mock API or static JSON fixtures (no real company data).
3. **Milestone 3** — Expose the RAG pipeline itself as a `search_knowledge_base` tool, calling `RAGService` (no duplicated RAG logic).
4. **Milestone 4** — Manual tool-calling loop (LLM → tool call → Python function → `ToolMessage` → LLM), understood before any agent abstraction is introduced.
5. **Milestone 5** — Agent with access to all four tools, exposed via a new `POST /assistant` endpoint (kept alongside `POST /ask`).
6. **Milestone 6** — LangGraph "match investigation" workflow (typed state, conditional routing, retry path), exposed via `POST /investigate`.
7. **Milestone 7** — MCP server (`mcp/server.py` + `mcp/tools/`) reusing the same service layer as the LangChain tools; verified against Claude Code as an MCP client.
8. **Milestone 8** — Evaluation dataset (`tests/evals/questions.json`) and basic observability (request id, latency, tool-call tracing, token usage).

**Correction to a note below**: the "`langgraph`, a non-goal" aside under "Verify LangChain import paths" was true for the RAG-only v1 scope (`docs/TDD.md`'s non-goals). LangGraph is now an explicit goal (Milestone 6) — that note is historical context for *why* `langchain_classic` was chosen over the full `langchain` meta-package at the time, not a still-standing constraint.

## Established conventions for continuing this work

(Full rules live in `.claude/rules/` and the global `CLAUDE.md` — this is just a pointer, not a restatement.)

- One TDD stage = one design spec (via brainstorming) → one implementation plan (via writing-plans) → inline execution → its own feature branch. **Updated 2026-08-09**: branches now fork directly off `master` (the old "off the previous stage's branch" chain was collapsed by merging everything to `master`) — merge back to `master` when a stage is verified, rather than defaulting to "keep as-is."
- Every external dependency (Liquipedia, OpenAI, Qdrant) is injected via an interface (`Source`, `Embeddings`, `BaseChatModel`, `QdrantClient`) specifically so the test suite never hits real network or costs real money.
- Never run `git commit` without printing the message first and getting the user's explicit go-ahead on that exact message.
- **Verify LangChain import paths/behavior by direct testing before writing them into a spec or plan — don't trust docs or memory.** This bit repeatedly during the last three features: `EnsembleRetriever`/`MultiQueryRetriever`/`ContextualCompressionRetriever` all turned out to live in `langchain_classic`, not `langchain_core` or the full `langchain` meta-package (which pulls in `langgraph`, a non-goal); `rank_bm25` is a lazy, undeclared dependency of `langchain_community`'s `BM25Retriever`; BM25's IDF formula degenerates to zero on corpora smaller than ~3 documents; `LLMListwiseRerank` silently passes a capability check but then fails at runtime against this project's fake chat model. Always run a throwaway `python -c` prototype against the real installed library before locking a test or design into a plan.
