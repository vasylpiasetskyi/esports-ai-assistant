from app.services.data_source import MockEsportsDataSource
from app.services.exceptions import MatchNotFoundError
from app.services.models import Match


class MatchService:
    def __init__(self, data_source: MockEsportsDataSource) -> None:
        self._data_source = data_source

    def get_match(self, game: str, match_id: str) -> Match:
        record = self._data_source.find_match(game, match_id)
        if record is None:
            raise MatchNotFoundError(f"No match '{match_id}' found for game '{game}'")
        return Match(**record)
