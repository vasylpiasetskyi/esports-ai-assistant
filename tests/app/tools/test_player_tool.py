import pytest

from app.services.exceptions import PlayerNotFoundError
from app.tools.player import make_get_player_tool


class FakePlayerService:
    def __init__(self, players: dict) -> None:
        self._players = players

    def get_player(self, game: str, player_name: str):
        key = (game, player_name)
        if key not in self._players:
            raise PlayerNotFoundError(f"No player named '{player_name}' found for game '{game}'")
        return self._players[key]


class FakePlayer:
    def __init__(self, **data) -> None:
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def test_get_player_tool_has_expected_name_and_schema():
    tool = make_get_player_tool(FakePlayerService({}))

    assert tool.name == "get_player"
    schema = tool.args_schema.model_json_schema()
    assert set(schema["required"]) == {"game", "player_name"}


def test_get_player_tool_returns_service_result_as_dict():
    fake_service = FakePlayerService(
        {("cs2", "s1mple"): FakePlayer(name="s1mple", game="cs2", team="NAVI")}
    )
    tool = make_get_player_tool(fake_service)

    result = tool.invoke({"game": "cs2", "player_name": "s1mple"})

    assert result == {"name": "s1mple", "game": "cs2", "team": "NAVI"}


def test_get_player_tool_propagates_not_found_error():
    tool = make_get_player_tool(FakePlayerService({}))

    with pytest.raises(PlayerNotFoundError):
        tool.invoke({"game": "cs2", "player_name": "unknown"})
