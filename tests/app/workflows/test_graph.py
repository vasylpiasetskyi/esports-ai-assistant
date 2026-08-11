from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from app.rag.chains import RagAnswer
from app.services.exceptions import MatchNotFoundError
from app.services.models import Match
from app.workflows.graph import build_investigation_graph
from app.workflows.nodes import route_after_analysis


class FakeToolCallingChatModel(FakeMessagesListChatModel):
    """See `tests/app/agents/test_esports_agent.py` (Milestone 5) and
    `tests/scripts/test_run_tool_loop.py` (Milestone 4) for the same
    pattern."""

    def bind_tools(self, tools, **kwargs):
        return self.bind(tools=tools, **kwargs)


class FakeMatchService:
    def __init__(self, match: Match | None) -> None:
        self._match = match

    def get_latest_match_for_team(self, game: str, team_name: str) -> Match:
        if self._match is None:
            raise MatchNotFoundError(f"No matches found for team '{team_name}' in game '{game}'")
        return self._match

    def get_match(self, game: str, match_id: str) -> Match:
        return self._match


class FakeRAGService:
    def __init__(self, answer: RagAnswer) -> None:
        self._answer = answer
        self.calls: list[tuple[str, str | None]] = []

    def answer(self, question: str, game: str | None = None) -> RagAnswer:
        self.calls.append((question, game))
        return self._answer


def _initial_state(question: str) -> dict:
    return {
        "question": question,
        "game": "",
        "team_name": None,
        "match_id": None,
        "evidence": [],
        "findings": [],
        "needs_more_data": False,
        "retry_count": 0,
        "final_answer": None,
    }


_NAVI_VS_VITALITY = Match(
    match_id="navi-vs-vitality-2026-08-01",
    game="cs2",
    teams=["NAVI", "Vitality"],
    score="1-2",
    status="finished",
    date="2026-08-01",
    tournament="IEM Cologne 2026",
)


def test_investigation_graph_produces_report_without_retry_when_evidence_is_sufficient():
    match_service = FakeMatchService(_NAVI_VS_VITALITY)
    rag_service = FakeRAGService(
        RagAnswer(answer="Vitality's AWPer had a standout series.", sources=[])
    )
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "QuestionAnalysis",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "EvidenceAnalysis",
                        "args": {"sufficient": True, "findings": ["NAVI lost 1-2 to Vitality."]},
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(content="NAVI lost their latest match 1-2 to Vitality."),
        ]
    )
    graph = build_investigation_graph(llm, match_service, rag_service)

    result = graph.invoke(_initial_state("Why did NAVI lose their latest match?"))

    assert result["retry_count"] == 0
    assert result["match_id"] == "navi-vs-vitality-2026-08-01"
    assert result["findings"] == ["NAVI lost 1-2 to Vitality."]
    assert result["final_answer"] == "NAVI lost their latest match 1-2 to Vitality."


def test_investigation_graph_retries_once_then_forces_termination():
    match_service = FakeMatchService(_NAVI_VS_VITALITY)
    rag_service = FakeRAGService(RagAnswer(answer="No detailed analysis available.", sources=[]))
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "QuestionAnalysis",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "EvidenceAnalysis",
                        "args": {"sufficient": False, "findings": []},
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "EvidenceAnalysis",
                        "args": {"sufficient": False, "findings": []},
                        "id": "call_3",
                    }
                ],
            ),
            AIMessage(content="Unable to fully determine why NAVI lost."),
        ]
    )
    graph = build_investigation_graph(llm, match_service, rag_service)

    result = graph.invoke(_initial_state("Why did NAVI lose their latest match?"))

    assert result["retry_count"] == 2
    assert len(rag_service.calls) == 2
    assert result["final_answer"] == "Unable to fully determine why NAVI lost."


def test_investigation_graph_degrades_gracefully_when_match_not_found():
    match_service = FakeMatchService(None)
    rag_service = FakeRAGService(RagAnswer(answer="NAVI is a well-known CS2 org.", sources=[]))
    llm = FakeToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "QuestionAnalysis",
                        "args": {"game": "cs2", "team_name": "NAVI"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "EvidenceAnalysis",
                        "args": {"sufficient": True, "findings": ["No recent match on record."]},
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(content="No recent match found for NAVI; here's general info instead."),
        ]
    )
    graph = build_investigation_graph(llm, match_service, rag_service)

    result = graph.invoke(_initial_state("Why did NAVI lose their latest match?"))

    assert result["match_id"] is None
    assert any(item.startswith("Error: ") for item in result["evidence"])
    assert result["final_answer"] == "No recent match found for NAVI; here's general info instead."


def test_route_after_analysis_generates_report_when_sufficient():
    state = {"needs_more_data": False, "retry_count": 0}

    assert route_after_analysis(state) == "generate_report"


def test_route_after_analysis_retries_when_insufficient_and_under_cap():
    state = {"needs_more_data": True, "retry_count": 1}

    assert route_after_analysis(state) == "retrieve_knowledge"


def test_route_after_analysis_forces_report_when_insufficient_and_at_cap():
    state = {"needs_more_data": True, "retry_count": 2}

    assert route_after_analysis(state) == "generate_report"
