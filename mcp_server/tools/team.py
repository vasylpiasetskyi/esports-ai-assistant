from mcp.server import MCPServer

from app.services.team_service import TeamService


def register_get_team_tool(server: MCPServer, team_service: TeamService) -> None:
    @server.tool(
        name="get_team",
        description="Look up structured information about an esports team: name, game, roster.",
    )
    def get_team(game: str, team_name: str) -> dict:
        return team_service.get_team(game, team_name).model_dump()
