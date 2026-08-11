# Esports AI Assistant — Development Roadmap

## 1. Project Goal

Extend the existing `esports-wiki-ai` RAG application into a production-style AI assistant for esports.

The project should progressively demonstrate:

1. LangChain RAG
2. LLM tools / tool calling
3. Agent architecture
4. LangGraph workflows
5. MCP server integration
6. Evaluation and observability

The existing RAG implementation is the foundation and should be preserved rather than rewritten unnecessarily.

---

# 2. Current Baseline

The repository already contains a working RAG pipeline:

```text
Liquipedia
    ↓
Crawler
    ↓
Normalized JSON
    ↓
Ingestion
    ↓
Chunking
    ↓
OpenAI Embeddings
    ↓
Qdrant
    ↓
Retriever
    ↓
RAG Chain
    ↓
FastAPI
```

Existing retrieval capabilities:

* dense vector search
* hybrid search
* BM25
* MultiQuery retrieval
* contextual compression
* source URLs
* game filtering
* FastAPI API

Existing endpoints:

```text
POST /ask
GET  /health
POST /crawl
POST /reindex
```

Do not remove or break these capabilities.

The existing `/ask` endpoint should remain available as a direct RAG endpoint.

---

# 3. Target Architecture

The final system should evolve toward:

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

The important architectural principle is:

```text
RAG = knowledge / unstructured information

Tools = structured or current information / actions

Agent = decides which capability to use

LangGraph = controls complex multi-step workflows

MCP = standardized interface for exposing tools to AI clients
```

---

# 4. Phase 1 — Refactor the RAG into a reusable service

Before implementing tools, make the existing RAG callable from application code.

## Goal

The RAG implementation must be usable as a normal Python service:

```python
result = rag_service.search(
    question="Who is s1mple?",
    game="cs2",
)
```

The service should hide:

* Qdrant implementation
* embedding implementation
* retriever configuration
* prompt construction
* LLM invocation

The caller should not need to know how Qdrant works.

## Required interface

Create a clear service boundary similar to:

```python
class RAGService:
    async def answer(
        self,
        question: str,
        game: str,
        *,
        use_hybrid: bool = False,
        use_multi_query: bool = False,
        use_compression: bool = False,
    ) -> RAGAnswer:
        ...
```

`RAGAnswer` should contain at minimum:

```text
answer
sources
```

Do not over-engineer this abstraction.

---

# 5. Phase 2 — Tools

## Goal

Learn and implement LangChain tools independently of agents.

The system should expose esports data through tools.

Start with only three tools:

```text
get_player
get_team
get_match
```

Additionally expose the existing RAG as:

```text
search_knowledge_base
```

---

## 5.1 Tool: get_player

Input:

```text
game
player_name
```

Example:

```text
get_player(
    game="cs2",
    player_name="s1mple"
)
```

Return structured data.

Example:

```json
{
  "name": "s1mple",
  "game": "cs2",
  "team": "NAVI"
}
```

Use Pydantic models for input/output where appropriate.

---

## 5.2 Tool: get_team

Input:

```text
game
team_name
```

Example:

```text
get_team(
    game="cs2",
    team_name="NAVI"
)
```

Return structured team information.

---

## 5.3 Tool: get_match

Input:

```text
game
match_id
```

Return structured match information:

```text
teams
score
status
date
tournament
```

---

# 6. Data Source for Tools

Do not use real company data or internal company APIs.

Use one of:

1. public esports APIs
2. Liquipedia/public data
3. a small local mock API
4. static JSON fixtures

For learning, a mock API is acceptable.

The important part is the architecture:

```text
LangChain Tool
      ↓
Service
      ↓
Data source
```

Do not put API/business logic directly inside the tool.

---

# 7. Tool Layer Architecture

Use this separation:

```text
tools/
    player.py
    team.py
    match.py
    knowledge.py
```

and:

```text
services/
    player_service.py
    team_service.py
    match_service.py
```

Example:

```text
LLM
 ↓
get_player tool
 ↓
PlayerService
 ↓
External API / mock API
```

The tool should be a thin LLM-facing adapter.

---

# 8. RAG as a Tool

Expose the existing RAG pipeline as a LangChain tool:

```text
search_knowledge_base
```

Input:

```text
question
game
```

Example:

```text
search_knowledge_base(
    question="Who is s1mple?",
    game="cs2"
)
```

The tool should call the existing `RAGService`.

Do not duplicate the RAG implementation.

---

# 9. Learn Tool Calling

Before creating an agent, implement the raw tool-calling loop manually.

Understand this flow:

```text
User
 ↓
LLM
 ↓
Tool call
 ↓
Python function
 ↓
Tool result
 ↓
LLM
 ↓
Final answer
```

Implement a small test flow where the model can call:

```text
get_player
get_team
get_match
search_knowledge_base
```

The goal is to understand:

* tool schemas
* tool descriptions
* arguments
* tool calls
* tool results
* ToolMessage
* multiple tool calls
* errors from tools

Do not immediately hide everything behind an agent abstraction.

---

# 10. Phase 3 — Agent

Once tools work independently, introduce an Agent.

## Goal

The user should be able to ask:

```text
Tell me about s1mple and his current team.
```

The agent should decide that it needs:

```text
search_knowledge_base
+
get_player
+
get_team
```

Another example:

```text
Why did NAVI lose their latest match?
```

The agent may need:

```text
get_team
get_match
search_knowledge_base
```

The exact tool sequence should not be hardcoded.

---

# 11. Agent Requirements

The agent should have access to:

```text
search_knowledge_base
get_player
get_team
get_match
```

The agent should:

* select tools
* provide tool arguments
* process tool results
* call multiple tools when necessary
* generate a final answer

Add a dedicated endpoint:

```text
POST /assistant
```

Example:

```json
{
  "question": "Why did NAVI lose their latest match?",
  "game": "cs2"
}
```

Keep:

```text
POST /ask
```

for direct RAG.

This allows comparison:

```text
/ask
    → direct RAG

/assistant
    → Agent + tools + RAG
```

---

# 12. Agent Error Handling

Implement basic handling for:

* invalid tool arguments
* unavailable data
* tool timeout
* tool exceptions
* empty search results
* LLM refusing/being unable to answer

The agent must not fabricate tool results.

If a tool fails, the final response should clearly indicate that the required information could not be retrieved.

---

# 13. Phase 4 — LangGraph

Do not immediately rewrite the entire Agent using LangGraph.

First identify a real workflow that benefits from explicit orchestration.

Implement:

# Match Investigation Workflow

Example question:

```text
Investigate why NAVI lost their latest match.
```

Workflow:

```text
START
  ↓
Understand investigation
  ↓
Get latest match
  ↓
Get match statistics
  ↓
Search knowledge base
  ↓
Analyze evidence
  ↓
Enough evidence?
  ├── NO → gather more information
  │
  └── YES
       ↓
   Generate report
       ↓
      END
```

---

# 14. LangGraph Concepts to Learn

Implement and understand:

* State
* Nodes
* Edges
* Conditional edges
* Tool nodes
* loops
* retries
* state updates
* checkpoints
* human-in-the-loop

Do not use LangGraph merely because it is available.

Every graph node should have a clear responsibility.

---

# 15. Suggested Graph State

Create a typed state similar to:

```python
class InvestigationState(TypedDict):
    question: str
    game: str
    match_id: str | None
    evidence: list[Evidence]
    findings: list[Finding]
    needs_more_data: bool
    final_answer: str | None
```

Keep state minimal.

Do not store unnecessary objects in graph state.

---

# 16. LangGraph Investigation Nodes

Possible nodes:

```text
analyze_question
get_match
get_match_data
retrieve_knowledge
analyze_evidence
decide_if_more_data_needed
generate_report
```

Conditional routing:

```text
analyze_evidence
        │
        ├── enough evidence → generate_report
        │
        └── insufficient → get_more_data
```

---

# 17. Phase 5 — MCP

Only start MCP after Tools, Agents and LangGraph are understood.

## Goal

Expose esports capabilities through an MCP server.

Create:

```text
mcp/
    server.py
    tools/
```

Expose:

```text
get_player
get_team
get_match
search_knowledge_base
```

The MCP implementation should call the same service layer as the LangChain tools.

Architecture:

```text
LangChain Tool
       │
       ▼
PlayerService
       │
       ▼
Data source


MCP Tool
       │
       ▼
PlayerService
       │
       ▼
Data source
```

Do not duplicate business logic.

---

# 18. MCP Server

Create an MCP server named something like:

```text
esports-ai
```

Expose read-only tools initially.

Example:

```text
get_player
get_team
get_match
search_knowledge_base
```

Do not implement destructive actions.

---

# 19. MCP Integration with Claude

Configure the MCP server as a local MCP server for Claude Code.

Test requests such as:

```text
Find information about s1mple.
```

```text
Get the latest match for NAVI.
```

```text
Search the esports knowledge base for information about the player.
```

Verify that Claude can:

1. discover tools
2. understand their descriptions
3. call them
4. receive structured results
5. use results in its answer

---

# 20. Phase 6 — Evaluation

Add a small evaluation dataset.

Example:

```text
tests/evals/
    questions.json
```

Each test case should contain:

```json
{
  "question": "Who is s1mple?",
  "game": "cs2",
  "expected_sources": ["..."]
}
```

Create separate evaluation categories:

```text
RAG questions
Tool questions
Agent questions
Investigation questions
```

Measure at least:

* answer correctness
* retrieval correctness
* source relevance
* tool selection
* tool argument correctness

Do not build a complicated evaluation framework.

A simple repeatable evaluation script is enough.

---

# 21. Phase 7 — Observability

Add basic observability.

Track:

```text
request_id
latency
LLM calls
tool calls
retrieval latency
number of retrieved documents
token usage
errors
```

For agent requests, log the execution flow:

```text
Agent
 ↓
get_match
 ↓
search_knowledge_base
 ↓
get_team
 ↓
final answer
```

Do not log secrets or sensitive data.

---

# 22. API Structure

Final API should expose separate responsibilities:

```text
GET  /health

POST /ask
    Direct RAG

POST /assistant
    Agent

POST /investigate
    LangGraph investigation workflow

POST /crawl
    Knowledge ingestion

POST /reindex
    Knowledge indexing
```

MCP should be a separate interface rather than another FastAPI endpoint.

---

# 23. Target Architecture

The final application should approximately look like:

```text
esports-ai-assistant/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── ask.py
│   │       ├── assistant.py
│   │       ├── investigate.py
│   │       └── health.py
│   │
│   ├── rag/
│   │   ├── service.py
│   │   ├── retrievers/
│   │   └── ...
│   │
│   ├── tools/
│   │   ├── player.py
│   │   ├── team.py
│   │   ├── match.py
│   │   └── knowledge.py
│   │
│   ├── services/
│   │   ├── player_service.py
│   │   ├── team_service.py
│   │   └── match_service.py
│   │
│   ├── agents/
│   │   └── esports_agent.py
│   │
│   └── workflows/
│       ├── state.py
│       ├── graph.py
│       └── nodes/
│
├── mcp/
│   ├── server.py
│   └── tools/
│
├── ingestion/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/
│
├── docs/
│   ├── architecture.md
│   ├── decisions.md
│   └── roadmap.md
│
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 24. Implementation Order

Do not implement everything at once.

Follow exactly this order:

## Milestone 1

Refactor existing RAG into:

```text
RAGService
```

Acceptance criteria:

* `/ask` still works
* existing retrieval modes still work
* existing tests pass

---

## Milestone 2

Implement:

```text
get_player
get_team
get_match
```

Acceptance criteria:

* each tool works independently
* each tool has a clear schema
* tool logic is separated from service logic
* tests exist

---

## Milestone 2.5

Restructure the existing flat top-level packages into the `app/` layout from
§23:

```text
api/       → app/api/
rag/       → app/rag/
tools/     → app/tools/
services/  → app/services/
```

`crawler/`, `ingestion/`, `scripts/`, `config/`, `data/` stay at the
repository root, matching §23. `app/agents/` and `app/workflows/` are not
created yet — they arrive with real content in Milestones 5 and 6, not as
empty stubs. `mcp/` is still Milestone 7.

No behavior changes: purely a physical move plus import-path updates.

Acceptance criteria:

* `/ask`, `/crawl`, `/reindex`, `/health` all still work
* all existing tests pass, moved to `tests/app/{api,rag,tools,services}/`
* no code outside `app/` imports from the old `api.`/`rag.`/`tools.`/`services.` paths
* ADR recorded (`docs/decisions.md`)

---

## Milestone 3

Expose:

```text
search_knowledge_base
```

as a tool.

Acceptance criteria:

* tool calls existing RAG service
* no RAG implementation duplication

---

## Milestone 4

Implement manual tool-calling loop.

Acceptance criteria:

```text
LLM
 ↓
tool call
 ↓
tool execution
 ↓
ToolMessage
 ↓
LLM
```

works with multiple tools.

---

## Milestone 5

Implement Agent.

Acceptance criteria:

* agent can select tools
* agent can call multiple tools
* agent can combine RAG + structured data
* `/assistant` endpoint works

---

## Milestone 6

Implement LangGraph investigation workflow.

Acceptance criteria:

* typed state
* multiple nodes
* conditional routing
* at least one retry/additional-data path
* final investigation report

---

## Milestone 7

Implement MCP server.

Acceptance criteria:

* Claude Code can discover MCP tools
* Claude Code can call tools
* MCP tools reuse service layer
* no duplicated business logic

---

## Milestone 8

Add evaluation and observability.

Acceptance criteria:

* repeatable evaluation dataset
* basic metrics
* execution tracing/logging
* documented limitations

---

# 25. Learning Rules

This is also a learning project.

Do not blindly copy code from tutorials.

For every new LangChain/LangGraph/MCP component, understand:

1. What problem does it solve?
2. What abstraction does it introduce?
3. What happens internally?
4. Why is it useful here?
5. What would happen without it?
6. What are its trade-offs?

Prefer official documentation over outdated tutorials.

Keep abstractions minimal.

Do not introduce a framework component unless the project has a reason to use it.

---

# 26. Definition of Done

The project is complete when a user can ask:

```text
Why did NAVI lose their latest match?
```

and the system can:

1. identify the relevant match
2. retrieve structured match data
3. retrieve relevant esports knowledge
4. call multiple tools
5. reason over the collected evidence
6. perform additional retrieval if evidence is insufficient
7. produce a concise investigation report
8. provide sources/evidence
9. expose the same capabilities through MCP

The project should demonstrate the progression:

```text
RAG
 ↓
Tools
 ↓
Tool Calling
 ↓
Agent
 ↓
LangGraph
 ↓
MCP
```

The main objective is not to build the largest possible application.

The objective is to demonstrate a clear understanding of how modern LLM applications are architected and how these technologies complement each other.
