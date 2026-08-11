import json
from pathlib import Path

import httpx

from crawler.models import PageSpec
from crawler.service import build_pipeline, run_crawl


def test_build_pipeline_runs_end_to_end_against_fake_transport(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"parse": {"text": {"*": "<p>Natus Vincere is a team from Ukraine.</p>"}}},
        )

    transport = httpx.MockTransport(handler)
    spec = PageSpec(
        game="cs2", category="teams", title="Natus Vincere", slug="navi", tags=["team", "ukraine"]
    )

    with httpx.Client(transport=transport) as http_client:
        pipeline = build_pipeline(http_client, base_dir=tmp_path)
        result = pipeline.run([spec])

    assert result.succeeded == ["Natus Vincere"]
    saved_file = tmp_path / "cs2" / "teams" / "navi.json"
    assert saved_file.exists()
    assert "Ukraine" in saved_file.read_text(encoding="utf-8")


def test_run_crawl_loads_config_and_writes_results(tmp_path: Path):
    config_path = tmp_path / "pages.json"
    config_path.write_text(
        json.dumps(
            [
                {
                    "game": "cs2",
                    "category": "teams",
                    "title": "Natus Vincere",
                    "slug": "navi",
                    "tags": ["team"],
                }
            ]
        )
    )
    data_dir = tmp_path / "raw"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"parse": {"text": {"*": "<p>Natus Vincere is a team from Ukraine.</p>"}}},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))

    result = run_crawl(config_path=config_path, base_dir=data_dir, http_client=http_client)

    assert result.succeeded == ["Natus Vincere"]
    assert (data_dir / "cs2" / "teams" / "navi.json").exists()
