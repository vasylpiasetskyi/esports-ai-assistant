from mcp.server import MCPServer

from app.services.player_service import PlayerService


def register_get_player_tool(server: MCPServer, player_service: PlayerService) -> None:
    @server.tool(
        name="get_player",
        description="Look up structured information about an esports player: name, game, current team.",
    )
    def get_player(game: str, player_name: str) -> dict:
        return player_service.get_player(game, player_name).model_dump()
