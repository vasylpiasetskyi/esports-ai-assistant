import pytest

from services.exceptions import TeamNotFoundError
from tools.team import make_get_team_tool


class FakeTeamService:
    def __init__(self, teams: dict) -> None:
        self._teams = teams

    def get_team(self, game: str, team_name: str):
        key = (game, team_name)
        if key not in self._teams:
            raise TeamNotFoundError(f"No team named '{team_name}' found for game '{game}'")
        return self._teams[key]


class FakeTeam:
    def __init__(self, **data) -> None:
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def test_get_team_tool_has_expected_name_and_schema():
    tool = make_get_team_tool(FakeTeamService({}))

    assert tool.name == "get_team"
    schema = tool.args_schema.model_json_schema()
    assert set(schema["required"]) == {"game", "team_name"}


def test_get_team_tool_returns_service_result_as_dict():
    fake_service = FakeTeamService(
        {("cs2", "NAVI"): FakeTeam(name="NAVI", game="cs2", players=["s1mple", "b1t"])}
    )
    tool = make_get_team_tool(fake_service)

    result = tool.invoke({"game": "cs2", "team_name": "NAVI"})

    assert result == {"name": "NAVI", "game": "cs2", "players": ["s1mple", "b1t"]}


def test_get_team_tool_propagates_not_found_error():
    tool = make_get_team_tool(FakeTeamService({}))

    with pytest.raises(TeamNotFoundError):
        tool.invoke({"game": "cs2", "team_name": "unknown"})
