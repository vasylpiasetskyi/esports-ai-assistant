from typing import Protocol, runtime_checkable

from crawler.models import PageSpec, RawPage


@runtime_checkable
class Source(Protocol):
    def fetch(self, spec: PageSpec) -> RawPage: ...


@runtime_checkable
class ContentParser(Protocol):
    def extract(self, raw_page: RawPage) -> str: ...
