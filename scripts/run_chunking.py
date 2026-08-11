import logging
from pathlib import Path

from langchain_core.documents import Document

from ingestion.loader import load_documents
from ingestion.splitter import split_documents

DATA_DIR = Path("data/raw")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(base_dir: Path = DATA_DIR) -> list[Document]:
    load_result = load_documents(base_dir)
    chunks = split_documents(load_result.documents)
    logger.info("Split %d documents into %d chunks", len(load_result.documents), len(chunks))
    for path, error in load_result.failed:
        logger.warning("Failed: %s (%s)", path, error)
    return chunks


def main() -> None:
    run()


if __name__ == "__main__":
    main()
