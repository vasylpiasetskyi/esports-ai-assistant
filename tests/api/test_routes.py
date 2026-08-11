import json

import httpx
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from qdrant_client import QdrantClient

import api.routes
import crawler.service
import ingestion.service
from api.main import app
from api.routes import get_embeddings, get_http_client, get_llm, get_qdrant_client
from ingestion.embeddings import EmbeddedChunk
from ingestion.indexer import COLLECTION_NAME, index_embedded_chunks
from rag.retriever import build_retriever


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

    monkeypatch.setattr(api.routes, "build_retriever", _spy_build_retriever)
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

    monkeypatch.setattr(api.routes, "build_retriever", _spy_build_retriever)
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

    monkeypatch.setattr(api.routes, "build_retriever", _spy_build_retriever)
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
