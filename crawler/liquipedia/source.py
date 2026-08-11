from datetime import UTC, datetime

from crawler.liquipedia.client import GAME_WIKI_MAP, LiquipediaApiClient
from crawler.models import PageSpec, RawPage


class LiquipediaSource:
    def __init__(self, client: LiquipediaApiClient) -> None:
        self._client = client

    def fetch(self, spec: PageSpec) -> RawPage:
        html = self._client.fetch_page_html(spec.game, spec.title)
        wiki = GAME_WIKI_MAP[spec.game]
        url = f"https://liquipedia.net/{wiki}/{spec.title.replace(' ', '_')}"
        return RawPage(html=html, url=url, retrieved_at=datetime.now(UTC))
