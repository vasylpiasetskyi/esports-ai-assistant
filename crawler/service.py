import logging
import time
from pathlib import Path

import httpx

from crawler.config import load_page_specs
from crawler.liquipedia.client import LiquipediaApiClient
from crawler.liquipedia.rate_limiter import RateLimiter
from crawler.liquipedia.source import LiquipediaSource
from crawler.parser import MediaWikiHtmlParser
from crawler.pipeline import CrawlPipeline, CrawlResult
from crawler.writer import JsonArticleWriter

CONFIG_PATH = Path("config/pages.json")
DATA_DIR = Path("data/raw")
USER_AGENT = "esports-wiki-ai/0.1 (learning project; contact: fatbrain@databet.space)"

logger = logging.getLogger(__name__)


def build_pipeline(http_client: httpx.Client, base_dir: Path = DATA_DIR) -> CrawlPipeline:
    rate_limiter = RateLimiter(min_interval_seconds=2.0, clock=time.monotonic, sleep_fn=time.sleep)
    api_client = LiquipediaApiClient(
        http_client=http_client, rate_limiter=rate_limiter, user_agent=USER_AGENT
    )
    source = LiquipediaSource(client=api_client)
    parser = MediaWikiHtmlParser()
    writer = JsonArticleWriter(base_dir=base_dir)
    return CrawlPipeline(source=source, parser=parser, writer=writer)


def run_crawl(
    config_path: Path | None = None,
    base_dir: Path | None = None,
    http_client: httpx.Client | None = None,
) -> CrawlResult:
    resolved_config_path = config_path if config_path is not None else CONFIG_PATH
    resolved_base_dir = base_dir if base_dir is not None else DATA_DIR
    specs = load_page_specs(resolved_config_path)
    owns_client = http_client is None
    client = http_client or httpx.Client()
    try:
        pipeline = build_pipeline(client, base_dir=resolved_base_dir)
        result = pipeline.run(specs)
    finally:
        if owns_client:
            client.close()
    logger.info("Crawled %d pages successfully", len(result.succeeded))
    for title, error in result.failed:
        logger.warning("Failed: %s (%s)", title, error)
    return result
