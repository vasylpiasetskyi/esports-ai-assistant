import asyncio

from mcp_server.server import build_server


class _StubPlayerService:
    def get_player(self, game, player_name):
        raise NotImplementedError


class _StubTeamService:
    def get_team(self, game, team_name):
        raise NotImplementedError


class _StubMatchService:
    def get_match(self, game, match_id):
        raise NotImplementedError


class _StubRAGService:
    def answer(self, question, game=None):
        raise NotImplementedError


def test_build_server_registers_all_four_tools():
    server = build_server(
        _StubPlayerService(), _StubTeamService(), _StubMatchService(), _StubRAGService()
    )

    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {
        "get_player",
        "get_team",
        "get_match",
        "search_knowledge_base",
    }
