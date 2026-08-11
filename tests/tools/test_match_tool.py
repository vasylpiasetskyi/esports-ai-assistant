import pytest

from services.exceptions import MatchNotFoundError
from tools.match import make_get_match_tool


class FakeMatchService:
    def __init__(self, matches: dict) -> None:
        self._matches = matches

    def get_match(self, game: str, match_id: str):
        key = (game, match_id)
        if key not in self._matches:
            raise MatchNotFoundError(f"No match '{match_id}' found for game '{game}'")
        return self._matches[key]


class FakeMatch:
    def __init__(self, **data) -> None:
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def test_get_match_tool_has_expected_name_and_schema():
    tool = make_get_match_tool(FakeMatchService({}))

    assert tool.name == "get_match"
    schema = tool.args_schema.model_json_schema()
    assert set(schema["required"]) == {"game", "match_id"}


def test_get_match_tool_returns_service_result_as_dict():
    fake_service = FakeMatchService(
        {
            ("cs2", "navi-vs-vitality-2026-08-01"): FakeMatch(
                match_id="navi-vs-vitality-2026-08-01",
                game="cs2",
                teams=["NAVI", "Vitality"],
                score="1-2",
                status="finished",
                date="2026-08-01",
                tournament="IEM Cologne 2026",
            )
        }
    )
    tool = make_get_match_tool(fake_service)

    result = tool.invoke({"game": "cs2", "match_id": "navi-vs-vitality-2026-08-01"})

    assert result["teams"] == ["NAVI", "Vitality"]
    assert result["tournament"] == "IEM Cologne 2026"


def test_get_match_tool_propagates_not_found_error():
    tool = make_get_match_tool(FakeMatchService({}))

    with pytest.raises(MatchNotFoundError):
        tool.invoke({"game": "cs2", "match_id": "unknown"})
