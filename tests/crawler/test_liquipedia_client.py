import httpx
import pytest

from crawler.exceptions import PageNotFoundError, SourceUnavailableError
from crawler.liquipedia.client import GAME_WIKI_MAP, LiquipediaApiClient


class NoOpRateLimiter:
    def wait(self) -> None:
        pass


def make_client(handler) -> LiquipediaApiClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return LiquipediaApiClient(
        http_client=http_client,
        rate_limiter=NoOpRateLimiter(),
        user_agent="esports-wiki-ai/0.1 (test)",
    )


def test_game_wiki_map_covers_all_v1_games():
    assert set(GAME_WIKI_MAP) == {"cs2", "dota2", "lol", "valorant"}


def test_fetch_page_html_returns_text_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/counterstrike/api.php"
        assert request.url.params["page"] == "Natus Vincere"
        assert request.url.params["redirects"] == "1"
        assert request.headers["User-Agent"] == "esports-wiki-ai/0.1 (test)"
        return httpx.Response(
            200,
            json={
                "parse": {
                    "title": "Natus Vincere",
                    "pageid": 19687,
                    "text": {"*": "<div>NAVI</div>"},
                }
            },
        )

    client = make_client(handler)

    html = client.fetch_page_html("cs2", "Natus Vincere")

    assert html == "<div>NAVI</div>"


def test_fetch_page_html_raises_page_not_found_on_missingtitle():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": {"code": "missingtitle", "info": "no such page"}})

    client = make_client(handler)

    with pytest.raises(PageNotFoundError):
        client.fetch_page_html("cs2", "Not A Real Page")


def test_fetch_page_html_raises_source_unavailable_on_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    client = make_client(handler)

    with pytest.raises(SourceUnavailableError):
        client.fetch_page_html("cs2", "Natus Vincere")


def test_fetch_page_html_waits_via_rate_limiter():
    waits: list[int] = []

    class RecordingRateLimiter:
        def wait(self) -> None:
            waits.append(1)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"parse": {"text": {"*": "<div>ok</div>"}}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = LiquipediaApiClient(
        http_client=http_client, rate_limiter=RecordingRateLimiter(), user_agent="ua"
    )

    client.fetch_page_html("cs2", "Inferno")

    assert waits == [1]
