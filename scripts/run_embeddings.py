import logging
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from ingestion.embeddings import EmbeddedChunk, embed_documents
from ingestion.loader import load_documents
from ingestion.splitter import split_documents

DATA_DIR = Path("data/raw")
EMBEDDING_MODEL = "text-embedding-3-small"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(base_dir: Path = DATA_DIR, embeddings: Embeddings | None = None) -> list[EmbeddedChunk]:
    embeddings = embeddings or OpenAIEmbeddings(model=EMBEDDING_MODEL)
    load_result = load_documents(base_dir)
    chunks = split_documents(load_result.documents)
    embedded_chunks = embed_documents(chunks, embeddings)
    logger.info("Embedded %d chunks", len(embedded_chunks))
    for path, error in load_result.failed:
        logger.warning("Failed: %s (%s)", path, error)
    return embedded_chunks


def main() -> None:
    run()


if __name__ == "__main__":
    main()
