from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.rag.service import RAGService


class SearchKnowledgeBaseInput(BaseModel):
    question: str = Field(description="The question to search the knowledge base for.")
    game: str | None = Field(
        default=None,
        description="Optional game slug, e.g. 'cs2', 'dota2', 'lol', 'valorant', to scope the search.",
    )


def make_search_knowledge_base_tool(rag_service: RAGService):
    """Bind a `search_knowledge_base` tool to a `RAGService` instance (see `app/tools/player.py`)."""

    @tool("search_knowledge_base", args_schema=SearchKnowledgeBaseInput)
    def search_knowledge_base(question: str, game: str | None = None) -> dict:
        """Search the esports knowledge base for information about games, maps, mechanics, and general esports topics."""
        result = rag_service.answer(question, game)
        return {"answer": result.answer, "sources": result.sources}

    return search_knowledge_base
