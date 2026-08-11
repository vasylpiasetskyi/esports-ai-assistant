import httpx

from crawler.exceptions import PageNotFoundError, SourceUnavailableError
from crawler.liquipedia.rate_limiter import RateLimiter

GAME_WIKI_MAP: dict[str, str] = {
    "cs2": "counterstrike",
    "dota2": "dota2",
    "lol": "leagueoflegends",
    "valorant": "valorant",
}


class LiquipediaApiClient:
    def __init__(
        self,
        http_client: httpx.Client,
        rate_limiter: RateLimiter,
        user_agent: str,
    ) -> None:
        self._http_client = http_client
        self._rate_limiter = rate_limiter
        self._user_agent = user_agent

    def fetch_page_html(self, game: str, title: str) -> str:
        wiki = GAME_WIKI_MAP[game]
        self._rate_limiter.wait()
        response = self._http_client.get(
            f"https://liquipedia.net/{wiki}/api.php",
            params={
                "action": "parse",
                "page": title,
                "format": "json",
                "prop": "text",
                "redirects": 1,
            },
            headers={"User-Agent": self._user_agent},
        )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"Liquipedia returned {response.status_code} for {title!r}"
            )
        payload = response.json()
        if "error" in payload:
            error_code = payload["error"].get("code")
            if error_code == "missingtitle":
                raise PageNotFoundError(f"Page {title!r} does not exist on the {wiki} wiki")
            raise SourceUnavailableError(f"Liquipedia API error {error_code!r} for {title!r}")
        return payload["parse"]["text"]["*"]
