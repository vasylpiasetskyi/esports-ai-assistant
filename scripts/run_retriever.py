import logging
import os

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

from app.rag.retriever import build_retriever
from ingestion.indexer import COLLECTION_NAME

EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_QDRANT_URL = "http://localhost:6333"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    client = QdrantClient(url=os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL))
    retriever = build_retriever(client, embeddings, collection_name=COLLECTION_NAME)

    print("Type a question (empty line to quit):")
    while True:
        query = input("> ").strip()
        if not query:
            break
        for i, document in enumerate(retriever.invoke(query), start=1):
            print(f"[{i}] {document.metadata.get('title')} ({document.metadata.get('url')})")
            print(document.page_content[:200])
            print()


if __name__ == "__main__":
    main()
