import asyncio
import json

import pytest
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.services.exceptions import TeamNotFoundError
from mcp_server.tools.team import register_get_team_tool


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


def _build_server(team_service) -> MCPServer:
    server = MCPServer("esports-ai")
    register_get_team_tool(server, team_service)
    return server


def test_get_team_tool_is_discoverable_with_expected_schema():
    server = _build_server(FakeTeamService({}))

    tools = asyncio.run(server.list_tools())

    assert len(tools) == 1
    assert tools[0].name == "get_team"
    assert tools[0].input_schema["required"] == ["game", "team_name"]


def test_get_team_tool_returns_service_result_as_dict():
    fake_service = FakeTeamService(
        {("cs2", "NAVI"): FakeTeam(name="NAVI", game="cs2", players=["s1mple", "b1t"])}
    )
    server = _build_server(fake_service)

    result = asyncio.run(server.call_tool("get_team", {"game": "cs2", "team_name": "NAVI"}))

    assert json.loads(result.content[0].text) == {
        "name": "NAVI",
        "game": "cs2",
        "players": ["s1mple", "b1t"],
    }


def test_get_team_tool_raises_tool_error_when_not_found():
    server = _build_server(FakeTeamService({}))

    with pytest.raises(ToolError, match="No team named 'unknown'"):
        asyncio.run(server.call_tool("get_team", {"game": "cs2", "team_name": "unknown"}))
