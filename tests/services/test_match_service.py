import pytest

from services.data_source import MockEsportsDataSource
from services.exceptions import MatchNotFoundError
from services.match_service import MatchService


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
