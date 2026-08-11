from datetime import UTC, datetime
from pathlib import Path

from crawler.models import RawPage
from crawler.parser import MediaWikiHtmlParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _make_raw_page(html: str) -> RawPage:
    return RawPage(
        html=html,
        url="https://liquipedia.net/counterstrike/Natus_Vincere",
        retrieved_at=datetime.now(UTC),
    )


def test_extract_removes_infobox_navbox_and_edit_links():
    html = _load_fixture("liquipedia_team_page.html")

    text = MediaWikiHtmlParser().extract(_make_raw_page(html))

    assert "Ukraine" in text
    assert "Location" not in text
    assert "navigation" not in text
    assert "[edit]" not in text
    assert "citation" not in text


def test_extract_collapses_whitespace():
    html = "<p>Hello   \n\n  world</p>"

    text = MediaWikiHtmlParser().extract(_make_raw_page(html))

    assert text == "Hello world"
