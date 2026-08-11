import pytest

from app.services.data_source import MockEsportsDataSource
from app.services.exceptions import TeamNotFoundError
from app.services.team_service import TeamService


def test_get_team_returns_matching_team():
    service = TeamService(MockEsportsDataSource())

    team = service.get_team("cs2", "NAVI")

    assert team.name == "NAVI"
    assert team.game == "cs2"
    assert team.players == ["s1mple", "b1t"]


def test_get_team_is_case_insensitive():
    service = TeamService(MockEsportsDataSource())

    team = service.get_team("cs2", "navi")

    assert team.name == "NAVI"


def test_get_team_raises_when_team_not_found():
    service = TeamService(MockEsportsDataSource())

    with pytest.raises(TeamNotFoundError):
        service.get_team("cs2", "unknown-team")
