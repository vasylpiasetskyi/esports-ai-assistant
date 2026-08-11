import asyncio
import json

import pytest
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.services.exceptions import PlayerNotFoundError
from mcp_server.tools.player import register_get_player_tool


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


def _build_server(player_service) -> MCPServer:
    server = MCPServer("esports-ai")
    register_get_player_tool(server, player_service)
    return server


def test_get_player_tool_is_discoverable_with_expected_schema():
    server = _build_server(FakePlayerService({}))

    tools = asyncio.run(server.list_tools())

    assert len(tools) == 1
    assert tools[0].name == "get_player"
    assert tools[0].input_schema["required"] == ["game", "player_name"]


def test_get_player_tool_returns_service_result_as_dict():
    fake_service = FakePlayerService(
        {("cs2", "s1mple"): FakePlayer(name="s1mple", game="cs2", team="NAVI")}
    )
    server = _build_server(fake_service)

    result = asyncio.run(server.call_tool("get_player", {"game": "cs2", "player_name": "s1mple"}))

    assert json.loads(result.content[0].text) == {"name": "s1mple", "game": "cs2", "team": "NAVI"}


def test_get_player_tool_raises_tool_error_when_not_found():
    server = _build_server(FakePlayerService({}))

    with pytest.raises(ToolError, match="No player named 'unknown'"):
        asyncio.run(server.call_tool("get_player", {"game": "cs2", "player_name": "unknown"}))
