from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.services.player_service import PlayerService


class GetPlayerInput(BaseModel):
    game: str = Field(description="Game slug, e.g. 'cs2', 'dota2', 'lol', 'valorant'.")
    player_name: str = Field(description="Player nickname, e.g. 's1mple'.")


def make_get_player_tool(player_service: PlayerService):
    """Bind a `get_player` tool to a `PlayerService` instance.

    A factory (instead of a module-level `@tool`) avoids a global `PlayerService`
    singleton, keeping dependency injection and no global state (see `claude.md`).
    """

    @tool("get_player", args_schema=GetPlayerInput)
    def get_player(game: str, player_name: str) -> dict:
        """Look up structured information about an esports player: name, game, current team."""
        return player_service.get_player(game, player_name).model_dump()

    return get_player
