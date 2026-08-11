import logging
from dataclasses import dataclass, field

from crawler.base import ContentParser, Source
from crawler.exceptions import CrawlerError
from crawler.models import PageSpec, RawArticle
from crawler.writer import JsonArticleWriter

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    succeeded: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


class CrawlPipeline:
    def __init__(self, source: Source, parser: ContentParser, writer: JsonArticleWriter) -> None:
        self._source = source
        self._parser = parser
        self._writer = writer

    def run(self, specs: list[PageSpec]) -> CrawlResult:
        result = CrawlResult()
        for spec in specs:
            try:
                raw_page = self._source.fetch(spec)
                content = self._parser.extract(raw_page)
                article = RawArticle(
                    title=spec.title,
                    game=spec.game,
                    category=spec.category,
                    url=raw_page.url,
                    content=content,
                    updated_at=raw_page.retrieved_at,
                    tags=spec.tags,
                )
                self._writer.save(article, slug=spec.slug)
                result.succeeded.append(spec.title)
            except CrawlerError as error:
                logger.warning("Failed to crawl %r: %s", spec.title, error)
                result.failed.append((spec.title, str(error)))
        return result
