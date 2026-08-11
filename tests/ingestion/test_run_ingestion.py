import json
from pathlib import Path

from scripts.run_ingestion import run


def test_run_returns_load_result_and_logs_summary(tmp_path: Path, caplog):
    game_dir = tmp_path / "cs2" / "maps"
    game_dir.mkdir(parents=True)
    (game_dir / "inferno.json").write_text(
        json.dumps(
            {
                "title": "Inferno",
                "game": "cs2",
                "category": "maps",
                "url": "https://liquipedia.net/counterstrike/Inferno",
                "content": "Inferno is a map.",
                "updated_at": "2026-07-27T20:52:27.349159Z",
                "tags": ["map"],
            }
        )
    )
    (game_dir / "broken.json").write_text("{not valid json")

    with caplog.at_level("INFO"):
        result = run(tmp_path)

    assert len(result.documents) == 1
    assert result.documents[0].metadata["title"] == "Inferno"
    assert len(result.failed) == 1
    assert "Loaded 1 documents" in caplog.text
