import json

import pytest

from app.services.data_source import MockEsportsDataSource
from app.services.exceptions import MatchNotFoundError
from app.services.match_service import MatchService


def test_get_match_returns_matching_match():
    service = MatchService(MockEsportsDataSource())

    match = service.get_match("cs2", "navi-vs-vitality-2026-08-01")

    assert match.teams == ["NAVI", "Vitality"]
    assert match.score == "1-2"
    assert match.status == "finished"
    assert match.tournament == "IEM Cologne 2026"


def test_get_match_raises_when_match_not_found():
    service = MatchService(MockEsportsDataSource())

    with pytest.raises(MatchNotFoundError):
        service.get_match("cs2", "unknown-match")


def test_get_match_raises_when_match_exists_for_different_game():
    service = MatchService(MockEsportsDataSource())

    with pytest.raises(MatchNotFoundError):
        service.get_match("lol", "navi-vs-vitality-2026-08-01")


def test_get_latest_match_for_team_returns_matching_match():
    service = MatchService(MockEsportsDataSource())

    match = service.get_latest_match_for_team("cs2", "NAVI")

    assert match.match_id == "navi-vs-vitality-2026-08-01"
    assert match.teams == ["NAVI", "Vitality"]


def test_get_latest_match_for_team_picks_most_recent_by_date(tmp_path):
    (tmp_path / "players.json").write_text("[]")
    (tmp_path / "teams.json").write_text("[]")
    (tmp_path / "matches.json").write_text(
        json.dumps(
            [
                {
                    "match_id": "navi-vs-spirit-2026-06-01",
                    "game": "cs2",
                    "teams": ["NAVI", "Spirit"],
                    "score": "2-0",
                    "status": "finished",
                    "date": "2026-06-01",
                    "tournament": "BLAST Spring 2026",
                },
                {
                    "match_id": "navi-vs-vitality-2026-08-01",
                    "game": "cs2",
                    "teams": ["NAVI", "Vitality"],
                    "score": "1-2",
                    "status": "finished",
                    "date": "2026-08-01",
                    "tournament": "IEM Cologne 2026",
                },
            ]
        )
    )
    service = MatchService(MockEsportsDataSource(tmp_path))

    match = service.get_latest_match_for_team("cs2", "NAVI")

    assert match.match_id == "navi-vs-vitality-2026-08-01"


def test_get_latest_match_for_team_raises_when_no_match_found():
    service = MatchService(MockEsportsDataSource())

    with pytest.raises(MatchNotFoundError):
        service.get_latest_match_for_team("cs2", "Astralis")
