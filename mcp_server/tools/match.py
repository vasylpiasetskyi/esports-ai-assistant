from mcp.server import MCPServer

from app.services.match_service import MatchService


def register_get_match_tool(server: MCPServer, match_service: MatchService) -> None:
    @server.tool(
        name="get_match",
        description="Look up structured match information: teams, score, status, date, tournament.",
    )
    def get_match(game: str, match_id: str) -> dict:
        return match_service.get_match(game, match_id).model_dump()
