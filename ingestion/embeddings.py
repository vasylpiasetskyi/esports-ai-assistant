from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


@dataclass
class EmbeddedChunk:
    document: Document
    embedding: list[float]


def embed_documents(documents: list[Document], embeddings: Embeddings) -> list[EmbeddedChunk]:
    vectors = embeddings.embed_documents([document.page_content for document in documents])
    return [
        EmbeddedChunk(document=document, embedding=vector)
        for document, vector in zip(documents, vectors)
    ]
