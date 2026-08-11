import json
from pathlib import Path

from langchain_core.embeddings import Embeddings

from scripts.run_embeddings import run


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


def test_run_embeds_loaded_and_split_documents_and_logs_summary(tmp_path: Path, caplog):
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

    with caplog.at_level("INFO"):
        embedded_chunks = run(tmp_path, embeddings=FakeEmbeddings())

    assert len(embedded_chunks) > 1
    assert "Embedded" in caplog.text
