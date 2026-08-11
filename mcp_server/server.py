import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from mcp.server import MCPServer
from qdrant_client import QdrantClient

from app.rag.service import RAGService
from app.services.data_source import MockEsportsDataSource
from app.services.match_service import MatchService
from app.services.player_service import PlayerService
from app.services.team_service import TeamService
from mcp_server.tools.knowledge import register_search_knowledge_base_tool
from mcp_server.tools.match import register_get_match_tool
from mcp_server.tools.player import register_get_player_tool
from mcp_server.tools.team import register_get_team_tool

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_QDRANT_URL = "http://localhost:6333"


def build_server(player_service, team_service, match_service, rag_service) -> MCPServer:
    server = MCPServer("esports-ai")
    register_get_player_tool(server, player_service)
    register_get_team_tool(server, team_service)
    register_get_match_tool(server, match_service)
    register_search_knowledge_base_tool(server, rag_service)
    return server


def main() -> None:
    data_source = MockEsportsDataSource()
    qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL))
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    llm = ChatOpenAI(model=CHAT_MODEL)
    rag_service = RAGService(qdrant_client, embeddings, llm)

    server = build_server(
        PlayerService(data_source),
        TeamService(data_source),
        MatchService(data_source),
        rag_service,
    )
    server.run()


if __name__ == "__main__":
    main()
