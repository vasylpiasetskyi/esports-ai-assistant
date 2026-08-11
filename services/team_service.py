from services.data_source import MockEsportsDataSource
from services.exceptions import TeamNotFoundError
from services.models import Team


class TeamService:
    def __init__(self, data_source: MockEsportsDataSource) -> None:
        self._data_source = data_source

    def get_team(self, game: str, team_name: str) -> Team:
        record = self._data_source.find_team(game, team_name)
        if record is None:
            raise TeamNotFoundError(f"No team named '{team_name}' found for game '{game}'")
        return Team(**record)
