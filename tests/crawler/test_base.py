from datetime import UTC, datetime

from crawler.base import ContentParser, Source
from crawler.models import PageSpec, RawPage


class FakeSource:
    def fetch(self, spec: PageSpec) -> RawPage:
        return RawPage(
            html="<p>ok</p>",
            url="https://example.test",
            retrieved_at=datetime.now(UTC),
        )


class FakeParser:
    def extract(self, raw_page: RawPage) -> str:
        return "ok"


class NotASource:
    pass


def test_fake_source_satisfies_source_protocol():
    assert isinstance(FakeSource(), Source)


def test_fake_parser_satisfies_content_parser_protocol():
    assert isinstance(FakeParser(), ContentParser)


def test_unrelated_class_does_not_satisfy_source_protocol():
    assert not isinstance(NotASource(), Source)
