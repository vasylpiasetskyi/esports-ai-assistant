import json
from pathlib import Path

from scripts.run_chunking import run


def test_run_loads_and_splits_documents_and_logs_summary(tmp_path: Path, caplog):
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
        chunks = run(tmp_path)

    assert len(chunks) > 1
    assert "Split 1 documents into" in caplog.text
