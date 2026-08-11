import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from app.agents.esports_agent import make_esports_agent
from app.rag.chains import RagAnswer
from app.services.exceptions import PlayerNotFoundError
from app.tools.knowledge import make_search_knowledge_base_tool
from app.tools.player import make_get_player_tool
from app.tools.team import make_get_team_tool


class FakeToolCallingChatModel(FakeMessagesListChatModel):
    """See `tests/scripts/test_run_tool_loop.py` (Milestone 4) for the same
    pattern: `FakeMessagesListChatModel` doesn't implement `bind_tools`
    (raises `NotImplementedError`) — override it with the generic,
    always-available `Runnable.bind()`."""

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


class FakeRAGService:
    def __init__(self, answer: RagAnswer) -> None:
        self._answer = answer

    def answer(self, question: str, game: str | None = None) -> RagAnswer:
        return self._answer


def test_agent_executes_single_tool_call_and_returns_final_answer():
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
    executor = make_esports_agent(llm, [player_tool])

    result = executor.invoke({"input": "Who is s1mple?"})

    assert result["output"] == "s1mple plays for NAVI."


def test_agent_combines_rag_and_structured_tools_in_one_run():
    player_tool = make_get_player_tool(
        FakePlayerService({("cs2", "s1mple"): FakePlayer(name="s1mple", game="cs2", team="NAVI")})
    )
    team_tool = make_get_team_tool(
        FakeTeamService({("cs2", "NAVI"): FakeTeam(name="NAVI", game="cs2", players=["s1mple"])})
    )
    knowledge_tool = make_search_knowledge_base_tool(
        FakeRAGService(
            RagAnswer(
                answer="NAVI is a CS2 org.",
                sources=["https://liquipedia.net/counterstrike/Natus_Vincere"],
            )
        )
    )
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge_base",
                        "args": {"question": "Tell me about NAVI"},
                        "id": "call_1",
                    },
                    {
                        "name": "get_player",
                        "args": {"game": "cs2", "player_name": "s1mple"},
                        "id": "call_2",
                    },
                    {
                        "name": "get_team",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_3",
                    },
                ],
            ),
            AIMessage(content="s1mple plays for NAVI, a CS2 org."),
        ]
    )
    executor = make_esports_agent(llm, [knowledge_tool, player_tool, team_tool])

    result = executor.invoke({"input": "Tell me about s1mple and his current team."})

    called_tools = {action.tool for action, _ in result["intermediate_steps"]}
    assert called_tools == {"search_knowledge_base", "get_player", "get_team"}
    assert result["output"] == "s1mple plays for NAVI, a CS2 org."


def test_agent_surfaces_tool_error_without_crashing():
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
    executor = make_esports_agent(llm, [player_tool])

    result = executor.invoke({"input": "Who is unknown?"})

    assert result["output"] == "I couldn't find that player."


def test_make_esports_agent_does_not_mutate_original_tools():
    player_tool = make_get_player_tool(FakePlayerService({}))
    llm = FakeToolCallingChatModel(responses=[AIMessage(content="ok")])

    make_esports_agent(llm, [player_tool])

    with pytest.raises(PlayerNotFoundError):
        player_tool.invoke({"game": "cs2", "player_name": "unknown"})
