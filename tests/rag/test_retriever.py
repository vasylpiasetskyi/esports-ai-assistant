import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from ingestion.embeddings import EmbeddedChunk
from ingestion.indexer import index_embedded_chunks
from rag.retriever import build_metadata_filter, build_retriever


def test_build_metadata_filter_builds_field_conditions_from_dict():
    result = build_metadata_filter({"game": "cs2", "category": "maps"})

    assert result == Filter(
        must=[
            FieldCondition(key="metadata.game", match=MatchValue(value="cs2")),
            FieldCondition(key="metadata.category", match=MatchValue(value="maps")),
        ]
    )


_VECTORS = {
    "Inferno content": [1.0, 0.0, 0.0],
    "Roshan content": [0.0, 1.0, 0.0],
    "Ahri content": [0.0, 0.0, 1.0],
}


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_VECTORS.get(text, [0.0, 0.0, 0.0]) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _VECTORS.get(text, [0.0, 0.0, 0.0])


def _seed_collection(client: QdrantClient) -> None:
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
        EmbeddedChunk(
            document=Document(
                page_content="Ahri content",
                metadata={
                    "game": "lol",
                    "category": "champions",
                    "title": "Ahri",
                    "url": "https://liquipedia.net/leagueoflegends/Ahri",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["champion"],
                    "chunk_index": 0,
                },
            ),
            embedding=_VECTORS["Ahri content"],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name="test-collection")


def test_similarity_search_returns_most_similar_document():
    client = QdrantClient(":memory:")
    _seed_collection(client)
    retriever = build_retriever(client, FakeEmbeddings(), collection_name="test-collection", k=1)

    results = retriever.invoke("Inferno content")

    assert len(results) == 1
    assert results[0].metadata["title"] == "Inferno"


def test_top_k_limits_result_count():
    client = QdrantClient(":memory:")
    _seed_collection(client)
    retriever = build_retriever(client, FakeEmbeddings(), collection_name="test-collection", k=2)

    results = retriever.invoke("Inferno content")

    assert len(results) == 2


def test_metadata_filter_overrides_raw_similarity():
    client = QdrantClient(":memory:")
    _seed_collection(client)
    retriever = build_retriever(
        client,
        FakeEmbeddings(),
        collection_name="test-collection",
        k=1,
        metadata_filter={"game": "dota2"},
    )

    # "Inferno content" is closest (by embedding) to the cs2 doc, but the
    # filter restricts candidates to game == "dota2".
    results = retriever.invoke("Inferno content")

    assert len(results) == 1
    assert results[0].metadata["title"] == "Roshan"


def test_mmr_search_type_runs_end_to_end():
    client = QdrantClient(":memory:")
    _seed_collection(client)
    retriever = build_retriever(
        client, FakeEmbeddings(), collection_name="test-collection", search_type="mmr", k=2
    )

    results = retriever.invoke("Inferno content")

    assert len(results) > 0


_NAVI_OVERVIEW = "Natus Vincere is a Ukrainian esports organization."
_HYBRID_VECTORS = {
    _NAVI_OVERVIEW: [1.0, 0.0, 0.0],
    "s1mple is a legendary CS2 player for Natus Vincere.": [0.0, 1.0, 0.0],
    "Roshan is a neutral objective in Dota 2.": [0.0, 0.0, 1.0],
}


class _HybridFakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_HYBRID_VECTORS.get(text, [0.0, 0.0, 0.0]) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        # Always resolves to the "overview" document's vector, simulating a
        # dense embedding that fails to separate the two documents — this is
        # the failure mode hybrid search is meant to catch.
        return _HYBRID_VECTORS[_NAVI_OVERVIEW]


def _seed_hybrid_collection(client: QdrantClient) -> None:
    # A third, unrelated filler document is required: with only 2 documents,
    # a term appearing in exactly one of them has BM25 document frequency
    # 1/2, which makes rank_bm25's IDF formula degenerate to exactly 0 (no
    # effect on scoring at all). A 3rd document keeps "s1mple"'s document
    # frequency at 1/3, giving it a positive IDF.
    chunks = [
        EmbeddedChunk(
            document=Document(
                page_content="Natus Vincere is a Ukrainian esports organization.",
                metadata={
                    "game": "cs2",
                    "category": "teams",
                    "title": "NAVI Overview",
                    "url": "https://liquipedia.net/counterstrike/Natus_Vincere",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["team"],
                    "chunk_index": 0,
                },
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="s1mple is a legendary CS2 player for Natus Vincere.",
                metadata={
                    "game": "cs2",
                    "category": "players",
                    "title": "s1mple Bio",
                    "url": "https://liquipedia.net/counterstrike/S1mple",
                    "updated_at": "2026-07-27T20:52:27.349159+00:00",
                    "tags": ["player"],
                    "chunk_index": 0,
                },
            ),
            embedding=[0.0, 1.0, 0.0],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="Roshan is a neutral objective in Dota 2.",
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
            embedding=[0.0, 0.0, 1.0],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name="test-hybrid")


def test_dense_only_misses_keyword_match_hybrid_surfaces_it():
    client = QdrantClient(":memory:")
    _seed_hybrid_collection(client)
    embeddings = _HybridFakeEmbeddings()

    dense_only = build_retriever(client, embeddings, collection_name="test-hybrid", k=1)
    hybrid = build_retriever(
        client, embeddings, collection_name="test-hybrid", k=1, use_hybrid=True
    )

    dense_titles = {doc.metadata["title"] for doc in dense_only.invoke("Tell me about s1mple")}
    hybrid_titles = {doc.metadata["title"] for doc in hybrid.invoke("Tell me about s1mple")}

    assert dense_titles == {"NAVI Overview"}
    assert "s1mple Bio" in hybrid_titles


def test_hybrid_mode_falls_back_to_dense_when_corpus_is_empty():
    client = QdrantClient(":memory:")
    _seed_collection(client)
    retriever = build_retriever(
        client,
        FakeEmbeddings(),
        collection_name="test-collection",
        k=1,
        metadata_filter={"game": "valorant"},
        use_hybrid=True,
    )

    results = retriever.invoke("Inferno content")

    assert results == []


def test_multi_query_surfaces_document_dense_only_misses():
    vectors = {
        "Inferno is a map in CS2.": [1.0, 0.0, 0.0],
        "Overpass is a map in CS2.": [0.0, 1.0, 0.0],
    }

    class _OddPhrasingFakeEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [vectors.get(text, [0.0, 0.0, 0.0]) for text in texts]

        def embed_query(self, text: str) -> list[float]:
            # Falls back to the Inferno vector for any phrasing it doesn't
            # recognize verbatim — simulating dense search misplacing an
            # oddly-phrased question near the wrong document.
            return vectors.get(text, vectors["Inferno is a map in CS2."])

    def meta(title: str, url: str) -> dict:
        return {
            "game": "cs2",
            "category": "maps",
            "title": title,
            "url": url,
            "updated_at": "2026-07-27T20:52:27.349159+00:00",
            "tags": ["map"],
            "chunk_index": 0,
        }

    client = QdrantClient(":memory:")
    chunks = [
        EmbeddedChunk(
            document=Document(
                page_content="Inferno is a map in CS2.", metadata=meta("Inferno", "u1")
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="Overpass is a map in CS2.", metadata=meta("Overpass", "u2")
            ),
            embedding=[0.0, 1.0, 0.0],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name="test-mq")
    embeddings = _OddPhrasingFakeEmbeddings()

    dense_only = build_retriever(client, embeddings, collection_name="test-mq", k=1)
    dense_titles = {doc.metadata["title"] for doc in dense_only.invoke("Tell me about Overpass")}
    assert dense_titles == {"Inferno"}

    fake_llm = FakeListChatModel(
        responses=["Overpass callouts\nOverpass is a map in CS2.\nOverpass strategy"]
    )
    multi_query = build_retriever(
        client, embeddings, collection_name="test-mq", k=1, use_multi_query=True, llm=fake_llm
    )
    multi_query_titles = {
        doc.metadata["title"] for doc in multi_query.invoke("Tell me about Overpass")
    }
    assert "Overpass" in multi_query_titles


def test_multi_query_without_llm_raises_value_error():
    client = QdrantClient(":memory:")
    _seed_collection(client)

    with pytest.raises(ValueError, match="llm is required"):
        build_retriever(
            client, FakeEmbeddings(), collection_name="test-collection", use_multi_query=True
        )


def test_compression_drops_irrelevant_document():
    vectors = {
        "Inferno is a CS2 map with bombsites A and B.": [1.0, 0.0, 0.0],
        "Dust2 has a long A corridor.": [0.0, 1.0, 0.0],
    }

    class _DistinctFakeEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [vectors.get(text, [0.0, 0.0, 0.0]) for text in texts]

        def embed_query(self, text: str) -> list[float]:
            # Always resolves to the Inferno vector, so retrieval order
            # (Inferno first, Dust2 second) is deterministic regardless of
            # the literal query text.
            return vectors["Inferno is a CS2 map with bombsites A and B."]

    def meta(title: str, url: str) -> dict:
        return {
            "game": "cs2",
            "category": "maps",
            "title": title,
            "url": url,
            "updated_at": "2026-07-27T20:52:27.349159+00:00",
            "tags": ["map"],
            "chunk_index": 0,
        }

    client = QdrantClient(":memory:")
    chunks = [
        EmbeddedChunk(
            document=Document(
                page_content="Inferno is a CS2 map with bombsites A and B.",
                metadata=meta("Inferno", "u1"),
            ),
            embedding=[1.0, 0.0, 0.0],
        ),
        EmbeddedChunk(
            document=Document(
                page_content="Dust2 has a long A corridor.", metadata=meta("Dust2", "u2")
            ),
            embedding=[0.0, 1.0, 0.0],
        ),
    ]
    index_embedded_chunks(chunks, client, collection_name="test-compression")
    embeddings = _DistinctFakeEmbeddings()

    uncompressed = build_retriever(client, embeddings, collection_name="test-compression", k=2)
    uncompressed_titles = [
        doc.metadata["title"] for doc in uncompressed.invoke("Tell me about Inferno")
    ]
    assert uncompressed_titles == ["Inferno", "Dust2"]

    fake_llm = FakeListChatModel(responses=["YES", "NO"])
    compressed = build_retriever(
        client,
        embeddings,
        collection_name="test-compression",
        k=2,
        use_compression=True,
        llm=fake_llm,
    )
    compressed_titles = [
        doc.metadata["title"] for doc in compressed.invoke("Tell me about Inferno")
    ]
    assert compressed_titles == ["Inferno"]


def test_compression_without_llm_raises_value_error():
    client = QdrantClient(":memory:")
    _seed_collection(client)

    with pytest.raises(ValueError, match="llm is required"):
        build_retriever(
            client, FakeEmbeddings(), collection_name="test-collection", use_compression=True
        )
