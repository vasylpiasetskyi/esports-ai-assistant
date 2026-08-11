import json

import httpx
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import Field
from qdrant_client import QdrantClient

import crawler.service
import ingestion.service
from app.api.main import app
from app.api.routes import get_embeddings, get_http_client, get_llm, get_qdrant_client
from app.rag import service as rag_service
from app.rag.retriever import build_retriever
from ingestion.embeddings import EmbeddedChunk
from ingestion.indexer import COLLECTION_NAME, index_embedded_chunks


def test_health_returns_ok(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class ConstantFakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


def _seed_client(client: QdrantClient) -> None:
    chunks = [
        EmbeddedChunk(
            document=Document(
                page_content="Inferno is a map in CS2.",
                metadata={
                    "game": "cs2",
                    "category": "maps",
                    "title": "Inferno",
                    "url": "https://liquipedia.net/counterstrike/Inferno",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["map"],
                    "chunk_index": 0,
                },
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="Baron Nashor is a neutral objective in LoL.",
                metadata={
                    "game": "lol",
                    "category": "mechanics",
                    "title": "Baron Nashor",
                    "url": "https://liquipedia.net/leagueoflegends/Baron_Nashor",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["mechanic"],
                    "chunk_index": 0,
                },
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name=COLLECTION_NAME)


def test_ask_returns_answer_and_sources(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: FakeListChatModel(
        responses=["Inferno is a CS2 map."]
    )

    try:
        with TestClient(app) as client:
            response = client.post("/ask", json={"question": "What is Inferno?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Inferno is a CS2 map."
    assert "https://liquipedia.net/counterstrike/Inferno" in body["sources"]


def test_ask_with_game_filter_only_returns_matching_sources(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: FakeListChatModel(
        responses=["Baron Nashor answer."]
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/ask", json={"question": "What is Baron Nashor?", "game": "lol"}
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert body["sources"] == ["https://liquipedia.net/leagueoflegends/Baron_Nashor"]


def test_ask_without_game_searches_across_all_games(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: FakeListChatModel(responses=["some answer"])

    try:
        with TestClient(app) as client:
            response = client.post("/ask", json={"question": "Tell me something."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["sources"]) >= 1


def _fake_liquipedia_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"parse": {"text": {"*": "<p>Natus Vincere is a team from Ukraine.</p>"}}},
    )


def _write_test_crawl_config(config_path):
    config_path.write_text(
        json.dumps(
            [
                {
                    "game": "cs2",
                    "category": "teams",
                    "title": "Natus Vincere",
                    "slug": "navi",
                    "tags": ["team"],
                }
            ]
        )
    )


def test_crawl_starts_background_crawl_and_writes_results(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(crawler.service, "DATA_DIR", tmp_path)
    config_path = tmp_path / "pages.json"
    _write_test_crawl_config(config_path)
    monkeypatch.setattr(crawler.service, "CONFIG_PATH", config_path)

    fake_http_client = httpx.Client(transport=httpx.MockTransport(_fake_liquipedia_handler))
    app.dependency_overrides[get_http_client] = lambda: fake_http_client

    try:
        with TestClient(app) as client:
            response = client.post("/crawl")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json() == {"status": "started"}
    assert (tmp_path / "cs2" / "teams" / "navi.json").exists()


def test_crawl_rejects_concurrent_requests(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with TestClient(app) as client:
        app.state.is_crawling = True
        response = client.post("/crawl")

    assert response.status_code == 409


def test_crawl_resets_in_progress_flag_after_completion(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(crawler.service, "DATA_DIR", tmp_path)
    config_path = tmp_path / "pages.json"
    _write_test_crawl_config(config_path)
    monkeypatch.setattr(crawler.service, "CONFIG_PATH", config_path)

    fake_http_client = httpx.Client(transport=httpx.MockTransport(_fake_liquipedia_handler))
    app.dependency_overrides[get_http_client] = lambda: fake_http_client

    try:
        with TestClient(app) as client:
            client.post("/crawl")
            assert app.state.is_crawling is False
            second_response = client.post("/crawl")
    finally:
        app.dependency_overrides.clear()

    assert second_response.status_code == 202


def test_reindex_starts_background_task_and_populates_collection(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    game_dir = tmp_path / "cs2" / "maps"
    game_dir.mkdir(parents=True)
    (game_dir / "inferno.json").write_text(
        json.dumps(
            {
                "title": "Inferno",
                "game": "cs2",
                "category": "maps",
                "url": "https://liquipedia.net/counterstrike/Inferno",
                "content": "word " * 500,
                "updated_at": "2026-07-27T20:52:27.349159Z",
                "tags": ["map"],
            }
        )
    )
    monkeypatch.setattr(ingestion.service, "DATA_DIR", tmp_path)

    qdrant_client = QdrantClient(":memory:")
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()

    try:
        with TestClient(app) as client:
            response = client.post("/reindex")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json() == {"status": "started"}
    assert qdrant_client.count(COLLECTION_NAME).count > 0


def test_ask_passes_use_hybrid_flag_to_build_retriever(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    captured_kwargs = {}

    def _spy_build_retriever(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return build_retriever(*args, **kwargs)

    monkeypatch.setattr(rag_service, "build_retriever", _spy_build_retriever)
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: FakeListChatModel(
        responses=["Inferno is a CS2 map."]
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/ask", json={"question": "What is Inferno?", "use_hybrid": True}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_kwargs.get("use_hybrid") is True


def test_ask_passes_use_multi_query_and_llm_to_build_retriever(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    captured_kwargs = {}

    def _spy_build_retriever(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return build_retriever(*args, **kwargs)

    monkeypatch.setattr(rag_service, "build_retriever", _spy_build_retriever)
    fake_llm = FakeListChatModel(responses=["Inferno is a CS2 map."])
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: fake_llm

    try:
        with TestClient(app) as client:
            response = client.post(
                "/ask", json={"question": "What is Inferno?", "use_multi_query": True}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_kwargs.get("use_multi_query") is True
    assert captured_kwargs.get("llm") is fake_llm


def test_ask_passes_use_compression_and_llm_to_build_retriever(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    captured_kwargs = {}

    def _spy_build_retriever(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return build_retriever(*args, **kwargs)

    monkeypatch.setattr(rag_service, "build_retriever", _spy_build_retriever)
    # "YES" is required, not an arbitrary sentence: the spy delegates to the
    # real build_retriever, so a real ContextualCompressionRetriever runs for
    # real here, and LLMChainFilter's BooleanOutputParser raises ValueError
    # on any response that doesn't literally contain "YES" or "NO".
    fake_llm = FakeListChatModel(responses=["YES"])
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: fake_llm

    try:
        with TestClient(app) as client:
            response = client.post(
                "/ask", json={"question": "What is Inferno?", "use_compression": True}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_kwargs.get("use_compression") is True
    assert captured_kwargs.get("llm") is fake_llm


class FakeToolCallingChatModel(FakeMessagesListChatModel):
    """See `tests/app/agents/test_esports_agent.py` (Milestone 5) and
    `tests/scripts/test_run_tool_loop.py` (Milestone 4) for the same
    pattern."""

    def bind_tools(self, tools, **kwargs):
        return self.bind(tools=tools, **kwargs)


class RecordingFakeChatModel(FakeToolCallingChatModel):
    received: list = Field(default_factory=list)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.received.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def test_assistant_returns_answer_and_sources_from_knowledge_base(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    # 3 responses, not 2: search_knowledge_base's RAGService.answer() calls
    # this same shared `llm` internally (via the RAG chain) to generate the
    # RAG answer text, in between the agent's own two reasoning calls — the
    # fake model cycles through `responses` for every invocation, agent and
    # RAG chain alike.
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge_base",
                        "args": {"question": "What is Inferno?"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="Inferno is a CS2 map."),
            AIMessage(content="Inferno is a CS2 map."),
        ]
    )
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: llm

    try:
        with TestClient(app) as client:
            response = client.post("/assistant", json={"question": "What is Inferno?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Inferno is a CS2 map."
    assert "https://liquipedia.net/counterstrike/Inferno" in body["sources"]


def test_assistant_folds_game_into_input_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    llm = RecordingFakeChatModel(responses=[AIMessage(content="Some answer.")])
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: llm

    try:
        with TestClient(app) as client:
            response = client.post("/assistant", json={"question": "Who is s1mple?", "game": "cs2"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    human_messages = [
        message
        for messages in llm.received
        for message in messages
        if isinstance(message, HumanMessage)
    ]
    assert any("cs2" in message.content for message in human_messages)


def test_investigate_returns_report_and_findings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    qdrant_client = QdrantClient(":memory:")
    _seed_client(qdrant_client)

    # 4 responses, in order: analyze_question (structured), the RAG chain
    # inside retrieve_knowledge (real RAGService shares this same llm — see
    # the Milestone 5 gotcha), analyze_evidence (structured, sufficient=True
    # — the no-retry happy path keeps this sequence short and unambiguous),
    # generate_report.
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "QuestionAnalysis",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="Inferno is a CS2 map favored by Vitality."),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "EvidenceAnalysis",
                        "args": {
                            "sufficient": True,
                            "findings": ["NAVI lost 1-2 to Vitality on Inferno."],
                        },
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(content="NAVI lost their latest match 1-2 to Vitality."),
        ]
    )
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant_client
    app.dependency_overrides[get_embeddings] = lambda: ConstantFakeEmbeddings()
    app.dependency_overrides[get_llm] = lambda: llm

    try:
        with TestClient(app) as client:
            response = client.post(
                "/investigate", json={"question": "Why did NAVI lose their latest match?"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["report"] == "NAVI lost their latest match 1-2 to Vitality."
    assert body["findings"] == ["NAVI lost 1-2 to Vitality on Inferno."]
