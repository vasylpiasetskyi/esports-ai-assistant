from langchain_core.documents import Document

from ingestion.splitter import split_documents


def _make_document(content: str, **metadata) -> Document:
    return Document(page_content=content, metadata=metadata)


def test_short_document_stays_a_single_chunk():
    document = _make_document(
        "A short piece of text.", game="cs2", category="maps", title="Inferno"
    )

    chunks = split_documents([document])

    assert len(chunks) == 1
    assert chunks[0].page_content == "A short piece of text."
    assert chunks[0].metadata["chunk_index"] == 0


def test_long_document_splits_into_multiple_sequential_chunks():
    long_text = "word " * 500  # well over the default chunk_size of 1000 chars
    document = _make_document(long_text, game="cs2", category="maps", title="Inferno")

    chunks = split_documents([document])

    assert len(chunks) > 1
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_chunks_inherit_source_document_metadata():
    document = _make_document(
        "word " * 500,
        game="cs2",
        category="maps",
        title="Inferno",
        url="https://liquipedia.net/counterstrike/Inferno",
        updated_at="2026-07-27T20:52:27.349159+00:00",
        tags=["map"],
    )

    chunks = split_documents([document])

    for chunk in chunks:
        assert chunk.metadata["game"] == "cs2"
        assert chunk.metadata["category"] == "maps"
        assert chunk.metadata["title"] == "Inferno"
        assert chunk.metadata["url"] == "https://liquipedia.net/counterstrike/Inferno"
        assert chunk.metadata["updated_at"] == "2026-07-27T20:52:27.349159+00:00"
        assert chunk.metadata["tags"] == ["map"]


def test_smaller_chunk_size_produces_more_chunks():
    document = _make_document("word " * 500, game="cs2", category="maps", title="Inferno")

    default_chunks = split_documents([document])
    small_chunks = split_documents([document], chunk_size=100, chunk_overlap=20)

    assert len(small_chunks) > len(default_chunks)


def test_chunk_index_resets_for_each_source_document():
    doc_a = _make_document("word " * 500, game="cs2", category="maps", title="Inferno")
    doc_b = _make_document("word " * 500, game="cs2", category="teams", title="Natus Vincere")

    chunks = split_documents([doc_a, doc_b])

    indices_a = [c.metadata["chunk_index"] for c in chunks if c.metadata["title"] == "Inferno"]
    indices_b = [
        c.metadata["chunk_index"] for c in chunks if c.metadata["title"] == "Natus Vincere"
    ]

    assert indices_a == list(range(len(indices_a)))
    assert indices_b == list(range(len(indices_b)))
