import logging
import os
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

from ingestion.embeddings import embed_documents
from ingestion.indexer import COLLECTION_NAME, index_embedded_chunks
from ingestion.loader import load_documents
from ingestion.splitter import split_documents

DATA_DIR = Path("data/raw")
EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_QDRANT_URL = "http://localhost:6333"

logger = logging.getLogger(__name__)


def run_reindex(
    base_dir: Path | None = None,
    embeddings: Embeddings | None = None,
    client: QdrantClient | None = None,
) -> int:
    resolved_base_dir = base_dir if base_dir is not None else DATA_DIR
    embeddings = embeddings or OpenAIEmbeddings(model=EMBEDDING_MODEL)
    client = client or QdrantClient(url=os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL))
    load_result = load_documents(resolved_base_dir)
    chunks = split_documents(load_result.documents)
    embedded_chunks = embed_documents(chunks, embeddings)
    indexed_count = index_embedded_chunks(embedded_chunks, client, COLLECTION_NAME)
    logger.info("Indexed %d points into %r", indexed_count, COLLECTION_NAME)
    for path, error in load_result.failed:
        logger.warning("Failed: %s (%s)", path, error)
    return indexed_count
