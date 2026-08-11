from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from qdrant_client import QdrantClient

from app.rag.chains import NO_CONTEXT_ANSWER
from app.rag.service import RAGService
from ingestion.embeddings import EmbeddedChunk
from ingestion.indexer import index_embedded_chunks

_VECTORS = {
    "Inferno content": [1.0, 0.0, 0.0],
    "Roshan content": [0.0, 1.0, 0.0],
}


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_VECTORS.get(text, [0.0, 0.0, 0.0]) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _VECTORS.get(text, [0.0, 0.0, 0.0])


def _seed_collection(client: QdrantClient, collection_name: str) -> None:
    chunks = [
        EmbeddedChunk(
            document=Document(
                page_content="Inferno content",
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
            embedding=_VECTORS["Inferno content"],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="Roshan content",
                metadata={
                    "game": "dota2",
                    "category": "mechanics",
                    "title": "Roshan",
                    "url": "https://liquipedia.net/dota2/Roshan",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["mechanic"],
                    "chunk_index": 0,
                },
            ),
            embedding=_VECTORS["Roshan content"],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name=collection_name)


def _build_service(llm: FakeListChatModel) -> RAGService:
    client = QdrantClient(":memory:")
    collection_name = "test-collection"
    _seed_collection(client, collection_name)
    return RAGService(client, FakeEmbeddings(), llm, collection_name=collection_name)


def test_answer_returns_llm_answer_and_source_for_matching_game():
    llm = FakeListChatModel(responses=["Inferno is a CS2 map."])
    service = _build_service(llm)

    result = service.answer("Tell me about Inferno", game="cs2")

    assert result.answer == "Inferno is a CS2 map."
    assert result.sources == ["https://liquipedia.net/counterstrike/Inferno"]


def test_answer_without_game_searches_across_all_games():
    llm = FakeListChatModel(responses=["some answer"])
    service = _build_service(llm)

    result = service.answer("Tell me about Roshan")

    assert set(result.sources) == {
        "https://liquipedia.net/counterstrike/Inferno",
        "https://liquipedia.net/dota2/Roshan",
    }


def test_answer_short_circuits_when_game_filter_excludes_all_matches():
    llm = FakeListChatModel(responses=["should not be used"])
    service = _build_service(llm)

    result = service.answer("Tell me about Inferno", game="lol")

    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == []
