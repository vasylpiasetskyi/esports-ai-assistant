from mcp.server import MCPServer

from app.rag.service import RAGService


def register_search_knowledge_base_tool(server: MCPServer, rag_service: RAGService) -> None:
    @server.tool(
        name="search_knowledge_base",
        description="Search the esports knowledge base for information about games, maps, mechanics, and general esports topics.",
    )
    def search_knowledge_base(question: str, game: str | None = None) -> dict:
        result = rag_service.answer(question, game)
        return {"answer": result.answer, "sources": result.sources}
