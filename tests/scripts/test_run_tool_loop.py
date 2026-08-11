import json

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.services.exceptions import PlayerNotFoundError
from app.tools.player import make_get_player_tool
from app.tools.team import make_get_team_tool
from scripts.run_tool_loop import run


class FakeToolCallingChatModel(FakeMessagesListChatModel):
    """`FakeMessagesListChatModel` doesn't implement `bind_tools` (raises
    `NotImplementedError`, inherited from `BaseChatModel`). Override it with
    the generic, always-available `Runnable.bind()` — the fake ignores the
    `tools` kwarg anyway, it just needs `bind_tools()` to not raise."""

    def bind_tools(self, tools, **kwargs):
        return self.bind(tools=tools, **kwargs)


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


class FakeTeamService:
    def __init__(self, teams: dict) -> None:
        self._teams = teams

    def get_team(self, game: str, team_name: str):
        return self._teams[(game, team_name)]


class FakeTeam:
    def __init__(self, **data) -> None:
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def test_run_executes_single_tool_call_then_returns_final_answer():
    player_tool = make_get_player_tool(
        FakePlayerService({("cs2", "s1mple"): FakePlayer(name="s1mple", game="cs2", team="NAVI")})
    )
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_player",
                        "args": {"game": "cs2", "player_name": "s1mple"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="s1mple plays for NAVI."),
        ]
    )

    messages = run(llm, [player_tool], "Who is s1mple?")

    assert [type(m) for m in messages] == [HumanMessage, AIMessage, ToolMessage, AIMessage]
    tool_message = messages[2]
    assert tool_message.tool_call_id == "call_1"
    assert json.loads(tool_message.content) == {"name": "s1mple", "game": "cs2", "team": "NAVI"}
    assert messages[-1].content == "s1mple plays for NAVI."


def test_run_executes_multiple_tool_calls_in_one_round():
    player_tool = make_get_player_tool(
        FakePlayerService({("cs2", "s1mple"): FakePlayer(name="s1mple", game="cs2", team="NAVI")})
    )
    team_tool = make_get_team_tool(
        FakeTeamService({("cs2", "NAVI"): FakeTeam(name="NAVI", game="cs2", players=["s1mple"])})
    )
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_player",
                        "args": {"game": "cs2", "player_name": "s1mple"},
                        "id": "call_1",
                    },
                    {
                        "name": "get_team",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_2",
                    },
                ],
            ),
            AIMessage(content="s1mple plays for NAVI."),
        ]
    )

    messages = run(llm, [player_tool, team_tool], "Tell me about s1mple and NAVI.")

    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert [tm.tool_call_id for tm in tool_messages] == ["call_1", "call_2"]
    assert json.loads(tool_messages[0].content) == {"name": "s1mple", "game": "cs2", "team": "NAVI"}
    assert json.loads(tool_messages[1].content) == {
        "name": "NAVI",
        "game": "cs2",
        "players": ["s1mple"],
    }


def test_run_surfaces_tool_error_as_tool_message():
    player_tool = make_get_player_tool(FakePlayerService({}))
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_player",
                        "args": {"game": "cs2", "player_name": "unknown"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="I couldn't find that player."),
        ]
    )

    messages = run(llm, [player_tool], "Who is unknown?")

    tool_message = messages[2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content.startswith("Error: ")
    assert "unknown" in tool_message.content
    assert messages[-1].content == "I couldn't find that player."


def test_run_returns_immediately_when_no_tool_call_is_made():
    player_tool = make_get_player_tool(FakePlayerService({}))
    llm = FakeToolCallingChatModel(responses=[AIMessage(content="I don't need a tool for that.")])

    messages = run(llm, [player_tool], "How are you?")

    assert [type(m) for m in messages] == [HumanMessage, AIMessage]
    assert messages[-1].content == "I don't need a tool for that."
