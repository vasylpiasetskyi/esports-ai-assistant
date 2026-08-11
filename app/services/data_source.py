import json
from pathlib import Path

DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures"


class MockEsportsDataSource:
    """Stands in for a real esports API (docs/roadmap-ai-assistant.md §6).

    Services depend on this class, not on JSON files directly, so this can be
    replaced with a real HTTP client later without changing any service or tool.
    """

    def __init__(self, fixtures_dir: Path = DEFAULT_FIXTURES_DIR) -> None:
        self._players = self._load(fixtures_dir / "players.json")
        self._teams = self._load(fixtures_dir / "teams.json")
        self._matches = self._load(fixtures_dir / "matches.json")

    @staticmethod
    def _load(path: Path) -> list[dict]:
        return json.loads(path.read_text())

    def find_player(self, game: str, player_name: str) -> dict | None:
        return next(
            (
                player
                for player in self._players
                if player["game"] == game and player["name"].lower() == player_name.lower()
            ),
            None,
        )

    def find_team(self, game: str, team_name: str) -> dict | None:
        return next(
            (
                team
                for team in self._teams
                if team["game"] == game and team["name"].lower() == team_name.lower()
            ),
            None,
        )

    def find_match(self, game: str, match_id: str) -> dict | None:
        return next(
            (
                match
                for match in self._matches
                if match["game"] == game and match["match_id"] == match_id
            ),
            None,
        )
