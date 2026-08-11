from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from qdrant_client import QdrantClient

from app.rag.chains import RagAnswer, answer_question
from app.rag.retriever import build_retriever
from ingestion.indexer import COLLECTION_NAME


class RAGService:
    """RAG as a reusable service, hiding Qdrant, embeddings, retriever
    configuration and LLM invocation behind a single `answer()` call.

    Callers (API routes, LangChain tools, the Agent) depend only on this
    class, never on `app.rag.retriever` or `app.rag.chains` directly.
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embeddings: Embeddings,
        llm: BaseChatModel,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self._qdrant_client = qdrant_client
        self._embeddings = embeddings
        self._llm = llm
        self._collection_name = collection_name

    def answer(
        self,
        question: str,
        game: str | None = None,
        *,
        use_hybrid: bool = False,
        use_multi_query: bool = False,
        use_compression: bool = False,
    ) -> RagAnswer:
        metadata_filter = {"game": game} if game else None
        retriever = build_retriever(
            self._qdrant_client,
            self._embeddings,
            collection_name=self._collection_name,
            metadata_filter=metadata_filter,
            use_hybrid=use_hybrid,
            use_multi_query=use_multi_query,
            use_compression=use_compression,
            llm=self._llm,
        )
        return answer_question(question, retriever, self._llm)
