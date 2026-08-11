import pytest

from services.data_source import MockEsportsDataSource
from services.exceptions import PlayerNotFoundError
from services.player_service import PlayerService


def test_get_player_returns_matching_player():
    service = PlayerService(MockEsportsDataSource())

    player = service.get_player("cs2", "s1mple")

    assert player.name == "s1mple"
    assert player.game == "cs2"
    assert player.team == "NAVI"


def test_get_player_is_case_insensitive():
    service = PlayerService(MockEsportsDataSource())

    player = service.get_player("cs2", "S1MPLE")

    assert player.name == "s1mple"


def test_get_player_raises_when_player_not_found():
    service = PlayerService(MockEsportsDataSource())

    with pytest.raises(PlayerNotFoundError):
        service.get_player("cs2", "unknown-player")


def test_get_player_raises_when_player_exists_for_different_game():
    service = PlayerService(MockEsportsDataSource())

    with pytest.raises(PlayerNotFoundError):
        service.get_player("dota2", "s1mple")
