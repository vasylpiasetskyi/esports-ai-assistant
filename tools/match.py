from langchain_core.tools import tool
from pydantic import BaseModel, Field

from services.match_service import MatchService


class GetMatchInput(BaseModel):
    game: str = Field(description="Game slug, e.g. 'cs2', 'dota2', 'lol', 'valorant'.")
    match_id: str = Field(description="Match id, e.g. 'navi-vs-vitality-2026-08-01'.")


def make_get_match_tool(match_service: MatchService):
    """Bind a `get_match` tool to a `MatchService` instance (see `tools/player.py`)."""

    @tool("get_match", args_schema=GetMatchInput)
    def get_match(game: str, match_id: str) -> dict:
        """Look up structured match information: teams, score, status, date, tournament."""
        return match_service.get_match(game, match_id).model_dump()

    return get_match
