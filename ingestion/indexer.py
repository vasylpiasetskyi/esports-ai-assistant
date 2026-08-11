import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ingestion.embeddings import EmbeddedChunk

COLLECTION_NAME = "esports-wiki"


def point_id(url: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#{chunk_index}"))


def to_point_struct(chunk: EmbeddedChunk) -> PointStruct:
    metadata = chunk.document.metadata
    return PointStruct(
        id=point_id(metadata["url"], metadata["chunk_index"]),
        vector=chunk.embedding,
        payload={"page_content": chunk.document.page_content, "metadata": metadata},
    )


def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def index_embedded_chunks(
    chunks: list[EmbeddedChunk],
    client: QdrantClient,
    collection_name: str = COLLECTION_NAME,
) -> int:
    if not chunks:
        return 0
    ensure_collection(client, collection_name, vector_size=len(chunks[0].embedding))
    points = [to_point_struct(chunk) for chunk in chunks]
    client.upsert(collection_name=collection_name, points=points)
    return len(points)
