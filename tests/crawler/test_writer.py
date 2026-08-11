import json
from datetime import UTC, datetime
from pathlib import Path

from crawler.models import RawArticle
from crawler.writer import JsonArticleWriter


def _make_article() -> RawArticle:
    return RawArticle(
        title="Natus Vincere",
        game="cs2",
        category="teams",
        url="https://liquipedia.net/counterstrike/Natus_Vincere",
        content="Natus Vincere is a team from Ukraine.",
        updated_at=datetime.now(UTC),
        tags=["team", "ukraine"],
    )


def test_save_writes_json_to_game_category_slug_path(tmp_path: Path):
    writer = JsonArticleWriter(base_dir=tmp_path)
    article = _make_article()

    saved_path = writer.save(article, slug="navi")

    expected_path = tmp_path / "cs2" / "teams" / "navi.json"
    assert saved_path == expected_path
    assert expected_path.exists()


def test_save_writes_valid_json_matching_article_fields(tmp_path: Path):
    writer = JsonArticleWriter(base_dir=tmp_path)
    article = _make_article()

    saved_path = writer.save(article, slug="navi")

    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["title"] == "Natus Vincere"
    assert data["game"] == "cs2"
    assert data["category"] == "teams"
    assert data["tags"] == ["team", "ukraine"]
