from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.services.team_service import TeamService


class GetTeamInput(BaseModel):
    game: str = Field(description="Game slug, e.g. 'cs2', 'dota2', 'lol', 'valorant'.")
    team_name: str = Field(description="Team name, e.g. 'NAVI'.")


def make_get_team_tool(team_service: TeamService):
    """Bind a `get_team` tool to a `TeamService` instance (see `tools/player.py`)."""

    @tool("get_team", args_schema=GetTeamInput)
    def get_team(game: str, team_name: str) -> dict:
        """Look up structured information about an esports team: name, game, roster."""
        return team_service.get_team(game, team_name).model_dump()

    return get_team
