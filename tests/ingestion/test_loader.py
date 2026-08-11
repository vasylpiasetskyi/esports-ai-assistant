import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ingestion.loader import (
    discover_json_files,
    load_documents,
    load_raw_article,
    to_document,
)
from ingestion.models import RawArticleRecord


def test_discover_json_files_finds_nested_json_files(tmp_path: Path):
    (tmp_path / "cs2" / "maps").mkdir(parents=True)
    (tmp_path / "cs2" / "teams").mkdir(parents=True)
    (tmp_path / "cs2" / "maps" / "inferno.json").write_text("{}")
    (tmp_path / "cs2" / "teams" / "navi.json").write_text("{}")
    (tmp_path / "cs2" / "teams" / "readme.txt").write_text("not json")

    found = discover_json_files(tmp_path)

    assert found == sorted(
        [
            tmp_path / "cs2" / "maps" / "inferno.json",
            tmp_path / "cs2" / "teams" / "navi.json",
        ]
    )


def test_discover_json_files_returns_empty_list_for_empty_dir(tmp_path: Path):
    assert discover_json_files(tmp_path) == []


def test_load_raw_article_parses_valid_file(tmp_path: Path):
    path = tmp_path / "navi.json"
    path.write_text(
        json.dumps(
            {
                "title": "Natus Vincere",
                "game": "cs2",
                "category": "teams",
                "url": "https://liquipedia.net/counterstrike/Natus_Vincere",
                "content": "Natus Vincere is a team from Ukraine.",
                "updated_at": "2026-07-27T20:52:29.454013Z",
                "tags": ["team", "ukraine"],
            }
        )
    )

    record = load_raw_article(path)

    assert record.title == "Natus Vincere"
    assert record.tags == ["team", "ukraine"]


def test_load_raw_article_raises_on_malformed_json(tmp_path: Path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json")

    with pytest.raises(json.JSONDecodeError):
        load_raw_article(path)


def test_load_raw_article_raises_on_schema_invalid_json(tmp_path: Path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"title": "Missing fields"}))

    with pytest.raises(ValidationError):
        load_raw_article(path)


def test_to_document_maps_content_and_metadata():
    record = RawArticleRecord(
        title="Inferno",
        game="cs2",
        category="maps",
        url="https://liquipedia.net/counterstrike/Inferno",
        content="Inferno is a map.",
        updated_at="2026-07-27T20:52:27.349159Z",
        tags=["map"],
    )

    document = to_document(record)

    assert document.page_content == "Inferno is a map."
    assert document.metadata == {
        "game": "cs2",
        "category": "maps",
        "title": "Inferno",
        "url": "https://liquipedia.net/counterstrike/Inferno",
        "updated_at": "2026-07-27T20:52:27.349159+00:00",
        "tags": ["map"],
    }


def test_load_documents_collects_valid_and_isolates_invalid(tmp_path: Path):
    game_dir = tmp_path / "cs2" / "maps"
    game_dir.mkdir(parents=True)
    valid_path = game_dir / "inferno.json"
    valid_path.write_text(
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
    invalid_path = game_dir / "broken.json"
    invalid_path.write_text("{not valid json")

    result = load_documents(tmp_path)

    assert len(result.documents) == 1
    assert result.documents[0].metadata["title"] == "Inferno"
    assert len(result.failed) == 1
    assert result.failed[0][0] == str(invalid_path)


def test_load_documents_returns_empty_result_for_empty_dir(tmp_path: Path):
    result = load_documents(tmp_path)

    assert result.documents == []
    assert result.failed == []
