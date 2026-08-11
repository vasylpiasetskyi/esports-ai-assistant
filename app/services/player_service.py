from app.services.data_source import MockEsportsDataSource
from app.services.exceptions import PlayerNotFoundError
from app.services.models import Player


class PlayerService:
    def __init__(self, data_source: MockEsportsDataSource) -> None:
        self._data_source = data_source

    def get_player(self, game: str, player_name: str) -> Player:
        record = self._data_source.find_player(game, player_name)
        if record is None:
            raise PlayerNotFoundError(f"No player named '{player_name}' found for game '{game}'")
        return Player(**record)
