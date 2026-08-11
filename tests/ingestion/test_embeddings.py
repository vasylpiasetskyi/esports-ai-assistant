from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ingestion.embeddings import embed_documents


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


def test_embed_documents_pairs_each_document_with_its_vector_in_order():
    documents = [
        Document(page_content="abc", metadata={"title": "A"}),
        Document(page_content="abcdefgh", metadata={"title": "B"}),
    ]

    embedded = embed_documents(documents, FakeEmbeddings())

    assert len(embedded) == 2
    assert embedded[0].document.metadata["title"] == "A"
    assert embedded[0].embedding == [3.0]
    assert embedded[1].document.metadata["title"] == "B"
    assert embedded[1].embedding == [8.0]


def test_embed_documents_returns_empty_list_for_empty_input():
    assert embed_documents([], FakeEmbeddings()) == []
