import pytest
from pydantic import ValidationError

from ingestion.models import RawArticleRecord


def test_valid_data_parses_into_record():
    record = RawArticleRecord(
        title="Natus Vincere",
        game="cs2",
        category="teams",
        url="https://liquipedia.net/counterstrike/Natus_Vincere",
        content="Natus Vincere is a team from Ukraine.",
        updated_at="2026-07-27T20:52:29.454013Z",
        tags=["team", "ukraine"],
    )
    assert record.title == "Natus Vincere"
    assert record.tags == ["team", "ukraine"]


def test_missing_required_field_raises_validation_error():
    with pytest.raises(ValidationError):
        RawArticleRecord(
            game="cs2",
            category="teams",
            url="https://liquipedia.net/counterstrike/Natus_Vincere",
            content="...",
            updated_at="2026-07-27T20:52:29.454013Z",
        )
