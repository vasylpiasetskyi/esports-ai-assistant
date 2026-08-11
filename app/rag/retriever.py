from langchain_classic.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_classic.retrievers.document_compressors import LLMChainFilter
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from ingestion.indexer import COLLECTION_NAME


def build_metadata_filter(conditions: dict[str, str]) -> Filter:
    return Filter(
        must=[
            FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
            for key, value in conditions.items()
        ]
    )


def _load_bm25_corpus(
    client: QdrantClient, collection_name: str, scroll_filter: Filter | None
) -> list[Document]:
    records, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=scroll_filter,
        limit=1000,
        with_payload=True,
    )
    return [
        Document(page_content=record.payload["page_content"], metadata=record.payload["metadata"])
        for record in records
    ]


def build_retriever(
    client: QdrantClient,
    embeddings: Embeddings,
    collection_name: str = COLLECTION_NAME,
    search_type: str = "similarity",
    k: int = 4,
    metadata_filter: dict[str, str] | None = None,
    use_hybrid: bool = False,
    use_multi_query: bool = False,
    use_compression: bool = False,
    llm: BaseChatModel | None = None,
) -> BaseRetriever:
    vector_store = QdrantVectorStore(
        client=client, collection_name=collection_name, embedding=embeddings
    )
    qdrant_filter = build_metadata_filter(metadata_filter) if metadata_filter else None
    search_kwargs = {"k": k}
    if qdrant_filter:
        search_kwargs["filter"] = qdrant_filter
    dense_retriever = vector_store.as_retriever(
        search_type=search_type, search_kwargs=search_kwargs
    )

    retriever: BaseRetriever = dense_retriever
    if use_hybrid:
        documents = _load_bm25_corpus(client, collection_name, qdrant_filter)
        if documents:
            bm25_retriever = BM25Retriever.from_documents(documents, k=k)
            retriever = EnsembleRetriever(
                retrievers=[dense_retriever, bm25_retriever], weights=[0.5, 0.5]
            )

    if use_multi_query:
        if llm is None:
            raise ValueError("llm is required when use_multi_query=True")
        retriever = MultiQueryRetriever.from_llm(retriever=retriever, llm=llm)

    if use_compression:
        if llm is None:
            raise ValueError("llm is required when use_compression=True")
        retriever = ContextualCompressionRetriever(
            base_compressor=LLMChainFilter.from_llm(llm), base_retriever=retriever
        )

    return retriever
