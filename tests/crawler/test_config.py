import json
from pathlib import Path

from crawler.config import load_page_specs
from crawler.models import PageSpec


def test_load_page_specs_parses_json_into_page_specs(tmp_path: Path):
    data = [
        {"game": "cs2", "category": "maps", "title": "Inferno", "slug": "inferno", "tags": ["map"]}
    ]
    config_path = tmp_path / "pages.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")

    specs = load_page_specs(config_path)

    assert specs == [
        PageSpec(game="cs2", category="maps", title="Inferno", slug="inferno", tags=["map"])
    ]


def test_repo_pages_config_loads_and_covers_all_v1_games():
    repo_config = Path(__file__).parents[2] / "config" / "pages.json"

    specs = load_page_specs(repo_config)

    assert len(specs) == 12
    assert {spec.game for spec in specs} == {"cs2", "dota2", "lol", "valorant"}
