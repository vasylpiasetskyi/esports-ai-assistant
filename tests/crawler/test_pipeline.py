from datetime import UTC, datetime

from crawler.exceptions import PageNotFoundError
from crawler.models import PageSpec, RawArticle, RawPage
from crawler.pipeline import CrawlPipeline


class FakeSource:
    def __init__(self, pages=None, raises=None):
        self._pages = pages or {}
        self._raises = raises or {}

    def fetch(self, spec: PageSpec) -> RawPage:
        if spec.title in self._raises:
            raise self._raises[spec.title]
        return self._pages[spec.title]


class FakeParser:
    def extract(self, raw_page: RawPage) -> str:
        return raw_page.html.upper()


class FakeWriter:
    def __init__(self) -> None:
        self.saved: list[tuple[RawArticle, str]] = []

    def save(self, article: RawArticle, slug: str):
        self.saved.append((article, slug))


def _raw_page(html: str) -> RawPage:
    return RawPage(html=html, url="https://example.test/page", retrieved_at=datetime.now(UTC))


def test_run_saves_article_for_each_successful_spec():
    spec = PageSpec(game="cs2", category="teams", title="Natus Vincere", slug="navi", tags=["team"])
    source = FakeSource(pages={"Natus Vincere": _raw_page("<p>navi</p>")})
    writer = FakeWriter()
    pipeline = CrawlPipeline(source=source, parser=FakeParser(), writer=writer)

    result = pipeline.run([spec])

    assert result.succeeded == ["Natus Vincere"]
    assert result.failed == []
    assert len(writer.saved) == 1
    saved_article, saved_slug = writer.saved[0]
    assert saved_article.content == "<P>NAVI</P>"
    assert saved_slug == "navi"


def test_run_continues_after_a_failed_spec():
    good_spec = PageSpec(game="cs2", category="maps", title="Inferno", slug="inferno")
    bad_spec = PageSpec(game="cs2", category="teams", title="Ghost Team", slug="ghost")
    source = FakeSource(
        pages={"Inferno": _raw_page("<p>map</p>")},
        raises={"Ghost Team": PageNotFoundError("missing")},
    )
    writer = FakeWriter()
    pipeline = CrawlPipeline(source=source, parser=FakeParser(), writer=writer)

    result = pipeline.run([bad_spec, good_spec])

    assert result.succeeded == ["Inferno"]
    assert len(result.failed) == 1
    assert result.failed[0][0] == "Ghost Team"
    assert len(writer.saved) == 1
