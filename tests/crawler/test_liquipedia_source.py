from datetime import UTC, datetime

from crawler.liquipedia.source import LiquipediaSource
from crawler.models import PageSpec


class FakeClient:
    def __init__(self, html: str) -> None:
        self._html = html
        self.calls: list[tuple[str, str]] = []

    def fetch_page_html(self, game: str, title: str) -> str:
        self.calls.append((game, title))
        return self._html


def test_fetch_returns_raw_page_with_html_and_url():
    client = FakeClient(html="<div>NAVI</div>")
    source = LiquipediaSource(client=client)
    spec = PageSpec(game="cs2", category="teams", title="Natus Vincere", slug="navi", tags=["team"])

    raw_page = source.fetch(spec)

    assert raw_page.html == "<div>NAVI</div>"
    assert raw_page.url == "https://liquipedia.net/counterstrike/Natus_Vincere"
    assert client.calls == [("cs2", "Natus Vincere")]


def test_fetch_sets_retrieved_at_close_to_now():
    client = FakeClient(html="<div>x</div>")
    source = LiquipediaSource(client=client)
    spec = PageSpec(game="cs2", category="maps", title="Inferno")

    before = datetime.now(UTC)
    raw_page = source.fetch(spec)
    after = datetime.now(UTC)

    assert before <= raw_page.retrieved_at <= after
