import asyncio
import json

from mcp.server import MCPServer

from app.rag.chains import RagAnswer
from mcp_server.tools.knowledge import register_search_knowledge_base_tool


class FakeRAGService:
    def __init__(self, answer: RagAnswer) -> None:
        self._answer = answer
        self.calls: list[tuple[str, str | None]] = []

    def answer(self, question: str, game: str | None = None) -> RagAnswer:
        self.calls.append((question, game))
        return self._answer


def _build_server(rag_service) -> MCPServer:
    server = MCPServer("esports-ai")
    register_search_knowledge_base_tool(server, rag_service)
    return server


def test_search_knowledge_base_tool_is_discoverable_with_expected_schema():
    server = _build_server(FakeRAGService(RagAnswer(answer="", sources=[])))

    tools = asyncio.run(server.list_tools())

    assert len(tools) == 1
    assert tools[0].name == "search_knowledge_base"
    assert tools[0].input_schema["required"] == ["question"]


def test_search_knowledge_base_tool_returns_answer_and_sources():
    fake_service = FakeRAGService(
        RagAnswer(
            answer="Inferno is a CS2 map.", sources=["https://liquipedia.net/counterstrike/Inferno"]
        )
    )
    server = _build_server(fake_service)

    result = asyncio.run(
        server.call_tool("search_knowledge_base", {"question": "What is Inferno?"})
    )

    assert json.loads(result.content[0].text) == {
        "answer": "Inferno is a CS2 map.",
        "sources": ["https://liquipedia.net/counterstrike/Inferno"],
    }
    assert fake_service.calls == [("What is Inferno?", None)]


def test_search_knowledge_base_tool_passes_game_through():
    fake_service = FakeRAGService(RagAnswer(answer="Baron Nashor answer.", sources=[]))
    server = _build_server(fake_service)

    asyncio.run(
        server.call_tool(
            "search_knowledge_base", {"question": "What is Baron Nashor?", "game": "lol"}
        )
    )

    assert fake_service.calls == [("What is Baron Nashor?", "lol")]
