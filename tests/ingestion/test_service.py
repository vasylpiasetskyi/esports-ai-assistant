import json
from pathlib import Path

from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient

from ingestion.service import run_reindex


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


def test_run_reindex_indexes_loaded_split_and_embedded_documents(tmp_path: Path, caplog):
    game_dir = tmp_path / "cs2" / "maps"
    game_dir.mkdir(parents=True)
    (game_dir / "inferno.json").write_text(
        json.dumps(
            {
                "title": "Inferno",
                "game": "cs2",
                "category": "maps",
                "url": "https://liquipedia.net/counterstrike/Inferno",
                "content": "word " * 500,
                "updated_at": "2026-07-27T20:52:27.349159Z",
                "tags": ["map"],
            }
        )
    )
    client = QdrantClient(":memory:")

    with caplog.at_level("INFO"):
        count = run_reindex(tmp_path, embeddings=FakeEmbeddings(), client=client)

    assert count > 1
    assert "Indexed" in caplog.text
