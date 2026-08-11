from langchain_core.documents import Document
from qdrant_client import QdrantClient

from ingestion.embeddings import EmbeddedChunk
from ingestion.indexer import ensure_collection, index_embedded_chunks, point_id, to_point_struct


def _make_chunk(**metadata) -> EmbeddedChunk:
    document = Document(page_content="Inferno is a map.", metadata=metadata)
    return EmbeddedChunk(document=document, embedding=[0.1, 0.2, 0.3])


def test_point_id_is_deterministic_for_same_url_and_chunk_index():
    assert point_id("https://example.test/a", 0) == point_id("https://example.test/a", 0)


def test_point_id_differs_for_different_chunk_index():
    assert point_id("https://example.test/a", 0) != point_id("https://example.test/a", 1)


def test_point_id_differs_for_different_url():
    assert point_id("https://example.test/a", 0) != point_id("https://example.test/b", 0)


def test_to_point_struct_builds_correct_vector_and_payload():
    chunk = _make_chunk(
        game="cs2",
        category="maps",
        title="Inferno",
        url="https://liquipedia.net/counterstrike/Inferno",
        updated_at="2026-07-27T20:52:27.349159+00:00",
        tags=["map"],
        chunk_index=0,
    )

    point = to_point_struct(chunk)

    assert point.id == point_id("https://liquipedia.net/counterstrike/Inferno", 0)
    assert point.vector == [0.1, 0.2, 0.3]
    assert point.payload["page_content"] == "Inferno is a map."
    assert point.payload["metadata"]["game"] == "cs2"
    assert point.payload["metadata"]["category"] == "maps"
    assert point.payload["metadata"]["title"] == "Inferno"
    assert point.payload["metadata"]["url"] == "https://liquipedia.net/counterstrike/Inferno"
    assert point.payload["metadata"]["tags"] == ["map"]
    assert point.payload["metadata"]["chunk_index"] == 0


def test_ensure_collection_creates_when_absent():
    client = QdrantClient(":memory:")

    ensure_collection(client, "test-collection", vector_size=3)

    assert client.collection_exists("test-collection")


def test_ensure_collection_is_idempotent_when_already_exists():
    client = QdrantClient(":memory:")
    ensure_collection(client, "test-collection", vector_size=3)

    ensure_collection(client, "test-collection", vector_size=3)

    assert client.collection_exists("test-collection")


def test_index_embedded_chunks_returns_zero_for_empty_input_without_creating_collection():
    client = QdrantClient(":memory:")

    count = index_embedded_chunks([], client, collection_name="test-collection")

    assert count == 0
    assert not client.collection_exists("test-collection")


def test_index_embedded_chunks_indexes_all_chunks():
    client = QdrantClient(":memory:")
    chunks = [
        _make_chunk(
            game="cs2",
            category="maps",
            title="Inferno",
            url="https://liquipedia.net/counterstrike/Inferno",
            updated_at="2026-07-27T20:52:27.349159+00:00",
            tags=["map"],
            chunk_index=0,
        ),
        _make_chunk(
            game="cs2",
            category="maps",
            title="Inferno",
            url="https://liquipedia.net/counterstrike/Inferno",
            updated_at="2026-07-27T20:52:27.349159+00:00",
            tags=["map"],
            chunk_index=1,
        ),
    ]

    count = index_embedded_chunks(chunks, client, collection_name="test-collection")

    assert count == 2
    assert client.count("test-collection").count == 2


def test_index_embedded_chunks_is_idempotent_on_rerun():
    client = QdrantClient(":memory:")
    chunks = [
        _make_chunk(
            game="cs2",
            category="maps",
            title="Inferno",
            url="https://liquipedia.net/counterstrike/Inferno",
            updated_at="2026-07-27T20:52:27.349159+00:00",
            tags=["map"],
            chunk_index=0,
        )
    ]

    index_embedded_chunks(chunks, client, collection_name="test-collection")
    index_embedded_chunks(chunks, client, collection_name="test-collection")

    assert client.count("test-collection").count == 1
