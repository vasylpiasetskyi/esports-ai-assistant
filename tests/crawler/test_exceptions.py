from crawler.exceptions import CrawlerError, PageNotFoundError, SourceUnavailableError


def test_page_not_found_is_a_crawler_error():
    assert issubclass(PageNotFoundError, CrawlerError)


def test_source_unavailable_is_a_crawler_error():
    assert issubclass(SourceUnavailableError, CrawlerError)
