import logging
from pathlib import Path

from ingestion.loader import LoadResult, load_documents

DATA_DIR = Path("data/raw")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run(base_dir: Path = DATA_DIR) -> LoadResult:
    result = load_documents(base_dir)
    logger.info("Loaded %d documents", len(result.documents))
    for path, error in result.failed:
        logger.warning("Failed: %s (%s)", path, error)
    return result


def main() -> None:
    run()


if __name__ == "__main__":
    main()
