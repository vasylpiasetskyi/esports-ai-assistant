import asyncio
import json

import pytest
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.services.exceptions import MatchNotFoundError
from mcp_server.tools.match import register_get_match_tool


class FakeMatchService:
    def __init__(self, matches: dict) -> None:
        self._matches = matches

    def get_match(self, game: str, match_id: str):
        key = (game, match_id)
        if key not in self._matches:
            raise MatchNotFoundError(f"No match '{match_id}' found for game '{game}'")
        return self._matches[key]


class FakeMatch:
    def __init__(self, **data) -> None:
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def _build_server(match_service) -> MCPServer:
    server = MCPServer("esports-ai")
    register_get_match_tool(server, match_service)
    return server


def test_get_match_tool_is_discoverable_with_expected_schema():
    server = _build_server(FakeMatchService({}))

    tools = asyncio.run(server.list_tools())

    assert len(tools) == 1
    assert tools[0].name == "get_match"
    assert tools[0].input_schema["required"] == ["game", "match_id"]


def test_get_match_tool_returns_service_result_as_dict():
    fake_service = FakeMatchService(
        {
            ("cs2", "navi-vs-vitality-2026-08-01"): FakeMatch(
                match_id="navi-vs-vitality-2026-08-01",
                game="cs2",
                teams=["NAVI", "Vitality"],
                score="1-2",
                status="finished",
                date="2026-08-01",
                tournament="IEM Cologne 2026",
            )
        }
    )
    server = _build_server(fake_service)

    result = asyncio.run(
        server.call_tool("get_match", {"game": "cs2", "match_id": "navi-vs-vitality-2026-08-01"})
    )

    assert json.loads(result.content[0].text) == {
        "match_id": "navi-vs-vitality-2026-08-01",
        "game": "cs2",
        "teams": ["NAVI", "Vitality"],
        "score": "1-2",
        "status": "finished",
        "date": "2026-08-01",
        "tournament": "IEM Cologne 2026",
    }


def test_get_match_tool_raises_tool_error_when_not_found():
    server = _build_server(FakeMatchService({}))

    with pytest.raises(ToolError, match="No match 'unknown'"):
        asyncio.run(server.call_tool("get_match", {"game": "cs2", "match_id": "unknown"}))
