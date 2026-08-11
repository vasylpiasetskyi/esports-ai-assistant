from app.rag.chains import RagAnswer
from app.tools.knowledge import make_search_knowledge_base_tool


class FakeRAGService:
    def __init__(self, answer: RagAnswer) -> None:
        self._answer = answer
        self.calls: list[tuple[str, str | None]] = []

    def answer(self, question: str, game: str | None = None) -> RagAnswer:
        self.calls.append((question, game))
        return self._answer


def test_search_knowledge_base_tool_has_expected_name_and_schema():
    tool = make_search_knowledge_base_tool(FakeRAGService(RagAnswer(answer="", sources=[])))

    assert tool.name == "search_knowledge_base"
    schema = tool.args_schema.model_json_schema()
    assert schema["required"] == ["question"]


def test_search_knowledge_base_tool_calls_rag_service_with_question_only():
    fake_service = FakeRAGService(
        RagAnswer(
            answer="Inferno is a CS2 map.", sources=["https://liquipedia.net/counterstrike/Inferno"]
        )
    )
    tool = make_search_knowledge_base_tool(fake_service)

    result = tool.invoke({"question": "What is Inferno?"})

    assert fake_service.calls == [("What is Inferno?", None)]
    assert result == {
        "answer": "Inferno is a CS2 map.",
        "sources": ["https://liquipedia.net/counterstrike/Inferno"],
    }


def test_search_knowledge_base_tool_passes_game_through():
    fake_service = FakeRAGService(RagAnswer(answer="Baron Nashor answer.", sources=[]))
    tool = make_search_knowledge_base_tool(fake_service)

    tool.invoke({"question": "What is Baron Nashor?", "game": "lol"})

    assert fake_service.calls == [("What is Baron Nashor?", "lol")]


def test_search_knowledge_base_tool_returns_empty_sources_list_unchanged():
    fake_service = FakeRAGService(RagAnswer(answer="I don't have enough information.", sources=[]))
    tool = make_search_knowledge_base_tool(fake_service)

    result = tool.invoke({"question": "What is a Baron Nashor?"})

    assert result["sources"] == []
